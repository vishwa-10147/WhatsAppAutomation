import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { apiClient } from '@/api/client'
import { authApi } from '@/api/auth'
import type { UserWithOrganizations, Organization } from '@/types/auth'

interface AuthContextType {
  user: UserWithOrganizations | null
  organizations: Organization[]
  currentOrganization: Organization | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name?: string; organization_name: string; organization_slug: string }) => Promise<void>
  logout: () => void
  switchOrganization: (org: Organization) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserWithOrganizations | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!apiClient.hasSession()) {
      setIsLoading(false)
      return
    }

    try {
      const userData = await authApi.getMe()
      setUser(userData)
      setOrganizations(userData.organizations)
      const currentOrgId = localStorage.getItem('current_organization_id')
      if (currentOrgId) {
        const org = userData.organizations.find((o) => o.id === currentOrgId)
        if (org) setCurrentOrganization(org)
      } else if (userData.organizations.length > 0) {
        setCurrentOrganization(userData.organizations[0])
        localStorage.setItem('current_organization_id', userData.organizations[0].id)
      }
    } catch (error) {
      apiClient.clearToken()
      setUser(null)
      setOrganizations([])
      setCurrentOrganization(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    await authApi.login({ email, password })
    apiClient.sessionStarted()
    await refreshUser()
  }

  const register = async (data: { email: string; password: string; full_name?: string; organization_name: string; organization_slug: string }) => {
    await authApi.register(data)
    apiClient.sessionStarted()
    await refreshUser()
  }

  const logout = () => {
    void authApi.logout().catch(() => undefined)
    apiClient.clearToken()
    setUser(null)
    setOrganizations([])
    setCurrentOrganization(null)
  }

  const switchOrganization = async (org: Organization) => {
    await authApi.switchOrganization({ organization_id: org.id })
    apiClient.sessionStarted()
    setCurrentOrganization(org)
    localStorage.setItem('current_organization_id', org.id)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        currentOrganization,
        isLoading,
        login,
        register,
        logout,
        switchOrganization,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
