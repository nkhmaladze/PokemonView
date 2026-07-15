import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import PriceDisplay from './PriceDisplay'

const currentPrice = {
  total_price: 161.64,
  item_price: 150.0,
  as_of: '2026-07-15T12:00:00Z',
  listing_count: 5,
}

describe('PriceDisplay', () => {
  it('renders total_price as the headline and item_price as an always-visible secondary line', () => {
    render(<PriceDisplay currentPrice={currentPrice} />)
    expect(screen.getByText('$161.64')).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })

  it('does not render listing_count', () => {
    render(<PriceDisplay currentPrice={currentPrice} />)
    expect(screen.queryByText(/5/)).not.toBeInTheDocument()
  })

  it('does not throw when listing_count is null/absent', () => {
    expect(() =>
      render(<PriceDisplay currentPrice={{ ...currentPrice, listing_count: null }} />)
    ).not.toThrow()
  })

  it('applies the display-size headline class when variant="display"', () => {
    render(<PriceDisplay currentPrice={currentPrice} variant="display" />)
    const total = screen.getByText('$161.64')
    expect(total.className).toContain('price__total--display')
  })

  it('applies the compact heading-size headline class by default', () => {
    render(<PriceDisplay currentPrice={currentPrice} />)
    const total = screen.getByText('$161.64')
    expect(total.className).not.toContain('price__total--display')
  })
})
