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

export async function logout(refreshToken?: string): Promise<void> {
  const token = refreshToken ?? localStorage.getItem('refreshToken') ?? undefined
  try {
    if (token) await client.post('/auth/logout', { refresh_token: token })
  } finally {
    clearAuthTokens()
  }
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export async function register(data: RegisterRequest): Promise<User> {
  const res = await client.post<User>('/auth/register', data)
  return res.data
}

export async function verifyEmail(token: string): Promise<User> {
  const res = await client.post<User>(`/auth/verify-email?token=${token}`)
  return res.data
}

export async function resendVerification(): Promise<void> {
  await client.post('/auth/resend-verification')
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/users/me')
  return res.data
}
