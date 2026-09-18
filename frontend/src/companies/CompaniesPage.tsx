import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ApiError, Company, getCompany, listCompanies } from '../lib/api'
import { CompanyForm } from './CompanyForm'

function statusOf(error: unknown) {
  return error instanceof ApiError ? error.status : (typeof error === 'object' && error !== null && 'status' in error ? Number(error.status) : 0)
}

function asApiError(error: unknown) {
  if (error instanceof ApiError) return error
  if (typeof error === 'object' && error !== null && 'status' in error && 'payload' in error) {
    const candidate = error as { status: number; payload: { code: string; message: string; fields?: Record<string, string[]> } }
    return new ApiError(candidate.status, candidate.payload)
  }
  return new ApiError(0, { code: 'NETWORK_ERROR', message: 'Erreur réseau. Réessayez.' })
}

export function CompanyErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  const navigate = useNavigate()
  useEffect(() => { if (error.status === 401) navigate('/login', { replace: true }) }, [error.status, navigate])
  if (error.status === 401) {
    return <p className="state">Session expirée. Redirection vers la connexion…</p>
  }
  if (error.status === 403) return <div className="alert error" role="alert">Accès refusé.</div>
  if (error.status === 404) return <div className="alert error" role="alert">Ressource introuvable.</div>
  return <div className="alert error" role="alert">Erreur réseau. Réessayez.{onRetry && <button className="link-button" onClick={onRetry}>Réessayer</button>}</div>
}

export function CompaniesPage() {
  const navigate = useNavigate(); const [companies, setCompanies] = useState<Company[]>([]); const [error, setError] = useState<ApiError | null>(null); const [loading, setLoading] = useState(true)
  const load = () => { setLoading(true); setError(null); listCompanies().then(setCompanies).catch((e) => { if (statusOf(e) === 401) { navigate('/login', { replace: true }); return }; setError(asApiError(e)) }).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  if (loading) return <p className="state">Chargement…</p>
  if (error) {
    return <CompanyErrorState error={error} onRetry={load} />
  }
  return <section><div className="page-heading"><div><p className="eyebrow">ESPACE AUTORISÉ</p><h1>Sociétés</h1></div><Link className="primary button-link" to="/app/companies/new">Nouvelle société</Link></div>{companies.length === 0 ? <div className="card state">Aucune société accessible.</div> : <div className="company-list">{companies.map((company) => <Link className="card company-row" to={`/app/companies/${company.id}`} key={company.id}><div><strong>{company.raison_sociale}</strong><span>{company.ville || 'Ville non renseignée'}</span></div><span className={`badge ${company.status.toLowerCase()}`}>{company.status === 'ACTIVE' ? 'Active' : 'Inactive'}</span></Link>)}</div>}</section>
}

export function CompanyCreatePage() { const navigate = useNavigate(); return <section><div className="page-heading"><h1>Nouvelle société</h1><Link to="/app/companies">Annuler</Link></div><CompanyForm onSaved={(company) => navigate(`/app/companies/${company.id}`)} /></section> }

export function CompanyDetailPage() {
  const { id = '' } = useParams(); const navigate = useNavigate(); const location = useLocation(); const [company, setCompany] = useState<Company | null>(null); const [editing, setEditing] = useState(location.pathname.endsWith('/edit')); const [error, setError] = useState<ApiError | null>(null)
  const load = async () => { setError(null); try { setCompany(await getCompany(id)) } catch (e) { if (statusOf(e) === 401) { navigate('/login', { replace: true }); return }; setError(asApiError(e)) } }
  useEffect(() => { void load() }, [id])
  useEffect(() => { if (company && !['OWNER', 'ADMIN'].includes(company.current_user_role ?? '')) setEditing(false) }, [company])
  if (error) {
    return <CompanyErrorState error={error} onRetry={load} />
  }
  if (!company) return <p className="state">Chargement…</p>
  const canEdit = company.current_user_role === 'OWNER' || company.current_user_role === 'ADMIN'
  if (editing && canEdit) return <section><div className="page-heading"><h1>Modifier la société</h1><button className="link-button" onClick={() => navigate(`/app/companies/${id}`)}>Annuler</button></div><CompanyForm company={company} onSaved={(saved) => { setCompany(saved); setEditing(false); navigate(`/app/companies/${id}`) }} /></section>
  return <section><div className="page-heading"><div><p className="eyebrow">SOCIÉTÉ</p><h1>{company.raison_sociale}</h1></div><div className="inline-actions">{canEdit && <button className="secondary" onClick={() => setEditing(true)}>Modifier</button>}<button className="link-button" onClick={() => navigate('/app/companies')}>Retour</button></div></div><div className="card detail-grid">{[['Forme juridique', company.forme_juridique], ['Capital social', company.capital_social ?? '—'], ['ICE', company.ice || '—'], ['IF', company.if_fiscal || '—'], ['RC', company.rc || '—'], ['CNSS', company.cnss || '—'], ['Adresse', company.adresse_complete || '—'], ['Ville', company.ville || '—'], ['Téléphone', company.telephone || '—'], ['E-mail', company.email || '—'], ['Site web', company.site_web || '—'], ['Représentant', `${company.representant_prenom} ${company.representant_nom}`.trim() || '—'], ['Fonction', company.representant_fonction || '—']].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</div></section>
}
