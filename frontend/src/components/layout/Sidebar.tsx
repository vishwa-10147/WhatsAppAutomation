import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  GitBranch,
  Users,
  MessageSquare,
  Send,
  Settings,
  Zap,
  Database,
  BarChart2,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  { name: 'Contacts', href: '/contacts', icon: Users },
  { name: 'Inbox', href: '/inbox', icon: MessageSquare },
  { name: 'Campaigns', href: '/campaigns', icon: Send },
  { name: 'Automations', href: '/automations', icon: Zap },
  { name: 'Integrations', href: '/integrations', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: BarChart2 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const { user, organizations, currentOrganization, switchOrganization } = useAuth()

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-card transition-all duration-200">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <MessageSquare className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold">WhatsApp Automation</span>
        </div>

        <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )
              }
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="border-t p-4">
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Organization
            </p>
            <div className="relative">
              <select
                value={currentOrganization?.id || ''}
                onChange={(e) => {
                  const org = organizations.find((o) => o.id === e.target.value)
                  if (org) switchOrganization(org)
                }}
                className="flex h-10 w-full appearance-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {user && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
                  <span className="text-sm font-medium text-primary-foreground">
                    {user.full_name?.[0] || user.email[0].toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{user.full_name || user.email}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
