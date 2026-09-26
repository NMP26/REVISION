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
  revision_application_mode?: 'GLOBAL_FORMULA' | 'PRICE_ASSIGNMENT'
  global_revision_group?: string | null
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

export type FormulaTerm = {
  id?: string; position: number; coefficient: string; term_type: 'INDEX_RATIO'; index_code: string;
  base_period_year: number | null; base_period_month: number | null; base_value: string | null;
  base_source: string; reference_note: string; created_at?: string; updated_at?: string
}
export type MarketFormula = {
  id: string; revision_group: string; version_number: number; label: string; expression_display: string;
  constant_term: string | null; status: 'DRAFT' | 'VALIDATED' | 'INACTIVE'; valid_from: string | null;
  valid_to: string | null; reference_period_year: number | null; reference_period_month: number | null;
  reference_rule_code: string; reference_source: string; created_by: string; created_at: string;
  updated_at: string; validated_at: string | null; source_template?: string | null; source_template_version?: number | null; terms: FormulaTerm[]
}
export type FormulaTemplate = {
  id: string; family_key: string; version_number: number; scope: 'GLOBAL' | 'COMPANY'; owner_company: string | null;
  code: string; designation: string; description: string; domain: string; expression_display: string;
  constant_term: string | null; status: 'DRAFT' | 'VERIFIED' | 'DEPRECATED'; valid_from: string | null; valid_to: string | null;
  source_type: 'OFFICIAL' | 'CONTRACT_EXAMPLE' | 'INTERNAL'; source_title: string; source_url: string;
  source_reference: string; source_date: string | null; verification_status: string; verified_at: string | null;
  verified_by: string | null; notes: string; created_at: string; updated_at: string; terms: FormulaTerm[]
}
export type RevisionGroup = {
  id: string; market: string; code: string; name: string; description: string; sort_order: number;
  active: boolean; notes: string; created_at: string; updated_at: string; formulas: MarketFormula[]
}
export type RevisionApplication = {
  revision_application_mode: 'GLOBAL_FORMULA' | 'PRICE_ASSIGNMENT'
  global_revision_group: string | null
  global_formula: MarketFormula | null
  price_schedule_required: boolean
  updated_at: string
  base_month?: string | null
  base_index_code?: string | null
  base_index_value?: string | null
  base_index_status?: 'DEFINITIVE' | 'PROVISIONAL' | 'PENDING_VALIDATION' | 'INDEX_NOT_AVAILABLE' | 'DATE_MISSING' | null
  base_index_source?: string | null
}
export type IndexDefinition = { id: string; code: string; designation: string; domain: string; active: boolean }
export type IndexPublication = { id: string; year: number; month: number; publication_date: string | null; source_url: string; document_reference: string; document_hash: string; source_type: 'OFFICIAL' | 'EXTERNAL_SECONDARY' | 'MANUAL_VALIDATED'; status: string; imported_at: string; validated_at: string | null }
export type MonthlyIndexValue = { id: string; index_definition: string; index_definition_detail: IndexDefinition; publication: string; publication_detail: IndexPublication; year: number; month: number; value: string; status: 'DEFINITIVE' | 'PROVISIONAL' | 'PENDING_VALIDATION'; source_url: string; source_document: string; source_reference: string; validated_at: string | null; created_at: string; updated_at: string }
export type ExternalIndexStaging = { id: string; source_provider: string; source_endpoint: string; retrieved_at: string; external_code: string; external_designation: string | null; year: number | null; month: number | null; raw_value: string; normalized_value: string | null; raw_payload_hash: string; previous_raw_value: string; previous_normalized_value: string | null; previous_raw_payload_hash: string; source_changed: boolean; comparison_status: string; validation_status: string; matched_index_definition: string | null; matched_index_definition_detail?: IndexDefinition | null; local_value: string | null; pdf_value: string | null; pdf_comparison_status: string; created_at: string; updated_at: string }
export type ExternalIndexStagingPage = { results: ExternalIndexStaging[]; count: number; page: number; page_size: number; has_next: boolean }
export type PriceSchedule = {
  id: string; market: string; status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED'; source_type: 'MANUAL' | 'IMPORT';
  name: string; notes: string; change_version: number; item_count: number; created_at: string; updated_at: string
}
export type PriceItem = {
  id: string; price_schedule: string; lot: string | null; price_number: string; designation: string; unit: string;
  estimated_quantity: string; unit_price_ht: string; estimated_amount_ht: string; revision_group: string | null;
  classification_status: 'PENDING_CLASSIFICATION' | 'REVISABLE' | 'NON_REVISABLE'; active: boolean; notes: string;
  created_at: string; updated_at: string
}
export type PriceItemPage = { count: number; next: number | null; previous: number | null; results: PriceItem[] }
export type PriceMatrix = {
  mode: 'GLOBAL_FORMULA' | 'PRICE_ASSIGNMENT'; price_schedule_required: boolean;
  formulas: Array<{ id: string; name: string; code: string; formulas: MarketFormula[] }>; items: PriceItem[]
}
export type Statement = { id: string; market: string; number: number; date: string; amount_ht: string; observation: string; allocation_method: 'ACTUAL_EXECUTION' | 'CALENDAR_DAY_PRORATA'; created_at: string; updated_at: string }
export type MonthlyWorkAllocation = { id: string; statement: string; year: number; month: number; work_days: string; created_at: string; updated_at: string }
export type StatementCalculationRow = { year: number; month: number; work_days: string; monthly_amount: string; amount_to_revise: string; monthly_amount_to_revise?: string; index_code: string | null; base_index: string | null; current_index: string | null; index_status: string; index_source: { publication?: string | null; source_type?: string | null; source_reference?: string | null }; ratio: string | null; variable_term?: string | null; K: string | null; K_minus_1: string | null; P_P0?: string | null; P_P0_minus_1?: string | null; revision_amount: string | null; calculation_status: string; available_for_calculation?: boolean }
export type StatementCalculation = { statement_id: string; statement_amount_ht: string; allocation_method: string; total_work_days: string; total_allocated_amount: string; total_revision: string | null; calculation_status: string; rounding_status: string; base_index: string | null; base_index_status: string | null; base_index_source: unknown; index_code: string | null; formula: { constant: string | null; coefficient: string | null; index_code: string | null; variable_term_label?: string | null }; monthly_results: StatementCalculationRow[]; message?: string }

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
export function listRevisionGroups(marketId: string) { return api<RevisionGroup[]>(`/markets/${marketId}/revision-groups/`) }
export function listIndexValues(query = '') { return api<MonthlyIndexValue[]>(`/indices/values/${query ? `?${query}` : ''}`) }
export function listIndexPublications() { return api<IndexPublication[]>('/indices/publications/') }
export function listExternalIndexStaging(query = '') { return api<ExternalIndexStagingPage>(`/indices/staging/${query ? `?${query}` : ''}`) }
export function getMarketBaseIndex(marketId: string) { return api<Record<string, unknown>>(`/markets/${marketId}/base-index/`) }
export function listStatements(marketId: string) { return api<Statement[]>(`/markets/${marketId}/statements/`) }
export function saveStatement(marketId: string, data: Record<string, unknown>, statementId?: string) { return api<Statement>(statementId ? `/markets/${marketId}/statements/${statementId}/` : `/markets/${marketId}/statements/`, { method: statementId ? 'PATCH' : 'POST', body: JSON.stringify(data) }) }
export function listMonthlyWorkAllocations(marketId: string, statementId: string) { return api<MonthlyWorkAllocation[]>(`/markets/${marketId}/statements/${statementId}/allocations/`) }
export function saveMonthlyWorkAllocation(marketId: string, statementId: string, data: Record<string, unknown>, allocationId?: string) { return api<MonthlyWorkAllocation>(allocationId ? `/markets/${marketId}/statements/${statementId}/allocations/${allocationId}/` : `/markets/${marketId}/statements/${statementId}/allocations/`, { method: allocationId ? 'PATCH' : 'POST', body: JSON.stringify(data) }) }
export function getStatementCalculation(marketId: string, statementId: string) { return api<StatementCalculation>(`/markets/${marketId}/statements/${statementId}/calculation/`) }
export function saveRevisionGroup(marketId: string, data: Record<string, unknown>, groupId?: string) {
  return api<RevisionGroup>(groupId ? `/markets/${marketId}/revision-groups/${groupId}/` : `/markets/${marketId}/revision-groups/`, { method: groupId ? 'PATCH' : 'POST', body: JSON.stringify(data) })
}
export function saveMarketFormula(marketId: string, groupId: string, data: Record<string, unknown>, formulaId?: string) {
  return api<MarketFormula>(formulaId ? `/markets/${marketId}/revision-groups/${groupId}/formulas/${formulaId}/` : `/markets/${marketId}/revision-groups/${groupId}/formulas/`, { method: formulaId ? 'PATCH' : 'POST', body: JSON.stringify(data) })
}
export function listFormulaTemplates(query = '') { return api<FormulaTemplate[]>(`/formula-templates/${query ? `?q=${encodeURIComponent(query)}` : ''}`) }
export function copyFormulaTemplate(marketId: string, groupId: string, templateId: string) {
  return api<MarketFormula>(`/markets/${marketId}/revision-groups/${groupId}/formulas/from-template/`, { method: 'POST', body: JSON.stringify({ template_id: templateId }) })
}
export function getRevisionApplication(marketId: string) { return api<RevisionApplication>(`/markets/${marketId}/revision-application/`) }
export function saveRevisionApplication(marketId: string, data: Record<string, unknown>) {
  return api<RevisionApplication>(`/markets/${marketId}/revision-application/`, { method: 'PATCH', body: JSON.stringify(data) })
}
export function getPriceSchedule(marketId: string) { return api<{ required: boolean; schedule: PriceSchedule | null }>(`/markets/${marketId}/price-schedule/`) }
export function createPriceSchedule(marketId: string, data: Record<string, unknown> = {}) {
  return api<PriceSchedule>(`/markets/${marketId}/price-schedule/`, { method: 'POST', body: JSON.stringify(data) })
}
export function listPriceItems(marketId: string, params: Record<string, string | number> = {}) {
  const query = new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)])).toString()
  return api<PriceItemPage>(`/markets/${marketId}/price-schedule/items/${query ? `?${query}` : ''}`)
}
export function savePriceItem(marketId: string, data: Record<string, unknown>, itemId?: string) {
  return api<PriceItem>(itemId ? `/markets/${marketId}/price-schedule/items/${itemId}/` : `/markets/${marketId}/price-schedule/items/`, { method: itemId ? 'PATCH' : 'POST', body: JSON.stringify(data) })
}
export function getPriceMatrix(marketId: string) { return api<PriceMatrix>(`/markets/${marketId}/price-schedule/matrix/`) }
export function assignPriceItems(marketId: string, data: Record<string, unknown>) {
  return api<{ updated: number; change_version: number }>(`/markets/${marketId}/price-schedule/assignments/`, { method: 'POST', body: JSON.stringify(data) })
}
export function validatePriceAssignment(marketId: string, expectedVersion?: number) {
  return api<{ validated: boolean; price_count: number; change_version: number }>(`/markets/${marketId}/price-schedule/assignments/`, { method: 'POST', body: JSON.stringify({ action: 'VALIDATE', expected_version: expectedVersion }) })
}
