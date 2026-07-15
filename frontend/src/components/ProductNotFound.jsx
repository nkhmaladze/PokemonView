import { Link, useRouteError } from 'react-router'
import styles from './ProductNotFound.module.css'

/**
 * ProductNotFound — the detail-route errorElement (SEARCH-02, 06-UI-SPEC.md
 * Copywriting Contract "Error state — product not found").
 *
 * Centralizes the API's 404 {"error":"not_found"} handling at the route
 * boundary (react-router errorElement) instead of a per-component
 * try/catch (RESEARCH Pattern 1). Always renders the fixed "not found"
 * copy for this route's errorElement — react-router only mounts this
 * element when the /products/:productId loader throws, and the only
 * loader-thrown error on this route is api/client.js's Error("not_found")
 * for an unknown product id (T-06-01: fixed literal copy only, no raw
 * error-content HTML rendering).
 */
export default function ProductNotFound() {
  // Read for potential future diagnostics only; the rendered copy below is
  // always the fixed UI-SPEC "not found" text regardless of error.message.
  useRouteError()

  return (
    <div className={styles.notFound}>
      <h1 className={styles.notFound__heading}>Product not found.</h1>
      <p className={styles.notFound__body}>
        This product may have been removed from the catalog.
      </p>
      <Link to="/" className={styles.notFound__link}>
        {'← Back to catalog'}
      </Link>
    </div>
  )
}
