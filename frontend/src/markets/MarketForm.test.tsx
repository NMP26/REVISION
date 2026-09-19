import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MarketForm } from './MarketForm'
import type { Company } from '../lib/api'

const companies: Company[] = [{ id: 'company-1', raison_sociale: 'Entreprise A', forme_juridique: '', capital_social: null, ice: '', if_fiscal: '', rc: '', cnss: '', adresse_complete: '', ville: '', telephone: '', email: '', site_web: '', representant_nom: '', representant_prenom: '', representant_fonction: '', logo: null, notes: '', status: 'ACTIVE', created_at: '', updated_at: '', archived_at: null, current_user_role: 'OWNER' }]

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
})
