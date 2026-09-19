import { describe, expect, it } from 'vitest'
import { formatDecimal, formatMoney, formatPercent } from './formatters'

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
