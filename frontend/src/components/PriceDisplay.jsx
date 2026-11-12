import styles from './PriceDisplay.module.css'

function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}

/**
 * PriceDisplay — total-led headline with an always-visible item-price
 * secondary line.
 *
 * Pure display formatter over the API's already-computed `current_price`
 * shape (total_price, item_price, as_of, plus a sample-size field —
 * catalog_service._product_summary). Never recomputes total_price (it
 * already equals item + shipping server-side). The sample-size field is
 * intentionally not rendered here — it is detail-page-only,
 * owned by ProductDetailPage.
 *
 * `variant="display"` selects the 28/600 Display-size headline used on
 * the product detail page; the default `"heading"` variant selects the
 * compact 18/600 Heading-size headline used in the list row.
 *
 * `align="end"` right-aligns both lines so the cents of every row in a
 * list line up down the page; the default leaves the block left-aligned.
 *
 * `showLabels` says in words which number is which: a "with shipping"
 * badge beside the headline total and an "item price" label beside the
 * grey line. The detail page turns it on. List rows use `itemLabel`
 * instead: just the word "item" before the grey amount, because the list's
 * header already says the bold price includes shipping.
 */
export default function PriceDisplay({
  currentPrice,
  variant = 'heading',
  align = 'start',
  showLabels = false,
  itemLabel = false,
}) {
  const totalClassName =
    variant === 'display'
      ? `${styles.price__total} ${styles['price__total--display']}`
      : styles.price__total
  const priceClassName =
    align === 'end' ? `${styles.price} ${styles['price--end']}` : styles.price

  if (!currentPrice) {
    return (
      <div className={priceClassName}>
        <span className={totalClassName}>{'—'}</span>
      </div>
    )
  }

  return (
    <div className={priceClassName}>
      <span className={styles.price__line}>
        <span className={totalClassName}>{formatCurrency(currentPrice.total_price)}</span>
        {showLabels && <span className={styles.price__badge}>with shipping</span>}
      </span>
      <span className={styles.price__line}>
        {itemLabel && !showLabels && <span className={styles.price__label}>item</span>}
        <span className={styles.price__secondary}>{formatCurrency(currentPrice.item_price)}</span>
        {showLabels && <span className={styles.price__label}>item price</span>}
      </span>
    </div>
  )
}
