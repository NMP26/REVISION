import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ApiError, Company, Consortium, ConsortiumMember, getConsortium, listCompanies, listConsortia, saveConsortium } from '../lib/api'
import { formatDecimal } from '../lib/formatters'

type MemberDraft = { company: string; role: ConsortiumMember['role']; share_percent: string }
type FormState = { owner_company: string; name: string; consortium_type: string; active: string; notes: string }

const emptyMember = (role: MemberDraft['role'] = 'MEMBER'): MemberDraft => ({ company: '', role, share_percent: '' })
const initialForm = (consortium?: Consortium): FormState => ({
  owner_company: consortium?.owner_company ?? '', name: consortium?.name ?? '', consortium_type: consortium?.consortium_type ?? '', active: consortium?.active === false ? 'false' : 'true', notes: consortium?.notes ?? '',
})
const initialMembers = (consortium?: Consortium): MemberDraft[] => consortium?.members.filter((member) => member.active).map((member) => ({ company: member.company, role: member.role, share_percent: member.share_percent ?? '' })) ?? [emptyMember('MANDATAIRE'), emptyMember()]

function roleLabel(role: ConsortiumMember['role']) { return role === 'MANDATAIRE' ? 'Mandataire' : 'Membre' }
function isEditor(company: Company) { return company.current_user_role === 'OWNER' || company.current_user_role === 'ADMIN' }
function errorFor(error: unknown) { return error instanceof ApiError ? error : new ApiError(0, { code: 'NETWORK_ERROR', message: 'Erreur réseau. Réessayez.' }) }
function companyName(companies: Company[], id: string) { return companies.find((company) => company.id === id)?.raison_sociale ?? 'Société inconnue' }

export function ConsortiumErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  const navigate = useNavigate()
  useEffect(() => { if (error.status === 401) navigate('/login', { replace: true }) }, [error.status, navigate])
  if (error.status === 401) return <p className="state">Session expirée. Redirection vers la connexion…</p>
  if (error.status === 403) return <div className="alert error" role="alert">Accès refusé.</div>
  if (error.status === 404) return <div className="alert error" role="alert">Groupement introuvable.</div>
  return <div className="alert error" role="alert">Erreur réseau. Réessayez.{onRetry && <button className="link-button" onClick={onRetry}>Réessayer</button>}</div>
}

function ConsortiumForm({ consortium, companies, onSaved, onCancel }: { consortium?: Consortium; companies: Company[]; onSaved: (value: Consortium) => void; onCancel: () => void }) {
  const [values, setValues] = useState<FormState>(initialForm(consortium))
  const [members, setMembers] = useState<MemberDraft[]>(initialMembers(consortium))
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [loading, setLoading] = useState(false)
  const editableCompanies = companies.filter(isEditor)

  useEffect(() => { setValues(initialForm(consortium)); setMembers(initialMembers(consortium)) }, [consortium])

  const update = (key: keyof FormState, value: string) => setValues((current) => ({ ...current, [key]: value }))
  const updateMember = (index: number, changes: Partial<MemberDraft>) => setMembers((current) => current.map((member, memberIndex) => memberIndex === index ? { ...member, ...changes } : member))
  const removeMember = (index: number) => setMembers((current) => current.filter((_, memberIndex) => memberIndex !== index))
  const usedCompanyIds = (except: number) => new Set(members.filter((_, index) => index !== except).map((member) => member.company).filter(Boolean))

  function shareUnits(value: string): bigint | null {
    const normalized = value.trim().replace(',', '.')
    const match = normalized.match(/^(\d+)(?:\.(\d{1,4}))?$/)
    if (!match) return null
    return BigInt(match[1]) * 10000n + BigInt((match[2] ?? '').padEnd(4, '0'))
  }

  function validate(): string | null {
    if (!values.owner_company) return 'Sélectionnez la société gestionnaire du groupement.'
    if (!values.name.trim()) return 'Le nom du groupement est obligatoire.'
    if (members.length < 2) return 'Ajoutez au moins deux membres.'
    if (members.some((member) => !member.company)) return 'Sélectionnez une Company pour chaque membre.'
    if (new Set(members.map((member) => member.company)).size !== members.length) return 'Une Company ne peut apparaître qu’une seule fois.'
    if (members.filter((member) => member.role === 'MANDATAIRE').length !== 1) return 'Choisissez exactement un mandataire parmi les membres.'
    const shares = members.map((member) => member.share_percent.trim())
    if (shares.some((share) => share && shareUnits(share) === null)) return 'Les quotes-parts doivent être des nombres décimaux positifs.'
    if (shares.every(Boolean) && shares.reduce<bigint>((sum, share) => sum + (shareUnits(share) ?? 0n), 0n) !== 1000000n) return 'La somme des quotes-parts doit être exactement 100,00 %.'
    return null
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setErrors({})
    const validation = validate()
    if (validation) { setError(validation); return }
    setLoading(true)
    try {
      const payload = {
        owner_company: values.owner_company,
        name: values.name.trim(),
        consortium_type: values.consortium_type.trim(),
        active: values.active === 'true',
        notes: values.notes,
        members: members.map((member, index) => ({ company: member.company, role: member.role, share_percent: member.share_percent.trim() || null, sort_order: index, active: true })),
      }
      onSaved(await saveConsortium(payload, consortium?.id))
    } catch (caught) {
      if (caught instanceof ApiError) { setError(caught.payload.message); setErrors(caught.payload.fields ?? {}) } else setError('Enregistrement impossible.')
    } finally { setLoading(false) }
  }

  return <form className="card company-form" onSubmit={submit}>
    {error && <div className="alert error" role="alert">{error}</div>}
    {errors.members && <div className="alert error" role="alert">{errors.members.join(' ')}</div>}
    <div className="form-grid">
      <label>Nom du groupement<input value={values.name} onChange={(event) => update('name', event.target.value)} required /></label>
      <label>Type du groupement<input value={values.consortium_type} onChange={(event) => update('consortium_type', event.target.value)} placeholder="Ex. Groupement solidaire" /></label>
    </div>
    <label>Société gestionnaire<select aria-label="Société gestionnaire" value={values.owner_company} onChange={(event) => update('owner_company', event.target.value)} disabled={Boolean(consortium)} required><option value="">Sélectionner une société</option>{editableCompanies.map((company) => <option key={company.id} value={company.id}>{company.raison_sociale}</option>)}</select><small className="muted">Société de votre espace qui gère ce groupement dans RevisionPrix.</small></label>
    <fieldset><legend>Composition</legend>
      {members.map((member, index) => <div className="consortium-member-row" key={index}>
        <label>Company membre<select aria-label={`Company membre ${index + 1}`} value={member.company} onChange={(event) => updateMember(index, { company: event.target.value })} required><option value="">Sélectionner une Company</option>{companies.map((company) => <option key={company.id} value={company.id} disabled={usedCompanyIds(index).has(company.id)}>{company.raison_sociale}</option>)}</select></label>
        <label>Rôle<select aria-label={`Rôle membre ${index + 1}`} value={member.role} onChange={(event) => updateMember(index, { role: event.target.value as MemberDraft['role'] })}><option value="MEMBER">Membre</option><option value="MANDATAIRE">Mandataire</option></select></label>
        <label>Quote-part (%)<input aria-label={`Quote-part membre ${index + 1}`} inputMode="decimal" placeholder="50.00" value={member.share_percent} onChange={(event) => updateMember(index, { share_percent: event.target.value })} /></label>
        {members.length > 2 && <button type="button" className="link-button consortium-remove" onClick={() => removeMember(index)}>Retirer</button>}
      </div>)}
      <div className="inline-actions"><button type="button" className="secondary" onClick={() => setMembers((current) => [...current, emptyMember()])}>Ajouter un membre</button></div>
      <p className="muted form-hint">Si toutes les quotes-parts sont renseignées, leur total doit être égal à 100,00 %.</p>
    </fieldset>
    <div className="form-grid"><label>Statut<select value={values.active} onChange={(event) => update('active', event.target.value)}><option value="true">Actif</option><option value="false">Inactif</option></select></label></div>
    <label>Notes<textarea value={values.notes} onChange={(event) => update('notes', event.target.value)} /></label>
    <div className="form-actions"><button type="button" className="secondary" onClick={onCancel}>Annuler</button><button type="submit" className="primary" disabled={loading}>{loading ? 'Enregistrement…' : consortium ? 'Enregistrer' : 'Créer le groupement'}</button></div>
  </form>
}

export function ConsortiaPage() {
  const navigate = useNavigate(); const [consortia, setConsortia] = useState<Consortium[]>([]); const [companies, setCompanies] = useState<Company[]>([]); const [error, setError] = useState<ApiError | null>(null); const [loading, setLoading] = useState(true)
  const load = () => { setLoading(true); setError(null); Promise.all([listConsortia(), listCompanies()]).then(([loadedConsortia, loadedCompanies]) => { setConsortia(loadedConsortia); setCompanies(loadedCompanies) }).catch((caught) => setError(errorFor(caught))).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  if (loading) return <p className="state">Chargement…</p>
  if (error) return <ConsortiumErrorState error={error} onRetry={load} />
  const canCreate = companies.some(isEditor)
  return <section><div className="page-heading"><div><p className="eyebrow">ESPACE AUTORISÉ</p><h1>Groupements</h1></div>{canCreate && <Link className="primary button-link" to="/app/consortia/new">Nouveau groupement</Link>}</div>{consortia.length === 0 ? <div className="card state">Aucun groupement accessible.</div> : <div className="company-list">{consortia.map((consortium) => { const activeMembers = consortium.members.filter((member) => member.active); const representative = activeMembers.find((member) => member.role === 'MANDATAIRE'); return <Link className="card company-row" to={`/app/consortia/${consortium.id}`} key={consortium.id}><div><strong>{consortium.name}</strong><span>{consortium.consortium_type || 'Type non renseigné'}</span><span>Mandataire : {representative ? representative.company_detail?.raison_sociale ?? representative.company : '—'}</span><span>Membres : {activeMembers.map((member) => member.company_detail?.raison_sociale ?? member.company).join(', ') || '—'}</span></div><span className={`badge ${consortium.active ? 'active' : 'inactive'}`}>{consortium.active ? 'Actif' : 'Inactif'}</span></Link>})}</div>}</section>
}

export function ConsortiumCreatePage() {
  const navigate = useNavigate(); const [companies, setCompanies] = useState<Company[] | null>(null); const [error, setError] = useState<ApiError | null>(null)
  useEffect(() => { listCompanies().then(setCompanies).catch((caught) => setError(errorFor(caught))) }, [])
  if (error) return <ConsortiumErrorState error={error} />
  if (!companies) return <p className="state">Chargement…</p>
  return <section><div className="page-heading"><h1>Nouveau groupement</h1><Link to="/app/consortia">Annuler</Link></div><ConsortiumForm companies={companies} onCancel={() => navigate('/app/consortia')} onSaved={(consortium) => navigate(`/app/consortia/${consortium.id}`)} /></section>
}

export function ConsortiumDetailPage() {
  const { id = '' } = useParams(); const navigate = useNavigate(); const location = useLocation(); const [consortium, setConsortium] = useState<Consortium | null>(null); const [companies, setCompanies] = useState<Company[]>([]); const [editing, setEditing] = useState(location.pathname.endsWith('/edit')); const [error, setError] = useState<ApiError | null>(null)
  const load = async () => { setError(null); try { const [loadedConsortium, loadedCompanies] = await Promise.all([getConsortium(id), listCompanies()]); setConsortium(loadedConsortium); setCompanies(loadedCompanies) } catch (caught) { setError(errorFor(caught)) } }
  useEffect(() => { void load() }, [id])
  if (error) return <ConsortiumErrorState error={error} onRetry={load} />
  if (!consortium) return <p className="state">Chargement…</p>
  const canEdit = companies.some((company) => company.id === consortium.owner_company && isEditor(company))
  if (editing && canEdit) return <section><div className="page-heading"><h1>Modifier le groupement</h1><button className="link-button" onClick={() => setEditing(false)}>Annuler</button></div><ConsortiumForm consortium={consortium} companies={companies} onCancel={() => setEditing(false)} onSaved={(saved) => { setConsortium(saved); setEditing(false) }} /></section>
  const activeMembers = consortium.members.filter((member) => member.active)
  return <section><div className="page-heading"><div><p className="eyebrow">GROUPEMENT</p><h1>{consortium.name}</h1><p className="muted">{consortium.consortium_type || 'Type non renseigné'}</p></div><div className="inline-actions">{canEdit && <button className="secondary" onClick={() => setEditing(true)}>Modifier</button>}<button className="link-button" onClick={() => navigate('/app/consortia')}>Retour</button></div></div><div className="card detail-grid"><div><dt>Type</dt><dd>{consortium.consortium_type || '—'}</dd></div><div><dt>Statut</dt><dd>{consortium.active ? 'Actif' : 'Inactif'}</dd></div><div><dt>Société gestionnaire</dt><dd>{companyName(companies, consortium.owner_company)}</dd></div><div><dt>Mandataire</dt><dd>{companyName(companies, activeMembers.find((member) => member.role === 'MANDATAIRE')?.company ?? '')}</dd></div></div><div className="section-heading"><div><p className="eyebrow">COMPOSITION</p><h2>Membres</h2></div></div><div className="card consortium-members-list">{activeMembers.map((member) => <div className="consortium-detail-row" key={member.id ?? member.company}><strong>{companyName(companies, member.company)}</strong><span>{roleLabel(member.role)}</span><span>{member.share_percent === null ? 'Quote-part non renseignée' : `${formatDecimal(member.share_percent)} %`}</span></div>)}</div>{consortium.notes && <div className="card consortium-notes"><dt>Notes</dt><p>{consortium.notes}</p></div>}</section>
}
