import { useEffect, useState } from 'react'
import { ApiError, FormulaTemplate, MarketFormula, RevisionApplication, RevisionGroup, copyFormulaTemplate, getRevisionApplication, listRevisionGroups, saveRevisionApplication, saveRevisionGroup } from '../lib/api'
import { FormulaCatalogSelector } from './FormulaCatalogSelector'

type Props = { marketId: string; role: string | null | undefined; initialMode?: RevisionApplication['revision_application_mode']; v1Simple?: boolean; onModeChange?: (mode: RevisionApplication['revision_application_mode']) => void }
const canEdit = (role: string | null | undefined) => role === 'OWNER' || role === 'ADMIN'
const message = (error: unknown) => error instanceof ApiError ? error.payload.message : 'Erreur réseau. Réessayez.'

function FormulaSummary({ formula, code, designation, application, editable, onChange }: { formula: MarketFormula; code: string; designation: string; application?: RevisionApplication | null; editable: boolean; onChange: () => void }) {
  const index = formula.terms[0]?.index_code
  const month = application?.base_month ? new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${application.base_month}-01T00:00:00Z`)) : null
  const baseValue = application ? ['DEFINITIVE', 'PROVISIONAL'].includes(application.base_index_status || '') ? application.base_index_value : application.base_index_status === 'DATE_MISSING' ? '—' : 'Index officiel non disponible dans la base' : formula.terms[0]?.base_value || 'Non renseigné'
  const baseMonth = application ? month || 'Date limite de remise des offres non renseignée' : null
  return <div className="formula-selected alert"><strong>Formule de révision</strong><h3><span>{code}</span> — {designation}</h3><p className="formula-expression">{formula.expression_display || 'Expression non renseignée'}</p>{application ? <><p>Mois de base : <strong>{baseMonth}</strong></p><p>{index || application.base_index_code || 'Index'}₀ : <strong>{baseValue}</strong></p>{application.base_index_source && <p className="muted">Source : {application.base_index_source}</p>}</> : <><p>Indice : <strong>{index || 'Non renseigné'}</strong></p><p>Indice de base : <strong>{baseValue}</strong></p></>}{editable && <button type="button" className="secondary" onClick={onChange}>Changer de formule</button>}</div>
}

export function RevisionApplicationSection({ marketId, role, initialMode, v1Simple = false, onModeChange }: Props) {
  const [application, setApplication] = useState<RevisionApplication | null>(null); const [groups, setGroups] = useState<RevisionGroup[]>([]); const [mode, setMode] = useState<RevisionApplication['revision_application_mode']>(initialMode ?? 'PRICE_ASSIGNMENT'); const [loading, setLoading] = useState(Boolean(initialMode)); const [saving, setSaving] = useState(false); const [error, setError] = useState('')
  const editable = canEdit(role)
  useEffect(() => { if (!initialMode) return; setLoading(true); Promise.all([getRevisionApplication(marketId), listRevisionGroups(marketId)]).then(([loaded, loadedGroups]) => { setApplication(loaded); setMode(loaded.revision_application_mode); setGroups(loadedGroups) }).catch((caught) => setError(message(caught))).finally(() => setLoading(false)) }, [marketId, initialMode])
  const saveMode = async (nextMode: RevisionApplication['revision_application_mode']) => { setError(''); setMode(nextMode); onModeChange?.(nextMode); if (nextMode !== 'PRICE_ASSIGNMENT') return; setSaving(true); try { const saved = await saveRevisionApplication(marketId, { revision_application_mode: nextMode, global_revision_group: null }); setApplication(saved); window.dispatchEvent(new CustomEvent('revision-application-mode-changed', { detail: nextMode })) } catch (caught) { setError(message(caught)) } finally { setSaving(false) } }
  const selectGlobal = async (template: FormulaTemplate) => {
    setSaving(true); setError('')
    try {
      const group = await saveRevisionGroup(marketId, { code: template.code, name: template.designation, sort_order: groups.length })
      const formula = await copyFormulaTemplate(marketId, group.id, template.id)
      const saved = await saveRevisionApplication(marketId, { revision_application_mode: 'GLOBAL_FORMULA', global_revision_group: group.id })
      setApplication({ ...saved, global_formula: formula }); setMode('GLOBAL_FORMULA'); onModeChange?.('GLOBAL_FORMULA'); window.dispatchEvent(new CustomEvent('revision-application-mode-changed', { detail: 'GLOBAL_FORMULA' })); setGroups((current) => [...current, { ...group, code: template.code, name: template.designation, formulas: [formula] }])
    } catch (caught) { setError(message(caught)); throw caught } finally { setSaving(false) }
  }
  const globalGroup = groups.find((group) => group.id === application?.global_revision_group)
  if (!initialMode) return null
  if (v1Simple) return <section aria-label="Formule de révision du marché"><div className="section-heading"><div><p className="eyebrow">FORMULE CONTRACTUELLE</p><h2>FORMULE DE RÉVISION DU MARCHÉ</h2><p className="muted">Une seule formule active couvre l'ensemble du marché.</p></div></div><div className="card company-form">{loading && <p className="state">Chargement…</p>}{error && <div className="alert error" role="alert">{error}</div>}{!loading && !application?.global_formula && <FormulaCatalogSelector editable={editable} onSelect={selectGlobal} ariaLabel="Formule de révision du marché" alwaysOpen />}{application?.global_formula && <FormulaSummary formula={application.global_formula} code={globalGroup?.code || application.global_formula.label} designation={globalGroup?.name || application.global_formula.label} application={application} editable={editable} onChange={() => setApplication((current) => current ? { ...current, global_formula: null, global_revision_group: null } : current)} />}</div></section>
  return <section aria-label="Application de la révision"><div className="section-heading"><div><p className="eyebrow">PÉRIMÈTRE DE RÉVISION</p><h2>Mode de révision</h2></div></div><div className="card company-form"><label className="checkbox-label"><input type="radio" name={`mode-${marketId}`} checked={mode === 'GLOBAL_FORMULA'} disabled={!editable || saving} onChange={() => setMode('GLOBAL_FORMULA')} /> Une seule formule pour l'ensemble du marché</label><label className="checkbox-label"><input type="radio" name={`mode-${marketId}`} checked={mode === 'PRICE_ASSIGNMENT'} disabled={!editable || saving} onChange={() => void saveMode('PRICE_ASSIGNMENT')} /> Plusieurs formules</label>{loading && <p className="state">Chargement…</p>}{error && <div className="alert error" role="alert">{error}</div>}
      {mode === 'GLOBAL_FORMULA' && !application?.global_formula && <FormulaCatalogSelector editable={editable} onSelect={selectGlobal} />}
      {mode === 'GLOBAL_FORMULA' && application?.global_formula && <FormulaSummary formula={application.global_formula} code={globalGroup?.code || application.global_formula.label} designation={globalGroup?.name || application.global_formula.label} editable={editable} onChange={() => setApplication((current) => current ? { ...current, global_formula: null, global_revision_group: null } : current)} />}
      {mode === 'PRICE_ASSIGNMENT' && <div className="workflow-step"><h3>Plusieurs formules</h3><p>Ajoutez le bordereau des prix du marché afin d'affecter les prix aux différentes formules de révision.</p><p className="muted">Après création du BDP, l’affectation se fait sur une page dédiée.</p></div>}
    </div></section>
}
