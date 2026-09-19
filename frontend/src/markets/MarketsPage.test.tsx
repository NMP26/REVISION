import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, Company, Market, getMarket, listCompanies, listMarketLots, listMarkets } from '../lib/api'
import { MarketDetailPage, MarketsPage } from './MarketsPage'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, getMarket: vi.fn(), listCompanies: vi.fn(), listMarketLots: vi.fn(), listMarkets: vi.fn() }
})

const market = (role: Market['current_user_role']): Market => ({ id: 'market-1', company: 'company-1', company_detail: { id: 'company-1', raison_sociale: 'Entreprise A' }, market_number: 'M-001', contracting_authority: 'Commune A', subject: 'Travaux', amount_ht: null, vat_rate: null, date_limite_remise_offres: null, date_ouverture_plis: null, date_signature: null, date_os_commencement: null, contract_duration_value: null, contract_duration_unit: null, formula_structure: 'SINGLE', status: 'ACTIVE', notes: '', created_at: '', updated_at: '', current_user_role: role, lots_count: 0 })

describe('MarketsPage', () => {
  beforeEach(() => { vi.mocked(listMarkets).mockReset(); vi.mocked(getMarket).mockReset(); vi.mocked(listCompanies).mockReset(); vi.mocked(listMarketLots).mockReset(); vi.mocked(listCompanies).mockResolvedValue([]) })

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
