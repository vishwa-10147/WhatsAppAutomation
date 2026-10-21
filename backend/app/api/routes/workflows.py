from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.api.routes.auth import get_current_org_id
from app.models import Workflow, WorkflowVersion, WorkflowExecution, NodeExecution, ScheduledJob
from app.services.workflow_engine import WorkflowEngine
from app.core.logging import get_logger

logger = get_logger("workflow.api")

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ==================== SCHEMAS ====================

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    data: dict = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    type: str = "default"


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: Optional[dict] = None
    is_template: bool = False


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    variables: Optional[dict] = None
    status: Optional[str] = None
    is_template: Optional[bool] = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    version: int
    is_template: bool
    variables: Optional[dict]
    created_at: str
    updated_at: str
    created_by_id: Optional[UUID]

    class Config:
        from_attributes = True


class WorkflowDetailResponse(WorkflowResponse):
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []


class WorkflowVersionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: Optional[dict] = None


class WorkflowVersionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    version: int
    name: str
    description: Optional[str]
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    variables: Optional[dict]
    is_published: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class WorkflowExecuteRequest(BaseModel):
    trigger_data: dict = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class WorkflowExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    version_id: Optional[UUID]
    status: str
    trigger_type: Optional[str]
    trigger_data: Optional[dict]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class NodeExecutionResponse(BaseModel):
    id: UUID
    execution_id: UUID
    node_id: str
    node_type: str
    status: str
    input_data: Optional[dict]
    output_data: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True


class ScheduledJobCreate(BaseModel):
    workflow_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    cron_expression: Optional[str] = None
    run_once_at: Optional[str] = None
    timezone: str = "UTC"
    trigger_data: Optional[dict] = None
    max_runs: Optional[int] = None


class ScheduledJobResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    cron_expression: Optional[str]
    run_once_at: Optional[str]
    timezone: str
    trigger_data: Optional[dict]
    status: str
    next_run_at: Optional[str]
    last_run_at: Optional[str]
    run_count: int
    max_runs: Optional[int]
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ==================== WORKFLOW CRUD ====================

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    # Validate workflow
    engine = WorkflowEngine(session, UUID(org_id))
    errors = engine.validate_workflow(
        [n.model_dump() for n in data.nodes],
        [e.model_dump() for e in data.edges],
    )
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    workflow = Workflow(
        organization_id=UUID(org_id),
        name=data.name,
        description=data.description,
        status="draft",
        version=1,
        is_template=data.is_template,
        variables=data.variables,
    )
    session.add(workflow)
    await session.flush()

    # Create initial version
    wf_version = WorkflowVersion(
        workflow_id=workflow.id,
        version=1,
        name=data.name,
        description=data.description,
        nodes=[n.model_dump() for n in data.nodes],
        edges=[e.model_dump() for e in data.edges],
        variables=data.variables,
        is_published=False,
    )
    session.add(wf_version)
    await session.commit()
    await session.refresh(workflow)

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        version=workflow.version,
        is_template=workflow.is_template,
        variables=workflow.variables,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        created_by_id=workflow.created_by_id,
    )


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    from uuid import UUID

    query = select(Workflow).where(Workflow.organization_id == UUID(org_id))
    if status_filter:
        query = query.where(Workflow.status == status_filter)
    query = query.order_by(desc(Workflow.updated_at)).limit(limit).offset(offset)

    result = await session.execute(query)
    workflows = result.scalars().all()

    return [
        WorkflowResponse(
            id=w.id,
            name=w.name,
            description=w.description,
            status=w.status,
            version=w.version,
            is_template=w.is_template,
            variables=w.variables,
            created_at=w.created_at.isoformat(),
            updated_at=w.updated_at.isoformat(),
            created_by_id=w.created_by_id,
        )
        for w in workflows
    ]


# ==================== SCHEDULED JOBS ====================

@router.post("/scheduled-jobs", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_job(
    data: ScheduledJobCreate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    engine = WorkflowEngine(session, UUID(org_id))
    job = await engine.create_scheduled_job(
        workflow_id=data.workflow_id,
        name=data.name,
        cron_expression=data.cron_expression,
        run_once_at=datetime.fromisoformat(data.run_once_at) if data.run_once_at else None,
        timezone=data.timezone,
        trigger_data=data.trigger_data,
        max_runs=data.max_runs,
    )

    return ScheduledJobResponse(
        id=job.id,
        workflow_id=job.workflow_id,
        name=job.name,
        cron_expression=job.cron_expression,
        run_once_at=job.run_once_at.isoformat() if job.run_once_at else None,
        timezone=job.timezone,
        trigger_data=job.trigger_data,
        status=job.status,
        next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
        last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
        run_count=job.run_count,
        max_runs=job.max_runs,
        is_active=job.is_active,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@router.get("/scheduled-jobs", response_model=List[ScheduledJobResponse])
async def list_scheduled_jobs(
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
    active_only: bool = Query(True),
):
    from uuid import UUID

    query = select(ScheduledJob).where(ScheduledJob.organization_id == UUID(org_id))
    if active_only:
        query = query.where(ScheduledJob.is_active == True)
    query = query.order_by(desc(ScheduledJob.created_at))

    result = await session.execute(query)
    jobs = result.scalars().all()

    return [
        ScheduledJobResponse(
            id=j.id,
            workflow_id=j.workflow_id,
            name=j.name,
            cron_expression=j.cron_expression,
            run_once_at=j.run_once_at.isoformat() if j.run_once_at else None,
            timezone=j.timezone,
            trigger_data=j.trigger_data,
            status=j.status,
            next_run_at=j.next_run_at.isoformat() if j.next_run_at else None,
            last_run_at=j.last_run_at.isoformat() if j.last_run_at else None,
            run_count=j.run_count,
            max_runs=j.max_runs,
            is_active=j.is_active,
            created_at=j.created_at.isoformat(),
            updated_at=j.updated_at.isoformat(),
        )
        for j in jobs
    ]


@router.delete("/scheduled-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_job(
    job_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(ScheduledJob).where(
            and_(
                ScheduledJob.id == job_id,
                ScheduledJob.organization_id == UUID(org_id),
            )
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")

    await session.delete(job)
    await session.commit()


@router.get("/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow(
    workflow_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.organization_id == UUID(org_id),
            )
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get latest version
    version_result = await session.execute(
        select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id
        ).order_by(desc(WorkflowVersion.version)).limit(1)
    )
    version = version_result.scalar_one_or_none()

    return WorkflowDetailResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        version=workflow.version,
        is_template=workflow.is_template,
        variables=workflow.variables,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        created_by_id=workflow.created_by_id,
        nodes=[WorkflowNode(**n) for n in (version.nodes if version else [])],
        edges=[WorkflowEdge(**e) for e in (version.edges if version else [])],
    )


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.organization_id == UUID(org_id),
            )
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if data.name is not None:
        workflow.name = data.name
    if data.description is not None:
        workflow.description = data.description
    if data.status is not None:
        workflow.status = data.status
    if data.is_template is not None:
        workflow.is_template = data.is_template
    if data.variables is not None:
        workflow.variables = data.variables

    await session.commit()
    await session.refresh(workflow)

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        version=workflow.version,
        is_template=workflow.is_template,
        variables=workflow.variables,
        created_at=workflow.created_at.isoformat(),
        updated_at=workflow.updated_at.isoformat(),
        created_by_id=workflow.created_by_id,
    )


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.organization_id == UUID(org_id),
            )
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    await session.delete(workflow)
    await session.commit()


# ==================== VERSIONS ====================

@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_version(
    workflow_id: UUID,
    data: WorkflowVersionCreate,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    # Verify workflow exists
    result = await session.execute(
        select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.organization_id == UUID(org_id),
            )
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get next version number
    version_result = await session.execute(
        select(func.max(WorkflowVersion.version)).where(
            WorkflowVersion.workflow_id == workflow_id
        )
    )
    next_version = (version_result.scalar() or 0) + 1

    # Validate
    engine = WorkflowEngine(session, UUID(org_id))
    errors = engine.validate_workflow(
        [n.model_dump() for n in data.nodes],
        [e.model_dump() for e in data.edges],
    )
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    version = WorkflowVersion(
        workflow_id=workflow_id,
        version=next_version,
        name=data.name,
        description=data.description,
        nodes=[n.model_dump() for n in data.nodes],
        edges=[e.model_dump() for e in data.edges],
        variables=data.variables,
        is_published=False,
    )
    session.add(version)

    # Update workflow version
    workflow.version = next_version
    await session.commit()
    await session.refresh(version)

    return WorkflowVersionResponse(
        id=version.id,
        workflow_id=version.workflow_id,
        version=version.version,
        name=version.name,
        description=version.description,
        nodes=[WorkflowNode(**n) for n in version.nodes],
        edges=[WorkflowEdge(**e) for e in version.edges],
        variables=version.variables,
        is_published=version.is_published,
        created_at=version.created_at.isoformat(),
        updated_at=version.updated_at.isoformat(),
    )


@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionResponse])
async def list_workflow_versions(
    workflow_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.organization_id == UUID(org_id),
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")

    version_result = await session.execute(
        select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id
        ).order_by(desc(WorkflowVersion.version))
    )
    versions = version_result.scalars().all()

    return [
        WorkflowVersionResponse(
            id=v.id,
            workflow_id=v.workflow_id,
            version=v.version,
            name=v.name,
            description=v.description,
            nodes=[WorkflowNode(**n) for n in v.nodes],
            edges=[WorkflowEdge(**e) for e in v.edges],
            variables=v.variables,
            is_published=v.is_published,
            created_at=v.created_at.isoformat(),
            updated_at=v.updated_at.isoformat(),
        )
        for v in versions
    ]


@router.post("/{workflow_id}/versions/{version_id}/publish")
async def publish_workflow_version(
    workflow_id: UUID,
    version_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WorkflowVersion).where(
            and_(
                WorkflowVersion.id == version_id,
                WorkflowVersion.workflow_id == workflow_id,
            )
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Unpublish other versions
    from sqlalchemy import update
    await session.execute(
        update(WorkflowVersion).where(
            and_(
                WorkflowVersion.workflow_id == workflow_id,
                WorkflowVersion.is_published == True,
            )
        ).values(is_published=False)
    )

    version.is_published = True
    
    # Update workflow status
    workflow_result = await session.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = workflow_result.scalar_one_or_none()
    if workflow:
        workflow.status = "published"

    await session.commit()

    return {"status": "published"}


# ==================== EXECUTION ====================

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    data: WorkflowExecuteRequest,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    # Get published version
    version_result = await session.execute(
        select(WorkflowVersion).where(
            and_(
                WorkflowVersion.workflow_id == workflow_id,
                WorkflowVersion.is_published == True,
            )
        ).order_by(desc(WorkflowVersion.version)).limit(1)
    )
    version = version_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=400, detail="No published version found. Publish a version first.")

    engine = WorkflowEngine(session, UUID(org_id))
    try:
        execution = await engine.create_execution(
            workflow_id=workflow_id,
            version_id=version.id,
            trigger_type="manual",
            trigger_data=data.trigger_data,
            idempotency_key=data.idempotency_key,
        )
        await engine.start_execution(execution.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        version_id=execution.version_id,
        status=execution.status,
        trigger_type=execution.trigger_type,
        trigger_data=execution.trigger_data,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        error_message=execution.error_message,
        created_at=execution.created_at.isoformat(),
    )


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    from uuid import UUID

    result = await session.execute(
        select(WorkflowExecution).where(
            and_(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.organization_id == UUID(org_id),
            )
        ).order_by(desc(WorkflowExecution.created_at)).limit(limit).offset(offset)
    )
    executions = result.scalars().all()

    return [
        WorkflowExecutionResponse(
            id=e.id,
            workflow_id=e.workflow_id,
            version_id=e.version_id,
            status=e.status,
            trigger_type=e.trigger_type,
            trigger_data=e.trigger_data,
            started_at=e.started_at.isoformat() if e.started_at else None,
            completed_at=e.completed_at.isoformat() if e.completed_at else None,
            error_message=e.error_message,
            created_at=e.created_at.isoformat(),
        )
        for e in executions
    ]


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(WorkflowExecution).where(
            and_(
                WorkflowExecution.id == execution_id,
                WorkflowExecution.organization_id == UUID(org_id),
            )
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        version_id=execution.version_id,
        status=execution.status,
        trigger_type=execution.trigger_type,
        trigger_data=execution.trigger_data,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        error_message=execution.error_message,
        created_at=execution.created_at.isoformat(),
    )


@router.get("/executions/{execution_id}/nodes", response_model=List[NodeExecutionResponse])
async def get_execution_nodes(
    execution_id: UUID,
    org_id: str = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session),
):
    from uuid import UUID

    result = await session.execute(
        select(NodeExecution).where(
            and_(
                NodeExecution.execution_id == execution_id,
                NodeExecution.execution_id.in_(
                    select(WorkflowExecution.id).where(
                        and_(
                            WorkflowExecution.id == execution_id,
                            WorkflowExecution.organization_id == UUID(org_id),
                        )
                    )
                )
            )
        ).order_by(NodeExecution.started_at)
    )
    node_execs = result.scalars().all()

    return [
        NodeExecutionResponse(
            id=n.id,
            execution_id=n.execution_id,
            node_id=n.node_id,
            node_type=n.node_type,
            status=n.status,
            input_data=n.input_data,
            output_data=n.output_data,
            error_message=n.error_message,
            started_at=n.started_at.isoformat() if n.started_at else None,
            completed_at=n.completed_at.isoformat() if n.completed_at else None,
        )
        for n in node_execs
    ]


