export type TicketStatus = 'new' | 'in_progress' | 'waiting_info' | 'resolved' | 'cancelled' | 'merged'
export type PriorityName = 'low' | 'normal' | 'high' | 'critical'

export interface Priority {
  id: number
  name: PriorityName
  sla_hours: number
  color_hex: string
}

export interface Attachment {
  id: number
  ticket_id: number
  comment_id: number | null
  original_filename: string
  stored_path: string
  size_bytes: number
  mimetype: string
  uploaded_by: number
  uploader_name: string | null
  url: string
  created_at: string
}

export interface Comment {
  id: number
  ticket_id: number
  author_id: number | null
  author_name: string | null
  author_role: string | null
  body: string
  is_internal: boolean
  created_at: string
  updated_at: string
  attachments?: Attachment[]
}

export interface Tag {
  id: number
  name: string
  color_hex: string
  created_at: string
}

export interface TicketListItem {
  id: number
  number: string
  title: string
  status: TicketStatus
  priority: Priority
  ticket_type_id: number | null
  ticket_type_name: string | null
  department_id: number | null
  department_name: string | null
  assignee_id: number | null
  assignee_name: string | null
  creator_id: number
  creator_name: string
  sla_deadline: string | null
  sla_violated: boolean
  created_at: string
  updated_at: string
  tags: Tag[]
}

export interface Ticket extends TicketListItem {
  description: string
  sla_paused_at: string | null
  sla_extra_minutes: number
  closed_at: string | null
  merged_into_id: number | null
  attachments?: Attachment[]
}

export interface TicketCreateRequest {
  title: string
  description: string
  type_id: number
  priority_id?: number
  department_id?: number | null
}

export interface TicketUpdateRequest {
  title?: string
  description?: string
}

export interface StatusChangeRequest {
  status: TicketStatus
}

export interface AssignRequest {
  department_id?: number | null
  assignee_id?: number | null
}

export interface TicketHistory {
  id: number
  ticket_id: number
  user_id: number | null
  user_name: string | null
  event_type: string
  payload: Record<string, unknown>
  created_at: string
}

export interface TicketFilters {
  status?: string
  priority_id?: number
  type_id?: number
  department_id?: number
  assignee_id?: number
  sla_violated?: boolean
  search?: string
  date_from?: string
  date_to?: string
  sort_by?: string
  page?: number
  page_size?: number
}

export interface SavedFilter {
  id: number
  user_id: number
  name: string
  filter_params: TicketFilters
  created_at: string
}

export const STATUS_TRANSITIONS: Record<TicketStatus, TicketStatus[]> = {
  new: ['in_progress', 'cancelled'],
  in_progress: ['waiting_info', 'resolved', 'cancelled'],
  waiting_info: ['in_progress', 'resolved', 'cancelled'],
  resolved: ['in_progress'],
  cancelled: [],
  merged: [],
}

// Переходы, доступные только user/admin (не agent)
export const STATUS_TRANSITIONS_USER_ONLY: TicketStatus[] = ['in_progress']

export const STATUS_TRANSITIONS_FROM_RESOLVED: TicketStatus[] = ['in_progress']

export const STATUS_LABELS: Record<TicketStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  waiting_info: 'Ожидает информации',
  resolved: 'Выполнена',
  cancelled: 'Отменена',
  merged: 'Объединена',
}

export const PRIORITY_LABELS: Record<PriorityName, string> = {
  low: 'Низкий',
  normal: 'Нормальный',
  high: 'Высокий',
  critical: 'Критичный',
}
