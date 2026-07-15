import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import TrendBadge from './TrendBadge'

describe('TrendBadge', () => {
  it('renders +X.X% with the up class for a positive pct_change', () => {
    render(<TrendBadge trend={{ status: 'ok', pct_change: 3.2 }} />)
    const badge = screen.getByText('+3.2%')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('trend-badge--up')
  })

  it('renders -X.X% with the down class for a negative pct_change', () => {
    render(<TrendBadge trend={{ status: 'ok', pct_change: -1.5 }} />)
    const badge = screen.getByText('-1.5%')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('trend-badge--down')
  })

  it('renders 0.0% with the flat (neutral-gray) class for exactly-zero pct_change', () => {
    render(<TrendBadge trend={{ status: 'ok', pct_change: 0 }} />)
    const badge = screen.getByText('0.0%')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('trend-badge--flat')
    expect(badge.className).not.toContain('trend-badge--up')
    expect(badge.className).not.toContain('trend-badge--down')
    expect(badge.className).not.toContain('trend-badge--muted')
  })

  it('renders a muted em-dash with aria-label for insufficient_data status', () => {
    render(<TrendBadge trend={{ status: 'insufficient_data', pct_change: null }} />)
    const badge = screen.getByLabelText('insufficient data')
    expect(badge).toBeInTheDocument()
    expect(badge.textContent).toBe('—')
    expect(badge.className).toContain('trend-badge--muted')
  })
})
