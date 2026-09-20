import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MarketForm } from './MarketForm'
import { saveMarket } from '../lib/api'
import type { Authority, Company } from '../lib/api'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, saveMarket: vi.fn() }
})

const companies: Company[] = [{ id: 'company-1', raison_sociale: 'Entreprise A', forme_juridique: '', capital_social: null, ice: '', if_fiscal: '', rc: '', cnss: '', adresse_complete: '', ville: '', telephone: '', email: '', site_web: '', representant_nom: '', representant_prenom: '', representant_fonction: '', logo: null, notes: '', status: 'ACTIVE', created_at: '', updated_at: '', archived_at: null, current_user_role: 'OWNER' }]
const secondCompany: Company = { ...companies[0], id: 'company-2', raison_sociale: 'Entreprise B' }
const authorities: Authority[] = [{ id: 'authority-1', name: 'Société Régionale Multiservices Souss-Massa', short_name: 'SRM-SM', active: true }]

describe('MarketForm', () => {
  it('affiche les champs métier et les libellés naturels du délai', () => {
    render(<MarketForm companies={companies} onSaved={vi.fn()} />)
    expect(screen.getByLabelText('Numéro du marché')).toBeRequired()
    expect(screen.getByLabelText("Maître d'ouvrage")).toBeRequired()
    expect(screen.getByText('Jours')).toBeInTheDocument()
    expect(screen.getByText('Mois')).toBeInTheDocument()
    expect(screen.getByText('Formule unique')).toBeInTheDocument()
    expect(screen.getByText('Formules multiples')).toBeInTheDocument()
  })

  it('permet de saisir les dates sans valeur par défaut inventée', () => {
    render(<MarketForm companies={companies} onSaved={vi.fn()} />)
    expect(screen.getByLabelText("Date d'ouverture des plis")).toHaveValue('')
    fireEvent.change(screen.getByLabelText("Date d'ouverture des plis"), { target: { value: '2026-09-19' } })
    expect(screen.getByLabelText("Date d'ouverture des plis")).toHaveValue('2026-09-19')
  })

  it('conserve les dates ISO lors de leur envoi à l’API', async () => {
    vi.mocked(saveMarket).mockResolvedValue({} as never)
    render(<MarketForm companies={companies} onSaved={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Société'), { target: { value: 'company-1' } })
    fireEvent.change(screen.getByLabelText('Numéro du marché'), { target: { value: 'M-001' } })
    fireEvent.change(screen.getByLabelText("Maître d'ouvrage"), { target: { value: 'Commune A' } })
    fireEvent.change(screen.getByLabelText('Objet'), { target: { value: 'Travaux' } })
    fireEvent.change(screen.getByLabelText("Date d'ouverture des plis"), { target: { value: '2026-09-19' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Créer le marché' }).closest('form')!)
    expect(await vi.waitFor(() => vi.mocked(saveMarket).mock.calls.length > 0)).toBe(true)
    expect(vi.mocked(saveMarket).mock.calls[0][0]).toEqual(expect.objectContaining({ date_ouverture_plis: '2026-09-19' }))
  })

  it('associe une suggestion d’autorité à son identifiant', () => {
    render(<MarketForm companies={companies} authorities={authorities} onSaved={vi.fn()} />)
    fireEvent.change(screen.getByLabelText("Maître d'ouvrage"), { target: { value: 'Société Rég' } })
    fireEvent.click(screen.getByRole('option', { name: /Société Régionale/ }))
    expect(screen.getByLabelText("Maître d'ouvrage")).toHaveValue('Société Régionale Multiservices Souss-Massa')
  })

  it('ajoute et retire dynamiquement des membres du groupement', () => {
    render(<MarketForm companies={[...companies, secondCompany]} onSaved={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('Groupement'))
    fireEvent.change(screen.getByLabelText('Société dossier'), { target: { value: 'company-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Créer un groupement' }))
    expect(screen.getAllByPlaceholderText('Quote-part %')).toHaveLength(2)
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un membre' }))
    expect(screen.getAllByPlaceholderText('Quote-part %')).toHaveLength(3)
    fireEvent.click(screen.getByRole('button', { name: 'Retirer le dernier' }))
    expect(screen.getAllByPlaceholderText('Quote-part %')).toHaveLength(2)
  })
})
