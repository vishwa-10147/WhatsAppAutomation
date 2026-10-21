import { Link } from 'react-router-dom'
import { Bell, LogOut, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'

export function Header() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const initial = user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur">
      <div className="flex-1" />
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </Button>
      <Button variant="ghost" size="icon" aria-label="Notifications" disabled>
        <Bell className="h-5 w-5" />
      </Button>
      <details className="relative">
        <summary className="flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-full bg-primary font-medium text-primary-foreground">
          {initial}
        </summary>
        <div className="absolute right-0 z-50 mt-2 w-56 rounded-md border bg-popover p-2 text-popover-foreground shadow-lg">
          <p className="px-2 py-1 text-sm font-medium">{user?.full_name || 'User'}</p>
          <p className="px-2 pb-2 text-xs text-muted-foreground">{user?.email}</p>
          <Link className="block rounded px-2 py-2 text-sm hover:bg-accent" to="/settings">Settings</Link>
          <button
            className="flex w-full items-center gap-2 rounded px-2 py-2 text-left text-sm text-destructive hover:bg-accent"
            onClick={logout}
            type="button"
          >
            <LogOut className="h-4 w-4" /> Log out
          </button>
        </div>
      </details>
    </header>
  )
}
