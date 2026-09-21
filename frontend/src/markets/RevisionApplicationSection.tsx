import { useEffect, useState } from 'react'
import { ApiError, RevisionApplication, RevisionGroup, getRevisionApplication, listRevisionGroups, saveRevisionApplication } from '../lib/api'

type Props = { marketId: string; role: string | null | undefined; initialMode?: RevisionApplication['revision_application_mode'] }
const canEdit = (role: string | null | undefined) => role === 'OWNER' || role === 'ADMIN'
const message = (error: unknown) => error instanceof ApiError ? error.payload.message : 'Erreur réseau. Réessayez.'

export function RevisionApplicationSection({ marketId, role, initialMode }: Props) {
  const [application, setApplication] = useState<RevisionApplication | null>(null)
  const [groups, setGroups] = useState<RevisionGroup[]>([])
  const [mode, setMode] = useState<RevisionApplication['revision_application_mode']>(initialMode ?? 'PRICE_ASSIGNMENT')
  const [groupId, setGroupId] = useState(''); const [loading, setLoading] = useState(Boolean(initialMode)); const [saving, setSaving] = useState(false); const [error, setError] = useState('')
  const editable = canEdit(role)
  useEffect(() => {
    if (!initialMode) return
    setLoading(true)
    Promise.all([getRevisionApplication(marketId), listRevisionGroups(marketId)]).then(([loaded, loadedGroups]) => { setApplication(loaded); setMode(loaded.revision_application_mode); setGroupId(loaded.global_revision_group ?? ''); setGroups(loadedGroups) }).catch((caught) => setError(message(caught))).finally(() => setLoading(false))
  }, [marketId, initialMode])
  const save = async (nextMode = mode) => {
    setError(''); setSaving(true)
    try { const saved = await saveRevisionApplication(marketId, { revision_application_mode: nextMode, global_revision_group: nextMode === 'GLOBAL_FORMULA' ? groupId || null : null }); setApplication(saved); setMode(saved.revision_application_mode); setGroupId(saved.global_revision_group ?? '') } catch (caught) { setError(message(caught)) } finally { setSaving(false) }
  }
  if (!initialMode) return null
  return <section aria-label="Application de la révision"><div className="section-heading"><div><p className="eyebrow">PÉRIMÈTRE DE RÉVISION</p><h2>Application de la révision</h2></div></div>
    <div className="card company-form"><p><strong>Comment la révision des prix s'applique-t-elle à ce marché ?</strong></p>
      <label><input type="radio" name={`mode-${marketId}`} checked={mode === 'GLOBAL_FORMULA'} disabled={!editable || saving} onChange={() => setMode('GLOBAL_FORMULA')} /> Une seule formule pour l'ensemble du marché</label>
      <label><input type="radio" name={`mode-${marketId}`} checked={mode === 'PRICE_ASSIGNMENT'} disabled={!editable || saving} onChange={() => { setMode('PRICE_ASSIGNMENT'); void save('PRICE_ASSIGNMENT') }} /> Affectation des formules prix par prix</label>
      {loading && <p className="state">Chargement…</p>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {mode === 'GLOBAL_FORMULA' && <label>Formule de révision<select value={groupId} disabled={!editable || saving} onChange={(event) => { setGroupId(event.target.value); if (event.target.value) void save('GLOBAL_FORMULA') }}><option value="">Sélectionner une formule</option>{groups.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}</select></label>}
      {mode === 'GLOBAL_FORMULA' && application?.global_formula && <div className="alert">Formule globale : {application.global_formula.label}<br />Partie fixe : {application.global_formula.constant_term ?? '—'}<br />Partie variable calculée selon les coefficients indicés.</div>}
      {mode === 'GLOBAL_FORMULA' && <p className="muted">Le BDP détaillé n'est pas obligatoire pour poursuivre la révision.</p>}
    </div>
  </section>
}
