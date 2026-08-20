import { describe, expect, it } from 'vitest'
import {
  formatAxisDate,
  formatTooltipDate,
  formatAxisPrice,
  formatTooltipValue,
} from './PriceHistoryChart'

describe('formatAxisDate', () => {
  it('formats an ISO timestamp as a short month/day', () => {
    expect(formatAxisDate('2026-08-18T14:30:00+00:00')).toBe('Aug 18')
  })

  it('is deterministic near a UTC day boundary regardless of local timezone', () => {
    expect(formatAxisDate('2026-08-18T23:45:00+00:00')).toBe('Aug 18')
  })
})

describe('formatTooltipDate', () => {
  it('formats an ISO timestamp as month/day/year', () => {
    expect(formatTooltipDate('2026-08-18T14:30:00+00:00')).toBe('Aug 18, 2026')
  })
})

describe('formatAxisPrice', () => {
  it('formats a number as a whole-dollar string with no decimal places', () => {
    expect(formatAxisPrice(150)).toBe('$150')
  })
})

describe('formatTooltipValue', () => {
  it('formats a value as a two-decimal dollar string paired with the series label', () => {
    expect(formatTooltipValue(172.5)).toEqual(['$172.50', 'Total price'])
  })

  it('rounds display-only to two decimal places', () => {
    expect(formatTooltipValue(172.559)).toEqual(['$172.56', 'Total price'])
  })
})
