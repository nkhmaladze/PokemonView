import styles from './AllTimeRangeBadge.module.css'

function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}

/**
 * AllTimeRangeBadge — 2-state all-time low/high price range badge (PRICE-09).
 *
 * Pure display formatter over the API's already-computed `all_time_range`
 * object (catalog_service.get_product_detail). Never recomputes or
 * re-derives the bounds — only formats the low/high the API already
 * derived via get_all_time_range.
 *
 * Branches on prop presence and `range.status` FIRST (insufficient_data ->
 * muted dash), then reads `range.high`/`range.low`, mirroring TrendBadge's
 * status-first discipline (06-UI-SPEC.md / 09-UI-SPEC.md D-UI-01).
 *
 * Unlike TrendBadge, this is a sibling rather than a reuse: the data shape
 * is two absolute dollar values with no direction, so it has exactly two
 * states (ok / insufficient_data) rather than TrendBadge's four
 * (up/down/flat/insufficient_data). See 09-UI-SPEC.md D-UI-01 for the
 * colour mapping this component's stylesheet encodes.
 */
export default function AllTimeRangeBadge({ range }) {
  if (!range || range.status === 'insufficient_data') {
    return (
      <span
        className={`${styles.range} ${styles['range--muted']}`}
        aria-label="insufficient data"
      >
        {'—'}
      </span>
    )
  }

  return (
    <span className={styles.range}>
      {formatCurrency(range.low)}
      {/* EN DASH (U+2013), deliberately distinct from the muted state's
          EM DASH (U+2014): the page's null-MSRP test matches the em dash
          with a single-match query, so reusing it here as a separator
          would make that query ambiguous and break an unrelated test. */}
      {' – '}
      {formatCurrency(range.high)}
    </span>
  )
}
