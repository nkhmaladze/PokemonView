import { createBrowserRouter } from 'react-router'
import CatalogPage from './pages/CatalogPage'
import ProductDetailPage from './pages/ProductDetailPage'
import ProductNotFound from './components/ProductNotFound'
import { getProducts, getProductDetail } from './api/client'

/**
 * The SPA's full route table (SEARCH-01/SEARCH-02).
 *
 * "/" -> CatalogPage, loader fetches the full catalog once via
 * getProducts() (no args — CatalogPage filters the loaded array
 * in-memory per D-14, never re-fetching per keystroke/chip click).
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
  },
  {
    path: '/products/:productId',
    Component: ProductDetailPage,
    loader: ({ params }) => getProductDetail(params.productId),
    errorElement: <ProductNotFound />,
  },
])
