import styles from './FreshnessIndicator.module.css'
import { formatRelativeTime } from '../utils/relativeTime'

/**
 * FreshnessIndicator — renders "Data as of {relative time}" from an
 * as_of ISO timestamp (PRICE-02, D-09/D-10).
 *
 * Delegates all time math to formatRelativeTime — never computes durations
 * itself and never renders an absolute timestamp (D-09). Mounted only on
 * the product detail page, never in list rows (D-10).
 */
export default function FreshnessIndicator({ asOf }) {
  return <p className={styles.freshness}>Data as of {formatRelativeTime(asOf)}</p>
}
