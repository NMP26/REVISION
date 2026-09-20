import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, Company, Consortium, getConsortium, listCompanies, listConsortia, saveConsortium } from '../lib/api'
import { ConsortiumCreatePage, ConsortiumDetailPage, ConsortiaPage } from './ConsortiaPage'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, getConsortium: vi.fn(), listCompanies: vi.fn(), listConsortia: vi.fn(), saveConsortium: vi.fn() }
})

const company = (id: string, name: string, role: Company['current_user_role']): Company => ({ id, raison_sociale: name, forme_juridique: '', capital_social: null, ice: '', if_fiscal: '', rc: '', rc_city: '', cnss: '', adresse_complete: '', ville: '', telephone: '', email: '', site_web: '', representant_nom: '', representant_prenom: '', representant_fonction: '', logo: null, notes: '', status: 'ACTIVE', created_at: '', updated_at: '', archived_at: null, current_user_role: role })
const companies = [company('ingc', 'INGC', 'MEMBER'), company('naxu', 'NAXU', 'OWNER')]
const consortium: Consortium = { id: 'consortium-1', owner_company: 'naxu', name: 'Groupement INGC/NAXU', consortium_type: 'Groupement solidaire', active: true, notes: '', created_at: '', updated_at: '', members: [{ id: 'member-1', company: 'ingc', company_detail: { id: 'ingc', raison_sociale: 'INGC' }, role: 'MANDATAIRE', share_percent: '50.0000', sort_order: 0, active: true }, { id: 'member-2', company: 'naxu', company_detail: { id: 'naxu', raison_sociale: 'NAXU' }, role: 'MEMBER', share_percent: '50.0000', sort_order: 1, active: true }] }

describe('Consortia pages', () => {
  beforeEach(() => {
    vi.mocked(listCompanies).mockResolvedValue(companies)
    vi.mocked(listConsortia).mockResolvedValue([consortium])
    vi.mocked(getConsortium).mockResolvedValue(consortium)
    vi.mocked(saveConsortium).mockReset()
  })

  it('liste le groupement, son mandataire et ses membres', async () => {
    render(<MemoryRouter><ConsortiaPage /></MemoryRouter>)
    expect(await screen.findByText('Groupement INGC/NAXU')).toBeInTheDocument()
    expect(screen.getByText('Groupement solidaire')).toBeInTheDocument()
    expect(screen.getByText('Mandataire : INGC')).toBeInTheDocument()
    expect(screen.getByText('Membres : INGC, NAXU')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Nouveau groupement' })).toHaveAttribute('href', '/app/consortia/new')
  })

  it('crée INGC/NAXU avec les Companies existantes et des quotes-parts décimales', async () => {
    vi.mocked(saveConsortium).mockResolvedValue(consortium)
    render(<MemoryRouter><ConsortiumCreatePage /></MemoryRouter>)
    fireEvent.change(await screen.findByLabelText('Nom du groupement'), { target: { value: 'Groupement INGC/NAXU' } })
    fireEvent.change(screen.getByLabelText('Type du groupement'), { target: { value: 'Groupement solidaire' } })
    fireEvent.change(await screen.findByRole('combobox', { name: 'Société gestionnaire' }), { target: { value: 'naxu' } })
    fireEvent.change(screen.getByLabelText('Company membre 1'), { target: { value: 'ingc' } })
    fireEvent.change(screen.getByLabelText('Rôle membre 1'), { target: { value: 'MANDATAIRE' } })
    fireEvent.change(screen.getByLabelText('Quote-part membre 1'), { target: { value: '50.00' } })
    fireEvent.change(screen.getByLabelText('Company membre 2'), { target: { value: 'naxu' } })
    fireEvent.change(screen.getByLabelText('Quote-part membre 2'), { target: { value: '50.00' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Créer le groupement' }).closest('form')!)
    expect(await vi.waitFor(() => vi.mocked(saveConsortium).mock.calls.length > 0)).toBe(true)
    expect(vi.mocked(saveConsortium).mock.calls[0][0]).toEqual(expect.objectContaining({ owner_company: 'naxu', name: 'Groupement INGC/NAXU', consortium_type: 'Groupement solidaire' }))
    expect(vi.mocked(saveConsortium).mock.calls[0][0]).toEqual(expect.objectContaining({ members: [{ company: 'ingc', role: 'MANDATAIRE', share_percent: '50.00', sort_order: 0, active: true }, { company: 'naxu', role: 'MEMBER', share_percent: '50.00', sort_order: 1, active: true }] }))
  })

  it('ajoute et retire des membres puis rejette doublon et total invalide', async () => {
    render(<MemoryRouter><ConsortiumCreatePage /></MemoryRouter>)
    await screen.findByLabelText('Nom du groupement')
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un membre' }))
    expect(screen.getAllByRole('button', { name: 'Retirer' })).toHaveLength(3)
    fireEvent.click(screen.getAllByRole('button', { name: 'Retirer' })[2])
    expect(screen.queryAllByRole('button', { name: 'Retirer' })).toHaveLength(0)
    fireEvent.change(screen.getByLabelText('Nom du groupement'), { target: { value: 'Groupement INGC/NAXU' } })
    fireEvent.change(await screen.findByRole('combobox', { name: 'Société gestionnaire' }), { target: { value: 'naxu' } })
    fireEvent.change(screen.getByLabelText('Company membre 1'), { target: { value: 'ingc' } })
    fireEvent.change(screen.getByLabelText('Company membre 2'), { target: { value: 'ingc' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Créer le groupement' }).closest('form')!)
    expect(await screen.findByRole('alert')).toHaveTextContent('Une Company ne peut apparaître qu’une seule fois.')
  })

  it('rejette un total de quotes-parts différent de 100,00 %', async () => {
    render(<MemoryRouter><ConsortiumCreatePage /></MemoryRouter>)
    fireEvent.change(await screen.findByLabelText('Nom du groupement'), { target: { value: 'Groupement INGC/NAXU' } })
    fireEvent.change(await screen.findByRole('combobox', { name: 'Société gestionnaire' }), { target: { value: 'naxu' } })
    fireEvent.change(screen.getByLabelText('Company membre 1'), { target: { value: 'ingc' } })
    fireEvent.change(screen.getByLabelText('Quote-part membre 1'), { target: { value: '40' } })
    fireEvent.change(screen.getByLabelText('Company membre 2'), { target: { value: 'naxu' } })
    fireEvent.change(screen.getByLabelText('Quote-part membre 2'), { target: { value: '50' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Créer le groupement' }).closest('form')!)
    expect(await screen.findByRole('alert')).toHaveTextContent('La somme des quotes-parts doit être exactement 100,00 %.')
  })

  it('affiche le détail 50/50 et permet la modification au OWNER', async () => {
    render(<MemoryRouter initialEntries={['/app/consortia/consortium-1']}><Routes><Route path="/app/consortia/:id" element={<ConsortiumDetailPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByText('Groupement INGC/NAXU')).toBeInTheDocument()
    expect(screen.getAllByText('Groupement solidaire')).toHaveLength(2)
    expect(screen.getAllByText('50,00 %')).toHaveLength(2)
    expect(screen.getAllByText('Mandataire')).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'Modifier' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Modifier' }))
    expect(screen.getByDisplayValue('Groupement INGC/NAXU')).toBeInTheDocument()
  })

  it('redirige une erreur 401 vers la connexion', async () => {
    vi.mocked(listConsortia).mockRejectedValue(new ApiError(401, { code: 'AUTHENTICATION_REQUIRED', message: 'Connexion requise.' }))
    render(<MemoryRouter initialEntries={['/app/consortia']}><Routes><Route path="/app/consortia" element={<ConsortiaPage />} /><Route path="/login" element={<p>Connexion</p>} /></Routes></MemoryRouter>)
    expect(await screen.findByText('Connexion')).toBeInTheDocument()
  })
})
