import { useEffect, useMemo, useState } from 'react'
import { ApiError, FormulaTemplate, listFormulaTemplates } from '../lib/api'

type Props = {
  editable: boolean
  onSelect: (template: FormulaTemplate) => void
  onCancel?: () => void
  ariaLabel?: string
  alwaysOpen?: boolean
}

const message = (error: unknown) => error instanceof ApiError ? error.payload.message : 'Erreur réseau. Réessayez.'

function searchableText(template: FormulaTemplate) {
  return [
    template.code,
    template.designation,
    template.domain,
    template.expression_display,
    ...template.terms.flatMap((term) => [term.index_code, term.coefficient]),
  ].join(' ').toLocaleLowerCase()
}

export function formulaExpression(template: FormulaTemplate) {
  return template.expression_display?.trim() || 'Expression non renseignée'
}

export function FormulaCatalogSelector({ editable, onSelect, onCancel, ariaLabel = 'Catalogue des formules officielles', alwaysOpen = false }: Props) {
  const [open, setOpen] = useState(alwaysOpen)
  const [query, setQuery] = useState('')
  const [templates, setTemplates] = useState<FormulaTemplate[]>([])
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open || loaded) return
    setLoading(true)
    setError('')
    listFormulaTemplates()
      .then((loadedTemplates) => { setTemplates(loadedTemplates); setLoaded(true) })
      .catch((caught) => setError(message(caught)))
      .finally(() => setLoading(false))
  }, [loaded, open])

  const filteredTemplates = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase()
    if (!normalizedQuery) return templates
    return templates.filter((template) => searchableText(template).includes(normalizedQuery))
  }, [query, templates])

  const select = async (template: FormulaTemplate) => {
    setBusy(template.id)
    setError('')
    try {
      await onSelect(template)
      setOpen(false)
      setQuery('')
    } catch (caught) {
      setError(message(caught))
    } finally {
      setBusy('')
    }
  }

  return <div className="formula-selector" aria-label={ariaLabel}>
    <button
      type="button"
      className="formula-selector-trigger"
      aria-haspopup="listbox"
      aria-expanded={open}
      onClick={() => { if (!alwaysOpen) setOpen((current) => !current) }}
    >
      <span>
        <strong>Formule officielle de révision</strong>
      <small>{open ? 'Choisissez une formule dans le catalogue' : 'Cliquez pour afficher le catalogue'}</small>
      </span>
      <span className="formula-selector-value">Sélectionner une formule <span aria-hidden="true">▾</span></span>
    </button>
    {open && <div className="formula-selector-popover" role="dialog" aria-label="Sélectionner une formule">
      <div className="formula-selector-search">
        <label htmlFor={`${ariaLabel.replaceAll(' ', '-')}-search`}>Rechercher une formule...</label>
        <input
          id={`${ariaLabel.replaceAll(' ', '-')}-search`}
          aria-label="Rechercher une formule..."
          placeholder="Rechercher une formule..."
          value={query}
          autoFocus
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      {error && <div className="alert error" role="alert">{error}</div>}
      {loading ? <p className="state">Chargement du catalogue…</p> : filteredTemplates.length === 0 ? <p className="state">Aucune formule disponible.</p> : <div className="formula-picker-list" role="listbox" aria-label="Formules disponibles">
        {Array.from(new Map(filteredTemplates.map((template) => [template.domain || 'Domaine non renseigné', filteredTemplates.filter((candidate) => (candidate.domain || 'Domaine non renseigné') === (template.domain || 'Domaine non renseigné'))])).entries()).map(([domain, domainTemplates]) => <section className="formula-domain" key={domain}><h4>{domain}</h4>{domainTemplates.map((template) => <article className="formula-card formula-option" key={template.id} role="option" aria-label={`${template.code} — ${template.designation}`}>
          <div className="formula-option-heading"><strong>{template.code}</strong><span className="badge">{template.status}</span></div>
          <p className="formula-designation">{template.designation || 'Désignation non renseignée'}</p>
          <p className="muted">{template.domain || 'Domaine non renseigné'}</p>
          <p className="formula-expression">{formulaExpression(template)}</p>
          <p className="muted">Version {template.version_number}</p>
          {editable ? <button type="button" className="primary" disabled={busy !== '' || template.status !== 'VERIFIED'} onClick={() => void select(template)}>{busy === template.id ? 'Sélection…' : template.status === 'VERIFIED' ? 'Sélectionner cette formule' : 'Non disponible'}</button> : <span className="muted">Lecture seule</span>}
        </article>)}</section>)}
      </div>}
      {onCancel && <button type="button" className="link-button" onClick={onCancel}>Annuler</button>}
    </div>}
  </div>
}
