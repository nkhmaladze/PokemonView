import { createBrowserRouter } from 'react-router'
import CatalogPage from './pages/CatalogPage'
import ProductDetailPage from './pages/ProductDetailPage'
import ProductNotFound from './components/ProductNotFound'
import CatalogLoadError from './components/CatalogLoadError'
import { getProducts, getProductDetail } from './api/client'

/**
 * The SPA's full route table (SEARCH-01/SEARCH-02).
 *
 * "/" -> CatalogPage, loader fetches the full catalog once via
 * getProducts() (no args — CatalogPage filters the loaded array
 * in-memory per D-14, never re-fetching per keystroke/chip click). A
 * rejected loader (network failure, non-2xx response) or an unexpected
 * render-time throw from a single malformed product row is caught by
 * errorElement CatalogLoadError — this is a backstop only; ProductRow's
 * child components (PriceDisplay/TrendBadge) are themselves guarded
 * against malformed per-row data so one bad row degrades in place
 * instead of reaching this boundary (CR-01).
 *
 * "/products/:productId" -> ProductDetailPage, loader fetches the
 * single-product detail via getProductDetail(params.productId). A
 * rejected loader (e.g. the API's 404 {"error":"not_found"}, surfaced
 * by api/client.js as a thrown Error) is caught by errorElement
 * ProductNotFound — 404 handling is centralized at the route boundary,
 * never a per-component try/catch (RESEARCH Pattern 1).
 */
export const router = createBrowserRouter([
  {
    path: '/',
    Component: CatalogPage,
    loader: () => getProducts(),
    errorElement: <CatalogLoadError />,
  },
  {
    path: '/products/:productId',
    Component: ProductDetailPage,
    loader: ({ params }) => getProductDetail(params.productId),
    errorElement: <ProductNotFound />,
  },
])
