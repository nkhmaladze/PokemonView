import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import FreshnessIndicator from './FreshnessIndicator'

describe('FreshnessIndicator', () => {
  it('renders "Data as of {relative time}" from an asOf ISO timestamp ~2 hours old', () => {
    const asOf = new Date(Date.now() - 2 * 3600 * 1000).toISOString()
    render(<FreshnessIndicator asOf={asOf} />)
    expect(screen.getByText(/Data as of/)).toBeInTheDocument()
    expect(screen.getByText(/hour/)).toBeInTheDocument()
  })
})
