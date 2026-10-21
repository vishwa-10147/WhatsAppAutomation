import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type {
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  WorkflowVersion,
  WorkflowExecution,
  NodeExecution,
  ScheduledJob,
  ScheduledJobCreate,
} from '@/types/workflow';

export function useWorkflows() {
  const queryClient = useQueryClient();

  const { data: workflows, isLoading, refetch } = useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await apiClient.get<Workflow[]>('/workflows');
      return response;
    },
  });

  const createWorkflow = useMutation({
    mutationFn: (data: WorkflowCreate) => apiClient.post<Workflow>('/workflows', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const updateWorkflow = useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkflowUpdate }) =>
      apiClient.patch<Workflow>(`/workflows/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const deleteWorkflow = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/workflows/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const getWorkflow = async (id: string) => {
    return apiClient.get<Workflow>(`/workflows/${id}`);
  };

  const createVersion = useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: { name: string; description?: string; nodes: any[]; edges: any[]; variables?: any } }) =>
      apiClient.post<WorkflowVersion>(`/workflows/${workflowId}/versions`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const publishVersion = useMutation({
    mutationFn: ({ workflowId, versionId }: { workflowId: string; versionId: string }) =>
      apiClient.post(`/workflows/${workflowId}/versions/${versionId}/publish`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const executeWorkflow = useMutation({
    mutationFn: ({ workflowId, data }: { workflowId: string; data: { trigger_data: any; idempotency_key?: string } }) =>
      apiClient.post<WorkflowExecution>(`/workflows/${workflowId}/execute`, data),
  });

  const getWorkflowExecutions = useQuery({
    queryKey: ['workflow-executions', 'workflowId'],
    queryFn: async ({ queryKey }) => {
      const [, workflowId] = queryKey;
      return apiClient.get<WorkflowExecution[]>(`/workflows/${workflowId}/executions`);
    },
    enabled: false,
  });

  const getExecution = async (id: string) => {
    return apiClient.get<WorkflowExecution>(`/workflows/executions/${id}`);
  };

  const getExecutionNodes = async (id: string) => {
    return apiClient.get<any[]>(`/workflows/executions/${id}/nodes`);
  };

  const createScheduledJob = useMutation({
    mutationFn: (data: ScheduledJobCreate) => apiClient.post(`/workflows/scheduled-jobs`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
  });

  const listScheduledJobs = useQuery({
    queryKey: ['scheduled-jobs'],
    queryFn: () => apiClient.get<any[]>('/workflows/scheduled-jobs'),
  });

  const deleteScheduledJob = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/workflows/scheduled-jobs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
  });

  return {
    workflows: workflows || [],
    isLoading,
    refetch,
    createWorkflow: createWorkflow.mutateAsync,
    updateWorkflow: updateWorkflow.mutateAsync,
    deleteWorkflow: deleteWorkflow.mutateAsync,
    getWorkflow,
    createVersion: createVersion.mutateAsync,
    publishVersion: publishVersion.mutateAsync,
    executeWorkflow: executeWorkflow.mutateAsync,
    getWorkflowExecutions,
    getExecution,
    getExecutionNodes,
    createScheduledJob: createScheduledJob.mutateAsync,
    listScheduledJobs: listScheduledJobs.data || [],
    deleteScheduledJob: deleteScheduledJob.mutateAsync,
  };
}