import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { IndicesPage } from './IndicesPage'
import { getOfficialDiscoveryStatus, listIndexDefinitions, listIndexPublications, listIndexValues } from '../lib/api'

vi.mock('../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../lib/api')>('../lib/api')
  return { ...actual, getOfficialDiscoveryStatus: vi.fn(), listIndexDefinitions: vi.fn(), listIndexPublications: vi.fn(), listIndexValues: vi.fn() }
})

const publication = { id: 'publication-1', year: 2026, month: 5, publication_date: null, source_url: '', source_page_url: '', source_pdf_url: '', document_reference: 'Bareme-mai-2026.pdf', document_hash: 'a'.repeat(64), source_type: 'OFFICIAL' as const, import_method: 'MANUAL' as const, status: 'VALIDATED', imported_at: '2026-10-01T00:00:00Z', validated_at: '2026-10-01T00:00:00Z', validated_by: null, indices_count: 2 }
const definition = { id: 'definition-1', code: 'BAT3', designation: 'Électricité', domain: 'BAT', active: true }
const value = { id: 'value-1', index_definition: definition.id, index_definition_detail: definition, publication: publication.id, publication_detail: publication, year: 2026, month: 5, value: '348.50000000', status: 'DEFINITIVE' as const, source_url: '', source_document: publication.document_reference, source_reference: '', validated_at: publication.validated_at, created_at: '', updated_at: '' }

describe('IndicesPage database-first consultation', () => {
  beforeEach(() => { vi.mocked(listIndexValues).mockResolvedValue({ results: [value], count: 1, page: 1, page_size: 50, has_next: false, has_previous: false }); vi.mocked(listIndexDefinitions).mockResolvedValue([definition]); vi.mocked(listIndexPublications).mockResolvedValue([publication]); vi.mocked(getOfficialDiscoveryStatus).mockResolvedValue({ status: 'AVAILABLE', checked_at: null, new_documents: 0, latest_new_document: null }) })

  it('affiche les filtres, la valeur Decimal formatée et les actions officielles', async () => {
    render(<IndicesPage />)
    expect(await screen.findByText('348,5')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'BASE DES INDICES' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Importer un barème officiel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Vérifier les nouvelles publications' })).toBeInTheDocument()
    expect(screen.queryByText(/Synchronisation externe/i)).not.toBeInTheDocument()
  })

  it('combine les filtres et demande la pagination à PostgreSQL via l’API', async () => {
    render(<IndicesPage />)
    await screen.findByText('348,5')
    fireEvent.change(screen.getByLabelText('Indice'), { target: { value: 'BAT3' } })
    fireEvent.change(screen.getByLabelText('Année'), { target: { value: '2026' } })
    fireEvent.change(screen.getByLabelText('Mois'), { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Filtrer' }))
    await vi.waitFor(() => expect(listIndexValues).toHaveBeenLastCalledWith(expect.stringContaining('code=BAT3')))
    expect(listIndexValues).toHaveBeenLastCalledWith(expect.stringContaining('year=2026'))
    expect(listIndexValues).toHaveBeenLastCalledWith(expect.stringContaining('month=5'))
    expect(listIndexValues).toHaveBeenLastCalledWith(expect.stringContaining('page=1'))
  })
})
