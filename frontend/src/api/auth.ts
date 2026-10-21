import { apiClient } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  SwitchOrganizationRequest,
  SwitchOrganizationResponse,
  Token,
  UserWithOrganizations,
  OrganizationMember,
} from '@/types/auth'

export const authApi = {
  async login(data: LoginRequest): Promise<Token> {
    return apiClient.post<Token>('/auth/login', data)
  },

  async logout(): Promise<void> {
    await apiClient.post<void>('/auth/logout')
  },

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    return apiClient.post<RegisterResponse>('/auth/register', data)
  },

  async getMe(): Promise<UserWithOrganizations> {
    return apiClient.get<UserWithOrganizations>('/auth/me')
  },

  async switchOrganization(data: SwitchOrganizationRequest): Promise<SwitchOrganizationResponse> {
    return apiClient.post<SwitchOrganizationResponse>('/auth/switch-organization', data)
  },

  async getOrganizationMembers(orgId: string): Promise<OrganizationMember[]> {
    return apiClient.get<OrganizationMember[]>(`/auth/organizations/${orgId}/members`)
  },
}

export const healthApi = {
  async health(): Promise<{ status: string; version: string; environment: string; database: string; redis: string }> {
    return apiClient.get('/health')
  },

  async ready(): Promise<{ ready: boolean; checks: Record<string, string> }> {
    return apiClient.get('/ready')
  },
}
