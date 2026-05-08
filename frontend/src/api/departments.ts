import client from './client'
import { Department } from '../types/user'

export async function getDepartments(): Promise<Department[]> {
  const res = await client.get<Department[]>('/departments')
  return res.data
}

export async function createDepartment(data: { name: string; description?: string }): Promise<Department> {
  const res = await client.post<Department>('/departments', data)
  return res.data
}

export async function updateDepartment(id: number, data: { name?: string; description?: string }): Promise<Department> {
  const res = await client.put<Department>(`/departments/${id}`, data)
  return res.data
}

export async function deleteDepartment(id: number): Promise<void> {
  await client.delete(`/departments/${id}`)
}
