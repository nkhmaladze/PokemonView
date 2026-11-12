import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'

// Recharts draws nothing in jsdom (no layout, so no measured size), which makes
// its tick labels untestable here. Replace the chart parts with plain
// pass-throughs and record the props the Y axis is given: that is exactly the
// wiring this file is about.
const yAxisProps = []

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  LineChart: ({ children }) => <div>{children}</div>,
  Line: () => null,
  CartesianGrid: () => null,
  XAxis: () => null,
  Tooltip: () => null,
  YAxis: (props) => {
    yAxisProps.push(props)
    return null
  },
}))

import PriceHistoryChart from './PriceHistoryChart'

const points = (prices) =>
  prices.map((total_price, i) => ({
    ts: `2026-08-${String(10 + i).padStart(2, '0')}T00:00:00+00:00`,
    total_price,
  }))

const lastYAxis = () => yAxisProps[yAxisProps.length - 1]

describe('PriceHistoryChart price axis wiring', () => {
  beforeEach(() => {
    yAxisProps.length = 0
  })

  it('gives the Y axis a zoomed domain and ticks instead of the default $0 start', () => {
    render(<PriceHistoryChart data={points([100, 104, 108, 112, 110, 111])} />)
    const { domain, ticks } = lastYAxis()
    expect(domain[0]).toBeGreaterThan(50)
    expect(domain[0]).toBeLessThanOrEqual(100)
    expect(domain[1]).toBeGreaterThanOrEqual(112)
    expect(ticks[0]).toBe(domain[0])
    expect(ticks[ticks.length - 1]).toBe(domain[1])
  })

  it('formats whole dollars when the ticks are at least $1 apart', () => {
    render(<PriceHistoryChart data={points([100, 104, 108, 112, 110, 111])} />)
    const { ticks, tickFormatter } = lastYAxis()
    for (const t of ticks) expect(tickFormatter(t)).toMatch(/^\$\d+$/)
  })

  it('formats cents, with no repeated labels, for a cheap narrow-range product', () => {
    render(<PriceHistoryChart data={points([9.44, 9.99, 9.5, 8.99, 9.44])} />)
    const { ticks, tickFormatter } = lastYAxis()
    const labels = ticks.map((t) => tickFormatter(t))
    for (const l of labels) expect(l).toMatch(/^\$\d+\.\d{2}$/)
    expect(new Set(labels).size).toBe(labels.length)
  })

  it('falls back to the default axis when no point has a usable price', () => {
    render(<PriceHistoryChart data={points([null, undefined])} />)
    const props = lastYAxis()
    expect(props.domain).toBeUndefined()
    expect(props.ticks).toBeUndefined()
    expect(props.tickFormatter(150)).toBe('$150')
  })
})
