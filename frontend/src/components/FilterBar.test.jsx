import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FilterBar, { PRODUCT_TYPE_OPTIONS } from './FilterBar'

const setGroups = [
  { era: 'Mega Evolution', sets: ['Delta Reign', 'Pitch Black'] },
  { era: 'Classic', sets: ['Base Set'] },
]

function renderBar(props = {}) {
  const handlers = {
    onProductType: vi.fn(),
    onEra: vi.fn(),
    onSetName: vi.fn(),
    onClear: vi.fn(),
  }
  render(
    <FilterBar
      productType={null}
      era={null}
      setName={null}
      eras={['Mega Evolution', 'Classic']}
      setGroups={setGroups}
      shown={3}
      total={10}
      hasFilters={false}
      {...handlers}
      {...props}
    />
  )
  return handlers
}

function optionLabels(select) {
  return Array.from(select.querySelectorAll('option')).map((o) => o.textContent)
}

describe('FilterBar', () => {
  it('exports the exact four raw product_type values (VALID_PRODUCT_TYPES, no invented types)', () => {
    expect(PRODUCT_TYPE_OPTIONS.map((o) => o.value)).toEqual([
      'booster_pack',
      'booster_box',
      'booster_bundle',
      'etb',
    ])
  })

  it('renders Type, Era and Set as dropdowns', () => {
    renderBar()
    expect(screen.getByRole('combobox', { name: 'Type' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Era' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Set' })).toBeInTheDocument()
  })

  it('lists "All types" first, then the four product types', () => {
    renderBar()
    expect(optionLabels(screen.getByRole('combobox', { name: 'Type' }))).toEqual([
      'All types',
      'Booster Pack',
      'Booster Box',
      'Booster Bundle',
      'ETB',
    ])
  })

  it('choosing a type calls onProductType with its raw value, and "All types" calls it with null', async () => {
    const user = userEvent.setup()
    const { onProductType } = renderBar()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Type' }), 'Booster Box')
    expect(onProductType).toHaveBeenLastCalledWith('booster_box')
    await user.selectOptions(screen.getByRole('combobox', { name: 'Type' }), 'All types')
    expect(onProductType).toHaveBeenLastCalledWith(null)
  })

  it('lists "All eras" first, then the given eras in the given order', () => {
    renderBar()
    expect(optionLabels(screen.getByRole('combobox', { name: 'Era' }))).toEqual([
      'All eras',
      'Mega Evolution',
      'Classic',
    ])
  })

  it('choosing an era calls onEra with its label, and "All eras" calls it with null', async () => {
    const user = userEvent.setup()
    const { onEra } = renderBar()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Era' }), 'Classic')
    expect(onEra).toHaveBeenLastCalledWith('Classic')
    await user.selectOptions(screen.getByRole('combobox', { name: 'Era' }), 'All eras')
    expect(onEra).toHaveBeenLastCalledWith(null)
  })

  it('with no era chosen, groups the Set options under era headings', () => {
    renderBar()
    const select = screen.getByRole('combobox', { name: 'Set' })
    const groups = Array.from(select.querySelectorAll('optgroup'))
    expect(groups.map((g) => g.label)).toEqual(['Mega Evolution', 'Classic'])
    expect(optionLabels(groups[0])).toEqual(['Delta Reign', 'Pitch Black'])
    expect(optionLabels(select)).toEqual([
      'All sets',
      'Delta Reign',
      'Pitch Black',
      'Base Set',
    ])
  })

  it('with an era chosen, lists only that era\'s sets and no headings', () => {
    renderBar({ era: 'Classic', setGroups: [{ era: 'Classic', sets: ['Base Set'] }] })
    const select = screen.getByRole('combobox', { name: 'Set' })
    expect(select.querySelectorAll('optgroup')).toHaveLength(0)
    expect(optionLabels(select)).toEqual(['All sets', 'Base Set'])
  })

  it('choosing a set calls onSetName with its raw name, and "All sets" calls it with null', async () => {
    const user = userEvent.setup()
    const { onSetName } = renderBar({ setName: 'Base Set' })
    const select = screen.getByRole('combobox', { name: 'Set' })
    expect(select).toHaveValue('Base Set')
    await user.selectOptions(select, 'Pitch Black')
    expect(onSetName).toHaveBeenLastCalledWith('Pitch Black')
    await user.selectOptions(select, 'All sets')
    expect(onSetName).toHaveBeenLastCalledWith(null)
  })

  it('marks only the dropdowns that are filtering', () => {
    renderBar({ productType: 'etb', era: 'Classic', setName: null })
    expect(screen.getByRole('combobox', { name: 'Type' }).className).toContain('select--active')
    expect(screen.getByRole('combobox', { name: 'Era' }).className).toContain('select--active')
    expect(screen.getByRole('combobox', { name: 'Set' }).className).not.toContain(
      'select--active'
    )
  })

  it('shows how many products match', () => {
    renderBar({ shown: 3, total: 10 })
    expect(screen.getByText('Showing 3 of 10 products')).toBeInTheDocument()
  })

  it('says "1 product" in the singular', () => {
    renderBar({ shown: 1, total: 1 })
    expect(screen.getByText('Showing 1 of 1 product')).toBeInTheDocument()
  })

  it('hides "Clear filters" when nothing is filtered', () => {
    renderBar({ hasFilters: false })
    expect(screen.queryByRole('button', { name: 'Clear filters' })).not.toBeInTheDocument()
  })

  it('shows "Clear filters" when something is filtered, and it calls onClear', async () => {
    const user = userEvent.setup()
    const { onClear } = renderBar({ hasFilters: true })
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(onClear).toHaveBeenCalledTimes(1)
  })

  it('announces the match count politely to screen readers', () => {
    renderBar()
    const status = screen.getByRole('status')
    expect(within(status).getByText('Showing 3 of 10 products')).toBeInTheDocument()
  })
})
