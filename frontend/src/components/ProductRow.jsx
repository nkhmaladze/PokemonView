import { Link } from 'react-router'
import styles from './ProductRow.module.css'
import PriceDisplay from './PriceDisplay'
import TrendBadge from './TrendBadge'

const PRODUCT_TYPE_GLYPH = {
  booster_pack: 'P',
  booster_box: 'B',
  booster_bundle: 'N',
  etb: 'E',
}

/**
 * ProductRow — one dense, clickable browse-list row (SEARCH-01, PRICE-01,
 * D-01/D-02/D-04/D-11).
 *
 * The whole row is a Link to the product detail route. Composes
 * PriceDisplay and TrendBadge rather than reimplementing their
 * formatting. Branches on `price_status` BEFORE ever touching
 * `current_price` (it is null whenever price_status is "no_data_yet" —
 * Pitfall 5), and never renders an <img> with a null/empty src when
 * `image_url` is absent (Pitfall 2) — a flat placeholder glyph is
 * rendered instead. The row's sample-size field is intentionally never
 * rendered here (detail-page only, D-08).
 *
 * Trend badges render defensively: only when `trend_7d`/`trend_30d` are
 * present on the row object (today's `GET /products` list contract does
 * not include them — see 06-05-PLAN.md Contract note). Their absence
 * must never throw.
 */
export default function ProductRow({ product }) {
  const isMuted = product.price_status === 'no_data_yet'
  const rowClassName = isMuted ? `${styles.row} ${styles['row--muted']}` : styles.row
  const hasTrends = Boolean(product.trend_7d || product.trend_30d)

  return (
    <Link
      to={`/products/${product.id}`}
      className={rowClassName}
      aria-label={`View ${product.display_name} pricing details`}
    >
      <span className={styles.thumb}>
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={`${product.display_name} thumbnail`}
            className={styles.thumb__img}
          />
        ) : (
          <span
            className={styles['thumb--placeholder']}
            data-testid="thumb-placeholder"
            aria-hidden="true"
          >
            {PRODUCT_TYPE_GLYPH[product.product_type] ?? '?'}
          </span>
        )}
      </span>

      <span className={styles.row__info}>
        <span className={styles.row__name}>{product.display_name}</span>
        <span className={styles.row__setBadge}>{product.set_name}</span>
      </span>

      <span className={styles.row__price}>
        {product.price_status === 'ok' ? (
          <PriceDisplay currentPrice={product.current_price} variant="heading" />
        ) : (
          <span className={styles.row__noData}>No pricing data yet</span>
        )}
      </span>

      {hasTrends && (
        <span className={styles.row__trends}>
          {product.trend_7d && <TrendBadge trend={product.trend_7d} />}
          {product.trend_30d && <TrendBadge trend={product.trend_30d} />}
        </span>
      )}
    </Link>
  )
}
