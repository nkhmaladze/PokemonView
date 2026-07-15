import styles from './PriceDisplay.module.css'

function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}

/**
 * PriceDisplay — total-led headline with an always-visible item-price
 * secondary line (PRICE-01, D-05).
 *
 * Pure display formatter over the API's already-computed `current_price`
 * shape (total_price, item_price, as_of, plus a sample-size field —
 * catalog_service._product_summary). Never recomputes total_price (it
 * already equals item + shipping server-side). The sample-size field is
 * intentionally not rendered here — it is detail-page-only (D-08),
 * owned by ProductDetailPage (06-06).
 *
 * `variant="display"` selects the 28/600 Display-size headline used on
 * the product detail page; the default `"heading"` variant selects the
 * compact 18/600 Heading-size headline used in the list row.
 */
export default function PriceDisplay({ currentPrice, variant = 'heading' }) {
  const totalClassName =
    variant === 'display'
      ? `${styles.price__total} ${styles['price__total--display']}`
      : styles.price__total

  if (!currentPrice) {
    return (
      <div className={styles.price}>
        <span className={totalClassName}>{'—'}</span>
      </div>
    )
  }

  return (
    <div className={styles.price}>
      <span className={totalClassName}>{formatCurrency(currentPrice.total_price)}</span>
      <span className={styles.price__secondary}>{formatCurrency(currentPrice.item_price)}</span>
    </div>
  )
}
