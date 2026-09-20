export type ApiErrorPayload = { code: string; message: string; fields?: Record<string, string[]> }

export class ApiError extends Error {
  payload: ApiErrorPayload
  status: number

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message)
    this.status = status
    this.payload = payload
  }
}

function csrfToken() {
  return document.cookie.split('; ').find((part) => part.startsWith('csrftoken='))?.split('=')[1] ?? ''
}

export async function api<T>(url: string, options: RequestInit = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (method !== 'GET' && method !== 'HEAD') headers.set('X-CSRFToken', decodeURIComponent(csrfToken()))
  const response = await fetch(`/api${url}`, { ...options, headers, credentials: 'same-origin' })
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => ({ code: 'INVALID_RESPONSE', message: 'Réponse invalide.' }))
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('auth-expired'))
    throw new ApiError(response.status, data)
  }
  return data as T
}

export const ensureCsrf = () => api<{ csrfToken: string }>('/auth/csrf/')

export type User = { id: string; email: string; first_name: string; last_name: string; is_active: boolean; is_staff: boolean; is_superuser: boolean }
export type Company = {
  id: string; raison_sociale: string; forme_juridique: string; capital_social: string | null; ice: string;
  if_fiscal: string; rc: string; rc_city?: string; cnss: string; adresse_complete: string; ville: string; telephone: string;
  email: string; site_web: string; representant_nom: string; representant_prenom: string;
  representant_fonction: string; logo: string | null; notes: string; status: 'ACTIVE' | 'INACTIVE';
  created_at: string; updated_at: string; archived_at: string | null
  current_user_role: 'OWNER' | 'ADMIN' | 'MEMBER' | null
}

export type Authority = { id: string; name: string; short_name: string; active: boolean; created_at?: string; updated_at?: string }
export type ConsortiumMember = { id?: string; company: string; company_detail?: { id: string; raison_sociale: string }; role: 'MANDATAIRE' | 'MEMBER'; share_percent: string | null; sort_order: number; active: boolean }
export type Consortium = { id: string; owner_company: string; name: string; consortium_type: string; active: boolean; notes: string; members: ConsortiumMember[]; created_at: string; updated_at: string }

export type Market = {
  id: string
  company: string
  company_detail: { id: string; raison_sociale: string }
  holder_type?: 'SOLE_COMPANY' | 'CONSORTIUM'
  holder_company?: string | null
  holder_company_detail?: { id: string; raison_sociale: string } | null
  consortium?: string | null
  consortium_detail?: { id: string; name: string; owner_company: string } | null
  authority?: string | null
  authority_detail?: Authority | null
  market_number: string
  contracting_authority: string
  subject: string
  amount_ht: string | null
  vat_rate: string | null
  date_limite_remise_offres: string | null
  date_ouverture_plis: string | null
  date_signature: string | null
  date_os_commencement: string | null
  contract_duration_value: number | null
  contract_duration_unit: 'DAYS' | 'MONTHS' | null
  formula_structure: 'SINGLE' | 'MULTIPLE'
  status: 'ACTIVE' | 'ARCHIVED'
  notes: string
  created_at: string
  updated_at: string
  current_user_role: 'OWNER' | 'ADMIN' | 'MEMBER' | null
  lots_count: number
}

export type MarketLot = {
  id: string
  market: string
  lot_number: string
  title: string
  description: string
  amount_ht: string | null
  display_order: number
  active: boolean
  notes: string
  created_at: string
  updated_at: string
}

export function login(email: string, password: string) {
  return api<User>('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) })
}
export function logout() { return api<void>('/auth/logout/', { method: 'POST' }) }
export function currentUser() { return api<User>('/auth/me/') }
export function changePassword(current_password: string, new_password: string) {
  return api<{ message: string }>('/auth/password/change/', { method: 'POST', body: JSON.stringify({ current_password, new_password }) })
}
export function listCompanies() { return api<Company[]>('/companies/') }
export function getCompany(id: string) { return api<Company>(`/companies/${id}/`) }
export function saveCompany(data: Record<string, unknown>, id?: string) {
  const body = data.logo instanceof File
    ? (() => { const form = new FormData(); Object.entries(data).forEach(([key, value]) => { if (value !== null && value !== undefined) form.append(key, value as string | Blob) }); return form })()
    : JSON.stringify(Object.fromEntries(Object.entries(data).filter(([key, value]) => key !== 'logo' && value !== null && value !== undefined)))
  return api<Company>(id ? `/companies/${id}/` : '/companies/', { method: id ? 'PATCH' : 'POST', body })
}
export function listAuthorities(query = '') { return api<Authority[]>(`/authorities/${query ? `?q=${encodeURIComponent(query)}` : ''}`) }
export function saveAuthority(data: Record<string, unknown>) { return api<Authority>('/authorities/', { method: 'POST', body: JSON.stringify(data) }) }
export function listConsortia() { return api<Consortium[]>('/consortia/') }
export function getConsortium(id: string) { return api<Consortium>(`/consortia/${id}/`) }
export function saveConsortium(data: Record<string, unknown>, id?: string) { return api<Consortium>(id ? `/consortia/${id}/` : '/consortia/', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(data) }) }

export function listMarkets() { return api<Market[]>('/markets/') }
export function getMarket(id: string) { return api<Market>(`/markets/${id}/`) }
export function saveMarket(data: Record<string, unknown>, id?: string) {
  const payload = Object.fromEntries(Object.entries(data).filter(([, value]) => value !== '' && value !== undefined))
  return api<Market>(id ? `/markets/${id}/` : '/markets/', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
}
export function listMarketLots(marketId: string) { return api<MarketLot[]>(`/markets/${marketId}/lots/`) }
export function saveMarketLot(data: Record<string, unknown>, marketId: string, lotId?: string) {
  const payload = Object.fromEntries(Object.entries(data).filter(([, value]) => value !== '' && value !== undefined))
  return api<MarketLot>(lotId ? `/markets/${marketId}/lots/${lotId}/` : `/markets/${marketId}/lots/`, { method: lotId ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
}
