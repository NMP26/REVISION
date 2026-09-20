import { describe, expect, it } from 'vitest'
import { formatDate, formatDecimal, formatMoney, formatPercent } from './formatters'

describe('date display formatters', () => {
  it.each([
    ['2025-11-19', '19/11/2025'],
    ['2026-04-23', '23/04/2026'],
    ['2024-01-01', '01/01/2024'],
    ['2024-01-31', '31/01/2024'],
    ['2024-02-29', '29/02/2024'],
  ])('formats the civil date %s as %s', (value, expected) => {
    expect(formatDate(value)).toBe(expected)
  })

  it.each([null, undefined, ''])('renders an empty date as a dash', (value) => {
    expect(formatDate(value)).toBe('—')
  })

  it('does not convert the civil date through a timezone', () => {
    expect(formatDate('2025-11-19')).toBe('19/11/2025')
  })
})

describe('financial display formatters', () => {
  it.each([
    ['6603156.00', '6 603 156,00 DH'],
    ['535776.00', '535 776,00 DH'],
    ['1234567.89', '1 234 567,89 DH'],
    ['0', '0,00 DH'],
  ])('formats money %s as %s', (value, expected) => {
    expect(formatMoney(value)).toBe(expected)
  })

  it.each([
    ['20.0000', '20,00 %'],
    ['10.5000', '10,50 %'],
  ])('formats percent %s as %s', (value, expected) => {
    expect(formatPercent(value)).toBe(expected)
  })

  it('formats decimal values without using binary floating point', () => {
    expect(formatDecimal('999.999', 2)).toBe('1 000,00')
    expect(formatDecimal('0001234,5', 2)).toBe('1 234,50')
    expect(formatDecimal('-0.00', 2)).toBe('0,00')
  })

  it('keeps empty values distinguishable from zero', () => {
    expect(formatMoney(null)).toBe('—')
    expect(formatMoney('0')).toBe('0,00 DH')
  })
})
