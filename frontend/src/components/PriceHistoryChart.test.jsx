import { afterEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import PriceHistoryChart, {
  formatAxisDate,
  formatTooltipDate,
  formatAxisPrice,
  formatTooltipValue,
} from './PriceHistoryChart'
import styles from './PriceHistoryChart.module.css'

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

describe('formatAxisDate under a non-UTC test timezone (CR-01 regression pin)', () => {
  // WR-03, 08-REVIEW.md: every fixture above hand-supplies a UTC-offset
  // string, which never exercised the naive/offset-less shape the
  // backend actually produced before CR-01's fix (a non-tz_aware
  // MongoClient). This block pins the corrected system behavior end to
  // end: an offset-less timestamp near a UTC day boundary, parsed under
  // a non-UTC test timezone, renders the WRONG day — proving the offset
  // suffix on the backend's `ts` (not this component) is what makes the
  // tick label correct.
  const originalTZ = process.env.TZ

  afterEach(() => {
    process.env.TZ = originalTZ
  })

  it('renders the wrong calendar day for an offset-less ts near a UTC day boundary', () => {
    process.env.TZ = 'America/New_York'
    // True UTC instant is Aug 18, 23:30 UTC. An offset-less string is
    // exactly what get_price_history produced before CR-01's fix — the
    // ECMAScript date-time spec parses it as *local* time (the test's
    // TZ), not UTC, so the wrong day comes out the other end.
    expect(formatAxisDate('2026-08-18T23:30:00.000')).toBe('Aug 19')
  })

  it('renders the correct calendar day once the ts carries a UTC offset', () => {
    process.env.TZ = 'America/New_York'
    // The same instant, but with the +00:00 suffix the fixed backend now
    // always emits, parses as the true UTC instant regardless of the
    // viewer's local timezone.
    expect(formatAxisDate('2026-08-18T23:30:00.000+00:00')).toBe('Aug 18')
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

  it('renders the insufficient-history message with the full-height centred class', () => {
    // Guards the fixed 280px frame so switching between states never
    // causes layout shift.
    render(<PriceHistoryChart data={[]} />)

    expect(screen.getByText('Not enough price history yet').className).toContain(
      styles.insufficient
    )
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
