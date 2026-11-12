/**
 * Y-axis range for the price chart.
 *
 * A line chart does not need a $0 baseline. Starting at $0 flattens every
 * product whose price sits far above it (a $46 to $40 slide is invisible on a
 * $0 to $60 axis), so the axis is fitted to the data instead. The risk of
 * fitting is the opposite one: a product that barely moves would be stretched
 * to fill the whole chart and look like a rollercoaster. So the visible range
 * never drops below MIN_VISIBLE_SPAN of the product's average price, and a
 * product that moves 4% is drawn as a gentle line rather than a dramatic one.
 *
 * Returns `{ domain: [low, high], ticks, decimals }` where `decimals` is how
 * many decimal places the tick labels need so no two labels read the same, or
 * null when there is nothing numeric to plot (the chart then keeps its default
 * axis).
 */
export const MIN_VISIBLE_SPAN = 0.2 // share of the average price
const PADDING = 0.08 // breathing room above and below the line, share of the span
const TARGET_INTERVALS = 5
const MIN_SPAN_DOLLARS = 0.5 // so a $0 series still gets a real axis

const round6 = (x) => Number(x.toFixed(6))

// Smallest "nice" step (1, 2, 5 times a power of ten) that is at least `raw`.
function niceStep(raw) {
  const base = 10 ** Math.floor(Math.log10(raw))
  const f = raw / base
  const nice = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10
  return nice * base
}

export function priceAxis(prices) {
  if (!Array.isArray(prices)) return null
  const values = prices.filter((p) => typeof p === 'number' && Number.isFinite(p))
  if (values.length === 0) return null

  let low = Math.min(...values)
  let high = Math.max(...values)
  const average = values.reduce((sum, p) => sum + p, 0) / values.length
  const minSpan = Math.max(MIN_VISIBLE_SPAN * Math.abs(average), MIN_SPAN_DOLLARS)

  let span = high - low
  if (span < minSpan) {
    const middle = (low + high) / 2
    low = middle - minSpan / 2
    high = middle + minSpan / 2
    span = minSpan
  }
  low = Math.max(0, low - span * PADDING)
  high += span * PADDING

  const step = niceStep((high - low) / TARGET_INTERVALS)
  const first = Math.floor(low / step + 1e-9) * step
  const last = Math.ceil(high / step - 1e-9) * step
  const count = Math.round((last - first) / step)
  const ticks = Array.from({ length: count + 1 }, (_, i) => round6(first + i * step))

  return {
    domain: [ticks[0], ticks[ticks.length - 1]],
    ticks,
    decimals: step < 1 ? 2 : 0,
  }
}
