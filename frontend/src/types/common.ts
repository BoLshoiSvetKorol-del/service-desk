export interface PagedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ApiError {
  detail: string | ValidationError[]
}

export interface ValidationError {
  loc: string[]
  msg: string
  type: string
}

function cleanMsg(msg: string): string {
  // Убираем технические префиксы Pydantic ("Value error, ", "String should ...")
  return msg
    .replace(/^value error,\s*/i, '')
    .replace(/^string should/i, 'Поле должно')
}

export function getErrorMessage(error: unknown): string {
  if (!error || typeof error !== 'object') return 'Неизвестная ошибка'
  const e = error as { response?: { data?: ApiError } }
  const detail = e.response?.data?.detail
  if (!detail) return 'Неизвестная ошибка'
  if (typeof detail === 'string') return detail
  return detail.map(v => cleanMsg(v.msg)).join('; ')
}
