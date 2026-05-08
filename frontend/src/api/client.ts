import axios, { AxiosRequestConfig } from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Добавляем access token к каждому запросу
client.interceptors.request.use((config) => {
  const { accessToken } = useAuthTokens()
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// При 401 — пробуем обновить токен и повторить запрос
let isRefreshing = false
let pendingQueue: Array<{ resolve: (t: string) => void; reject: (e: unknown) => void }> = []

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original: AxiosRequestConfig & { _retry?: boolean } = error.config

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    original._retry = true

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject })
      }).then((token) => {
        original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
        return client(original)
      })
    }

    isRefreshing = true

    try {
      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) throw new Error('No refresh token')

      const res = await axios.post<{ access_token: string; refresh_token: string }>(
        '/api/v1/auth/refresh',
        { refresh_token: refreshToken },
      )
      const { access_token, refresh_token } = res.data

      setAuthTokens(access_token, refresh_token)
      pendingQueue.forEach(({ resolve }) => resolve(access_token))

      original.headers = { ...original.headers, Authorization: `Bearer ${access_token}` }
      return client(original)
    } catch (refreshError) {
      pendingQueue.forEach(({ reject }) => reject(refreshError))
      clearAuthTokens()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
      pendingQueue = []
    }
  },
)

// Простое in-memory хранилище токенов (не Zustand, чтобы избежать circular imports)
let _accessToken: string | null = null

function useAuthTokens() {
  return { accessToken: _accessToken }
}

export function setAuthTokens(accessToken: string, refreshToken: string) {
  _accessToken = accessToken
  localStorage.setItem('refreshToken', refreshToken)
}

export function clearAuthTokens() {
  _accessToken = null
  localStorage.removeItem('refreshToken')
}

export function getAccessToken() {
  return _accessToken
}

export default client
