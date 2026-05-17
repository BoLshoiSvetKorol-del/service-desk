export type UserRole = 'admin' | 'department_head' | 'agent' | 'user'

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: UserRole
  department_id: number | null
  phone: string | null
  contact_info: string | null
  is_active: boolean
  is_email_verified: boolean
  created_at: string
  updated_at?: string
}

export interface Department {
  id: number
  name: string
  description: string | null
  created_at: string
}

export interface TicketType {
  id: number
  name: string
  service_type: string | null
  work_direction: string | null
  default_department_id: number | null
  is_active: boolean
}
