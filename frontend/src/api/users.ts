import client from './client'
import { User } from '../types/user'
import { PagedResponse } from '../types/common'

export interface UserCreateRequest {
  username: string
  email: string
  password: string
  full_name: string
  role: string
  department_id?: number | null
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
  role?: string
  department_id?: number | null
}

export async function getUsers(params?: Record<string, unknown>): Promise<PagedResponse<User>> {
  const res = await client.get<PagedResponse<User>>('/users', { params })
  return res.data
}

export async function createUser(data: UserCreateRequest): Promise<User> {
  const res = await client.post<User>('/users', data)
  return res.data
}

export async function updateUser(id: number, data: UserUpdateRequest): Promise<User> {
  const res = await client.put<User>(`/users/${id}`, data)
  return res.data
}

export async function toggleUserActive(id: number, is_active: boolean): Promise<User> {
  const res = await client.patch<User>(`/users/${id}/activate`, { is_active })
  return res.data
}
