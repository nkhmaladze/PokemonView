import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterChips, { PRODUCT_TYPE_OPTIONS, SET_OPTIONS } from './FilterChips'

describe('FilterChips', () => {
  it('exports the exact four raw product_type values (VALID_PRODUCT_TYPES, no invented types)', () => {
    expect(PRODUCT_TYPE_OPTIONS.map((o) => o.value)).toEqual([
      'booster_pack',
      'booster_box',
      'booster_bundle',
      'etb',
    ])
  })

  it('exports the exact four set names (SET_ORDER)', () => {
    expect(SET_OPTIONS.map((o) => o.value)).toEqual([
      'Pitch Black',
      'Chaos Rising',
      'Perfect Order',
      'Ascended Heroes',
    ])
  })

  it('renders all four product_type chip labels', () => {
    render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        setName={null}
        onSetName={() => {}}
      />
    )
    expect(screen.getByRole('button', { name: 'Booster Pack' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Booster Box' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Booster Bundle' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'ETB' })).toBeInTheDocument()
  })

  it('renders all four set chip labels', () => {
    render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        setName={null}
        onSetName={() => {}}
      />
    )
    expect(screen.getByRole('button', { name: 'Pitch Black' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chaos Rising' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Perfect Order' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ascended Heroes' })).toBeInTheDocument()
  })

  it('clicking an inactive product_type chip calls onProductType with its raw value', async () => {
    const user = userEvent.setup()
    const onProductType = vi.fn()
    render(
      <FilterChips
        productType={null}
        onProductType={onProductType}
        setName={null}
        onSetName={() => {}}
      />
    )
    await user.click(screen.getByRole('button', { name: 'Booster Box' }))
    expect(onProductType).toHaveBeenCalledWith('booster_box')
  })

  it('clicking the already-active product_type chip calls onProductType(null) (toggle off)', async () => {
    const user = userEvent.setup()
    const onProductType = vi.fn()
    render(
      <FilterChips
        productType="booster_box"
        onProductType={onProductType}
        setName={null}
        onSetName={() => {}}
      />
    )
    await user.click(screen.getByRole('button', { name: 'Booster Box' }))
    expect(onProductType).toHaveBeenCalledWith(null)
  })

  it('applies the active class to the currently-selected product_type chip only', () => {
    render(
      <FilterChips
        productType="booster_box"
        onProductType={() => {}}
        setName={null}
        onSetName={() => {}}
      />
    )
    const active = screen.getByRole('button', { name: 'Booster Box' })
    const inactive = screen.getByRole('button', { name: 'Booster Pack' })
    expect(active.className).toContain('chip--active')
    expect(inactive.className).not.toContain('chip--active')
  })

  it('clicking a set chip calls onSetName with its raw value, and toggles off when already active', async () => {
    const user = userEvent.setup()
    const onSetName = vi.fn()
    const { rerender } = render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        setName={null}
        onSetName={onSetName}
      />
    )
    await user.click(screen.getByRole('button', { name: 'Pitch Black' }))
    expect(onSetName).toHaveBeenCalledWith('Pitch Black')

    rerender(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        setName="Pitch Black"
        onSetName={onSetName}
      />
    )
    await user.click(screen.getByRole('button', { name: 'Pitch Black' }))
    expect(onSetName).toHaveBeenCalledWith(null)
  })
})
