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
    expect(screen.queryByText('5', { exact: true })).not.toBeInTheDocument()
    expect(screen.queryByText(/listing/i)).not.toBeInTheDocument()
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

  it('right-aligns both price lines when align="end" (list rows)', () => {
    render(<PriceDisplay currentPrice={currentPrice} align="end" />)
    const wrapper = screen.getByText('$161.64').closest('div')
    expect(wrapper.className).toContain('price--end')
  })

  it('leaves the price block left-aligned by default (detail page)', () => {
    render(<PriceDisplay currentPrice={currentPrice} />)
    const wrapper = screen.getByText('$161.64').closest('div')
    expect(wrapper.className).not.toContain('price--end')
  })

  it('right-aligns the missing-price dash too when align="end"', () => {
    render(<PriceDisplay currentPrice={null} align="end" />)
    expect(screen.getByText('—').closest('div').className).toContain('price--end')
  })

  it('shows no labels by default (list rows)', () => {
    render(<PriceDisplay currentPrice={currentPrice} />)
    expect(screen.queryByText('with shipping')).not.toBeInTheDocument()
    expect(screen.queryByText('item price')).not.toBeInTheDocument()
  })

  it('with showLabels, badges the total as "with shipping" and labels the grey line "item price"', () => {
    render(<PriceDisplay currentPrice={currentPrice} showLabels />)
    expect(screen.getByText('with shipping')).toBeInTheDocument()
    expect(screen.getByText('item price')).toBeInTheDocument()
    // the amounts stay in their own elements so they can still be read on their own
    expect(screen.getByText('$161.64')).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })

  it('with showLabels, the badge sits on the total line and the label on the item line', () => {
    render(<PriceDisplay currentPrice={currentPrice} showLabels />)
    const totalLine = screen.getByText('$161.64').parentElement
    const itemLine = screen.getByText('$150.00').parentElement
    expect(totalLine).toContainElement(screen.getByText('with shipping'))
    expect(itemLine).toContainElement(screen.getByText('item price'))
    expect(totalLine).not.toBe(itemLine)
  })

  it('shows no labels when there is no price, even with showLabels', () => {
    render(<PriceDisplay currentPrice={null} showLabels />)
    expect(screen.queryByText('with shipping')).not.toBeInTheDocument()
    expect(screen.queryByText('item price')).not.toBeInTheDocument()
  })
})
