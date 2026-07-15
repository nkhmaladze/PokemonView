import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import ProductDetailPage from './ProductDetailPage'

const useLoaderDataMock = vi.fn()

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  }
})

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
    <MemoryRouter>
      <ProductDetailPage />
    </MemoryRouter>
  )
}

describe('ProductDetailPage', () => {
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
})
