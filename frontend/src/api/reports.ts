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
  // Try RFC 5987 encoded name first (filename*=UTF-8''...)
  const rfc5987Match = disposition.match(/filename\*=UTF-8''([^;\s]+)/i)
  const fallbackMatch = disposition.match(/filename=["']?([^"';\n]+)["']?/)
  const rawFilename = rfc5987Match
    ? decodeURIComponent(rfc5987Match[1])
    : fallbackMatch ? fallbackMatch[1] : `Отчёт_ServiceDesk.${ext}`
  const filename = rawFilename
  const url = URL.createObjectURL(res.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
