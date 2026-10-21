export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login_at: string | null
}

export interface Organization {
  id: string
  name: string
  slug: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface OrganizationMember {
  id: string
  user_id: string
  organization_id: string
  role: 'admin' | 'member' | 'viewer'
  user: User
  created_at: string
  updated_at: string
}

export interface Token {
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
  organization_name: string
  organization_slug: string
}

export interface RegisterResponse {
  user: User
  organization: Organization
  token: Token
}

export interface SwitchOrganizationRequest {
  organization_id: string
}

export interface SwitchOrganizationResponse {
  token: Token
  organization: Organization
}

export interface UserWithOrganizations extends User {
  organizations: Organization[]
}
