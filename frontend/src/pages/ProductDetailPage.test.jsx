import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import ProductDetailPage from './ProductDetailPage'
import { getPriceHistory } from '../api/client'

const useLoaderDataMock = vi.fn()

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  }
})

vi.mock('../api/client', () => ({ getPriceHistory: vi.fn() }))

const okProduct = {
  id: 'p1',
  set_name: 'Chaos Rising',
  product_type: 'booster_box',
  display_name: 'Chaos Rising Booster Box',
  release_date: '2026-03-01',
  msrp: 161.64,
  image_url: null,
  verified: true,
  price_status: 'ok',
  current_price: {
    total_price: 150,
    item_price: 145,
    as_of: '2026-07-15T00:00:00Z',
    listing_count: 5,
  },
  trend_7d: { pct_change: 2.5, status: 'ok' },
  trend_30d: { pct_change: -1.2, status: 'ok' },
}

function renderDetail(product) {
  useLoaderDataMock.mockReturnValue(product)
  return render(
    <MemoryRouter initialEntries={[`/products/${product.id}`]}>
      <Routes>
        <Route path="/products/:productId" element={<ProductDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProductDetailPage', () => {
  beforeEach(() => {
    getPriceHistory.mockReset()
    getPriceHistory.mockResolvedValue([])
  })

  it('renders total price, item price, both trend badges, freshness caption, and sample-size caption for an "ok" product', () => {
    renderDetail(okProduct)

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('$145.00')).toBeInTheDocument()
    expect(screen.getByText('+2.5%')).toBeInTheDocument()
    expect(screen.getByText('-1.2%')).toBeInTheDocument()
    expect(screen.getByText(/Data as of/)).toBeInTheDocument()
    expect(screen.getByText('Based on 5 active listing(s)')).toBeInTheDocument()
  })

  it('shows "Sample size unavailable" when listing_count is null', () => {
    renderDetail({
      ...okProduct,
      current_price: { ...okProduct.current_price, listing_count: null },
    })

    expect(screen.getByText('Sample size unavailable')).toBeInTheDocument()
  })

  it('renders a graceful no-data state for a "no_data_yet" product without throwing, and still shows both trend badges', () => {
    const noDataProduct = {
      ...okProduct,
      price_status: 'no_data_yet',
      current_price: null,
      trend_7d: { pct_change: null, status: 'insufficient_data' },
      trend_30d: { pct_change: null, status: 'insufficient_data' },
    }

    expect(() => renderDetail(noDataProduct)).not.toThrow()
    expect(screen.getByText('No pricing data yet')).toBeInTheDocument()
    expect(screen.getAllByLabelText('insufficient data')).toHaveLength(2)
    expect(screen.queryByText(/Data as of/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Based on/)).not.toBeInTheDocument()
  })

  it('shows "—" for a null msrp and "TBD" for a null release_date', () => {
    renderDetail({ ...okProduct, msrp: null, release_date: null })

    expect(screen.getByText(/—/)).toBeInTheDocument()
    expect(screen.getByText(/TBD/)).toBeInTheDocument()
  })

  it('shows the price headline before the history fetch resolves, then renders the chart once it does (D-05)', async () => {
    const historyData = [
      { ts: '2026-07-14T00:00:00Z', total_price: 145 },
      { ts: '2026-07-15T00:00:00Z', total_price: 148 },
      { ts: '2026-07-16T00:00:00Z', total_price: 150 },
    ]
    let resolveHistory
    getPriceHistory.mockReturnValue(
      new Promise((resolve) => {
        resolveHistory = resolve
      })
    )

    renderDetail(okProduct)

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('Loading price history…')).toBeInTheDocument()

    resolveHistory(historyData)

    expect(await screen.findByTestId('price-history-chart')).toBeInTheDocument()
    expect(screen.getByText('Price History')).toBeInTheDocument()
  })

  it('shows a chart-scoped error message and keeps the price headline when the history fetch rejects (D-05)', async () => {
    getPriceHistory.mockRejectedValue(new Error('network error'))

    renderDetail(okProduct)

    expect(
      await screen.findByText("Couldn't load price history. Try refreshing the page.")
    ).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })
})
