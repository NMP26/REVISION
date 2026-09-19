import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MarketLotForm } from './MarketLotForm'

describe('MarketLotForm', () => {
  it('affiche le formulaire réutilisable et les contraintes de saisie', () => {
    render(<MarketLotForm marketId="market-1" onSaved={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Ajouter le lot' })).toBeInTheDocument()
    expect(screen.getByLabelText('Numéro du lot')).toBeRequired()
    expect(screen.getByLabelText('Titre')).toBeRequired()
    expect(screen.getByLabelText("Ordre d'affichage")).toHaveAttribute('min', '0')
  })
})
