import React, { useState, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  NodeTypes,
  EdgeTypes,
  addEdge,
  Connection,
  Edge,
  Node,
  MarkerType,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  NodeProps,
  EdgeProps,
  ConnectionMode,
} from '@xyflow/react';
import { Save, Play, Pause, Copy, Trash2, Plus, Minus, Download, Upload } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Label } from '@/components/ui/Label';
import { Separator } from '@/components/ui/Separator';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/Dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/Tooltip';
import { Tooltip } from '@/components/ui/Tooltip';
import { cn } from '@/lib/utils';
import { useWorkflows } from '@/hooks/useWorkflows';
import { WorkflowNode, WorkflowEdge } from '@/types/workflow';

const NODE_TYPES = {
  trigger_message: 'Message Received',
  trigger_keyword: 'Keyword Match',
  trigger_webhook: 'Webhook Received',
  trigger_schedule: 'Scheduled',
  trigger_manual: 'Manual Trigger',
  condition_keyword: 'Keyword Check',
  condition_segment: 'Segment Check',
  condition_time: 'Time Check',
  condition_api: 'API Response',
  condition_previous: 'Previous Result',
  action_send_text: 'Send Text',
  action_send_template: 'Send Template',
  action_send_media: 'Send Media',
  action_wait: 'Wait',
  action_http: 'HTTP Request',
  action_branch: 'Branch',
  action_update_contact: 'Update Contact',
  action_create_task: 'Create Task',
  action_ai: 'AI Assistant',
  action_end: 'End Flow',
};

const NODE_CATEGORIES = {
  triggers: [
    'trigger_message',
    'trigger_keyword',
    'trigger_webhook',
    'trigger_schedule',
    'trigger_manual',
  ],
  conditions: [
    'condition_keyword',
    'condition_segment',
    'condition_time',
    'condition_api',
    'condition_previous',
  ],
  actions: [
    'action_send_text',
    'action_send_template',
    'action_send_media',
    'action_wait',
    'action_http',
    'action_branch',
    'action_update_contact',
    'action_create_task',
    'action_ai',
    'action_end',
  ],
};

const NODE_COLORS = {
  triggers: 'bg-green-500',
  conditions: 'bg-blue-500',
  actions: 'bg-purple-500',
};

const initialNodes: WorkflowNode[] = [
  {
    id: '1',
    type: 'trigger_message',
    position: { x: 250, y: 50 },
    data: { label: 'Message Received', config: {} },
  },
];

const initialEdges: WorkflowEdge[] = [];

// Custom node components
const TriggerNode = ({ data }: NodeProps<WorkflowNode['data']>) => (
  <div className="bg-green-100 border-2 border-green-500 rounded-lg px-3 py-2 min-w-[140px] text-center">
    <Handle type="target" position={Position.Top} className="bg-green-500" />
    <div className="font-medium text-green-900">{data.label}</div>
    <Handle type="source" position={Position.Bottom} className="bg-green-500" />
  </div>
);

const ConditionNode = ({ data }: NodeProps<WorkflowNode['data']>) => (
  <div className="bg-blue-100 border-2 border-blue-500 rounded-lg px-3 py-2 min-w-[140px] text-center">
    <Handle type="target" position={Position.Top} className="bg-blue-500" />
    <div className="font-medium text-blue-900">{data.label}</div>
    <Handle type="source" position={Position.Bottom} className="bg-blue-500" />
  </div>
);

const ActionNode = ({ data }: NodeProps<WorkflowNode['data']>) => (
  <div className="bg-purple-100 border-2 border-purple-500 rounded-lg px-3 py-2 min-w-[140px] text-center">
    <Handle type="target" position={Position.Top} className="bg-purple-500" />
    <div className="font-medium text-purple-900">{data.label}</div>
    <Handle type="source" position={Position.Bottom} className="bg-purple-500" />
  </div>
);

const EndNode = ({ data }: NodeProps<WorkflowNode['data']>) => (
  <div className="bg-gray-100 border-2 border-gray-500 rounded-lg px-3 py-2 min-w-[140px] text-center">
    <Handle type="target" position={Position.Top} className="bg-gray-500" />
    <div className="font-medium text-gray-900">{data.label}</div>
  </div>
);

const nodeTypes: NodeTypes = {
  trigger_message: TriggerNode,
  trigger_keyword: TriggerNode,
  trigger_webhook: TriggerNode,
  trigger_schedule: TriggerNode,
  trigger_manual: TriggerNode,
  condition_keyword: ConditionNode,
  condition_segment: ConditionNode,
  condition_time: ConditionNode,
  condition_api: ConditionNode,
  condition_previous: ConditionNode,
  action_send_text: ActionNode,
  action_send_template: ActionNode,
  action_send_media: ActionNode,
  action_wait: ActionNode,
  action_http: ActionNode,
  action_branch: ActionNode,
  action_update_contact: ActionNode,
  action_create_task: ActionNode,
  action_ai: ActionNode,
  action_end: EndNode,
};

const edgeTypes: EdgeTypes = {
  default: (props: EdgeProps) => (
    <Edge
      {...props}
      markerEnd={MarkerType.ArrowClosed}
      style={{ strokeWidth: 2 }}
      animated={true}
    />
  ),
  true: (props: EdgeProps) => (
    <Edge
      {...props}
      markerEnd={MarkerType.ArrowClosed}
      style={{ strokeWidth: 2, stroke: '#22c55e' }}
      animated={true}
      label="Yes"
      labelStyle={{ fill: '#22c55e', fontSize: 10 }}
      labelBgStyle={{ fill: 'white', padding: 2 }}
      labelBgBorderRadius={2}
      labelBgPadding={[2, 4]}
    />
  ),
  false: (props: EdgeProps) => (
    <Edge
      {...props}
      markerEnd={MarkerType.ArrowClosed}
      style={{ strokeWidth: 2, stroke: '#ef4444' }}
      animated={true}
      label="No"
      labelStyle={{ fill: '#ef4444', fontSize: 10 }}
      labelBgStyle={{ fill: 'white', padding: 2 }}
      labelBgBorderRadius={2}
      labelBgPadding={[2, 4]}
    />
  ),
};

function NodePalette() {
  return (
    <div className="w-64 bg-card border-r p-4 overflow-y-auto">
      <h3 className="font-semibold mb-4">Node Palette</h3>
      <div className="space-y-3">
        {Object.entries(NODE_CATEGORIES).map(([category, types]) => (
          <div key={category} className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </h4>
            <div className="space-y-1">
              {types.map((type) => (
                <div
                  key={type}
                  className={cn(
                    'p-2 rounded-lg cursor-grab hover:shadow-md transition-shadow',
                    NODE_COLORS[category as keyof typeof NODE_COLORS] + '/10 border border-current/20'
                  )}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData('application/reactflow', JSON.stringify({
                      type,
                      data: { label: NODE_TYPES[type] || type, config: {} },
                    }));
                  }}
                >
                  <span className={cn('text-xs font-medium', NODE_COLORS[category as keyof typeof NODE_COLORS])}>
                    {NODE_TYPES[type] || type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NodeConfigPanel({ node, onUpdate, onClose }: { node: WorkflowNode | null; onUpdate: (id: string, data: Partial<WorkflowNode['data']>) => void; onClose: () => void }) {
  if (!node) return null;

  return (
    <div className="w-80 bg-card border-l p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Configure Node</h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">×</button>
      </div>
      <div className="space-y-4">
        <div>
          <Label>Node Label</Label>
          <Input
            value={node.data?.label || ''}
            onChange={(e) => onUpdate(node.id, { ...node.data, label: e.target.value })}
          />
        </div>
        <div>
          <Label>Node Type</Label>
          <Input value={NODE_TYPES[node.type as keyof typeof NODE_TYPES] || node.type} readOnly />
        </div>
        <Separator />
        <div>
          <Label>Configuration</Label>
          <div className="space-y-2">
            {Object.entries(node.data?.config || {}).map(([key, value]) => (
              <div key={key} className="flex gap-2">
                <Input
                  value={key}
                  readOnly
                  className="w-1/3 bg-muted"
                />
                <Input
                  value={JSON.stringify(value)}
                  onChange={(e) => {
                    const newConfig = { ...node.data.config, [key]: JSON.parse(e.target.value) };
                    onUpdate(node.id, { ...node.data, config: newConfig });
                  }}
                />
              </div>
            ))}
            <Button variant="outline" size="sm" onClick={() => {
              const newConfig = { ...node.data.config, [`config_${Date.now()}`]: '' };
              onUpdate(node.id, { ...node.data, config: newConfig });
            }}>
              <Plus className="mr-1 h-3 w-3" /> Add Config
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function WorkflowEditorPage() {
  const { workflows, createWorkflow, updateWorkflow, getWorkflow } = useWorkflows();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [activeTab, setActiveTab] = useState('editor');
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge({ ...params, type: 'default', animated: true }, eds));
    setIsDirty(true);
  }, []);

  const onNodeClick = useCallback((_, node: Node) => {
    const workflowNode = nodes.find(n => n.id === node.id);
    if (workflowNode) {
      setSelectedNode(workflowNode);
      setShowConfig(true);
    }
  }, [nodes]);

  const onNodeDragStop = useCallback((_, node: Node) => {
    const workflowNode = nodes.find(n => n.id === node.id);
    if (workflowNode && (workflowNode.position.x !== node.position.x || workflowNode.position.y !== node.position.y)) {
      setNodes((nds) => nds.map(n => n.id === node.id ? { ...n, position: node.position } : n));
      setIsDirty(true);
    }
  }, [nodes]);

  const onEdgeTypeChange = useCallback((edgeId: string, type: string) => {
    setEdges((eds) => eds.map(e => e.id === edgeId ? { ...e, type } : e));
    setIsDirty(true);
  }, []);

  const addNodeFromPalette = useCallback((type: string) => {
    const newNode: WorkflowNode = {
      id: `${type}_${Date.now()}`,
      type,
      position: { x: 250, y: 250 },
      data: { label: NODE_TYPES[type as keyof typeof NODE_TYPES] || type, config: {} },
    };
    setNodes((nds) => [...nds, newNode]);
    setIsDirty(true);
  }, []);

  const handleNodeUpdate = useCallback((id: string, data: Partial<WorkflowNode['data']>) => {
    setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, ...data } } : n));
    setSelectedNode(nds => nds.find(n => n.id === id) || null);
    setIsDirty(true);
  }, []);

  const saveWorkflow = async () => {
    setIsSaving(true);
    try {
      if (currentWorkflowId) {
        await updateWorkflow(currentWorkflowId, {
          name: workflowName,
          description: workflowDescription,
          nodes,
          edges,
        });
      } else {
        const result = await createWorkflow({
          name: workflowName,
          description: workflowDescription,
          nodes,
          edges,
        });
        setCurrentWorkflowId(result.id);
      }
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to save workflow:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const loadWorkflow = async (id: string) => {
    try {
      const wf = await getWorkflow(id);
      setCurrentWorkflowId(wf.id);
      setWorkflowName(wf.name);
      setWorkflowDescription(wf.description || '');
      setNodes(wf.nodes || initialNodes);
      setEdges(wf.edges || initialEdges);
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to load workflow:', error);
    }
  };

  const handleNodeDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    try {
      const data = JSON.parse(event.dataTransfer.getData('application/reactflow'));
      const reactFlowInstance = event.currentTarget._reactFlowInstance;
      if (reactFlowInstance) {
        const position = reactFlowInstance.project({
          x: event.clientX,
          y: event.clientY,
        });
        const newNode: WorkflowNode = {
          id: `${data.type}_${Date.now()}`,
          type: data.type,
          position,
          data: data.data,
        };
        setNodes((nds) => [...nds, newNode]);
        setIsDirty(true);
      }
    } catch (e) {
      console.error('Failed to add node from palette:', e);
    }
  }, []);

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col bg-background">
        {/* Top Bar */}
        <div className="flex items-center justify-between border-b bg-card px-4 py-3">
          <div className="flex items-center gap-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="hidden md:flex">
              <TabsList>
                <TabsTrigger value="editor">Editor</TabsTrigger>
                <TabsTrigger value="versions">Versions</TabsTrigger>
                <TabsTrigger value="executions">Executions</TabsTrigger>
              </TabsList>
            </Tabs>
            <Input
              value={workflowName}
              onChange={(e) => { setWorkflowName(e.target.value); setIsDirty(true); }}
              placeholder="Workflow name"
              className="w-64"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => {
              // Download workflow as JSON
              const data = JSON.stringify({ nodes, edges, name: workflowName, description: workflowDescription }, null, 2);
              const blob = new Blob([data], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${workflowName}.json`;
              a.click();
            }}>
              <Download className="h-4 w-4 mr-1" /> Export
            </Button>
            <Button variant="outline" size="sm" onClick={saveWorkflow} disabled={isSaving || !isDirty}>
              {isSaving ? <span className="animate-spin">⟳</span> : <Save className="h-4 w-4 mr-1" />} Save
            </Button>
            <Button size="sm" onClick={() => { /* Test run */ }}>
              <Play className="h-4 w-4 mr-1" /> Test
            </Button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Left Palette */}
          <div className="w-64 border-r bg-card flex-shrink-0" onDrop={handleNodeDrop} onDragOver={(e) => e.preventDefault()}>
            <NodePalette />
          </div>

          {/* Center Canvas */}
          <div className="flex-1 relative overflow-hidden" onDrop={handleNodeDrop} onDragOver={(e) => e.preventDefault()}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onNodeDragStop={onNodeDragStop}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              fitView
              defaultViewport={{ x: 0, y: 0, zoom: 1 }}
              connectionMode={ConnectionMode.Loose}
              deleteKey="Backspace"
              proOptions={{ hideAttribution: true }}
              onInit={(instance) => {
                (event.currentTarget as any)._reactFlowInstance = instance;
              }}
            >
              <Background color="#e5e7eb" gap={16} />
              <Controls />
              <MiniMap />
            </ReactFlow>
            
            {/* Node Config Panel */}
            {showConfig && selectedNode && (
              <div className="absolute right-0 top-0 bottom-0 w-80 bg-card border-l shadow-xl z-10">
                <NodeConfigPanel
                  node={selectedNode}
                  onUpdate={handleNodeUpdate}
                  onClose={() => setShowConfig(false)}
                />
              </div>
            )}
          </div>

          {/* Right Sidebar - Workflow List */}
          <div className="w-80 border-l bg-card flex-shrink-0 overflow-y-auto">
            <div className="p-4 border-b">
              <h3 className="font-semibold">Workflows</h3>
            </div>
            <div className="p-4 space-y-2">
              {workflows.map((wf) => (
                <div
                  key={wf.id}
                  className={cn(
                    'p-3 rounded-lg cursor-pointer transition-colors',
                    currentWorkflowId === wf.id
                      ? 'bg-primary/10 border border-primary'
                      : 'hover:bg-accent'
                  )}
                  onClick={() => loadWorkflow(wf.id)}
                >
                  <div className="font-medium">{wf.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {wf.status} • v{wf.version} • {wf.updated_at}
                  </div>
                </div>
              ))}
              <Button variant="outline" className="w-full mt-4" onClick={() => {
                setCurrentWorkflowId(null);
                setWorkflowName('New Workflow');
                setWorkflowDescription('');
                setNodes(initialNodes);
                setEdges(initialEdges);
                setIsDirty(false);
              }}>
                <Plus className="mr-1 h-4 w-4" /> New Workflow
              </Button>
            </div>
          </div>
        </div>

        {/* Node Config Sidebar */}
        {showConfig && selectedNode && (
          <div className="w-80 border-l bg-card">
            <NodeConfigPanel
              node={selectedNode}
              onUpdate={handleNodeUpdate}
              onClose={() => setShowConfig(false)}
            />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}