import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import CatalogPage from './pages/CatalogPage'
import ProductDetailPage from './pages/ProductDetailPage'
import ProductNotFound from './components/ProductNotFound'
import { getProducts, getProductDetail } from './api/client'

vi.mock('./api/client', () => ({
  getProducts: vi.fn(),
  getProductDetail: vi.fn(),
}))

const products = [
  {
    id: 'p1',
    set_name: 'Chaos Rising',
    product_type: 'booster_box',
    display_name: 'Chaos Rising Booster Box',
    image_url: null,
    price_status: 'ok',
    current_price: {
      total_price: 150,
      item_price: 145,
      as_of: '2026-07-15T00:00:00Z',
      listing_count: 5,
    },
  },
]

/**
 * router.test.jsx — integration test for the route table (SEARCH-01/02).
 *
 * Mirrors router.jsx's exact route/loader/errorElement wiring but built
 * with createMemoryRouter + initialEntries (jsdom has no real browser
 * history) and the api/client module mocked so getProducts/getProductDetail
 * are injected stubs, not real fetch calls.
 */
function buildTestRouter(initialEntries) {
  return createMemoryRouter(
    [
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
    ],
    { initialEntries }
  )
}

describe('router', () => {
  it('renders CatalogPage with loader-fed rows at "/"', async () => {
    getProducts.mockResolvedValue(products)

    const router = buildTestRouter(['/'])
    render(<RouterProvider router={router} />)

    expect(
      await screen.findByText('Chaos Rising Booster Box')
    ).toBeInTheDocument()
  })

  it('renders the ProductNotFound state at "/products/unknown" when the detail loader rejects with "not_found"', async () => {
    getProductDetail.mockRejectedValue(new Error('not_found'))

    const router = buildTestRouter(['/products/unknown'])
    render(<RouterProvider router={router} />)

    expect(await screen.findByText('Product not found.')).toBeInTheDocument()
    expect(screen.getByText('← Back to catalog')).toBeInTheDocument()
  })
})
