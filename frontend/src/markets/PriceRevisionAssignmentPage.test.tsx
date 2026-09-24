import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Market, PriceMatrix, PriceSchedule, RevisionApplication, RevisionGroup, assignPriceItems, copyFormulaTemplate, getMarket, getPriceMatrix, getPriceSchedule, getRevisionApplication, listFormulaTemplates, listRevisionGroups, saveRevisionGroup } from '../lib/api'
import { PriceRevisionAssignmentPage } from './PriceRevisionAssignmentPage'
import { PriceScheduleSection } from './PriceScheduleSection'
import { RevisionApplicationSection } from './RevisionApplicationSection'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, assignPriceItems: vi.fn(), copyFormulaTemplate: vi.fn(), getMarket: vi.fn(), getPriceMatrix: vi.fn(), getPriceSchedule: vi.fn(), getRevisionApplication: vi.fn(), listFormulaTemplates: vi.fn(), listRevisionGroups: vi.fn(), saveRevisionGroup: vi.fn() }
})

const market = (mode: Market['revision_application_mode'] = 'PRICE_ASSIGNMENT'): Market => ({ id: 'market-1', company: 'company-1', company_detail: { id: 'company-1', raison_sociale: 'Entreprise A' }, market_number: 'M-001', contracting_authority: 'Commune A', subject: 'Travaux', amount_ht: null, vat_rate: null, date_limite_remise_offres: null, date_ouverture_plis: null, date_signature: null, date_os_commencement: null, contract_duration_value: null, contract_duration_unit: null, formula_structure: 'MULTIPLE', revision_application_mode: mode, global_revision_group: null, status: 'ACTIVE', notes: '', created_at: '', updated_at: '', current_user_role: 'OWNER', lots_count: 0 })
const group = (id = 'group-1', name = 'Formule 1'): RevisionGroup => ({ id, market: 'market-1', code: id === 'group-1' ? 'BAT3' : 'TR2', name, description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [{ id: `${id}-formula`, revision_group: id, version_number: 1, label: id === 'group-1' ? 'BAT3' : 'TR2', expression_display: id === 'group-1' ? 'P = P₀ × [0,15 + 0,85 × (BAT3 / BAT3₀)]' : 'P = P₀ × [expression réelle du catalogue]', constant_term: '0.15000000', status: 'VALIDATED', valid_from: null, valid_to: null, reference_period_year: null, reference_period_month: null, reference_rule_code: '', reference_source: '', created_by: 'user-1', created_at: '', updated_at: '', validated_at: '', terms: [] }] })
const schedule: PriceSchedule = { id: 'schedule-1', market: 'market-1', status: 'DRAFT', source_type: 'MANUAL', name: '', notes: '', change_version: 2, item_count: 3, created_at: '', updated_at: '' }
const matrix: PriceMatrix = { mode: 'PRICE_ASSIGNMENT', price_schedule_required: true, formulas: [{ id: 'group-1', name: 'Formule 1', code: 'BAT3', formulas: group().formulas }], items: [
  { id: 'item-1', price_schedule: 'schedule-1', lot: null, price_number: '001', designation: 'Fourniture câble HTA', unit: 'ml', estimated_quantity: '1', unit_price_ht: '1', estimated_amount_ht: '1', revision_group: 'group-1', classification_status: 'REVISABLE', active: true, notes: '', created_at: '', updated_at: '' },
  { id: 'item-2', price_schedule: 'schedule-1', lot: null, price_number: '002', designation: 'Pose câble HTA', unit: 'ml', estimated_quantity: '1', unit_price_ht: '1', estimated_amount_ht: '1', revision_group: null, classification_status: 'PENDING_CLASSIFICATION', active: true, notes: '', created_at: '', updated_at: '' },
  { id: 'item-3', price_schedule: 'schedule-1', lot: null, price_number: '003', designation: 'Tranchée', unit: 'ml', estimated_quantity: '1', unit_price_ht: '1', estimated_amount_ht: '1', revision_group: null, classification_status: 'NON_REVISABLE', active: true, notes: '', created_at: '', updated_at: '' },
] }
const application: RevisionApplication = { revision_application_mode: 'PRICE_ASSIGNMENT', global_revision_group: null, global_formula: null, price_schedule_required: true, updated_at: '' }

describe('LOT 2B multi-formula workflow', () => {
  beforeEach(() => { vi.mocked(getMarket).mockResolvedValue(market()); vi.mocked(getRevisionApplication).mockResolvedValue(application); vi.mocked(getPriceSchedule).mockResolvedValue({ required: true, schedule }); vi.mocked(getPriceMatrix).mockResolvedValue(matrix); vi.mocked(listRevisionGroups).mockResolvedValue([group()]); vi.mocked(listFormulaTemplates).mockResolvedValue([{ id: 'template-tr2', family_key: 'tr2', version_number: 1, scope: 'GLOBAL', owner_company: null, code: 'TR2', designation: 'TR2', description: '', domain: 'Voirie', expression_display: 'P = P₀ × [expression réelle du catalogue]', constant_term: '0.15', status: 'VERIFIED', valid_from: null, valid_to: null, source_type: 'OFFICIAL', source_title: 'Catalogue', source_url: '', source_reference: '', source_date: null, verification_status: 'VERIFIED', verified_at: null, verified_by: null, notes: '', created_at: '', updated_at: '', terms: [] }]); vi.mocked(assignPriceItems).mockResolvedValue({ updated: 1, change_version: 3 }); vi.mocked(saveRevisionGroup).mockResolvedValue(group('group-2', 'TR2')); vi.mocked(copyFormulaTemplate).mockResolvedValue(group('group-2', 'TR2').formulas[0]); })

  it('affiche le BDP avant les formules et sans libellé artificiel sur la page marché', async () => {
    render(<RevisionApplicationSection marketId="market-1" role="OWNER" initialMode="PRICE_ASSIGNMENT" />)
    expect(await screen.findByText("Ajoutez le bordereau des prix du marché afin d'affecter les prix aux différentes formules de révision.")).toBeInTheDocument()
    expect(screen.queryByText('Ajouter une formule de révision')).not.toBeInTheDocument()
    expect(screen.queryByText('ELEC')).not.toBeInTheDocument()
  })

  it('ouvre la page dédiée, affiche l’expression et les compteurs de classification', async () => {
    render(<MemoryRouter initialEntries={['/app/markets/market-1/price-revision-assignment']}><Routes><Route path="/app/markets/:id/price-revision-assignment" element={<PriceRevisionAssignmentPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByText('Affectation des formules de révision')).toBeInTheDocument()
    expect(screen.getByText('P = P₀ × [0,15 + 0,85 × (BAT3 / BAT3₀)]')).toBeInTheDocument()
    expect(screen.getByText('3 prix au total')).toBeInTheDocument()
    expect(screen.getByText('1 affectés')).toBeInTheDocument()
    expect(screen.getByText('1 restant(s) à affecter')).toBeInTheDocument()
    expect(screen.getAllByText(/PENDING_CLASSIFICATION/).length).toBeGreaterThan(0)
    expect(screen.getByText('Sans révision explicite')).toBeInTheDocument()
  })

  it('affecte un prix par la route bulk exclusive et permet une seconde formule du catalogue', async () => {
    render(<MemoryRouter initialEntries={['/app/markets/market-1/price-revision-assignment']}><Routes><Route path="/app/markets/:id/price-revision-assignment" element={<PriceRevisionAssignmentPage />} /></Routes></MemoryRouter>)
    await screen.findByText('Affectation des formules de révision')
    await screen.findByText('1 prix sélectionné(s).')
    fireEvent.click(screen.getByRole('checkbox', { name: /002 — Pose câble HTA/ }))
    await screen.findByText('2 prix sélectionné(s).')
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer l’affectation' }))
    await vi.waitFor(() => expect(assignPriceItems).toHaveBeenCalledWith('market-1', expect.objectContaining({ action: 'ASSIGN', revision_group_id: 'group-1', price_item_ids: ['item-1', 'item-2'] })))
    fireEvent.click(screen.getByRole('button', { name: '+ Ajouter une formule' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Sélectionner cette formule' }))
    await vi.waitFor(() => expect(saveRevisionGroup).toHaveBeenCalledWith('market-1', expect.objectContaining({ name: 'TR2' })))
    expect(copyFormulaTemplate).toHaveBeenCalledWith('market-1', 'group-2', 'template-tr2')
  })

  it('affiche directement un BDP existant avec ses actions', async () => {
    render(<MemoryRouter><PriceScheduleSection marketId="market-1" role="OWNER" mode="PRICE_ASSIGNMENT" /></MemoryRouter>)
    expect(await screen.findByText('Bordereau disponible — 3 prix')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Affecter les formules aux prix' })).toHaveAttribute('href', '/app/markets/market-1/price-revision-assignment')
  })

  it('affiche le CODE et l’expression après sélection en formule unique', async () => {
    vi.mocked(getRevisionApplication).mockResolvedValue({ ...application, revision_application_mode: 'GLOBAL_FORMULA', global_revision_group: 'group-1', global_formula: group().formulas[0], price_schedule_required: false })
    vi.mocked(listRevisionGroups).mockResolvedValue([group()])
    render(<RevisionApplicationSection marketId="market-1" role="OWNER" initialMode="GLOBAL_FORMULA" />)
    expect(await screen.findByText('BAT3')).toBeInTheDocument()
    expect(screen.getByText('P = P₀ × [0,15 + 0,85 × (BAT3 / BAT3₀)]')).toBeInTheDocument()
    expect(screen.queryByText('ELEC')).not.toBeInTheDocument()
  })
})
