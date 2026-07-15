import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import ProductRow from './ProductRow'

const okProduct = {
  id: 'abc123',
  set_name: 'Chaos Rising',
  product_type: 'booster_box',
  display_name: 'Chaos Rising Booster Box',
  image_url: 'https://example.com/box.png',
  price_status: 'ok',
  current_price: {
    total_price: 150,
    item_price: 145,
    as_of: '2026-07-15T12:00:00Z',
    listing_count: 5,
  },
}

const noImageProduct = {
  ...okProduct,
  id: 'noimg1',
  image_url: null,
}

const noDataProduct = {
  id: 'nodata1',
  set_name: 'Pitch Black',
  product_type: 'etb',
  display_name: 'Pitch Black ETB',
  image_url: null,
  price_status: 'no_data_yet',
  current_price: null,
}

function renderRow(product) {
  return render(
    <MemoryRouter>
      <ProductRow product={product} />
    </MemoryRouter>
  )
}

describe('ProductRow', () => {
  it('renders name/price and links to /products/{id} for an "ok" product', () => {
    renderRow(okProduct)
    const link = screen.getByRole('link', {
      name: 'View Chaos Rising Booster Box pricing details',
    })
    expect(link).toHaveAttribute('href', '/products/abc123')
    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.getByText('Chaos Rising')).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })

  it('renders a placeholder thumbnail (not a broken img) when image_url is null', () => {
    const { container } = renderRow(noImageProduct)
    expect(container.querySelector('img')).not.toBeInTheDocument()
    expect(container.querySelector('[data-testid="thumb-placeholder"]')).toBeInTheDocument()
  })

  it('renders muted "No pricing data yet" for a no_data_yet product without throwing', () => {
    renderRow(noDataProduct)
    const link = screen.getByRole('link', {
      name: 'View Pitch Black ETB pricing details',
    })
    expect(link.className).toContain('row--muted')
    expect(screen.getByText('No pricing data yet')).toBeInTheDocument()
    expect(screen.queryByText(/\$/)).not.toBeInTheDocument()
  })
})
