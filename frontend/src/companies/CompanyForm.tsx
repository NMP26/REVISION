import { FormEvent, useEffect, useState } from 'react'
import { ApiError, Company, saveCompany } from '../lib/api'

type Props = { company?: Company; onSaved: (company: Company) => void }
type FormState = Record<string, string | File | null>
const fields = [
  ['raison_sociale', 'Raison sociale', true], ['forme_juridique', 'Forme juridique'], ['capital_social', 'Capital social'],
  ['ice', 'ICE'], ['if_fiscal', 'IF'], ['rc', 'RC'], ['cnss', 'CNSS'], ['adresse_complete', 'Adresse'],
  ['ville', 'Ville'], ['telephone', 'Téléphone'], ['email', 'E-mail'], ['site_web', 'Site web'],
  ['representant_nom', 'Nom du représentant'], ['representant_prenom', 'Prénom du représentant'],
  ['representant_fonction', 'Qualité / fonction'],
] as const

export function CompanyForm({ company, onSaved }: Props) {
  const [values, setValues] = useState<FormState>({ status: company?.status ?? 'ACTIVE', notes: company?.notes ?? '', logo: null })
  const [errors, setErrors] = useState<Record<string, string[]>>({}); const [error, setError] = useState(''); const [loading, setLoading] = useState(false)
  useEffect(() => { if (company) { const next: FormState = { status: company.status, notes: company.notes, logo: null }; fields.forEach(([key]) => { next[key] = company[key as keyof Company] as string }); setValues(next) } }, [company])
  const update = (key: string, value: string | File | null) => setValues((current) => ({ ...current, [key]: value }))
  async function submit(event: FormEvent) { event.preventDefault(); setError(''); setErrors({}); setLoading(true); try { onSaved(await saveCompany(values, company?.id)) } catch (caught) { if (caught instanceof ApiError) { setError(caught.payload.message); setErrors(caught.payload.fields ?? {}) } else setError('Enregistrement impossible.') } finally { setLoading(false) } }
  return <form className="card company-form" onSubmit={submit}>
    {error && <div className="alert error" role="alert">{error}</div>}
    <div className="form-grid">{fields.map(([key, label, required]) => <label key={key}>{label}<input type={key === 'email' ? 'email' : key === 'site_web' ? 'url' : key === 'capital_social' ? 'number' : 'text'} step={key === 'capital_social' ? '0.01' : undefined} value={String(values[key] ?? '')} onChange={(e) => update(key, e.target.value)} required={required} />{errors[key] && <small className="field-error">{errors[key].join(' ')}</small>}</label>)}</div>
    <label>Notes<textarea value={String(values.notes ?? '')} onChange={(e) => update('notes', e.target.value)} /></label>
    {company && <label>Statut<select value={String(values.status)} onChange={(e) => update('status', e.target.value)}><option value="ACTIVE">Active</option><option value="INACTIVE">Inactive</option></select></label>}
    <label>Logo (JPG, PNG ou WebP, 5 MiB maximum)<input type="file" accept=".jpg,.jpeg,.png,.webp" onChange={(e) => update('logo', e.target.files?.[0] ?? null)} /></label>
    <div className="form-actions"><button type="submit" className="primary" disabled={loading}>{loading ? 'Enregistrement…' : company ? 'Enregistrer' : 'Créer la société'}</button></div>
  </form>
}
