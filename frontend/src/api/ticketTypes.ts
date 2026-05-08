import client from './client'
import { TicketType } from '../types/user'

export async function getTicketTypes(): Promise<TicketType[]> {
  const res = await client.get<TicketType[]>('/ticket-types')
  return res.data
}

export async function createTicketType(data: {
  name: string
  service_type?: string
  work_direction?: string
  default_department_id?: number | null
}): Promise<TicketType> {
  const res = await client.post<TicketType>('/ticket-types', data)
  return res.data
}

export async function updateTicketType(id: number, data: {
  name?: string
  service_type?: string
  work_direction?: string
  default_department_id?: number | null
  is_active?: boolean
}): Promise<TicketType> {
  const res = await client.put<TicketType>(`/ticket-types/${id}`, data)
  return res.data
}

export async function deleteTicketType(id: number): Promise<void> {
  await client.delete(`/ticket-types/${id}`)
}
