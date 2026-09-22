import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Market, Statement } from '../lib/api'
import { StatementSection } from './StatementSection'

const api = vi.hoisted(() => ({ listStatements: vi.fn(), saveStatement: vi.fn(), listMonthlyWorkAllocations: vi.fn(), saveMonthlyWorkAllocation: vi.fn(), getStatementCalculation: vi.fn() }))
vi.mock('../lib/api', async () => ({ ...(await vi.importActual('../lib/api')), ...api }))

const market = { id: 'market-1', market_number: '10006299/4500004338', subject: 'Travaux', date_os_commencement: '2026-04-23', date_limite_remise_offres: '2025-11-19' } as Market
const statement = { id: 'statement-1', market: market.id, number: 1, date: '2026-08-31', amount_ht: '535776.00', observation: '', allocation_method: 'ACTUAL_EXECUTION', created_at: '', updated_at: '' } as Statement

describe('StatementSection', () => {
  beforeEach(() => { vi.clearAllMocks(); api.listStatements.mockResolvedValue([]); api.listMonthlyWorkAllocations.mockResolvedValue([]); api.saveStatement.mockResolvedValue(statement); api.saveMonthlyWorkAllocation.mockImplementation(async (_market: string, _statement: string, data: Record<string, unknown>) => ({ id: `allocation-${data.month}`, statement: statement.id, year: data.year, month: data.month, work_days: data.work_days, created_at: '', updated_at: '' })); api.getStatementCalculation.mockResolvedValue({ statement_id: statement.id, statement_amount_ht: statement.amount_ht, allocation_method: 'ACTUAL_EXECUTION', total_work_days: '30.00', total_allocated_amount: '535776.00', total_revision: null, calculation_status: 'INDEX_NOT_AVAILABLE', rounding_status: 'ROUNDING_POLICY_PENDING', base_index: '337.8', base_index_status: 'DEFINITIVE', base_index_source: null, index_code: 'BAT3', formula: { constant: '0.15', coefficient: '0.85', index_code: 'BAT3' }, monthly_results: [{ year: 2026, month: 8, work_days: '30.00', monthly_amount: '535776.00', amount_to_revise: '535776.00', index_code: 'BAT3', base_index: '337.8', current_index: null, index_status: 'INDEX_NOT_AVAILABLE', index_source: {}, ratio: null, K: null, K_minus_1: null, revision_amount: null, calculation_status: 'INDEX_NOT_AVAILABLE' }] }) })

  it('creates a simple statement without BDP fields and keeps zero months visible', async () => {
    render(<StatementSection market={market} editable />)
    fireEvent.click(await screen.findByRole('button', { name: /nouveau décompte/i }))
    fireEvent.change(screen.getByLabelText(/montant ht/i), { target: { value: '535776.00' } })
    fireEvent.change(screen.getByLabelText(/date/i), { target: { value: '2026-08-31' } })
    fireEvent.click(screen.getByRole('button', { name: 'Créer' }))
    await waitFor(() => expect(api.saveStatement).toHaveBeenCalled())
    fireEvent.click(await screen.findByRole('button', { name: /afficher les mois/i }))
    expect((await screen.findAllByDisplayValue('0')).length).toBe(5)
    expect(screen.getByText(/avril 2026/i)).toBeInTheDocument()
    expect(screen.getByText(/août 2026/i)).toBeInTheDocument()
    expect(screen.queryByText(/BDP obligatoire/i)).not.toBeInTheDocument()
  })

  it('shows a blocked calculation preview when the index is missing', async () => {
    api.listStatements.mockResolvedValue([statement])
    render(<StatementSection market={market} editable />)
    fireEvent.click(await screen.findByRole('button', { name: /afficher les mois/i }))
    fireEvent.click(screen.getByRole('button', { name: /enregistrer les jours/i }))
    await waitFor(() => expect(api.saveMonthlyWorkAllocation).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: /calculer la note/i }))
    expect((await screen.findAllByText('Index non disponible')).length).toBeGreaterThan(0)
    expect(screen.queryByText('INDEX_NOT_AVAILABLE')).not.toBeInTheDocument()
    expect(screen.getByText('535 776,00 DH')).toBeInTheDocument()
  })
})
