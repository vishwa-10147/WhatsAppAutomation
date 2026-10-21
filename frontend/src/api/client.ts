import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance
  private sessionAvailable = true

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
      withCredentials: true,
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  sessionStarted() {
    this.sessionAvailable = true
  }

  clearToken() {
    this.sessionAvailable = false
    localStorage.removeItem('current_organization_id')
  }

  loadToken() {
    this.sessionAvailable = true
  }

  hasSession(): boolean {
    return this.sessionAvailable
  }

  async get<T>(url: string, params?: Record<string, unknown>) {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: unknown) {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async put<T>(url: string, data?: unknown) {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: unknown) {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string) {
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new ApiClient()

apiClient.loadToken()
