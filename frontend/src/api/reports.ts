import client from './client'

export interface ReportParams {
  date_from?: string
  date_to?: string
  department_id?: number
  type_id?: number
  priority_id?: number
  groupby?: 'day' | 'week' | 'month'
}

export interface CountDataPoint {
  period: string
  count: number
}

export interface StatusDataPoint {
  status: string
  count: number
}

export interface AvgResolutionDataPoint {
  priority: string
  avg_hours: number | null
}

export interface SLAComplianceData {
  total: number
  compliant: number
  compliance_rate: number
}

export async function getTicketsCount(params?: ReportParams): Promise<CountDataPoint[]> {
  const res = await client.get<{ items: CountDataPoint[]; total: number }>('/reports/tickets-count', { params })
  return res.data.items
}

export async function getTicketsByStatus(params?: ReportParams): Promise<StatusDataPoint[]> {
  const res = await client.get<StatusDataPoint[]>('/reports/by-status', { params })
  return res.data
}

export async function getAvgResolutionTime(params?: ReportParams): Promise<AvgResolutionDataPoint[]> {
  const res = await client.get<AvgResolutionDataPoint[]>('/reports/avg-resolution-time', { params })
  return res.data
}

export async function getSLACompliance(params?: ReportParams): Promise<SLAComplianceData> {
  const res = await client.get<SLAComplianceData>('/reports/sla-compliance', { params })
  return res.data
}

export async function exportTickets(format: 'csv' | 'xlsx', params?: ReportParams): Promise<void> {
  const res = await client.get('/reports/export', {
    params: { format, ...params },
    responseType: 'blob',
  })
  const ext = format === 'xlsx' ? 'xlsx' : 'csv'
  const disposition: string = res.headers['content-disposition'] ?? ''
  const match = disposition.match(/filename[^;=\n]*=["']?([^"';\n]+)["']?/)
  const filename = match ? match[1] : `Ticket_System.${ext}`
  const url = URL.createObjectURL(res.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
