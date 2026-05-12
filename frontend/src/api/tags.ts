import client from './client'

export interface Tag {
  id: number
  name: string
  color_hex: string
  created_at: string
}

export async function getTags(): Promise<Tag[]> {
  const res = await client.get<Tag[]>('/tags')
  return res.data
}

export async function createTag(name: string, color_hex: string = '#1677ff'): Promise<Tag> {
  const res = await client.post<Tag>('/tags', { name, color_hex })
  return res.data
}

export async function deleteTag(id: number): Promise<void> {
  await client.delete(`/tags/${id}`)
}

export async function setTicketTags(ticketId: number, tag_ids: number[]): Promise<Tag[]> {
  const res = await client.put<Tag[]>(`/tags/tickets/${ticketId}/tags`, { tag_ids })
  return res.data
}
