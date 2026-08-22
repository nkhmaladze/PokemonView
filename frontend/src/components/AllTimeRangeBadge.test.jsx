import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import AllTimeRangeBadge from './AllTimeRangeBadge'

describe('AllTimeRangeBadge', () => {
  it('renders the low bound, an en dash separator, then the high bound for an ok range', () => {
    render(<AllTimeRangeBadge range={{ high: 172.5, low: 129.99, status: 'ok' }} />)
    const badge = screen.getByText('$129.99 – $172.50')
    expect(badge).toBeInTheDocument()
  })

  it('renders both bounds when high equals low, never collapsed or suppressed (a single collected price point is real data, not insufficient data)', () => {
    render(<AllTimeRangeBadge range={{ high: 29.99, low: 29.99, status: 'ok' }} />)
    const badge = screen.getByText('$29.99 – $29.99')
    expect(badge).toBeInTheDocument()
  })

  it('renders a muted em-dash with aria-label for explicit insufficient_data status', () => {
    render(<AllTimeRangeBadge range={{ high: null, low: null, status: 'insufficient_data' }} />)
    const badge = screen.getByLabelText('insufficient data')
    expect(badge).toBeInTheDocument()
    expect(badge.textContent).toBe('—')
    expect(badge.className).toContain('range--muted')
  })

  it('renders the muted state without throwing when range is null or the prop is absent (last line of defense behind ROADMAP success criterion 4)', () => {
    expect(() => render(<AllTimeRangeBadge range={null} />)).not.toThrow()
    const nullBadge = screen.getByLabelText('insufficient data')
    expect(nullBadge.textContent).toBe('—')

    expect(() => render(<AllTimeRangeBadge />)).not.toThrow()
    const noPropBadges = screen.getAllByLabelText('insufficient data')
    expect(noPropBadges.length).toBeGreaterThan(0)
  })

  it("ok state's class list contains the base class and not the muted modifier", () => {
    render(<AllTimeRangeBadge range={{ high: 172.5, low: 129.99, status: 'ok' }} />)
    const badge = screen.getByText('$129.99 – $172.50')
    expect(badge.className).toContain('range')
    expect(badge.className).not.toContain('range--muted')
  })
})
