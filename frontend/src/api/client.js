/**
 * Thin native-fetch data layer over the Flask API's two /products routes
 * (api/blueprints/products.py). No third-party HTTP client dependency. Only
 * these two path prefixes may ever be requested — Flask-CORS is scoped to
 * r"/products*" only (CR-02).
 */

const BASE = '' // relative — Vite dev proxy (or same-origin prod) handles routing

async function request(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request failed: ${res.status}`)
  }
  return res.json()
}

/**
 * GET /products — browse/search/filter the catalog.
 * Accepts optional server-side filters for API-shape completeness, but per
 * D-14 the catalog loader (06-05) calls this with no arguments and filters
 * client-side against the full loaded array.
 */
export const getProducts = (filters = {}) => {
  const params = new URLSearchParams()
  if (filters.set) params.set('set', filters.set)
  if (filters.product_type) params.set('product_type', filters.product_type)
  if (filters.q) params.set('q', filters.q)
  const qs = params.toString()
  return request(`/products${qs ? `?${qs}` : ''}`)
}

/** GET /products/<product_id> — single-product detail assembly. */
export const getProductDetail = (productId) => request(`/products/${productId}`)
