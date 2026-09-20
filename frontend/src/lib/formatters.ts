export type DecimalValue = string | number | bigint

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return match ? `${match[3]}/${match[2]}/${match[1]}` : '—'
}

function decimalParts(value: DecimalValue): { negative: boolean; integer: string; fraction: string } | null {
  const raw = String(value).trim().replace(',', '.')
  const match = raw.match(/^([+-]?)(\d+)(?:\.(\d+))?$/)
  if (!match) return null

  return {
    negative: match[1] === '-',
    integer: match[2].replace(/^0+(?=\d)/, ''),
    fraction: match[3] ?? '',
  }
}

function roundFraction(integer: string, fraction: string, decimals: number) {
  const kept = fraction.slice(0, decimals).padEnd(decimals, '0')
  const shouldRound = fraction.length > decimals && fraction[decimals] >= '5'
  if (!shouldRound) return { integer, fraction: kept }

  const digits = `${integer}${kept}`.split('').map((digit) => digit.charCodeAt(0) - 48)
  let index = digits.length - 1
  while (index >= 0 && digits[index] === 9) {
    digits[index] = 0
    index -= 1
  }
  if (index < 0) {
    const combined = `1${'0'.repeat(digits.length)}`
    return decimals === 0
      ? { integer: combined, fraction: '' }
      : { integer: combined.slice(0, -decimals), fraction: combined.slice(-decimals) }
  }
  digits[index] += 1
  const combined = digits.join('').padStart(integer.length + decimals, '0')
  return decimals === 0
    ? { integer: combined, fraction: '' }
    : { integer: combined.slice(0, -decimals) || '0', fraction: combined.slice(-decimals) }
}

function groupThousands(integer: string) {
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

export function formatDecimal(value: DecimalValue | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || !Number.isInteger(decimals) || decimals < 0) return '—'
  const parts = decimalParts(value)
  if (!parts) return '—'
  const rounded = roundFraction(parts.integer, parts.fraction, decimals)
  const sign = parts.negative && (rounded.integer !== '0' || rounded.fraction.replace(/0/g, '') !== '') ? '-' : ''
  return `${sign}${groupThousands(rounded.integer)}${decimals > 0 ? `,${rounded.fraction}` : ''}`
}

export function formatMoney(value: DecimalValue | null | undefined): string {
  const formatted = formatDecimal(value, 2)
  return formatted === '—' ? formatted : `${formatted} DH`
}

export function formatPercent(value: DecimalValue | null | undefined): string {
  const formatted = formatDecimal(value, 2)
  return formatted === '—' ? formatted : `${formatted} %`
}
