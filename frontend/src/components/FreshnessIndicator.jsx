import styles from './FreshnessIndicator.module.css'
import { formatRelativeTime } from '../utils/relativeTime'

/**
 * FreshnessIndicator — renders "Data as of {relative time}" from an
 * as_of ISO timestamp.
 *
 * Delegates all time math to formatRelativeTime — never computes durations
 * itself and never renders an absolute timestamp. Mounted only on
 * the product detail page, never in list rows.
 */
export default function FreshnessIndicator({ asOf }) {
  return <p className={styles.freshness}>Data as of {formatRelativeTime(asOf)}</p>
}
