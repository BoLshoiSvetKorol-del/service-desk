import client from './client'
import type { SavedFilter, TicketFilters } from '../types/ticket'

export async function getSavedFilters(): Promise<SavedFilter[]> {
  const res = await client.get<SavedFilter[]>('/filters')
  return res.data
}

export async function createSavedFilter(name: string, filter_params: TicketFilters): Promise<SavedFilter> {
  const res = await client.post<SavedFilter>('/filters', { name, filter_params })
  return res.data
}

export async function deleteSavedFilter(id: number): Promise<void> {
  await client.delete(`/filters/${id}`)
}
