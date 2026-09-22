import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { FormulaTemplate, getRevisionApplication, listFormulaTemplates, listRevisionGroups, saveRevisionApplication, saveRevisionGroup, copyFormulaTemplate } from '../lib/api'
import { RevisionApplicationSection } from './RevisionApplicationSection'
import { FormulaCatalogSelector } from './FormulaCatalogSelector'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, copyFormulaTemplate: vi.fn(), getRevisionApplication: vi.fn(), listFormulaTemplates: vi.fn(), listRevisionGroups: vi.fn(), saveRevisionApplication: vi.fn(), saveRevisionGroup: vi.fn() }
})

const template = (code: string, designation: string, expression = `P = P₀ × [0,15 + 0,85 × ${code}/${code}₀]`): FormulaTemplate => ({
  id: `template-${code}`, family_key: `family-${code}`, version_number: 1, scope: 'GLOBAL', owner_company: null,
  code, designation, description: '', domain: code.startsWith('BAT') ? 'Bâtiment' : 'Travaux routiers', expression_display: expression,
  constant_term: '0.15', status: 'VERIFIED', valid_from: null, valid_to: null, source_type: 'OFFICIAL', source_title: 'Catalogue V1', source_url: '', source_reference: 'V1', source_date: null,
  verification_status: 'VERIFIED', verified_at: null, verified_by: null, notes: '', created_at: '', updated_at: '', terms: [{ id: `term-${code}`, position: 1, coefficient: '0.85', term_type: 'INDEX_RATIO', index_code: code, base_period_year: null, base_period_month: null, base_value: null, base_source: '', reference_note: '' }],
})

describe('V1-A — marché simple + formule unique', () => {
  beforeEach(() => {
    vi.mocked(listFormulaTemplates).mockResolvedValue([template('BAT1', 'Gros œuvre, revêtement, étanchéité'), template('BAT3', 'Électricité'), template('TR1', 'Terrassements')])
    vi.mocked(listRevisionGroups).mockResolvedValue([])
    vi.mocked(getRevisionApplication).mockResolvedValue({ revision_application_mode: 'PRICE_ASSIGNMENT', global_revision_group: null, global_formula: null, price_schedule_required: true, updated_at: '' })
    vi.mocked(saveRevisionGroup).mockResolvedValue({ id: 'group-1', market: 'market-1', code: 'BAT3', name: 'Électricité', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [] })
    vi.mocked(copyFormulaTemplate).mockResolvedValue({ id: 'formula-1', revision_group: 'group-1', version_number: 1, label: 'Électricité', expression_display: 'P = P₀ × [0,15 + 0,85 × BAT3/BAT3₀]', constant_term: '0.15', status: 'DRAFT', valid_from: null, valid_to: null, reference_period_year: null, reference_period_month: null, reference_rule_code: '', reference_source: '', source_template: 'template-BAT3', source_template_version: 1, created_by: 'user-1', created_at: '', updated_at: '', validated_at: null, terms: [template('BAT3', 'Électricité').terms[0]] })
    vi.mocked(saveRevisionApplication).mockResolvedValue({ revision_application_mode: 'GLOBAL_FORMULA', global_revision_group: 'group-1', global_formula: null, price_schedule_required: false, updated_at: '' })
  })

  it('ouvre le catalogue sans recherche préalable et affiche code, désignation et expression', async () => {
    render(<FormulaCatalogSelector editable onSelect={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /Sélectionner une formule/ }))
    expect(await screen.findByText('BAT3')).toBeInTheDocument()
    expect(screen.getByText('Électricité')).toBeInTheDocument()
    expect(screen.getByText('P = P₀ × [0,15 + 0,85 × BAT3/BAT3₀]')).toBeInTheDocument()
  })

  it('utilise la recherche comme filtre facultatif du catalogue', async () => {
    render(<FormulaCatalogSelector editable onSelect={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /Sélectionner une formule/ }))
    const search = await screen.findByRole('textbox', { name: 'Rechercher une formule...' })
    expect(screen.getByText('BAT1')).toBeInTheDocument()
    fireEvent.change(search, { target: { value: 'BAT3' } })
    expect(screen.getByText('BAT3')).toBeInTheDocument()
    expect(screen.queryByText('BAT1')).not.toBeInTheDocument()
  })

  it('présente le parcours V1 comme une formule unique sans options multi-formules', async () => {
    render(<RevisionApplicationSection marketId="market-1" role="OWNER" initialMode="GLOBAL_FORMULA" v1Simple />)
    expect(await screen.findByText('FORMULE DE RÉVISION DU MARCHÉ')).toBeInTheDocument()
    expect(screen.queryByText("Une seule formule pour l'ensemble du marché")).not.toBeInTheDocument()
    expect(screen.queryByText('Plusieurs formules')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Sélectionner une formule/ }))
    expect(await screen.findByText('BAT3')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Rechercher une formule...' })).toBeInTheDocument()
  })
})
