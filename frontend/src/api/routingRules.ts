import client from './client'

export interface RoutingRule {
  id: number
  name: string
  keywords: string | null
  ticket_type_id: number | null
  department_id: number
  assignee_id: number | null
  priority: number
  is_active: boolean
  created_at: string
  department: { id: number; name: string }
  ticket_type: { id: number; name: string } | null
  assignee: { id: number; full_name: string } | null
}

export interface RoutingTestResult {
  matched: boolean
  rule_id: number | null
  rule_name: string | null
  department_id: number | null
  department_name: string | null
  assignee_id: number | null
  assignee_name: string | null
  fallback_used: boolean
}

export async function getRoutingRules(): Promise<RoutingRule[]> {
  const res = await client.get<RoutingRule[]>('/routing-rules')
  return res.data
}

export async function createRoutingRule(data: {
  name: string
  keywords?: string | null
  ticket_type_id?: number | null
  department_id: number
  assignee_id?: number | null
  priority?: number
  is_active?: boolean
}): Promise<RoutingRule> {
  const res = await client.post<RoutingRule>('/routing-rules', data)
  return res.data
}

export async function updateRoutingRule(id: number, data: {
  name?: string
  keywords?: string | null
  ticket_type_id?: number | null
  department_id?: number
  assignee_id?: number | null
  priority?: number
  is_active?: boolean
}): Promise<RoutingRule> {
  const res = await client.put<RoutingRule>(`/routing-rules/${id}`, data)
  return res.data
}

export async function deleteRoutingRule(id: number): Promise<void> {
  await client.delete(`/routing-rules/${id}`)
}

export async function testRouting(data: {
  title: string
  description?: string
  type_id?: number | null
}): Promise<RoutingTestResult> {
  const res = await client.post<RoutingTestResult>('/routing-rules/test', data)
  return res.data
}
