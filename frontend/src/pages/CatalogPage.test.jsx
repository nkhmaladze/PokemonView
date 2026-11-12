import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import CatalogPage from './CatalogPage'

const useLoaderDataMock = vi.fn()

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  }
})

const price = {
  total_price: 150,
  item_price: 145,
  as_of: '2026-07-15T00:00:00Z',
  listing_count: 5,
}

const products = [
  {
    id: 'p1',
    set_name: 'Chaos Rising',
    release_date: '2026-05-22',
    product_type: 'booster_box',
    display_name: 'Chaos Rising Booster Box',
    image_url: null,
    price_status: 'ok',
    current_price: price,
  },
  {
    id: 'p2',
    set_name: 'Perfect Order',
    release_date: '2026-03-27',
    product_type: 'etb',
    display_name: 'Perfect Order ETB',
    image_url: null,
    price_status: 'ok',
    current_price: { ...price, total_price: 45, item_price: 42 },
  },
  {
    id: 'p3',
    set_name: 'Pitch Black',
    release_date: '2026-07-17',
    product_type: 'booster_pack',
    display_name: 'Pitch Black Booster Pack',
    image_url: null,
    price_status: 'no_data_yet',
    current_price: null,
  },
  {
    id: 'p4',
    set_name: 'Surging Sparks',
    release_date: '2024-11-08',
    product_type: 'booster_box',
    display_name: 'Surging Sparks Booster Box',
    image_url: null,
    price_status: 'ok',
    current_price: price,
  },
  {
    id: 'p5',
    set_name: 'Base Set',
    release_date: '1999-01-09',
    product_type: 'booster_box',
    display_name: 'Base Set Booster Box',
    image_url: null,
    price_status: 'ok',
    current_price: price,
  },
]

function renderCatalog(data = products) {
  useLoaderDataMock.mockReturnValue(data)
  return render(
    <MemoryRouter>
      <CatalogPage />
    </MemoryRouter>
  )
}

function optionLabels(select) {
  return Array.from(select.querySelectorAll('option')).map((o) => o.textContent)
}

const typeSelect = () => screen.getByRole('combobox', { name: 'Type' })
const eraSelect = () => screen.getByRole('combobox', { name: 'Era' })
const setSelect = () => screen.getByRole('combobox', { name: 'Set' })

describe('CatalogPage', () => {
  it('renders one ProductRow per product from loader data as a flat continuous list', () => {
    renderCatalog()
    for (const product of products) {
      expect(screen.getByText(product.display_name)).toBeInTheDocument()
    }
  })

  it('typing a substring filters the list in-memory with no additional fetch', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.type(screen.getByLabelText('Search products'), 'box')

    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.getByText('Surging Sparks Booster Box')).toBeInTheDocument()
    expect(screen.getByText('Base Set Booster Box')).toBeInTheDocument()
    expect(screen.queryByText('Perfect Order ETB')).not.toBeInTheDocument()
    expect(screen.queryByText('Pitch Black Booster Pack')).not.toBeInTheDocument()
    // loader is only ever invoked to seed useLoaderData, never re-invoked per keystroke
    expect(useLoaderDataMock).toHaveBeenCalled()
  })

  it('choosing a product type narrows the list', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(typeSelect(), 'ETB')

    expect(screen.getByText('Perfect Order ETB')).toBeInTheDocument()
    expect(screen.queryByText('Chaos Rising Booster Box')).not.toBeInTheDocument()
    expect(screen.queryByText('Pitch Black Booster Pack')).not.toBeInTheDocument()
  })

  it('shows the "No products found" empty state when filters produce zero matches', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.type(screen.getByLabelText('Search products'), 'zzzzzznotfound')

    expect(screen.getByText('No products found')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Try a different search term, or clear your filters to see the full catalog.'
      )
    ).toBeInTheDocument()
  })

  it('offers only the eras that have products, newest first', () => {
    renderCatalog()
    expect(optionLabels(eraSelect())).toEqual([
      'All eras',
      'Mega Evolution',
      'Scarlet & Violet',
      'Classic',
    ])
  })

  it('choosing an era narrows the list', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(eraSelect(), 'Mega Evolution')

    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.getByText('Perfect Order ETB')).toBeInTheDocument()
    expect(screen.getByText('Pitch Black Booster Pack')).toBeInTheDocument()
    expect(screen.queryByText('Surging Sparks Booster Box')).not.toBeInTheDocument()
    expect(screen.queryByText('Base Set Booster Box')).not.toBeInTheDocument()
  })

  it('with no era chosen, the Set dropdown lists each set once, grouped by era in loader order', () => {
    renderCatalog()
    const groups = Array.from(setSelect().querySelectorAll('optgroup'))
    expect(groups.map((g) => g.label)).toEqual(['Mega Evolution', 'Scarlet & Violet', 'Classic'])
    expect(optionLabels(setSelect())).toEqual([
      'All sets',
      'Chaos Rising',
      'Perfect Order',
      'Pitch Black',
      'Surging Sparks',
      'Base Set',
    ])
  })

  it('choosing an era limits the Set dropdown to that era', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(eraSelect(), 'Mega Evolution')

    expect(optionLabels(setSelect())).toEqual([
      'All sets',
      'Chaos Rising',
      'Perfect Order',
      'Pitch Black',
    ])
  })

  it('choosing a set narrows the list', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(setSelect(), 'Perfect Order')

    expect(screen.getByText('Perfect Order ETB')).toBeInTheDocument()
    expect(screen.queryByText('Chaos Rising Booster Box')).not.toBeInTheDocument()
  })

  it('changing the era clears a chosen set that belongs to a different era', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(setSelect(), 'Base Set')
    expect(screen.getByText('Base Set Booster Box')).toBeInTheDocument()

    await user.selectOptions(eraSelect(), 'Mega Evolution')

    expect(setSelect()).toHaveValue('')
    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.queryByText('Base Set Booster Box')).not.toBeInTheDocument()
  })

  it('changing the era keeps a chosen set that belongs to the new era', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(setSelect(), 'Perfect Order')
    await user.selectOptions(eraSelect(), 'Mega Evolution')

    expect(setSelect()).toHaveValue('Perfect Order')
    expect(screen.getByText('Perfect Order ETB')).toBeInTheDocument()
    expect(screen.queryByText('Chaos Rising Booster Box')).not.toBeInTheDocument()
  })

  it('combines type, era and search', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.selectOptions(typeSelect(), 'Booster Box')
    await user.selectOptions(eraSelect(), 'Mega Evolution')
    await user.type(screen.getByLabelText('Search products'), 'chaos')

    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.queryByText('Surging Sparks Booster Box')).not.toBeInTheDocument()
    expect(screen.queryByText('Perfect Order ETB')).not.toBeInTheDocument()
  })

  it('shows how many products match', async () => {
    const user = userEvent.setup()
    renderCatalog()
    expect(screen.getByText('Showing 5 of 5 products')).toBeInTheDocument()

    await user.selectOptions(typeSelect(), 'ETB')
    expect(screen.getByText('Showing 1 of 5 products')).toBeInTheDocument()
  })

  it('"Clear filters" appears once something is filtered and resets search, type, era and set', async () => {
    const user = userEvent.setup()
    renderCatalog()
    expect(screen.queryByRole('button', { name: 'Clear filters' })).not.toBeInTheDocument()

    await user.type(screen.getByLabelText('Search products'), 'box')
    await user.selectOptions(typeSelect(), 'Booster Box')
    await user.selectOptions(eraSelect(), 'Mega Evolution')
    await user.selectOptions(setSelect(), 'Chaos Rising')
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))

    expect(screen.getByLabelText('Search products')).toHaveValue('')
    expect(typeSelect()).toHaveValue('')
    expect(eraSelect()).toHaveValue('')
    expect(setSelect()).toHaveValue('')
    expect(screen.getByText('Showing 5 of 5 products')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Clear filters' })).not.toBeInTheDocument()
  })

  it('keeps a product with no release date in the full list, under an "Other" heading in the Set dropdown', async () => {
    const user = userEvent.setup()
    renderCatalog([
      ...products,
      {
        id: 'p6',
        set_name: 'Mystery Set',
        release_date: null,
        product_type: 'etb',
        display_name: 'Mystery Set ETB',
        image_url: null,
        price_status: 'no_data_yet',
        current_price: null,
      },
    ])
    expect(screen.getByText('Mystery Set ETB')).toBeInTheDocument()
    const groups = Array.from(setSelect().querySelectorAll('optgroup'))
    expect(groups.map((g) => g.label)).toEqual([
      'Mega Evolution',
      'Scarlet & Violet',
      'Classic',
      'Other',
    ])
    // not a real era, so it is not offered as one
    expect(optionLabels(eraSelect())).not.toContain('Other')

    await user.selectOptions(eraSelect(), 'Classic')
    expect(screen.queryByText('Mystery Set ETB')).not.toBeInTheDocument()
  })

  it('keeps the list plain: no column header and no price captions on the rows', () => {
    renderCatalog()
    expect(screen.queryByText('Product')).not.toBeInTheDocument()
    expect(screen.queryByText('Price with shipping')).not.toBeInTheDocument()
    expect(screen.queryByText('with shipping')).not.toBeInTheDocument()
    expect(screen.queryByText('item')).not.toBeInTheDocument()
    expect(screen.queryByText('item price')).not.toBeInTheDocument()
  })
})
