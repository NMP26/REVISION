import { FormEvent, useEffect, useState } from 'react'
import { ApiError, MarketFormula, FormulaTerm, RevisionGroup, listRevisionGroups, saveMarketFormula, saveRevisionGroup } from '../lib/api'

type Props = { marketId: string; role: string | null | undefined }
type TermDraft = Omit<FormulaTerm, 'id' | 'created_at' | 'updated_at'>

const blankTerm = (position: number): TermDraft => ({ position, coefficient: '', term_type: 'INDEX_RATIO', index_code: '', base_period_year: null, base_period_month: null, base_value: '', base_source: '', reference_note: '' })
const blankFormula = () => ({ label: '', expression_display: '', constant_term: '', status: 'DRAFT' as const, terms: [blankTerm(1)] })
const canEdit = (role: string | null | undefined) => role === 'OWNER' || role === 'ADMIN'

function errorMessage(error: unknown) { return error instanceof ApiError ? error.payload.message : 'Erreur réseau. Réessayez.' }

function FormulaEditor({ marketId, group, formula, onSaved, onCancel }: { marketId: string; group: RevisionGroup; formula?: MarketFormula; onSaved: () => void; onCancel: () => void }) {
  const [values, setValues] = useState(() => formula ? { label: formula.label, expression_display: formula.expression_display, constant_term: formula.constant_term ?? '', status: formula.status, terms: formula.terms.map(({ id: _id, created_at: _created, updated_at: _updated, ...term }) => term) } : blankFormula())
  const [error, setError] = useState(''); const [saving, setSaving] = useState(false)
  const locked = formula?.status === 'VALIDATED' || formula?.status === 'INACTIVE'
  const updateTerm = (index: number, changes: Partial<TermDraft>) => setValues((current) => ({ ...current, terms: current.terms.map((term, termIndex) => termIndex === index ? { ...term, ...changes } : term) }))
  const save = async (status = values.status) => {
    setError(''); setSaving(true)
    try {
      await saveMarketFormula(marketId, group.id, { label: values.label, expression_display: values.expression_display, constant_term: values.constant_term || null, status, terms: values.terms.map((term, index) => ({ ...term, position: index + 1, base_value: term.base_value || null })) }, formula?.id)
      onSaved()
    } catch (caught) { setError(errorMessage(caught)) } finally { setSaving(false) }
  }
  const submit = (event: FormEvent) => { event.preventDefault(); void save() }
  return <form className="card company-form" onSubmit={submit}>
    <h3>{formula ? `Formule v${formula.version_number}` : 'Nouvelle formule'}</h3>
    {error && <div className="alert error" role="alert">{error}</div>}
    {locked && <div className="alert">Cette formule est verrouillée car elle est {formula?.status === 'VALIDATED' ? 'validée' : 'inactive'}.</div>}
    <label>Libellé<input value={values.label} disabled={locked} onChange={(event) => setValues((current) => ({ ...current, label: event.target.value }))} required /></label>
    <label>Expression affichée<input value={values.expression_display} disabled={locked} onChange={(event) => setValues((current) => ({ ...current, expression_display: event.target.value }))} placeholder="K = 0,15 + 0,85 × BAT3/BAT3₀" /></label>
    <label>Constante C<input value={values.constant_term} disabled={locked} inputMode="decimal" onChange={(event) => setValues((current) => ({ ...current, constant_term: event.target.value }))} /></label>
    <h4>Termes</h4>
    {values.terms.map((term, index) => <div className="form-grid" key={index}>
      <input aria-label={`Position ${index + 1}`} value={index + 1} readOnly />
      <input aria-label={`Coefficient ${index + 1}`} value={term.coefficient} disabled={locked} placeholder="0,85000000" inputMode="decimal" onChange={(event) => updateTerm(index, { coefficient: event.target.value })} />
      <input aria-label={`Code index ${index + 1}`} value={term.index_code} disabled={locked} placeholder="BAT3" onChange={(event) => updateTerm(index, { index_code: event.target.value })} />
      <input aria-label={`Valeur de base ${index + 1}`} value={term.base_value ?? ''} disabled={locked} placeholder="337,80000000" inputMode="decimal" onChange={(event) => updateTerm(index, { base_value: event.target.value })} />
      {!locked && <button type="button" className="link-button" onClick={() => setValues((current) => ({ ...current, terms: current.terms.filter((_, termIndex) => termIndex !== index).map((item, termIndex) => ({ ...item, position: termIndex + 1 })) }))} disabled={values.terms.length === 1}>Supprimer</button>}
    </div>)}
    {!locked && <div className="inline-actions"><button type="button" className="secondary" onClick={() => setValues((current) => ({ ...current, terms: [...current.terms, blankTerm(current.terms.length + 1)] }))}>Ajouter un terme</button><button type="submit" className="primary" disabled={saving}>{saving ? 'Enregistrement…' : 'Enregistrer'}</button>{formula && <button type="button" className="secondary" disabled={saving} onClick={() => void save('VALIDATED')}>Valider</button>}</div>}
    <button type="button" className="link-button" onClick={onCancel}>Annuler</button>
  </form>
}

export function RevisionFormulaSection({ marketId, role }: Props) {
  const [groups, setGroups] = useState<RevisionGroup[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState(''); const [editing, setEditing] = useState<{ group: RevisionGroup; formula?: MarketFormula } | null>(null); const [newGroup, setNewGroup] = useState(false); const [groupName, setGroupName] = useState(''); const [groupCode, setGroupCode] = useState('')
  const editable = canEdit(role)
  const load = () => { setLoading(true); setError(''); listRevisionGroups(marketId).then(setGroups).catch((caught) => setError(errorMessage(caught))).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [marketId])
  const createGroup = async () => { try { const created = await saveRevisionGroup(marketId, { code: groupCode, name: groupName, sort_order: groups.length }); setGroups((current) => [...current, created]); setGroupName(''); setGroupCode(''); setNewGroup(false) } catch (caught) { setError(errorMessage(caught)) } }
  const deactivate = async (group: RevisionGroup, formula: MarketFormula) => { try { await saveMarketFormula(marketId, group.id, { status: 'INACTIVE' }, formula.id); load() } catch (caught) { setError(errorMessage(caught)) } }
  if (loading) return <section><div className="section-heading"><h2>Formules de révision</h2></div><p className="state">Chargement…</p></section>
  return <section aria-label="Formules de révision"><div className="section-heading"><div><p className="eyebrow">STRUCTURE CONTRACTUELLE</p><h2>Formules de révision</h2></div>{editable && <button className="primary" onClick={() => setNewGroup(true)}>Ajouter un groupe</button>}</div>
    {error && <div className="alert error" role="alert">{error}<button className="link-button" onClick={load}>Réessayer</button></div>}
    {newGroup && <div className="card company-form"><label>Code<input value={groupCode} onChange={(event) => setGroupCode(event.target.value)} /></label><label>Nom<input value={groupName} onChange={(event) => setGroupName(event.target.value)} /></label><div className="inline-actions"><button className="primary" type="button" onClick={() => void createGroup()}>Créer le groupe</button><button className="link-button" type="button" onClick={() => setNewGroup(false)}>Annuler</button></div></div>}
    {groups.length === 0 && !newGroup ? <div className="card state">Aucun groupe de révision n’est enregistré.</div> : groups.map((group) => <div className="card" key={group.id}><div className="section-heading"><div><h3>{group.name}</h3><span className="muted">{group.code}</span></div>{editable && <button className="secondary" onClick={() => setEditing({ group })}>Ajouter une formule</button>}</div>{group.formulas.length === 0 && <p className="muted">Aucune formule. Créez une formule DRAFT pour commencer.</p>}{group.formulas.map((formula) => <div className="formula-card" key={formula.id}><div className="inline-actions"><strong>{formula.label}</strong><span className={`badge ${formula.status.toLowerCase()}`}>{formula.status === 'DRAFT' ? 'Brouillon' : formula.status === 'VALIDATED' ? 'Validée' : 'Inactive'}</span><span>Version {formula.version_number}</span></div>{formula.expression_display && <p>{formula.expression_display}</p>}<p>Constante : {formula.constant_term ?? '—'}</p><ul>{formula.terms.map((term) => <li key={term.id ?? term.position}>{term.index_code} — coefficient {term.coefficient} — base {term.base_value ?? '—'}</li>)}</ul>{editable && formula.status === 'DRAFT' && <button className="secondary" onClick={() => setEditing({ group, formula })}>Modifier</button>}{editable && formula.status === 'VALIDATED' && <button className="secondary" onClick={() => void deactivate(group, formula)}>Désactiver</button>}</div>)}</div>)}
    {editing && <FormulaEditor marketId={marketId} group={editing.group} formula={editing.formula} onSaved={() => { setEditing(null); load() }} onCancel={() => setEditing(null)} />}
  </section>
}
