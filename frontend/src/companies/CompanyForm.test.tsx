import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { CompanyForm } from './CompanyForm'

describe('CompanyForm', () => {
  it('requires the legal name and renders the reusable create form', () => {
    render(<CompanyForm onSaved={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Créer la société' })).toBeInTheDocument()
    const name = screen.getByLabelText('Raison sociale')
    expect(name).toBeRequired()
    fireEvent.change(name, { target: { value: 'Société test' } })
    expect(name).toHaveValue('Société test')
  })

  it('réutilise le même formulaire en édition', () => {
    render(<CompanyForm company={{ id: '1', raison_sociale: 'Société test', forme_juridique: '', capital_social: null, ice: '', if_fiscal: '', rc: '', cnss: '', adresse_complete: '', ville: '', telephone: '', email: '', site_web: '', representant_nom: '', representant_prenom: '', representant_fonction: '', logo: null, notes: '', status: 'ACTIVE', created_at: '', updated_at: '', archived_at: null, current_user_role: 'OWNER' }} onSaved={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeInTheDocument()
  })
})
