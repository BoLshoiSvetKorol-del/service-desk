import client from './client'
import type { Priority } from '../types/ticket'

export async function getPriorities(): Promise<Priority[]> {
  const res = await client.get<Priority[]>('/priorities')
  return res.data
}
