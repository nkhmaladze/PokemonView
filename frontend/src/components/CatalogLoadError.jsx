import { useRouteError } from 'react-router'
import styles from './CatalogLoadError.module.css'

/**
 * CatalogLoadError — the catalog route's (`/`) errorElement, added as a
 * backstop so a loader rejection (network failure, non-2xx response) or an
 * unexpected render-time throw for a single malformed product row no
 * longer takes down the entire catalog list with react-router's default
 * unstyled "Unexpected Application Error!" screen (CR-01, WR-05).
 *
 * Mirrors ProductNotFound's token-styled layout pattern for visual
 * consistency between the app's two error states. Read for potential
 * future diagnostics only, same as ProductNotFound — the rendered copy
 * below is always the fixed "couldn't load" text regardless of the
 * underlying error.
 */
export default function CatalogLoadError() {
  useRouteError()

  return (
    <div className={styles.loadError}>
      <h1 className={styles.loadError__heading}>{"Couldn't load the catalog."}</h1>
      <p className={styles.loadError__body}>
        Something went wrong loading product pricing data. Please try refreshing the page.
      </p>
    </div>
  )
}
