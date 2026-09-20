import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, Company, getCompany } from '../lib/api'
import { CompanyDetailPage, CompanyErrorState } from './CompaniesPage'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, getCompany: vi.fn() }
})

const company = (role: Company['current_user_role']): Company => ({
  id: 'company-1', raison_sociale: 'Société test', forme_juridique: '', capital_social: null,
  ice: '', if_fiscal: '', rc: '', rc_city: '', cnss: '', adresse_complete: '', ville: '', telephone: '',
  email: '', site_web: '', representant_nom: '', representant_prenom: '', representant_fonction: '',
  logo: null, notes: '', status: 'ACTIVE', created_at: '', updated_at: '', archived_at: null,
  current_user_role: role,
})

function renderDetail() {
  return render(<MemoryRouter initialEntries={['/app/companies/company-1']}><Routes><Route path="/app/companies/:id" element={<CompanyDetailPage />} /><Route path="/login" element={<p>Connexion</p>} /></Routes></MemoryRouter>)
}

describe('CompanyDetailPage permissions and errors', () => {
  beforeEach(() => vi.mocked(getCompany).mockReset())

  it.each([['OWNER'], ['ADMIN']])('%s voit l’action édition', async (role) => {
    vi.mocked(getCompany).mockResolvedValue(company(role as Company['current_user_role']))
    renderDetail()
    expect(await screen.findByRole('button', { name: 'Modifier' })).toBeInTheDocument()
  })

  it('MEMBER ne voit pas l’action édition', async () => {
    vi.mocked(getCompany).mockResolvedValue(company('MEMBER'))
    renderDetail()
    await screen.findByText('Société test')
    expect(screen.queryByRole('button', { name: 'Modifier' })).not.toBeInTheDocument()
  })

  it('affiche le RC et sa ville séparément sans déduire la ville générale', async () => {
    vi.mocked(getCompany).mockResolvedValue({ ...company('OWNER'), rc: '13165', rc_city: 'Inezgane', ville: 'Agadir' })
    renderDetail()
    expect(await screen.findByText('13165 – Inezgane')).toBeInTheDocument()
    expect(screen.getByText('Agadir')).toBeInTheDocument()
  })

  it('affiche un état 403', () => {
    render(<MemoryRouter><CompanyErrorState error={new ApiError(403, { code: 'PERMISSION_DENIED', message: 'Action non autorisée.' })} /></MemoryRouter>)
    expect(screen.getByRole('alert')).toHaveTextContent('Accès refusé.')
  })

  it('affiche un état 404 distinct', () => {
    render(<MemoryRouter><CompanyErrorState error={new ApiError(404, { code: 'NOT_FOUND', message: 'Société introuvable.' })} /></MemoryRouter>)
    expect(screen.getByRole('alert')).toHaveTextContent('Ressource introuvable.')
  })

  it('affiche une erreur réseau générique et permet de réessayer', () => {
    const retry = vi.fn()
    render(<MemoryRouter><CompanyErrorState error={new ApiError(0, { code: 'NETWORK_ERROR', message: 'internal detail' })} onRetry={retry} /></MemoryRouter>)
    expect(screen.getByRole('alert')).toHaveTextContent('Erreur réseau. Réessayez.')
    expect(screen.queryByText('internal detail')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument()
  })

  it('redirige les 401 vers la connexion', async () => {
    render(<MemoryRouter initialEntries={['/app/companies/company-1']}><Routes><Route path="/app/companies/:id" element={<CompanyErrorState error={new ApiError(401, { code: 'AUTHENTICATION_REQUIRED', message: 'Connexion requise.' })} />} /><Route path="/login" element={<p>Connexion</p>} /></Routes></MemoryRouter>)
    await waitFor(() => expect(screen.getByText('Connexion')).toBeInTheDocument())
  })
})
