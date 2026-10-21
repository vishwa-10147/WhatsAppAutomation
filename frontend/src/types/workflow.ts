export interface WorkflowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: {
    label: string
    config: Record<string, any>
  }
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  type?: string
}

export interface Workflow {
  id: string
  name: string
  description: string | null
  status: string
  version: number
  is_template: boolean
  variables: Record<string, any> | null
  created_at: string
  updated_at: string
  created_by_id: string | null
}

export interface WorkflowDetail extends Workflow {
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface WorkflowVersion {
  id: string
  workflow_id: string
  version: number
  name: string
  description: string | null
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  variables: Record<string, any> | null
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface WorkflowExecution {
  id: string
  workflow_id: string
  version_id: string | null
  status: string
  trigger_type: string | null
  trigger_data: Record<string, any> | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
}

export interface NodeExecution {
  id: string
  execution_id: string
  node_id: string
  node_type: string
  status: string
  input_data: Record<string, any> | null
  output_data: Record<string, any> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

export interface ScheduledJob {
  id: string
  workflow_id: string
  name: string
  cron_expression: string | null
  run_once_at: string | null
  timezone: string
  trigger_data: Record<string, any> | null
  status: string
  next_run_at: string | null
  last_run_at: string | null
  run_count: number
  max_runs: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ScheduledJobCreate {
  workflow_id: string
  name: string
  cron_expression?: string
  run_once_at?: string
  timezone: string
  trigger_data?: Record<string, any>
  max_runs?: number
}