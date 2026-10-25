import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterChips, { PRODUCT_TYPE_OPTIONS } from './FilterChips'

describe('FilterChips', () => {
  it('exports the exact four raw product_type values (VALID_PRODUCT_TYPES, no invented types)', () => {
    expect(PRODUCT_TYPE_OPTIONS.map((o) => o.value)).toEqual([
      'booster_pack',
      'booster_box',
      'booster_bundle',
      'etb',
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

  it('renders a Set dropdown with "All sets" first, then the given sets in the given order', () => {
    render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        sets={['Delta Reign', 'Pitch Black', 'Base Set']}
        setName={null}
        onSetName={() => {}}
      />
    )
    const select = screen.getByRole('combobox', { name: 'Set' })
    const labels = Array.from(select.querySelectorAll('option')).map((o) => o.textContent)
    expect(labels).toEqual(['All sets', 'Delta Reign', 'Pitch Black', 'Base Set'])
  })

  it('choosing a set calls onSetName with its raw name', async () => {
    const user = userEvent.setup()
    const onSetName = vi.fn()
    render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        sets={['Pitch Black', 'Base Set']}
        setName={null}
        onSetName={onSetName}
      />
    )
    await user.selectOptions(screen.getByRole('combobox', { name: 'Set' }), 'Base Set')
    expect(onSetName).toHaveBeenCalledWith('Base Set')
  })

  it('choosing "All sets" calls onSetName(null)', async () => {
    const user = userEvent.setup()
    const onSetName = vi.fn()
    render(
      <FilterChips
        productType={null}
        onProductType={() => {}}
        sets={['Pitch Black', 'Base Set']}
        setName="Base Set"
        onSetName={onSetName}
      />
    )
    const select = screen.getByRole('combobox', { name: 'Set' })
    expect(select).toHaveValue('Base Set')
    await user.selectOptions(select, 'All sets')
    expect(onSetName).toHaveBeenCalledWith(null)
  })
})
