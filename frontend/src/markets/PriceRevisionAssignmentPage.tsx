import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError, FormulaTemplate, Market, MarketFormula, PriceItem, PriceMatrix, PriceSchedule, RevisionApplication, RevisionGroup, assignPriceItems, copyFormulaTemplate, getMarket, getPriceMatrix, getPriceSchedule, getRevisionApplication, listFormulaTemplates, listRevisionGroups, saveRevisionGroup, validatePriceAssignment } from '../lib/api'

const canEdit = (role: Market['current_user_role'] | undefined) => role === 'OWNER' || role === 'ADMIN'
const message = (error: unknown) => error instanceof ApiError ? error.payload.message : 'Erreur réseau. Réessayez.'

function FormulaPicker({ marketId, groups, onAdded, onCancel }: { marketId: string; groups: RevisionGroup[]; onAdded: () => void; onCancel: () => void }) {
  const [query, setQuery] = useState('')
  const [templates, setTemplates] = useState<FormulaTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const load = () => { setLoading(true); setError(''); listFormulaTemplates(query).then(setTemplates).catch((caught) => setError(message(caught))).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  const select = async (template: FormulaTemplate) => {
    setBusy(template.id); setError('')
    try {
      const group = await saveRevisionGroup(marketId, { code: `FORMULA-${Date.now()}`, name: template.designation, sort_order: groups.length })
      await copyFormulaTemplate(marketId, group.id, template.id)
      onAdded()
    } catch (caught) { setError(message(caught)) } finally { setBusy('') }
  }
  return <div className="card company-form" aria-label="Catalogue universel des formules">
    <div className="section-heading"><div><h3>Choisir une formule du catalogue</h3><p className="muted">La formule est sélectionnée selon le contrat/CPS, jamais selon la désignation du prix.</p></div><button type="button" className="link-button" onClick={onCancel}>Fermer</button></div>
    {error && <div className="alert error" role="alert">{error}</div>}
    <div className="inline-actions"><input aria-label="Rechercher une formule" placeholder="Rechercher BAT3, TR2…" value={query} onChange={(event) => setQuery(event.target.value)} /><button type="button" className="secondary" onClick={load}>Rechercher</button></div>
    {loading ? <p className="state">Chargement du catalogue…</p> : templates.length === 0 ? <p className="state">Aucune formule disponible.</p> : <div className="formula-picker-list">{templates.map((template) => <article className="formula-card" key={template.id}><div className="inline-actions"><strong>{template.code || template.designation}</strong><span className="badge">{template.status}</span></div><p>{template.expression_display || 'Expression non renseignée'}</p><p className="muted">{template.designation}</p><button type="button" className="primary" disabled={busy !== '' || template.status !== 'VERIFIED'} onClick={() => void select(template)}>{busy === template.id ? 'Ajout…' : 'Sélectionner cette formule'}</button></article>)}</div>}
  </div>
}

function formulaForGroup(group: RevisionGroup): MarketFormula | undefined { return group.formulas.find((formula) => formula.status !== 'INACTIVE') }

function FormulaAssignmentCard({ group, groups, items, editable, busy, onSave }: { group: RevisionGroup; groups: RevisionGroup[]; items: PriceItem[]; editable: boolean; busy: boolean; onSave: (group: RevisionGroup, selectedIds: string[]) => void }) {
  const formula = formulaForGroup(group)
  const [selected, setSelected] = useState<string[]>(() => items.filter((item) => item.revision_group === group.id).map((item) => item.id))
  useEffect(() => { setSelected(items.filter((item) => item.revision_group === group.id).map((item) => item.id)) }, [items, group.id])
  return <article className="card assignment-card">
    <div className="assignment-card-heading"><div><p className="eyebrow">FORMULE</p><h3>{formula?.label || group.name}</h3><p className="formula-expression">{formula?.expression_display || 'Expression non renseignée'}</p></div><span className="badge">{group.code}</span></div>
    <p className="muted">Sélectionnez les prix qui relèvent explicitement de cette formule.</p>
    <div className="assignment-items">{items.map((item) => { const checked = selected.includes(item.id); const assignedElsewhere = Boolean(item.revision_group && item.revision_group !== group.id); const assignedGroup = groups.find((candidate) => candidate.id === item.revision_group); const blocked = item.classification_status === 'NON_REVISABLE' || assignedElsewhere; return <label className={`assignment-item ${blocked ? 'is-blocked' : ''}`} key={item.id}><input type="checkbox" checked={checked} disabled={!editable || busy || blocked} onChange={(event) => setSelected((current) => event.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))} /><span><strong>{item.price_number} — {item.designation}</strong><small>{item.classification_status === 'NON_REVISABLE' ? 'Sans révision explicite' : assignedElsewhere ? `Déjà affecté à ${assignedGroup?.code || 'une autre formule'}` : item.classification_status === 'PENDING_CLASSIFICATION' ? 'À affecter' : checked ? `Sélectionné pour ${group.code}` : 'Non affecté'}</small></span></label> })}</div>
    <div className="inline-actions"><p className="form-hint">{selected.length} prix sélectionné(s).</p>{editable && <button type="button" className="primary" disabled={busy} onClick={() => onSave(group, selected)}>Enregistrer l’affectation</button>}</div>
  </article>
}

export function PriceRevisionAssignmentPage() {
  const { id = '' } = useParams(); const navigate = useNavigate()
  const [market, setMarket] = useState<Market | null>(null); const [application, setApplication] = useState<RevisionApplication | null>(null); const [schedule, setSchedule] = useState<PriceSchedule | null>(null); const [groups, setGroups] = useState<RevisionGroup[]>([]); const [matrix, setMatrix] = useState<PriceMatrix | null>(null); const [loading, setLoading] = useState(true); const [busy, setBusy] = useState(false); const [picker, setPicker] = useState(false); const [validated, setValidated] = useState(false); const [error, setError] = useState('')
  const load = async () => { setLoading(true); setError(''); try { const [loadedMarket, loadedApplication, loadedSchedule, loadedGroups] = await Promise.all([getMarket(id), getRevisionApplication(id), getPriceSchedule(id), listRevisionGroups(id)]); setMarket(loadedMarket); setApplication(loadedApplication); setSchedule(loadedSchedule.schedule); setGroups(loadedGroups); setMatrix(loadedSchedule.schedule ? await getPriceMatrix(id) : null) } catch (caught) { setError(message(caught)) } finally { setLoading(false) } }
  useEffect(() => { void load() }, [id])
  const items = matrix?.items ?? []
  const total = items.length; const affected = items.filter((item) => item.revision_group !== null).length; const nonRevisable = items.filter((item) => item.classification_status === 'NON_REVISABLE').length; const pending = items.filter((item) => item.classification_status === 'PENDING_CLASSIFICATION').length; const remaining = items.filter((item) => item.revision_group === null && item.classification_status !== 'NON_REVISABLE').length
  const complete = total > 0 && remaining === 0 && pending === 0
  const editable = canEdit(market?.current_user_role)
  const groupIds = useMemo(() => new Set(groups.map((group) => group.id)), [groups])
  const saveGroup = async (group: RevisionGroup, selectedIds: string[]) => { if (!schedule) return; setBusy(true); setError(''); try { let version = schedule.change_version; const currentIds = items.filter((item) => item.revision_group === group.id).map((item) => item.id); const removed = currentIds.filter((itemId) => !selectedIds.includes(itemId)); if (removed.length > 0) { const result = await assignPriceItems(id, { action: 'UNASSIGN', price_item_ids: removed, expected_version: version }); version = result.change_version } if (selectedIds.length > 0) await assignPriceItems(id, { action: 'ASSIGN', revision_group_id: group.id, price_item_ids: selectedIds, expected_version: version }); await load() } catch (caught) { setError(message(caught)) } finally { setBusy(false) } }
  const markNonRevisable = async (item: PriceItem) => { if (!schedule) return; setBusy(true); setError(''); setValidated(false); try { await assignPriceItems(id, { action: 'NON_REVISABLE', price_item_ids: [item.id], expected_version: schedule.change_version }); await load() } catch (caught) { setError(message(caught)) } finally { setBusy(false) } }
  const validate = async () => { if (!schedule) return; setBusy(true); setError(''); try { await validatePriceAssignment(id, schedule.change_version); setValidated(true) } catch (caught) { setValidated(false); setError(message(caught)) } finally { setBusy(false) } }
  if (loading) return <p className="state">Chargement de l’affectation…</p>
  if (error && !market) return <div className="alert error" role="alert">{error}</div>
  if (!market) return null
  if (application?.revision_application_mode !== 'PRICE_ASSIGNMENT') return <section><div className="alert">Ce marché n’est pas configuré en mode Plusieurs formules.</div><Link className="secondary button-link" to={`/app/markets/${id}`}>Retour au marché</Link></section>
  return <section aria-label="Affectation des formules de révision"><div className="page-heading"><div><p className="eyebrow">MARCHÉ {market.market_number}</p><h1>Affectation des formules de révision</h1><p className="muted">Associez les prix du bordereau aux formules prévues par le marché.</p></div><Link className="link-button" to={`/app/markets/${id}`}>Retour au marché</Link></div>
    {error && <div className="alert error" role="alert">{error}</div>}
    {!schedule && <div className="card state"><h2>Bordereau requis</h2><p>Ajoutez d’abord le bordereau des prix depuis la page du marché.</p><Link className="primary button-link" to={`/app/markets/${id}`}>Retourner au BDP</Link></div>}
    {schedule && <><div className="assignment-summary card"><div><strong>{total} prix au total</strong><span>{affected} affectés</span><span>{remaining} restant(s) à affecter</span>{nonRevisable > 0 && <span>{nonRevisable} sans révision explicite</span>}</div><div className={complete ? 'assignment-ready' : 'assignment-warning'}>{validated ? 'Affectation validée' : complete ? 'Affectation complète — validation disponible' : `${pending} prix PENDING_CLASSIFICATION à traiter`}</div></div>
      <div className="section-heading"><div><h2>Formules du marché</h2><p className="muted">Ajoutez les formules prévues au contrat, puis affectez les prix.</p></div>{editable && <button type="button" className="primary" onClick={() => setPicker(true)}>+ Ajouter une formule</button>}</div>
      {picker && <FormulaPicker marketId={id} groups={groups} onAdded={() => { setPicker(false); void load() }} onCancel={() => setPicker(false)} />}
      {groups.filter((group) => groupIds.has(group.id)).length === 0 && <div className="card state">Aucune formule n’est encore associée à ce marché.</div>}
      <div className="assignment-grid">{groups.map((group) => <FormulaAssignmentCard key={group.id} group={group} groups={groups} items={items} editable={editable} busy={busy} onSave={saveGroup} />)}</div>
      {items.some((item) => item.classification_status === 'PENDING_CLASSIFICATION') && <div className="card pending-list"><h3>Prix restant à décider</h3><p className="muted">Un prix PENDING_CLASSIFICATION ne peut pas être validé sans formule ou déclaration explicite Sans révision.</p>{items.filter((item) => item.classification_status === 'PENDING_CLASSIFICATION').map((item) => <div className="pending-row" key={item.id}><span><strong>{item.price_number} — {item.designation}</strong><small>PENDING_CLASSIFICATION</small></span>{editable && <button type="button" className="secondary" disabled={busy} onClick={() => void markNonRevisable(item)}>Déclarer Sans révision</button>}</div>)}</div>}
      {pending > 0 && <div className="alert warning"><strong>Validation impossible :</strong> les prix PENDING_CLASSIFICATION doivent rester visibles et être affectés ou déclarés explicitement Sans révision.</div>}
      {editable && <div className="assignment-validation"><button type="button" className="primary" disabled={busy || !complete} onClick={() => void validate()}>Valider l’affectation</button>{!complete && <span className="muted">Chaque prix doit être affecté à une formule ou déclaré Sans révision.</span>}</div>}
      {total === 0 && <div className="card state">Le BDP est vide. Saisissez ou importez les prix avant l’affectation.</div>}
    </>}
  </section>
}
