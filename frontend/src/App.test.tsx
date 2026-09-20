import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from './App'
import type { Company } from './lib/api'

vi.mock('./lib/api', async () => {
  const actual = await vi.importActual<typeof import('./lib/api')>('./lib/api')
  return {
    ...actual,
    ensureCsrf: vi.fn().mockResolvedValue({ csrfToken: 'test' }),
    currentUser: vi.fn().mockResolvedValue({ id: 'user-1', email: 'test@example.com', first_name: 'Test', last_name: 'User', is_active: true, is_staff: false, is_superuser: false }),
    listCompanies: vi.fn().mockResolvedValue([{ id: 'company-1', raison_sociale: 'NAXU', current_user_role: 'OWNER' } as Company]),
    listConsortia: vi.fn().mockResolvedValue([]),
  }
})

describe('Application navigation', () => {
  it('expose les sections Sociétés, Groupements et Marchés', async () => {
    render(<MemoryRouter initialEntries={['/app/consortia']}><App /></MemoryRouter>)
    expect(await screen.findByRole('link', { name: 'Groupements' })).toHaveAttribute('href', '/app/consortia')
    expect(screen.getByRole('link', { name: 'Sociétés' })).toHaveAttribute('href', '/app/companies')
    expect(screen.getByRole('link', { name: 'Marchés' })).toHaveAttribute('href', '/app/markets')
  })
})
