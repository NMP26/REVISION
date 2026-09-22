import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, Company, FormulaTemplate, Market, copyFormulaTemplate, getMarket, listAuthorities, listCompanies, listConsortia, listFormulaTemplates, listMarketLots, listMarkets, listRevisionGroups, saveMarketFormula, saveRevisionGroup } from '../lib/api'
import { MarketDetailPage, MarketsPage } from './MarketsPage'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, copyFormulaTemplate: vi.fn(), getMarket: vi.fn(), listAuthorities: vi.fn(), listCompanies: vi.fn(), listConsortia: vi.fn(), listFormulaTemplates: vi.fn(), listMarketLots: vi.fn(), listMarkets: vi.fn(), listRevisionGroups: vi.fn(), saveMarketFormula: vi.fn(), saveRevisionGroup: vi.fn() }
})

const market = (role: Market['current_user_role']): Market => ({ id: 'market-1', company: 'company-1', company_detail: { id: 'company-1', raison_sociale: 'Entreprise A' }, market_number: 'M-001', contracting_authority: 'Commune A', subject: 'Travaux', amount_ht: null, vat_rate: null, date_limite_remise_offres: null, date_ouverture_plis: null, date_signature: null, date_os_commencement: null, contract_duration_value: null, contract_duration_unit: null, formula_structure: 'MULTIPLE', status: 'ACTIVE', notes: '', created_at: '', updated_at: '', current_user_role: role, lots_count: 0 })

describe('MarketsPage', () => {
  beforeEach(() => { vi.mocked(listMarkets).mockReset(); vi.mocked(getMarket).mockReset(); vi.mocked(listAuthorities).mockReset(); vi.mocked(listCompanies).mockReset(); vi.mocked(listConsortia).mockReset(); vi.mocked(listFormulaTemplates).mockReset(); vi.mocked(copyFormulaTemplate).mockReset(); vi.mocked(listMarketLots).mockReset(); vi.mocked(listRevisionGroups).mockReset(); vi.mocked(saveMarketFormula).mockReset(); vi.mocked(saveRevisionGroup).mockReset(); vi.mocked(listCompanies).mockResolvedValue([]); vi.mocked(listAuthorities).mockResolvedValue([]); vi.mocked(listConsortia).mockResolvedValue([]); vi.mocked(listRevisionGroups).mockResolvedValue([]) })

  const template = (status: FormulaTemplate['status'] = 'VERIFIED'): FormulaTemplate => ({ id: 'template-1', family_key: 'family-1', version_number: 1, scope: 'GLOBAL', owner_company: null, code: 'EXAMPLE-001', designation: 'Modèle contractuel', description: '', domain: 'Test', expression_display: 'K = C + A × I/I₀', constant_term: '0.15000000', status, valid_from: null, valid_to: null, source_type: 'CONTRACT_EXAMPLE', source_title: 'CPS de test', source_url: '', source_reference: 'FIXTURE-001', source_date: null, verification_status: 'VERIFIED', verified_at: '', verified_by: null, notes: '', created_at: '', updated_at: '', terms: [{ id: 'template-term-1', position: 1, coefficient: '0.85000000', term_type: 'INDEX_RATIO', index_code: 'IDX-TEST', base_period_year: null, base_period_month: null, base_value: '100.00000000', base_source: '', reference_note: '' }] })

  it('affiche un état vide', async () => {
    vi.mocked(listMarkets).mockResolvedValue([])
    render(<MemoryRouter><MarketsPage /></MemoryRouter>)
    expect(await screen.findByText('Aucun marché accessible.')).toBeInTheDocument()
  })

  it('affiche les marchés et leurs informations principales', async () => {
    vi.mocked(listMarkets).mockResolvedValue([market('OWNER')])
    render(<MemoryRouter><MarketsPage /></MemoryRouter>)
    expect(await screen.findByText('M-001')).toBeInTheDocument()
    expect(screen.getByText('Entreprise A · Commune A')).toBeInTheDocument()
  })

  it('affiche les lots et l’action de modification pour OWNER', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER'))
    vi.mocked(listMarketLots).mockResolvedValue([{ id: 'lot-1', market: 'market-1', lot_number: '1', title: 'Lot principal', description: '', amount_ht: null, display_order: 0, active: true, notes: '', created_at: '', updated_at: '' }])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByText('Lot 1 — Lot principal')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Modifier' })).toHaveLength(2)
  })

  it('affiche une formule multi-termes avec son statut et ses décimales', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER'))
    vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([{
      id: 'group-1', market: 'market-1', code: 'ELEC', name: 'Travaux électriques', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '',
      formulas: [{ id: 'formula-1', revision_group: 'group-1', version_number: 1, label: 'Formule BAT3', expression_display: 'K = 0,15 + 0,85 × BAT3/BAT3₀', constant_term: '0.15000000', status: 'VALIDATED', valid_from: null, valid_to: null, reference_period_year: null, reference_period_month: null, reference_rule_code: '', reference_source: '', created_by: 'user-1', created_at: '', updated_at: '', validated_at: '', terms: [{ id: 'term-1', position: 1, coefficient: '0.85000000', term_type: 'INDEX_RATIO', index_code: 'BAT3', base_period_year: null, base_period_month: null, base_value: '337.80000000', base_source: '', reference_note: '' }] }],
    }])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    await vi.waitFor(() => expect(screen.getByText('Formules de révision')).toBeInTheDocument())
    expect(screen.getByText('Travaux électriques')).toBeInTheDocument()
    expect(screen.getByText('Validée')).toBeInTheDocument()
    expect(screen.getByText('Partie variable calculée : 0.85000000')).toBeInTheDocument()
    expect(screen.getByText('K = 0,15 + 0,85 × BAT3/BAT3₀')).toBeInTheDocument()
  })

  it('permet d’éditer un DRAFT et de demander sa validation', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([{ id: 'group-1', market: 'market-1', code: 'ELEC', name: 'Électricité', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [{ id: 'formula-1', revision_group: 'group-1', version_number: 1, label: 'Brouillon', expression_display: '', constant_term: '0.15', status: 'DRAFT', valid_from: null, valid_to: null, reference_period_year: null, reference_period_month: null, reference_rule_code: '', reference_source: '', created_by: 'user-1', created_at: '', updated_at: '', validated_at: null, terms: [{ id: 'term-1', position: 1, coefficient: '0.85', term_type: 'INDEX_RATIO', index_code: 'BAT3', base_period_year: null, base_period_month: null, base_value: '100', base_source: '', reference_note: '' }] }] }])
    vi.mocked(saveMarketFormula).mockResolvedValue({} as never)
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    await screen.findAllByText('Brouillon')
    const editButtons = await screen.findAllByRole('button', { name: 'Modifier' })
    fireEvent.click(editButtons[editButtons.length - 1])
    fireEvent.change(screen.getByLabelText('Partie fixe'), { target: { value: '0.20' } })
    fireEvent.click(screen.getByRole('button', { name: 'Valider' }))
    await vi.waitFor(() => expect(saveMarketFormula).toHaveBeenCalledWith('market-1', 'group-1', expect.objectContaining({ status: 'VALIDATED' }), 'formula-1'))
  })

  it('affiche un template GLOBAL et le copie vers une formule DRAFT', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([{ id: 'group-1', market: 'market-1', code: 'GEN', name: 'Général', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [] }])
    vi.mocked(listFormulaTemplates).mockResolvedValue([template()]); vi.mocked(copyFormulaTemplate).mockResolvedValue({} as never)
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Choisir une formule' }))
    expect(await screen.findByText('Modèle contractuel')).toBeInTheDocument()
    expect(screen.getByText('Vérifiez que cette formule correspond au CPS de votre marché.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Sélectionner cette formule' }))
    await vi.waitFor(() => expect(copyFormulaTemplate).toHaveBeenCalledWith('market-1', 'group-1', 'template-1'))
  })

  it('permet au MEMBER de consulter les templates sans pouvoir les copier', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('MEMBER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([{ id: 'group-1', market: 'market-1', code: 'GEN', name: 'Général', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [] }])
    vi.mocked(listFormulaTemplates).mockResolvedValue([template()])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Consulter les formules' }))
    expect(await screen.findByText('Modèle contractuel')).toBeInTheDocument()
    expect(screen.getByText('Lecture seule')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sélectionner cette formule' })).not.toBeInTheDocument()
  })

  it('affiche les erreurs backend de mutation de formule', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([])
    vi.mocked(saveRevisionGroup).mockResolvedValue({ id: 'group-1', market: 'market-1', code: 'GEN', name: 'Général', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [] })
    vi.mocked(listFormulaTemplates).mockResolvedValue([template()])
    vi.mocked(copyFormulaTemplate).mockRejectedValue(new ApiError(400, { code: 'VALIDATION_ERROR', message: 'Formule invalide.' }))
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Ajouter une formule de révision' }))
    fireEvent.click(screen.getByRole('button', { name: 'Choisir dans la bibliothèque' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Sélectionner cette formule' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Formule invalide.')
  })

  it('verrouille une formule INACTIVE sans action de mutation', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(listRevisionGroups).mockResolvedValue([{ id: 'group-1', market: 'market-1', code: 'ELEC', name: 'Électricité', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [{ id: 'formula-1', revision_group: 'group-1', version_number: 1, label: 'Inactive', expression_display: '', constant_term: '0.15', status: 'INACTIVE', valid_from: null, valid_to: null, reference_period_year: null, reference_period_month: null, reference_rule_code: '', reference_source: '', created_by: 'user-1', created_at: '', updated_at: '', validated_at: null, terms: [] }] }])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findAllByText('Inactive')).toHaveLength(2)
    expect(screen.queryByRole('button', { name: 'Désactiver' })).not.toBeInTheDocument()
  })

  it('ne propose pas d’écriture de formule au MEMBER', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('MEMBER')); vi.mocked(listMarketLots).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    await screen.findByText('Formules de révision')
    expect(screen.queryByRole('button', { name: 'Ajouter une formule de révision' })).not.toBeInTheDocument()
  })

  it('permet à OWNER de créer un groupe de révision', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('OWNER')); vi.mocked(listMarketLots).mockResolvedValue([])
    vi.mocked(saveRevisionGroup).mockResolvedValue({ id: 'group-2', market: 'market-1', code: 'GEN', name: 'Général', description: '', sort_order: 0, active: true, notes: '', created_at: '', updated_at: '', formulas: [] })
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Ajouter une formule de révision' }))
    fireEvent.change(screen.getByLabelText('Nom de la formule'), { target: { value: 'Général' } })
    fireEvent.click(screen.getByRole('button', { name: 'Choisir dans la bibliothèque' }))
    await vi.waitFor(() => expect(saveRevisionGroup).toHaveBeenCalledWith('market-1', expect.objectContaining({ name: 'Général', sort_order: 0 })))
  })

  it('distingue le titulaire société de la société gestionnaire', async () => {
    vi.mocked(getMarket).mockResolvedValue({
      ...market('OWNER'),
      company_detail: { id: 'company-1', raison_sociale: 'Société gestionnaire' },
      holder_type: 'SOLE_COMPANY',
      holder_company: 'company-2',
      holder_company_detail: { id: 'company-2', raison_sociale: 'Titulaire société' },
    })
    vi.mocked(listMarketLots).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect((await screen.findByText('Titulaire :')).parentElement).toHaveTextContent('Titulaire : Titulaire société')
    expect(screen.getByText('Société gestionnaire :').parentElement).toHaveTextContent('Société gestionnaire : Société gestionnaire')
    expect(screen.queryByText(/^Titulaire : Société gestionnaire$/)).not.toBeInTheDocument()
  })

  it('affiche le Consortium titulaire sans le confondre avec la société gestionnaire', async () => {
    vi.mocked(getMarket).mockResolvedValue({
      ...market('OWNER'),
      company_detail: { id: 'naxu', raison_sociale: 'NAXU' },
      holder_type: 'CONSORTIUM',
      holder_company: null,
      holder_company_detail: null,
      consortium: 'consortium-1',
      consortium_detail: { id: 'consortium-1', name: 'INGC/NAXU', owner_company: 'naxu' },
    })
    vi.mocked(listMarketLots).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect((await screen.findByText('Titulaire :')).parentElement).toHaveTextContent('Titulaire : Groupement INGC/NAXU')
    expect(screen.getByText('Société gestionnaire :').parentElement).toHaveTextContent('Société gestionnaire : NAXU')
    expect(screen.queryByText('Titulaire : NAXU')).not.toBeInTheDocument()
  })

  it('affiche les dates métier au format français sans décalage', async () => {
    vi.mocked(getMarket).mockResolvedValue({
      ...market('OWNER'),
      date_limite_remise_offres: '2025-11-19',
      date_ouverture_plis: '2025-11-19',
      date_signature: '2025-12-01',
      date_os_commencement: '2026-04-23',
    })
    vi.mocked(listMarketLots).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findAllByText('19/11/2025')).toHaveLength(2)
    expect(screen.getByText('01/12/2025')).toBeInTheDocument()
    expect(screen.getByText('23/04/2026')).toBeInTheDocument()
  })

  it('MEMBER ne voit pas l’action d’édition', async () => {
    vi.mocked(getMarket).mockResolvedValue(market('MEMBER')); vi.mocked(listMarketLots).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    await screen.findByText("Aucun lot n'est enregistré.")
    expect(screen.queryByRole('button', { name: 'Modifier' })).not.toBeInTheDocument()
  })

  it('affiche les erreurs 403 et 404 via le détail', async () => {
    vi.mocked(getMarket).mockRejectedValue(new ApiError(404, { code: 'NOT_FOUND', message: 'introuvable' }))
    vi.mocked(listMarketLots).mockRejectedValue(new ApiError(404, { code: 'NOT_FOUND', message: 'introuvable' }))
    render(<MemoryRouter initialEntries={['/app/markets/market-1']}><Routes><Route path="/app/markets/:id" element={<MarketDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('alert')).toHaveTextContent('Ressource introuvable.')
  })

  it('affiche 403 et les erreurs réseau sur la liste', async () => {
    vi.mocked(listMarkets).mockRejectedValueOnce(new ApiError(403, { code: 'PERMISSION_DENIED', message: 'refusé' }))
    vi.mocked(listCompanies).mockResolvedValue([])
    render(<MemoryRouter><MarketsPage /></MemoryRouter>)
    expect(await screen.findByRole('alert')).toHaveTextContent('Accès refusé.')

    vi.mocked(listMarkets).mockRejectedValueOnce(new ApiError(0, { code: 'NETWORK_ERROR', message: 'réseau' }))
    render(<MemoryRouter><MarketsPage /></MemoryRouter>)
    expect(await screen.findByText('Erreur réseau. Réessayez.')).toBeInTheDocument()
  })

  it('redirige une session 401 vers la connexion', async () => {
    vi.mocked(listMarkets).mockRejectedValue(new ApiError(401, { code: 'AUTHENTICATION_REQUIRED', message: 'connexion' }))
    vi.mocked(listCompanies).mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/app/markets']}><Routes><Route path="/app/markets" element={<MarketsPage />} /><Route path="/login" element={<p>Connexion</p>} /></Routes></MemoryRouter>)
    expect(await screen.findByText('Connexion')).toBeInTheDocument()
  })
})
