import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { cn } from '@/lib/utils'

export function MainLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className={cn('lg:pl-64', 'transition-all duration-200')}>
        <Header />
        <main className="p-4 lg:p-6" role="main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}