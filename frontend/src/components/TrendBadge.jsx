import styles from './TrendBadge.module.css'

/**
 * TrendBadge — 4-state color-coded percent-change badge (PRICE-03).
 *
 * Pure display formatter over the API's already-computed
 * `{ pct_change, status }` trend object (catalog_service.get_product_detail).
 * Never recomputes pct_change — only formats the value the API already
 * derived via compute_pct_change.
 *
 * Branches on `trend.status` FIRST (insufficient_data -> muted dash,
 * resolving RESEARCH.md Open Question 2/06-UI-SPEC.md's locked
 * 4-state table), then on the sign of `pct_change` for the "ok" case.
 */
export default function TrendBadge({ trend }) {
  if (trend.status === 'insufficient_data') {
    return (
      <span
        className={`${styles['trend-badge']} ${styles['trend-badge--muted']}`}
        aria-label="insufficient data"
      >
        {'—'}
      </span>
    )
  }

  const isUp = trend.pct_change > 0
  const isDown = trend.pct_change < 0
  const sign = isUp ? '+' : ''
  const modifier = isUp
    ? 'trend-badge--up'
    : isDown
      ? 'trend-badge--down'
      : 'trend-badge--flat'

  return (
    <span className={`${styles['trend-badge']} ${styles[modifier]}`}>
      {sign}
      {trend.pct_change.toFixed(1)}%
    </span>
  )
}
