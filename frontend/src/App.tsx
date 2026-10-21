import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/hooks/useAuthContext'
import { ThemeProvider } from '@/hooks/useTheme'
import { MainLayout } from '@/components/layout/MainLayout'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { WorkflowsPage } from '@/features/workflows/WorkflowsPage'
import { ContactsPage } from '@/features/contacts/ContactsPage'
import { InboxPage } from '@/features/inbox/InboxPage'
import { CampaignsPage } from '@/features/campaigns/CampaignsPage'
import { AutomationsPage } from '@/features/automations/AutomationsPage'
import { IntegrationsPage } from '@/features/integrations/IntegrationsPage'
import { AnalyticsPage } from '@/features/analytics/AnalyticsPage'
import { SettingsPage } from '@/features/settings/SettingsPage'
import { useAuth } from '@/hooks/useAuth'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="workflows" element={<WorkflowsPage />} />
            <Route path="contacts" element={<ContactsPage />} />
            <Route path="inbox" element={<InboxPage />} />
            <Route path="campaigns" element={<CampaignsPage />} />
            <Route path="automations" element={<AutomationsPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  )
}