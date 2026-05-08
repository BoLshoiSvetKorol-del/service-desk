import client, { setAuthTokens, clearAuthTokens } from './client'
import { User } from '../types/user'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export async function login(data: LoginRequest): Promise<{ tokens: TokenResponse; user: User }> {
  const tokensRes = await client.post<TokenResponse>('/auth/login', data)
  const tokens = tokensRes.data
  setAuthTokens(tokens.access_token, tokens.refresh_token)

  const userRes = await client.get<User>('/users/me')
  return { tokens, user: userRes.data }
}

export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem('refreshToken')
  try {
    if (refreshToken) await client.post('/auth/logout', { refresh_token: refreshToken })
  } finally {
    clearAuthTokens()
  }
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/users/me')
  return res.data
}
