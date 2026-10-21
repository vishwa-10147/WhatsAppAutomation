import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Workflow, WorkflowVersion, WorkflowExecution, NodeExecution,
    ScheduledJob, WorkflowStatus, WorkflowExecutionStatus, NodeExecutionStatus,
    ScheduledJobStatus
)
from app.services.whatsapp import WhatsAppService
from app.integrations.whatsapp.base import WhatsAppMessage, MessageType
from app.core.logging import get_logger

logger = get_logger("workflow.engine")


class NodeType(str, Enum):
    # Triggers
    TRIGGER_MESSAGE = "trigger_message"
    TRIGGER_KEYWORD = "trigger_keyword"
    TRIGGER_WEBHOOK = "trigger_webhook"
    TRIGGER_SCHEDULE = "trigger_schedule"
    TRIGGER_MANUAL = "trigger_manual"
    
    # Conditions
    CONDITION_KEYWORD = "condition_keyword"
    CONDITION_SEGMENT = "condition_segment"
    CONDITION_TIME = "condition_time"
    CONDITION_API = "condition_api"
    CONDITION_PREVIOUS = "condition_previous"
    
    # Actions
    ACTION_SEND_TEXT = "action_send_text"
    ACTION_SEND_TEMPLATE = "action_send_template"
    ACTION_SEND_MEDIA = "action_send_media"
    ACTION_WAIT = "action_wait"
    ACTION_HTTP = "action_http"
    ACTION_BRANCH = "action_branch"
    ACTION_UPDATE_CONTACT = "action_update_contact"
    ACTION_CREATE_TASK = "action_create_task"
    ACTION_AI = "action_ai"
    ACTION_END = "action_end"


class WorkflowValidationError(Exception):
    pass


class WorkflowEngine:
    def __init__(self, session: AsyncSession, organization_id: UUID):
        self.session = session
        self.organization_id = organization_id
        self.whatsapp_service: Optional[WhatsAppService] = None

    async def _get_whatsapp_service(self) -> WhatsAppService:
        if self.whatsapp_service is None:
            self.whatsapp_service = WhatsAppService(self.session, self.organization_id)
        return self.whatsapp_service

    # ==================== VALIDATION ====================

    def validate_workflow(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        errors = []
        node_ids = {n["id"] for n in nodes}
        
        # Check for start node
        trigger_nodes = [n for n in nodes if n["type"].startswith("trigger_")]
        if len(trigger_nodes) == 0:
            errors.append("Workflow must have at least one trigger node")
        elif len(trigger_nodes) > 1:
            errors.append("Workflow can only have one trigger node")
        
        # Check node references
        for edge in edges:
            if edge["source"] not in node_ids:
                errors.append(f"Edge references unknown source node: {edge['source']}")
            if edge["target"] not in node_ids:
                errors.append(f"Edge references unknown target node: {edge['target']}")
        
        # Check for cycles (simple DFS)
        adj = {nid: [] for nid in node_ids}
        for edge in edges:
            adj[edge["source"]].append(edge["target"])
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        
        for node_id in node_ids:
            if node_id not in visited:
                if has_cycle(node_id):
                    errors.append("Workflow contains cycles")
                    break
        
        # Validate node configurations
        for node in nodes:
            node_errors = self._validate_node_config(node)
            errors.extend([f"Node {node['id']}: {e}" for e in node_errors])
        
        return errors

    def _validate_node_config(self, node: Dict) -> List[str]:
        errors = []
        config = node.get("config", {})
        node_type = node.get("type", "")
        
        if node_type == NodeType.TRIGGER_KEYWORD:
            if not config.get("keyword"):
                errors.append("Keyword trigger requires 'keyword' config")
        
        elif node_type == NodeType.ACTION_SEND_TEXT:
            if not config.get("text"):
                errors.append("Send text action requires 'text' config")
        
        elif node_type == NodeType.ACTION_SEND_TEMPLATE:
            if not config.get("template_name"):
                errors.append("Template action requires 'template_name' config")
            if not config.get("language_code"):
                errors.append("Template action requires 'language_code' config")
        
        elif node_type == NodeType.ACTION_WAIT:
            duration = config.get("duration_seconds")
            if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
                errors.append("Wait action requires positive 'duration_seconds' config")
        
        elif node_type == NodeType.ACTION_HTTP:
            if not config.get("url"):
                errors.append("HTTP action requires 'url' config")
            if not config.get("method"):
                errors.append("HTTP action requires 'method' config")
        
        elif node_type == NodeType.ACTION_BRANCH:
            if not config.get("condition"):
                errors.append("Branch action requires 'condition' config")
        
        return errors

    # ==================== EXECUTION ====================

    async def create_execution(
        self,
        workflow_id: UUID,
        version_id: UUID,
        trigger_type: str,
        trigger_data: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> WorkflowExecution:
        # Check idempotency
        if idempotency_key:
            existing = await self.session.execute(
                select(WorkflowExecution).where(
                    and_(
                        WorkflowExecution.organization_id == self.organization_id,
                        WorkflowExecution.idempotency_key == idempotency_key,
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Execution with this idempotency key already exists")

        # Get workflow version
        version = await self.session.get(WorkflowVersion, version_id)
        if not version or version.workflow_id != workflow_id:
            raise ValueError("Invalid workflow version")

        execution = WorkflowExecution(
            organization_id=self.organization_id,
            workflow_id=workflow_id,
            version_id=version_id,
            status=WorkflowExecutionStatus.PENDING,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            idempotency_key=idempotency_key,
        )
        self.session.add(execution)
        await self.session.flush()

        # Create node executions for all nodes
        nodes = version.nodes or []
        for node in nodes:
            node_exec = NodeExecution(
                execution_id=execution.id,
                node_id=node["id"],
                node_type=node["type"],
                status=NodeExecutionStatus.PENDING,
            )
            self.session.add(node_exec)

        await self.session.commit()
        return execution

    async def start_execution(self, execution_id: UUID) -> None:
        execution = await self.session.get(WorkflowExecution, execution_id)
        if not execution:
            raise ValueError("Execution not found")
        
        execution.status = WorkflowExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        await self.session.commit()
        
        # Start async processing
        asyncio.create_task(self._process_execution(execution.id))

    async def _process_execution(self, execution_id: UUID) -> None:
        from app.db.session import async_session_maker
        
        async with async_session_maker() as session:
            engine = WorkflowEngine(session, self.organization_id)
            await engine._execute_workflow(execution_id)

    async def _execute_workflow(self, execution_id: UUID) -> None:
        # Get execution with node executions
        result = await self.session.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if not execution:
            return

        # Get version and nodes
        version = await self.session.get(WorkflowVersion, execution.version_id)
        if not version:
            execution.status = WorkflowExecutionStatus.FAILED
            execution.error_message = "Workflow version not found"
            execution.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return

        nodes = {n["id"]: n for n in (version.nodes or [])}
        edges = version.edges or []

        # Build adjacency list
        adj = {nid: [] for nid in nodes}
        for edge in edges:
            adj[edge["source"]].append({"target": edge["target"], "source_handle": edge.get("sourceHandle")})

        # Find start node (trigger)
        start_nodes = [nid for nid, node in nodes.items() if node["type"].startswith("trigger_")]
        if not start_nodes:
            execution.status = WorkflowExecutionStatus.FAILED
            execution.error_message = "No trigger node found"
            execution.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return

        current_node_id = start_nodes[0]
        execution_context = {"trigger_data": execution.trigger_data}

        while current_node_id:
            node = nodes.get(current_node_id)
            if not node:
                break

            # Get or create node execution
            result = await self.session.execute(
                select(NodeExecution).where(
                    and_(
                        NodeExecution.execution_id == execution_id,
                        NodeExecution.node_id == current_node_id,
                    )
                )
            )
            node_exec = result.scalar_one_or_none()
            
            if not node_exec:
                node_exec = NodeExecution(
                    execution_id=execution_id,
                    node_id=current_node_id,
                    node_type=node["type"],
                    status=NodeExecutionStatus.PENDING,
                )
                self.session.add(node_exec)
                await self.session.flush()

            # Execute node
            try:
                node_exec.status = NodeExecutionStatus.RUNNING
                node_exec.started_at = datetime.now(timezone.utc)
                node_exec.input_data = execution_context.copy()
                await self.session.flush()

                output = await self._execute_node(node, execution_context, execution)
                
                node_exec.status = NodeExecutionStatus.COMPLETED
                node_exec.completed_at = datetime.now(timezone.utc)
                node_exec.output_data = output
                execution_context.update(output)

            except Exception as e:
                logger.error("node_execution_failed", execution_id=str(execution_id), node_id=current_node_id, error=str(e))
                node_exec.status = NodeExecutionStatus.FAILED
                node_exec.completed_at = datetime.now(timezone.utc)
                node_exec.error_message = str(e)
                
                execution.status = WorkflowExecutionStatus.FAILED
                execution.error_message = f"Node {current_node_id} failed: {str(e)}"
                execution.completed_at = datetime.now(timezone.utc)
                await self.session.commit()
                return

            await self.session.flush()

            # Determine next node
            next_nodes = adj.get(current_node_id, [])
            if not next_nodes:
                break
            
            # For branching, evaluate condition
            if len(next_nodes) > 1:
                current_node_id = self._evaluate_branch(node, next_nodes, execution_context)
            else:
                current_node_id = next_nodes[0]["target"]

        # Complete execution
        execution.status = WorkflowExecutionStatus.COMPLETED
        execution.completed_at = datetime.now(timezone.utc)
        await self.session.commit()

    async def _execute_node(self, node: Dict, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        node_type = node["type"]
        config = node.get("config", {})
        
        # Trigger nodes - already have context from trigger_data
        if node_type.startswith("trigger_"):
            return {"trigger_data": context.get("trigger_data", {})}
        
        # Condition nodes
        elif node_type == NodeType.CONDITION_KEYWORD:
            text = context.get("trigger_data", {}).get("text", "")
            keyword = config.get("keyword", "")
            result = keyword.lower() in text.lower()
            return {"condition_result": result}
        
        elif node_type == NodeType.CONDITION_PREVIOUS:
            # Check if previous node succeeded
            return {"condition_result": True}
        
        # Action nodes
        elif node_type == NodeType.ACTION_SEND_TEXT:
            return await self._action_send_text(config, context)
        
        elif node_type == NodeType.ACTION_SEND_TEMPLATE:
            return await self._action_send_template(config, context)
        
        elif node_type == NodeType.ACTION_WAIT:
            await asyncio.sleep(config.get("duration_seconds", 1))
            return {}
        
        elif node_type == NodeType.ACTION_HTTP:
            return await self._action_http(config, context)
        
        elif node_type == NodeType.ACTION_BRANCH:
            return {}
        
        elif node_type == NodeType.ACTION_AI:
            return await self._action_ai(config, context)
        
        elif node_type == NodeType.ACTION_END:
            return {}
        
        return {}

    async def _action_send_text(self, config: Dict, context: Dict) -> Dict[str, Any]:
        service = await self._get_whatsapp_service()
        to = config.get("to") or context.get("trigger_data", {}).get("from_number")
        text = config.get("text", "")
        
        if not to:
            raise ValueError("No recipient specified for send text action")
        
        result = await service.send_text_message(to, text)
        return {"message_id": result.message_id, "status": result.status.value}

    async def _action_send_template(self, config: Dict, context: Dict) -> Dict[str, Any]:
        service = await self._get_whatsapp_service()
        to = config.get("to") or context.get("trigger_data", {}).get("from_number")
        template_name = config.get("template_name")
        language_code = config.get("language_code", "en_US")
        components = config.get("components", [])
        
        if not to or not template_name:
            raise ValueError("Missing required template config")
        
        result = await service.send_template_message(to, template_name, language_code, components)
        return {"message_id": result.message_id, "status": result.status.value}

    async def _action_http(self, config: Dict, context: Dict) -> Dict[str, Any]:
        import httpx
        
        url = config.get("url")
        method = config.get("method", "GET")
        headers = config.get("headers", {})
        body = config.get("body")
        
        # Simple template interpolation
        if isinstance(body, str):
            for key, value in context.items():
                body = body.replace(f"{{{{{key}}}}}", str(value))
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, json=body if isinstance(body, dict) else None)
            return {"status_code": response.status_code, "body": response.text}

    async def _action_ai(self, config: Dict, context: Dict) -> Dict[str, Any]:
        # Placeholder for AI integration (Phase 5)
        return {"ai_response": "AI integration coming in Phase 5"}

    def _evaluate_branch(self, node: Dict, next_nodes: List[Dict], context: Dict) -> str:
        config = node.get("config", {})
        condition = config.get("condition", "true")
        
        # Simple condition evaluation
        # In production, use a safe expression evaluator
        try:
            # Replace context variables
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)):
                    condition = condition.replace(f"{{{{{key}}}}}", str(value))
            
            # Very basic eval - use proper library in production
            result = eval(condition, {"__builtins__": {}}, {})
            
            if result:
                # True branch - first edge
                return next_nodes[0]["target"]
            else:
                # False branch - second edge
                return next_nodes[1]["target"] if len(next_nodes) > 1 else next_nodes[0]["target"]
        except Exception:
            # Default to first edge on error
            return next_nodes[0]["target"]

    # ==================== SCHEDULED JOBS ====================

    async def create_scheduled_job(
        self,
        workflow_id: UUID,
        name: str,
        cron_expression: Optional[str] = None,
        run_once_at: Optional[datetime] = None,
        timezone: str = "UTC",
        trigger_data: Optional[Dict] = None,
        max_runs: Optional[int] = None,
    ) -> ScheduledJob:
        if not cron_expression and not run_once_at:
            raise ValueError("Either cron_expression or run_once_at required")
        
        job = ScheduledJob(
            organization_id=self.organization_id,
            workflow_id=workflow_id,
            name=name,
            cron_expression=cron_expression,
            run_once_at=run_once_at,
            timezone=timezone,
            trigger_data=trigger_data or {},
            status=ScheduledJobStatus.PENDING,
            next_run_at=run_once_at,
            max_runs=max_runs,
        )
        self.session.add(job)
        await self.session.commit()
        return job

    async def process_scheduled_jobs(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(ScheduledJob).where(
                and_(
                    ScheduledJob.organization_id == self.organization_id,
                    ScheduledJob.is_active == True,
                    ScheduledJob.status.in_([ScheduledJobStatus.PENDING, ScheduledJobStatus.RUNNING]),
                    or_(
                        and_(ScheduledJob.cron_expression.isnot(None), ScheduledJob.next_run_at <= now),
                        and_(ScheduledJob.run_once_at.isnot(None), ScheduledJob.run_once_at <= now),
                    ),
                )
            )
        )
        jobs = result.scalars().all()
        
        processed = 0
        for job in jobs:
            try:
                job.status = ScheduledJobStatus.RUNNING
                job.last_run_at = now
                job.run_count += 1
                
                # Create execution
                await self.create_execution(
                    workflow_id=job.workflow_id,
                    version_id=job.workflow_id,  # TODO: get latest published version
                    trigger_type="schedule",
                    trigger_data=job.trigger_data or {},
                )
                
                # Update next run
                if job.cron_expression:
                    job.next_run_at = self._calculate_next_cron(job.cron_expression, now)
                else:
                    job.status = ScheduledJobStatus.COMPLETED
                    job.is_active = False
                
                if job.max_runs and job.run_count >= job.max_runs:
                    job.status = ScheduledJobStatus.COMPLETED
                    job.is_active = False
                
                processed += 1
            except Exception as e:
                logger.error("scheduled_job_failed", job_id=str(job.id), error=str(e))
                job.status = ScheduledJobStatus.FAILED
            
            await self.session.commit()
        
        return processed

    def _calculate_next_cron(self, cron_expr: str, from_time: datetime) -> datetime:
        # Simplified - use croniter in production
        from datetime import timedelta
        return from_time + timedelta(minutes=5)