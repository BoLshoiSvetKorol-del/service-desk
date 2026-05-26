import client from './client'

export interface RatingData {
  id: number
  ticket_id: number
  rating: number
  comment: string | null
  created_at: string
}

export async function submitRating(
  ticketId: number,
  rating: number,
  comment?: string,
): Promise<RatingData> {
  const res = await client.post<RatingData>(`/tickets/${ticketId}/rating`, { rating, comment: comment || null })
  return res.data
}

export async function getRating(ticketId: number): Promise<RatingData | null> {
  const res = await client.get<RatingData | null>(`/tickets/${ticketId}/rating`)
  return res.data
}
