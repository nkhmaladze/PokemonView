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
 * the locked "Not enough price history yet" message instead of an
 * empty axis frame (D-07, D-08).
 */

function formatAxisDate(ts) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(
    new Date(ts)
  )
}

function formatTooltipDate(ts) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(ts))
}

function formatDollars(value) {
  return `$${Number(value).toFixed(2)}`
}

function formatTooltipValue(value) {
  return [formatDollars(value), 'Total price']
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
          <YAxis stroke="var(--text-secondary)" tickFormatter={formatDollars} />
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
