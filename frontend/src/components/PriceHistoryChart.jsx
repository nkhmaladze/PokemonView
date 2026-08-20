import styles from './PriceHistoryChart.module.css'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

/**
 * PriceHistoryChart — full-axes line chart over a product's price
 * history (PRICE-07, D-01, D-07, D-08).
 *
 * Pure display layer over the array the history endpoint already
 * returned (`getPriceHistory`, `GET /products/<id>/history`). Never
 * recomputes or reorders the series — every data point plotted is
 * exactly one of the objects the API response contained, in the order
 * it returned them. Fewer than two points is not an error; it renders
 * the locked insufficient-history copy instead of an empty axis frame
 * (D-07, D-08).
 */

/**
 * price_points timestamps are stored and returned in UTC, and the
 * ingestion cadence that produces them is UTC-based. Pinning the display
 * timezone here keeps a given point's tick label identical for every
 * viewer and makes these functions assertable in tests without
 * manipulating the process timezone. Switching to viewer-local time
 * later is a display-only change confined to these two option objects.
 */
export function formatAxisDate(ts) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(ts))
}

export function formatTooltipDate(ts) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(ts))
}

export function formatAxisPrice(value) {
  return `$${Math.round(Number(value))}`
}

export function formatTooltipValue(value) {
  return [`$${Number(value).toFixed(2)}`, 'Total price']
}

export default function PriceHistoryChart({ data }) {
  if (!data || data.length < 2) {
    return <p className={styles.insufficient}>Not enough price history yet</p>
  }

  return (
    <div className={styles.chartWrap} data-testid="price-history-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--color-divider)" strokeDasharray="3 3" />
          <XAxis dataKey="ts" stroke="var(--text-secondary)" tickFormatter={formatAxisDate} />
          <YAxis stroke="var(--text-secondary)" tickFormatter={formatAxisPrice} />
          <Tooltip
            labelFormatter={formatTooltipDate}
            formatter={formatTooltipValue}
            contentStyle={{ background: 'var(--color-surface)', border: 'none' }}
          />
          <Line
            type="monotone"
            dataKey="total_price"
            stroke="var(--color-accent)"
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
