import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import PriceHistoryChart, {
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

// Fixture builder — one day apart, ascending prices, ISO-string timestamps.
function buildPoints(count) {
  return Array.from({ length: count }, (_, i) => ({
    ts: `2026-08-${String(10 + i).padStart(2, '0')}T00:00:00+00:00`,
    total_price: 100 + i,
  }))
}

describe('PriceHistoryChart', () => {
  it('renders the insufficient-history message for an empty array', () => {
    render(<PriceHistoryChart data={[]} />)

    expect(screen.getByText('Not enough price history yet')).toBeInTheDocument()
    expect(screen.queryByTestId('price-history-chart')).not.toBeInTheDocument()
  })

  it('renders the insufficient-history message for a single point', () => {
    // D-07: two points are the minimum needed to draw a line, so one point
    // is deliberately in the same bucket as zero.
    render(<PriceHistoryChart data={buildPoints(1)} />)

    expect(screen.getByText('Not enough price history yet')).toBeInTheDocument()
    expect(screen.queryByTestId('price-history-chart')).not.toBeInTheDocument()
  })

  it('renders the insufficient-history message for null and undefined without throwing', () => {
    // Covers the defensive guard for a caller whose fetch hasn't resolved yet.
    const { rerender } = render(<PriceHistoryChart data={null} />)
    expect(screen.getByText('Not enough price history yet')).toBeInTheDocument()

    rerender(<PriceHistoryChart data={undefined} />)
    expect(screen.getByText('Not enough price history yet')).toBeInTheDocument()
  })

  it('renders the chart at exactly two points', () => {
    // Threshold assertion: one step below renders the message, this step
    // renders the line.
    render(<PriceHistoryChart data={buildPoints(2)} />)

    expect(screen.getByTestId('price-history-chart')).toBeInTheDocument()
    expect(screen.queryByText('Not enough price history yet')).not.toBeInTheDocument()
  })

  it('renders the chart for a longer series without mutating its input', () => {
    // The component is a pure display layer over an already-ordered series
    // and must never sort, slice or rewrite it in place.
    const points = buildPoints(5)
    const snapshot = structuredClone(points)

    render(<PriceHistoryChart data={points} />)

    expect(screen.getByTestId('price-history-chart')).toBeInTheDocument()
    expect(points).toEqual(snapshot)
  })
})
