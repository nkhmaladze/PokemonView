import { describe, expect, it } from 'vitest'
import { MIN_VISIBLE_SPAN, priceAxis } from './priceAxis'

const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length

// Series shapes taken from real products.
const smoothFall = [46, 45.5, 44.8, 43.2, 42, 41.4, 40.2, 39.6, 39.4, 40, 39.5, 38.5] // bundle: $46 -> ~$40
const flatBox = [479.99, 484, 489.99, 495, 499.5, 500, 500, 500] // box: +4%
const spiky = [190, 175, 96.08, 1180, 210, 195, 190] // one wild spike
const cheapPack = [8.99, 9.44, 9.99, 9.5, 9.44]

describe('priceAxis', () => {
  it('does not start at $0 when the prices are far from it', () => {
    const { domain } = priceAxis(smoothFall)
    expect(domain[0]).toBeGreaterThan(30)
    expect(domain[0]).toBeLessThan(38.5)
  })

  it('always contains every price, for every shape', () => {
    for (const series of [smoothFall, flatBox, spiky, cheapPack, [5, 5, 5], [0.99, 1.2]]) {
      const { domain } = priceAxis(series)
      expect(domain[0]).toBeLessThanOrEqual(Math.min(...series))
      expect(domain[1]).toBeGreaterThanOrEqual(Math.max(...series))
    }
  })

  it('never goes below $0', () => {
    for (const series of [spiky, [0.5, 0.6, 0.55], [1, 40]]) {
      expect(priceAxis(series).domain[0]).toBeGreaterThanOrEqual(0)
    }
  })

  it('keeps a flat product looking flat: the visible span is at least the minimum share of its price', () => {
    // flatBox moves ~4%; without a floor that would fill the whole chart.
    const { domain } = priceAxis(flatBox)
    expect(domain[1] - domain[0]).toBeGreaterThanOrEqual(MIN_VISIBLE_SPAN * mean(flatBox))
  })

  it('gives a constant series a real range instead of a zero-height axis', () => {
    const { domain, ticks } = priceAxis([9.99, 9.99, 9.99])
    expect(domain[1]).toBeGreaterThan(domain[0])
    expect(Number.isFinite(domain[0]) && Number.isFinite(domain[1])).toBe(true)
    expect(ticks.some((t) => t <= 9.99)).toBe(true)
    expect(ticks.some((t) => t >= 9.99)).toBe(true)
  })

  it('lets a spiky series use the full range: the spike still sets the scale', () => {
    const { domain } = priceAxis(spiky)
    expect(domain[0]).toBe(0)
    expect(domain[1]).toBeGreaterThanOrEqual(1180)
  })

  it('returns ascending, evenly spaced ticks that start and end exactly on the domain', () => {
    for (const series of [smoothFall, flatBox, spiky, cheapPack]) {
      const { domain, ticks } = priceAxis(series)
      expect(ticks[0]).toBe(domain[0])
      expect(ticks[ticks.length - 1]).toBe(domain[1])
      expect(ticks.length).toBeGreaterThanOrEqual(3)
      expect(ticks.length).toBeLessThanOrEqual(9)
      const steps = ticks.slice(1).map((t, i) => Number((t - ticks[i]).toFixed(6)))
      expect(new Set(steps).size).toBe(1)
      expect(steps[0]).toBeGreaterThan(0)
    }
  })

  it('uses whole-dollar labels when ticks are at least $1 apart', () => {
    expect(priceAxis(smoothFall).decimals).toBe(0)
    expect(priceAxis(spiky).decimals).toBe(0)
  })

  it('uses cents when ticks are under $1 apart, so labels never repeat ("$10, $10, $10")', () => {
    const { ticks, decimals } = priceAxis(cheapPack)
    expect(decimals).toBe(2)
    const labels = ticks.map((t) => t.toFixed(decimals))
    expect(new Set(labels).size).toBe(labels.length)
  })

  it('ignores missing or non-numeric prices', () => {
    const { domain } = priceAxis([null, 40, undefined, 'x', 44, NaN, 42])
    expect(domain[0]).toBeLessThanOrEqual(40)
    expect(domain[1]).toBeGreaterThanOrEqual(44)
  })

  it('returns null when there is nothing to plot, so the chart falls back to its default axis', () => {
    expect(priceAxis([])).toBeNull()
    expect(priceAxis(null)).toBeNull()
    expect(priceAxis([null, undefined, NaN])).toBeNull()
  })

  it('does not mutate its input', () => {
    const input = [3, 1, 2]
    priceAxis(input)
    expect(input).toEqual([3, 1, 2])
  })
})
