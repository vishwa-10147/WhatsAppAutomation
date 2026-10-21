import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { authApi } from '@/api/auth'
import type { LoginRequest, RegisterRequest, SwitchOrganizationRequest } from '@/types/auth'

export { useAuth } from './useAuthContext'

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: () => {
      apiClient.sessionStarted()
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useRegister() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: () => {
      apiClient.sessionStarted()
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => authApi.getMe(),
    enabled: apiClient.hasSession(),
    retry: false,
  })
}

export function useSwitchOrganization() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SwitchOrganizationRequest) => authApi.switchOrganization(data),
    onSuccess: () => {
      apiClient.sessionStarted()
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return () => {
    apiClient.clearToken()
    queryClient.clear()
  }
}
