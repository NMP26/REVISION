import { FormEvent, useEffect, useState } from 'react'
import { ApiError, Authority, Company, Consortium, Market, saveAuthority, saveConsortium, saveMarket } from '../lib/api'

type Props = { market?: Market; companies: Company[]; authorities?: Authority[]; consortia?: Consortium[]; onSaved: (market: Market) => void; onConsortiumCreated?: (consortium: Consortium) => void }
type FormState = Record<string, string>
type MemberDraft = { company: string; role: 'MANDATAIRE' | 'MEMBER'; share_percent: string }

const initial = (market?: Market): FormState => ({
  company: market?.company ?? '', holder_type: market?.holder_type ?? 'SOLE_COMPANY', holder_company: market?.holder_company ?? '', consortium: market?.consortium ?? '', authority: market?.authority ?? '', contracting_authority: market?.contracting_authority ?? '', market_number: market?.market_number ?? '', subject: market?.subject ?? '', amount_ht: market?.amount_ht ?? '', vat_rate: market?.vat_rate ?? '', date_limite_remise_offres: market?.date_limite_remise_offres ?? '', date_ouverture_plis: market?.date_ouverture_plis ?? '', date_signature: market?.date_signature ?? '', date_os_commencement: market?.date_os_commencement ?? '', contract_duration_value: market?.contract_duration_value?.toString() ?? '', contract_duration_unit: market?.contract_duration_unit ?? '', formula_structure: market?.formula_structure ?? 'SINGLE', status: market?.status ?? 'ACTIVE', notes: market?.notes ?? '',
})

const emptyMember = (role: MemberDraft['role'] = 'MEMBER'): MemberDraft => ({ company: '', role, share_percent: '' })
const EMPTY_AUTHORITIES: Authority[] = []
const EMPTY_CONSORTIA: Consortium[] = []

export function MarketForm({ market, companies, authorities = EMPTY_AUTHORITIES, consortia = EMPTY_CONSORTIA, onSaved, onConsortiumCreated }: Props) {
  const [values, setValues] = useState<FormState>(initial(market))
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [authorityQuery, setAuthorityQuery] = useState(market?.contracting_authority ?? '')
  const [authoritySuggestions, setAuthoritySuggestions] = useState<Authority[]>(authorities)
  const [creatingAuthority, setCreatingAuthority] = useState(false)
  const [newAuthorityName, setNewAuthorityName] = useState('')
  const [creatingConsortium, setCreatingConsortium] = useState(false)
  const [newConsortiumName, setNewConsortiumName] = useState('')
  const [newMembers, setNewMembers] = useState<MemberDraft[]>([emptyMember('MANDATAIRE'), emptyMember()])

  const editableCompanies = companies.filter((company) => ['OWNER', 'ADMIN'].includes(company.current_user_role ?? ''))

  useEffect(() => {
    setValues(initial(market))
    setAuthorityQuery(market?.contracting_authority ?? '')
  }, [market])

  useEffect(() => {
    const selected = consortia.find((consortium) => consortium.id === values.consortium)
    if (selected?.members?.length) {
      setNewMembers(selected.members.map((member) => ({ company: member.company, role: member.role, share_percent: member.share_percent ?? '' })))
    }
  }, [consortia, values.consortium])

  useEffect(() => {
    const query = authorityQuery.trim().toLowerCase()
    setAuthoritySuggestions((query ? authorities.filter((item) => `${item.name} ${item.short_name}`.toLowerCase().includes(query)) : authorities).slice(0, 8))
  }, [authorityQuery, authorities])

  const update = (key: string, value: string) => setValues((current) => ({ ...current, [key]: value }))
  const updateMember = (index: number, changes: Partial<MemberDraft>) => setNewMembers((current) => current.map((member, memberIndex) => memberIndex === index ? { ...member, ...changes } : member))

  function selectAuthority(authority: Authority) {
    setAuthorityQuery(authority.name)
    setValues((current) => ({ ...current, authority: authority.id, contracting_authority: authority.name }))
  }

  async function createAuthority() {
    if (!newAuthorityName.trim() || !values.company) return
    try {
      const authority = await saveAuthority({ name: newAuthorityName, company: values.company })
      selectAuthority(authority)
      setCreatingAuthority(false)
      setNewAuthorityName('')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.payload.message : 'Création impossible.')
    }
  }

  async function createConsortium() {
    setError('')
    const activeMembers = newMembers.filter((member) => member.company)
    const companiesUsed = activeMembers.map((member) => member.company)
    const mandataires = activeMembers.filter((member) => member.role === 'MANDATAIRE')
    if (!newConsortiumName.trim() || !values.company) return
    if (activeMembers.length < 2) { setError('Ajoutez au moins deux sociétés au groupement.'); return }
    if (new Set(companiesUsed).size !== companiesUsed.length) { setError('Une société ne peut apparaître qu’une seule fois.'); return }
    if (mandataires.length !== 1) { setError('Le groupement doit comporter exactement un mandataire actif.'); return }
    try {
      const members = activeMembers.map((member, index) => ({ company: member.company, role: member.role, share_percent: member.share_percent || null, sort_order: index, active: true }))
      const selected = consortia.find((item) => item.id === values.consortium)
      const consortium = await saveConsortium({ owner_company: values.company, name: newConsortiumName || selected?.name, members }, selected?.id)
      onConsortiumCreated?.(consortium)
      setValues((current) => ({ ...current, holder_type: 'CONSORTIUM', consortium: consortium.id, holder_company: '' }))
      setCreatingConsortium(false)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.payload.message : 'Création impossible.')
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setErrors({}); setLoading(true)
    try {
      const payload: Record<string, unknown> = { ...values, company: values.company || undefined, holder_company: values.holder_type === 'SOLE_COMPANY' ? (values.holder_company || values.company) : null, consortium: values.holder_type === 'CONSORTIUM' ? values.consortium : null, authority: values.authority || null, contract_duration_value: values.contract_duration_value ? Number(values.contract_duration_value) : null }
      if (!values.company) delete payload.company
      if (!values.authority) delete payload.authority
      onSaved(await saveMarket(payload, market?.id))
    } catch (caught) {
      if (caught instanceof ApiError) { setError(caught.payload.message); setErrors(caught.payload.fields ?? {}) } else setError('Enregistrement impossible.')
    } finally { setLoading(false) }
  }

  return <form className="card company-form" onSubmit={submit}>
    {error && <div className="alert error" role="alert">{error}</div>}
    {!market && <><fieldset><legend>Type de titulaire</legend><label><input type="radio" checked={values.holder_type === 'SOLE_COMPANY'} onChange={() => update('holder_type', 'SOLE_COMPANY')} /> Société</label><label><input type="radio" checked={values.holder_type === 'CONSORTIUM'} onChange={() => update('holder_type', 'CONSORTIUM')} /> Groupement</label></fieldset><label>Société dossier<select value={values.company} onChange={(e) => update('company', e.target.value)} required><option value="">Sélectionner une société</option>{editableCompanies.map((company) => <option key={company.id} value={company.id}>{company.raison_sociale}</option>)}</select>{errors.company && <small className="field-error">{errors.company.join(' ')}</small>}</label></>}
    {values.holder_type === 'SOLE_COMPANY' && <label>Société titulaire<select value={values.holder_company || values.company} onChange={(e) => update('holder_company', e.target.value)} required><option value="">Sélectionner une société</option>{companies.map((company) => <option key={company.id} value={company.id}>{company.raison_sociale}</option>)}</select></label>}
    {values.holder_type === 'CONSORTIUM' && <><label>Groupement<select value={values.consortium} onChange={(e) => update('consortium', e.target.value)} required><option value="">Sélectionner un groupement</option>{consortia.map((consortium) => <option key={consortium.id} value={consortium.id}>{consortium.name}</option>)}</select></label><button type="button" className="secondary" onClick={() => { const selected = consortia.find((item) => item.id === values.consortium); setNewConsortiumName(selected?.name ?? ''); setCreatingConsortium(true) }}>{values.consortium ? 'Modifier le groupement' : 'Créer un groupement'}</button></>}
    {market && <label>Société dossier<input value={market.company_detail.raison_sociale} readOnly /></label>}
    <div className="form-grid"><label>Numéro du marché<input value={values.market_number} onChange={(e) => update('market_number', e.target.value)} required />{errors.market_number && <small className="field-error">{errors.market_number.join(' ')}</small>}</label><label>Maître d'ouvrage<input value={authorityQuery} onChange={(e) => { setAuthorityQuery(e.target.value); update('contracting_authority', e.target.value); update('authority', '') }} required aria-autocomplete="list" />{authoritySuggestions.length > 0 && <div role="listbox" aria-label="Suggestions de maîtres d’ouvrage">{authoritySuggestions.map((authority) => <button type="button" role="option" key={authority.id} onClick={() => selectAuthority(authority)}>{authority.name}{authority.short_name ? ` (${authority.short_name})` : ''}</button>)}</div>}<button type="button" className="link-button" onClick={() => setCreatingAuthority(true)}>Créer un nouveau maître d’ouvrage</button>{errors.contracting_authority && <small className="field-error">{errors.contracting_authority.join(' ')}</small>}</label></div>
    {creatingAuthority && <div className="card"><label>Nom officiel<input value={newAuthorityName} onChange={(e) => setNewAuthorityName(e.target.value)} /></label><button type="button" className="primary" onClick={() => void createAuthority()}>Créer</button></div>}
    {creatingConsortium && <div className="card"><label>Dénomination<input value={newConsortiumName} onChange={(e) => setNewConsortiumName(e.target.value)} /></label>{newMembers.map((member, index) => { const usedByOther = new Set(newMembers.filter((_, memberIndex) => memberIndex !== index).map((item) => item.company)); return <div className="form-grid" key={index}><select aria-label={`Entreprise membre ${index + 1}`} value={member.company} onChange={(e) => updateMember(index, { company: e.target.value })}><option value="">Entreprise</option>{companies.map((company) => <option key={company.id} value={company.id} disabled={usedByOther.has(company.id)}>{company.raison_sociale}</option>)}</select><select aria-label={`Rôle membre ${index + 1}`} value={member.role} onChange={(e) => { const role = e.target.value as MemberDraft['role']; setNewMembers((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, role } : role === 'MANDATAIRE' ? { ...item, role: 'MEMBER' } : item)) }}><option value="MANDATAIRE">Mandataire</option><option value="MEMBER">Membre</option></select><input aria-label={`Quote-part membre ${index + 1}`} placeholder="Quote-part %" value={member.share_percent} onChange={(e) => updateMember(index, { share_percent: e.target.value })} />{newMembers.length > 2 && <button type="button" className="link-button" onClick={() => setNewMembers((current) => current.filter((_, memberIndex) => memberIndex !== index))}>Retirer</button>}</div>})}<div className="inline-actions"><button type="button" className="secondary" onClick={() => setNewMembers((current) => [...current, emptyMember()])}>Ajouter un membre</button>{newMembers.length > 2 && <button type="button" className="link-button" onClick={() => setNewMembers((current) => current.slice(0, -1))}>Retirer le dernier</button>}</div><button type="button" className="primary" onClick={() => void createConsortium()}>Enregistrer le groupement</button></div>}
    <label>Objet<textarea value={values.subject} onChange={(e) => update('subject', e.target.value)} required />{errors.subject && <small className="field-error">{errors.subject.join(' ')}</small>}</label><div className="form-grid"><label>Montant HT<input type="number" min="0" step="0.01" value={values.amount_ht} onChange={(e) => update('amount_ht', e.target.value)} /></label><label>TVA (%)<input type="number" min="0" max="100" step="0.01" value={values.vat_rate} onChange={(e) => update('vat_rate', e.target.value)} /></label></div>
    <fieldset><legend>Dates factuelles</legend><div className="form-grid">{[['date_limite_remise_offres', 'Date limite de remise des offres'], ['date_ouverture_plis', "Date d'ouverture des plis"], ['date_signature', 'Date de signature'], ['date_os_commencement', "Date d'OS de commencement"]].map(([key, label]) => <label key={key}>{label}<input type="date" value={values[key]} onChange={(e) => update(key, e.target.value)} /></label>)}</div></fieldset><fieldset><legend>Délai contractuel</legend><div className="form-grid"><label>Valeur<input type="number" min="1" step="1" value={values.contract_duration_value} onChange={(e) => update('contract_duration_value', e.target.value)} /></label><label>Unité<select value={values.contract_duration_unit} onChange={(e) => update('contract_duration_unit', e.target.value)}><option value="">Non renseignée</option><option value="DAYS">Jours</option><option value="MONTHS">Mois</option></select></label></div></fieldset><div className="form-grid"><label>Structure contractuelle<select value={values.formula_structure} onChange={(e) => update('formula_structure', e.target.value)}><option value="SINGLE">Formule unique</option><option value="MULTIPLE">Formules multiples</option></select></label>{market && <label>Statut<select value={values.status} onChange={(e) => update('status', e.target.value)}><option value="ACTIVE">Active</option><option value="ARCHIVED">Archivée</option></select></label>}</div><label>Notes<textarea value={values.notes} onChange={(e) => update('notes', e.target.value)} /></label><div className="form-actions"><button type="submit" className="primary" disabled={loading}>{loading ? 'Enregistrement…' : market ? 'Enregistrer' : 'Créer le marché'}</button></div>
  </form>
}
