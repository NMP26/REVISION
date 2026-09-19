import { FormEvent, useEffect, useState } from 'react'
import { ApiError, Company, Market, saveMarket } from '../lib/api'

type Props = { market?: Market; companies: Company[]; onSaved: (market: Market) => void }
type FormState = Record<string, string>

const initial = (market?: Market): FormState => ({
  company: market?.company ?? '', market_number: market?.market_number ?? '',
  contracting_authority: market?.contracting_authority ?? '', subject: market?.subject ?? '',
  amount_ht: market?.amount_ht ?? '', vat_rate: market?.vat_rate ?? '',
  date_limite_remise_offres: market?.date_limite_remise_offres ?? '', date_ouverture_plis: market?.date_ouverture_plis ?? '',
  date_signature: market?.date_signature ?? '', date_os_commencement: market?.date_os_commencement ?? '',
  contract_duration_value: market?.contract_duration_value?.toString() ?? '', contract_duration_unit: market?.contract_duration_unit ?? '',
  formula_structure: market?.formula_structure ?? 'SINGLE', status: market?.status ?? 'ACTIVE', notes: market?.notes ?? '',
})

export function MarketForm({ market, companies, onSaved }: Props) {
  const [values, setValues] = useState<FormState>(initial(market))
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const editableCompanies = companies.filter((company) => ['OWNER', 'ADMIN'].includes(company.current_user_role ?? ''))
  useEffect(() => setValues(initial(market)), [market])
  const update = (key: string, value: string) => setValues((current) => ({ ...current, [key]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setErrors({}); setLoading(true)
    try {
      const payload: Record<string, unknown> = { ...values, contract_duration_value: values.contract_duration_value ? Number(values.contract_duration_value) : null }
      if (!values.company) delete payload.company
      onSaved(await saveMarket(payload, market?.id))
    } catch (caught) {
      if (caught instanceof ApiError) { setError(caught.payload.message); setErrors(caught.payload.fields ?? {}) } else setError('Enregistrement impossible.')
    } finally { setLoading(false) }
  }

  return <form className="card company-form" onSubmit={submit}>
    {error && <div className="alert error" role="alert">{error}</div>}
    {!market && <label>Société<select value={values.company} onChange={(e) => update('company', e.target.value)} required><option value="">Sélectionner une société</option>{editableCompanies.map((company) => <option key={company.id} value={company.id}>{company.raison_sociale}</option>)}</select>{errors.company && <small className="field-error">{errors.company.join(' ')}</small>}</label>}
    {market && <label>Société<input value={market.company_detail.raison_sociale} readOnly /></label>}
    <div className="form-grid">
      <label>Numéro du marché<input value={values.market_number} onChange={(e) => update('market_number', e.target.value)} required />{errors.market_number && <small className="field-error">{errors.market_number.join(' ')}</small>}</label>
      <label>Maître d'ouvrage<input value={values.contracting_authority} onChange={(e) => update('contracting_authority', e.target.value)} required />{errors.contracting_authority && <small className="field-error">{errors.contracting_authority.join(' ')}</small>}</label>
    </div>
    <label>Objet<textarea value={values.subject} onChange={(e) => update('subject', e.target.value)} required />{errors.subject && <small className="field-error">{errors.subject.join(' ')}</small>}</label>
    <div className="form-grid">
      <label>Montant HT<input type="number" min="0" step="0.01" value={values.amount_ht} onChange={(e) => update('amount_ht', e.target.value)} />{errors.amount_ht && <small className="field-error">{errors.amount_ht.join(' ')}</small>}</label>
      <label>TVA (%)<input type="number" min="0" max="100" step="0.01" value={values.vat_rate} onChange={(e) => update('vat_rate', e.target.value)} />{errors.vat_rate && <small className="field-error">{errors.vat_rate.join(' ')}</small>}</label>
    </div>
    <fieldset><legend>Dates factuelles</legend><div className="form-grid">{[
      ['date_limite_remise_offres', 'Date limite de remise des offres'], ['date_ouverture_plis', "Date d'ouverture des plis"],
      ['date_signature', 'Date de signature'], ['date_os_commencement', "Date d'OS de commencement"],
    ].map(([key, label]) => <label key={key}>{label}<input type="date" value={values[key]} onChange={(e) => update(key, e.target.value)} />{errors[key] && <small className="field-error">{errors[key].join(' ')}</small>}</label>)}</div></fieldset>
    <fieldset><legend>Délai contractuel</legend><div className="form-grid"><label>Valeur<input type="number" min="1" step="1" value={values.contract_duration_value} onChange={(e) => update('contract_duration_value', e.target.value)} />{errors.contract_duration_value && <small className="field-error">{errors.contract_duration_value.join(' ')}</small>}</label><label>Unité<select value={values.contract_duration_unit} onChange={(e) => update('contract_duration_unit', e.target.value)}><option value="">Non renseignée</option><option value="DAYS">Jours</option><option value="MONTHS">Mois</option></select>{errors.contract_duration_unit && <small className="field-error">{errors.contract_duration_unit.join(' ')}</small>}</label></div></fieldset>
    <div className="form-grid"><label>Structure contractuelle<select value={values.formula_structure} onChange={(e) => update('formula_structure', e.target.value)}><option value="SINGLE">Formule unique</option><option value="MULTIPLE">Formules multiples</option></select></label>{market && <label>Statut<select value={values.status} onChange={(e) => update('status', e.target.value)}><option value="ACTIVE">Active</option><option value="ARCHIVED">Archivée</option></select></label>}</div>
    <label>Notes<textarea value={values.notes} onChange={(e) => update('notes', e.target.value)} /></label>
    <div className="form-actions"><button type="submit" className="primary" disabled={loading}>{loading ? 'Enregistrement…' : market ? 'Enregistrer' : 'Créer le marché'}</button></div>
  </form>
}
