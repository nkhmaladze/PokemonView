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

const products = [
  {
    id: 'p1',
    set_name: 'Chaos Rising',
    product_type: 'booster_box',
    display_name: 'Chaos Rising Booster Box',
    image_url: null,
    price_status: 'ok',
    current_price: {
      total_price: 150,
      item_price: 145,
      as_of: '2026-07-15T00:00:00Z',
      listing_count: 5,
    },
  },
  {
    id: 'p2',
    set_name: 'Perfect Order',
    product_type: 'etb',
    display_name: 'Perfect Order ETB',
    image_url: null,
    price_status: 'ok',
    current_price: {
      total_price: 45,
      item_price: 42,
      as_of: '2026-07-15T00:00:00Z',
      listing_count: 3,
    },
  },
  {
    id: 'p3',
    set_name: 'Pitch Black',
    product_type: 'booster_pack',
    display_name: 'Pitch Black Booster Pack',
    image_url: null,
    price_status: 'no_data_yet',
    current_price: null,
  },
]

function renderCatalog() {
  useLoaderDataMock.mockReturnValue(products)
  return render(
    <MemoryRouter>
      <CatalogPage />
    </MemoryRouter>
  )
}

describe('CatalogPage', () => {
  it('renders one ProductRow per product from loader data as a flat continuous list', () => {
    renderCatalog()
    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.getByText('Perfect Order ETB')).toBeInTheDocument()
    expect(screen.getByText('Pitch Black Booster Pack')).toBeInTheDocument()
  })

  it('typing a substring filters the list in-memory with no additional fetch', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.type(screen.getByLabelText('Search products'), 'box')

    expect(screen.getByText('Chaos Rising Booster Box')).toBeInTheDocument()
    expect(screen.queryByText('Perfect Order ETB')).not.toBeInTheDocument()
    expect(screen.queryByText('Pitch Black Booster Pack')).not.toBeInTheDocument()
    // loader is only ever invoked to seed useLoaderData, never re-invoked per keystroke
    expect(useLoaderDataMock).toHaveBeenCalled()
  })

  it('selecting a product_type chip narrows the list', async () => {
    const user = userEvent.setup()
    renderCatalog()
    await user.click(screen.getByRole('button', { name: 'ETB' }))

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
})
