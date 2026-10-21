import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { healthApi } from '@/api/auth'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { CheckCircle, XCircle, Database, Server, Activity, TrendingUp, GitBranch, Users, Settings, Send } from 'lucide-react'
import { cn } from '@/lib/utils'

export function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.health(),
    refetchInterval: 30000,
  })

  const { data: ready, isLoading: readyLoading } = useQuery({
    queryKey: ['ready'],
    queryFn: () => healthApi.ready(),
    refetchInterval: 30000,
  })

  const statusItems = [
    { label: 'API Status', status: health?.status === 'alive', icon: Activity, description: 'Process liveness check' },
    { label: 'Database', status: ready?.checks.database === 'ok', icon: Database, description: 'PostgreSQL readiness check' },
    { label: 'Queue', status: ready?.checks.redis === 'ok', icon: Server, description: 'Redis readiness check' },
    { label: 'Readiness', status: ready?.ready, icon: TrendingUp, description: 'Required service checks' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your WhatsApp Automation platform status and key metrics.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statusItems.map((item) => (
          <Card key={item.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{item.label}</CardTitle>
              <item.icon
                className={cn('h-4 w-4', item.status ? 'text-green-500' : 'text-destructive')}
                aria-hidden="true"
              />
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {item.status ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-destructive" />
                )}
                <span className={cn('text-2xl font-bold', item.status ? 'text-green-500' : 'text-destructive')}>
                  {item.status ? 'Ready' : (healthLoading || readyLoading) ? 'Checking' : 'Unavailable'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Messaging activity</CardTitle>
          <CardDescription>Production metrics appear here when message and workflow records are available.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No messaging metrics are available yet. Configure a WhatsApp Business account after the integration milestone is complete.</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to get started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link to="/workflows" className="p-4 rounded-lg border hover:bg-accent transition-colors">
              <GitBranch className="h-6 w-6 text-primary mb-2" />
              <h3 className="font-medium">Create Workflow</h3>
              <p className="text-sm text-muted-foreground mt-1">Build your first automation</p>
            </Link>
            <Link to="/contacts" className="p-4 rounded-lg border hover:bg-accent transition-colors">
              <Users className="h-6 w-6 text-primary mb-2" />
              <h3 className="font-medium">Add Contacts</h3>
              <p className="text-sm text-muted-foreground mt-1">Import or add contacts</p>
            </Link>
            <Link to="/integrations" className="p-4 rounded-lg border hover:bg-accent transition-colors">
              <Settings className="h-6 w-6 text-primary mb-2" />
              <h3 className="font-medium">Configure WhatsApp</h3>
              <p className="text-sm text-muted-foreground mt-1">Set up your WhatsApp account</p>
            </Link>
            <Link to="/campaigns" className="p-4 rounded-lg border hover:bg-accent transition-colors">
              <Send className="h-6 w-6 text-primary mb-2" />
              <h3 className="font-medium">Create Campaign</h3>
              <p className="text-sm text-muted-foreground mt-1">Send template messages</p>
            </Link>
          </div>
        </CardContent>
      </Card>

      {(healthLoading || readyLoading) && (
        <div className="fixed bottom-4 right-4 bg-muted p-2 rounded text-sm text-muted-foreground">
          Loading system status...
        </div>
      )}
    </div>
  )
}
