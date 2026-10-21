import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import String, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index, DateTime, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, OrganizationModel


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Workflow(BaseModel):
    __tablename__ = "workflows"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus, name="workflow_status", native_enum=False),
        default=WorkflowStatus.DRAFT,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_template: Mapped[bool] = mapped_column(default=False, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship()
    created_by: Mapped[Optional["User"]] = relationship()
    versions: Mapped[List["WorkflowVersion"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    executions: Mapped[List["WorkflowExecution"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_org_status", "organization_id", "status"),
        Index("ix_workflow_org_created", "organization_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, status={self.status})>"


class WorkflowVersion(BaseModel):
    __tablename__ = "workflow_versions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nodes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)

    workflow: Mapped["Workflow"] = relationship(back_populates="versions")
    created_by: Mapped[Optional["User"]] = relationship()

    __table_args__ = (
        UniqueConstraint("workflow_id", "version", name="uq_workflow_version"),
        Index("ix_workflow_version_workflow", "workflow_id", "version"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowVersion(workflow_id={self.workflow_id}, version={self.version})>"


class WorkflowExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(WorkflowExecutionStatus, name="workflow_execution_status", native_enum=False),
        default=WorkflowExecutionStatus.PENDING,
        nullable=False,
    )
    trigger_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
    )

    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    version: Mapped[Optional["WorkflowVersion"]] = relationship()
    node_executions: Mapped[List["NodeExecution"]] = relationship(back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_execution_org_status", "organization_id", "status"),
        Index("ix_execution_workflow", "workflow_id", "started_at"),
        Index("ix_execution_idempotency", "idempotency_key"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class NodeExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class NodeExecution(BaseModel):
    __tablename__ = "node_executions"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        SQLEnum(NodeExecutionStatus, name="node_execution_status", native_enum=False),
        default=NodeExecutionStatus.PENDING,
        nullable=False,
    )
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    execution: Mapped["WorkflowExecution"] = relationship(back_populates="node_executions")

    __table_args__ = (
        Index("ix_node_execution_exec_node", "execution_id", "node_id"),
        Index("ix_node_execution_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<NodeExecution(execution_id={self.execution_id}, node_id={self.node_id}, status={self.status})>"


class ScheduledJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledJob(BaseModel):
    __tablename__ = "scheduled_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    run_once_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(ScheduledJobStatus, name="scheduled_job_status", native_enum=False),
        default=ScheduledJobStatus.PENDING,
        nullable=False,
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_runs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    organization: Mapped["Organization"] = relationship()
    workflow: Mapped["Workflow"] = relationship()

    __table_args__ = (
        Index("ix_scheduled_job_next_run", "next_run_at"),
        Index("ix_scheduled_job_org_active", "organization_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ScheduledJob(id={self.id}, name={self.name}, status={self.status})>"