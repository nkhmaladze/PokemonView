import { useEffect, useState } from 'react'
import { Link, useLoaderData, useParams } from 'react-router'
import styles from './ProductDetailPage.module.css'
import PriceDisplay from '../components/PriceDisplay'
import TrendBadge from '../components/TrendBadge'
import FreshnessIndicator from '../components/FreshnessIndicator'
import PriceHistoryChart from '../components/PriceHistoryChart'
import { getPriceHistory } from '../api/client'

const PRODUCT_TYPE_GLYPH = {
  booster_pack: 'P',
  booster_box: 'B',
  booster_bundle: 'N',
  etb: 'E',
}

// Human-readable labels for the raw snake_case product_type enum, mirroring
// FilterChips.jsx's PRODUCT_TYPE_OPTIONS label set (WR-03) — never render
// the raw API enum value directly to the user.
const PRODUCT_TYPE_LABELS = {
  booster_pack: 'Booster Pack',
  booster_box: 'Booster Box',
  booster_bundle: 'Booster Bundle',
  etb: 'ETB',
}

function formatMsrp(msrp) {
  return typeof msrp === 'number' ? `$${msrp.toFixed(2)}` : '—'
}

function formatSampleSize(listingCount) {
  return typeof listingCount === 'number'
    ? `Based on ${listingCount} active listing(s)`
    : 'Sample size unavailable'
}

/**
 * ProductDetailPage — the single-product route (`/products/:productId`),
 * SEARCH-02, PRICE-01/02/03, D-08.
 *
 * Reads the detail object via useLoaderData() (route wiring is 06-07's
 * scope) and composes PriceDisplay (variant="display"), TrendBadge
 * (7d + 30d), and FreshnessIndicator over the exact
 * catalog_service.get_product_detail() response shape — never
 * recomputing total_price/pct_change client-side.
 *
 * Branches on `price_status` BEFORE ever touching `current_price` (it
 * is null whenever price_status is "no_data_yet" — Pitfall 5); the two
 * trend fields are always-present objects and render unconditionally in
 * both price states. The sample-size caption reads the current_price's
 * listing_count field only inside the "ok" branch, falling back to
 * "Sample size unavailable" when it is null/absent (D-08). MSRP and
 * release_date fall back to "—"/"TBD" when null so a pre-release
 * product (e.g. Pitch Black) never crashes the page (Pitfall 3). Never
 * renders the `verified` field (UI-SPEC Layout Notes). The page also
 * renders a separate Price History section fed by an independent
 * post-mount fetch against the history endpoint (PRICE-07, 08-CONTEXT.md
 * D-03, D-04, D-05) — the loader response itself still carries no
 * series (D-06 of 08-CONTEXT.md, D-11 of 05-CONTEXT.md).
 */
export default function ProductDetailPage() {
  const product = useLoaderData()
  const { productId } = useParams()
  const [history, setHistory] = useState(null) // null = loading
  const [historyError, setHistoryError] = useState(null)

  // T-08-10: the `cancelled` guard exists for two overlapping cases, not
  // just unmount — a user can navigate away to a different product mid-
  // request (re-running this effect on a new `productId` before the prior
  // fetch settles), and a slow response for the product they left must
  // never overwrite the chart of the product they navigated to.
  useEffect(() => {
    let cancelled = false
    setHistory(null)
    setHistoryError(null)
    getPriceHistory(productId)
      .then((data) => {
        if (!cancelled) setHistory(data)
      })
      .catch((err) => {
        if (!cancelled) setHistoryError(err)
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  return (
    <div className={styles.detail}>
      <Link to="/" className={styles.backLink}>
        {'← Back to catalog'}
      </Link>

      <div className={styles.detail__header}>
        <span className={styles.detail__thumb}>
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={`${product.display_name} thumbnail`}
              className={styles.detail__thumbImg}
            />
          ) : (
            <span
              className={styles['detail__thumb--placeholder']}
              data-testid="thumb-placeholder"
              aria-hidden="true"
            >
              {PRODUCT_TYPE_GLYPH[product.product_type] ?? '?'}
            </span>
          )}
        </span>

        <div className={styles.detail__headerInfo}>
          <h1 className={styles.detail__title}>{product.display_name}</h1>
          <span className={styles.detail__badge}>{product.set_name}</span>
          <span className={styles.detail__badge}>
            {PRODUCT_TYPE_LABELS[product.product_type] ?? product.product_type}
          </span>
        </div>
      </div>

      {product.price_status === 'ok' ? (
        <div className={styles.detail__priceSection}>
          <PriceDisplay currentPrice={product.current_price} variant="display" />
          <p className={styles.sampleSize}>
            {formatSampleSize(product.current_price.listing_count)}
          </p>
          <FreshnessIndicator asOf={product.current_price.as_of} />
        </div>
      ) : (
        <div className={styles.detail__priceSection}>
          <p className={styles.detail__noData}>No pricing data yet</p>
        </div>
      )}

      <div className={styles.detail__trendSection}>
        <div className={styles.trend}>
          <span className={styles.trendLabel}>7d</span>
          <TrendBadge trend={product.trend_7d} />
        </div>
        <div className={styles.trend}>
          <span className={styles.trendLabel}>30d</span>
          <TrendBadge trend={product.trend_30d} />
        </div>
      </div>

      <div className={styles.detail__historySection}>
        <h2 className={styles.sectionHeading}>Price History</h2>
        <div className={styles.historyChartFrame}>
          {historyError ? (
            <p className={styles.historyMessage}>
              Couldn't load price history. Try refreshing the page.
            </p>
          ) : history === null ? (
            <p className={styles.historyMessage}>Loading price history…</p>
          ) : (
            <PriceHistoryChart data={history} />
          )}
        </div>
      </div>

      <div className={styles.detail__meta}>
        <span>MSRP: {formatMsrp(product.msrp)}</span>
        <span>Release date: {product.release_date ?? 'TBD'}</span>
      </div>
    </div>
  )
}
