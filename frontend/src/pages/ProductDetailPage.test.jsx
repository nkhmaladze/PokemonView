import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import ProductDetailPage from './ProductDetailPage'
import { getPriceHistory } from '../api/client'

const useLoaderDataMock = vi.fn()

vi.mock('react-router', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  }
})

vi.mock('../api/client', () => ({ getPriceHistory: vi.fn() }))

const okProduct = {
  id: 'p1',
  set_name: 'Chaos Rising',
  product_type: 'booster_box',
  display_name: 'Chaos Rising Booster Box',
  release_date: '2026-03-01',
  msrp: 161.64,
  image_url: null,
  verified: true,
  price_status: 'ok',
  current_price: {
    total_price: 150,
    item_price: 145,
    as_of: '2026-07-15T00:00:00Z',
    listing_count: 5,
  },
  trend_7d: { pct_change: 2.5, status: 'ok' },
  trend_30d: { pct_change: -1.2, status: 'ok' },
}

function renderDetail(product) {
  useLoaderDataMock.mockReturnValue(product)
  return render(
    <MemoryRouter initialEntries={[`/products/${product.id}`]}>
      <Routes>
        <Route path="/products/:productId" element={<ProductDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

// A promise plus its own resolve/reject, so a test can assert an in-flight
// state before deciding how the request settles. An already-resolved mock
// would settle before the first synchronous assertion ran and the loading
// state would never be observable — this is what makes D-05's ordering
// property assertable.
function deferred() {
  let resolve
  let reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('ProductDetailPage', () => {
  beforeEach(() => {
    getPriceHistory.mockReset()
    getPriceHistory.mockResolvedValue([])
  })

  it('renders total price, item price, both trend badges, freshness caption, and sample-size caption for an "ok" product', () => {
    renderDetail(okProduct)

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('$145.00')).toBeInTheDocument()
    expect(screen.getByText('+2.5%')).toBeInTheDocument()
    expect(screen.getByText('-1.2%')).toBeInTheDocument()
    expect(screen.getByText(/Data as of/)).toBeInTheDocument()
    expect(screen.getByText('Based on 5 active listing(s)')).toBeInTheDocument()
  })

  it('shows "Sample size unavailable" when listing_count is null', () => {
    renderDetail({
      ...okProduct,
      current_price: { ...okProduct.current_price, listing_count: null },
    })

    expect(screen.getByText('Sample size unavailable')).toBeInTheDocument()
  })

  it('renders a graceful no-data state for a "no_data_yet" product without throwing, and still shows both trend badges', () => {
    const noDataProduct = {
      ...okProduct,
      price_status: 'no_data_yet',
      current_price: null,
      trend_7d: { pct_change: null, status: 'insufficient_data' },
      trend_30d: { pct_change: null, status: 'insufficient_data' },
    }

    expect(() => renderDetail(noDataProduct)).not.toThrow()
    expect(screen.getByText('No pricing data yet')).toBeInTheDocument()
    expect(screen.getAllByLabelText('insufficient data')).toHaveLength(2)
    expect(screen.queryByText(/Data as of/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Based on/)).not.toBeInTheDocument()
  })

  it('shows "—" for a null msrp and "TBD" for a null release_date', () => {
    renderDetail({ ...okProduct, msrp: null, release_date: null })

    expect(screen.getByText(/—/)).toBeInTheDocument()
    expect(screen.getByText(/TBD/)).toBeInTheDocument()
  })

  it('shows the price headline before the history fetch resolves, then renders the chart once it does (D-05)', async () => {
    const historyData = [
      { ts: '2026-07-14T00:00:00Z', total_price: 145 },
      { ts: '2026-07-15T00:00:00Z', total_price: 148 },
      { ts: '2026-07-16T00:00:00Z', total_price: 150 },
    ]
    let resolveHistory
    getPriceHistory.mockReturnValue(
      new Promise((resolve) => {
        resolveHistory = resolve
      })
    )

    renderDetail(okProduct)

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('Loading price history…')).toBeInTheDocument()

    resolveHistory(historyData)

    expect(await screen.findByTestId('price-history-chart')).toBeInTheDocument()
    expect(screen.getByText('Price History')).toBeInTheDocument()
  })

  it('shows a chart-scoped error message and keeps the price headline when the history fetch rejects (D-05)', async () => {
    getPriceHistory.mockRejectedValue(new Error('network error'))

    renderDetail(okProduct)

    expect(
      await screen.findByText("Couldn't load price history. Try refreshing the page.")
    ).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
  })

  it('shows price, badges and meta before the history request settles', async () => {
    // D-05: the loader-driven content is paintable while the second
    // request is still open, which is the whole reason this is a
    // separate fetch rather than a field on the detail response.
    const { promise, resolve } = deferred()
    getPriceHistory.mockReturnValue(promise)

    renderDetail(okProduct)

    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('+2.5%')).toBeInTheDocument()
    expect(screen.getByText('-1.2%')).toBeInTheDocument()
    expect(screen.getByText(/MSRP:/)).toBeInTheDocument()
    expect(screen.getByText('Loading price history…')).toBeInTheDocument()

    resolve([
      { ts: '2026-07-14T00:00:00Z', total_price: 145 },
      { ts: '2026-07-15T00:00:00Z', total_price: 148 },
      { ts: '2026-07-16T00:00:00Z', total_price: 150 },
    ])

    expect(await screen.findByTestId('price-history-chart')).toBeInTheDocument()
    expect(screen.queryByText('Loading price history…')).not.toBeInTheDocument()
  })

  it('contains a failed history request to the chart section', async () => {
    // The route's ProductNotFound errorElement only catches loader and
    // render-time throws, so this rejection has no route-level safety
    // net — its containment is the component's own responsibility.
    const { promise, reject } = deferred()
    getPriceHistory.mockReturnValue(promise)

    renderDetail(okProduct)
    reject(new Error('network error'))

    expect(
      await screen.findByText("Couldn't load price history. Try refreshing the page.")
    ).toBeInTheDocument()
    expect(screen.getByText('$150.00')).toBeInTheDocument()
    expect(screen.getByText('+2.5%')).toBeInTheDocument()
    expect(screen.getByText('-1.2%')).toBeInTheDocument()
    expect(screen.getByText(/MSRP:/)).toBeInTheDocument()
    expect(screen.queryByTestId('price-history-chart')).not.toBeInTheDocument()
    expect(screen.queryByText('Product not found.')).not.toBeInTheDocument()
  })

  it('requests history for the product in the URL, with an abortable signal', () => {
    // WR-02, 08-REVIEW.md: the fetch cancellation guard must thread a real
    // AbortSignal through to the client, not just discard a stale result.
    renderDetail({ ...okProduct, id: 'p2' })

    expect(getPriceHistory).toHaveBeenCalledTimes(1)
    expect(getPriceHistory).toHaveBeenCalledWith('p2', { signal: expect.any(AbortSignal) })
  })

  it('aborts the in-flight history request on unmount', () => {
    // WR-02: unmounting must actually cancel the underlying fetch (not
    // merely discard its eventual result) — assert the signal passed to
    // getPriceHistory is aborted once the component unmounts.
    const { unmount } = renderDetail(okProduct)

    const { signal } = getPriceHistory.mock.calls[0][1]
    expect(signal.aborted).toBe(false)

    unmount()

    expect(signal.aborted).toBe(true)
  })

  it('discards a history response that settles after unmount', async () => {
    // The observable half of the cancellation guard described in the
    // UI-SPEC's `partial` consideration: the same flag that stops a late
    // response from reaching a torn-down tree is what stops a slow
    // response for a previously-viewed product from overwriting the
    // chart of the product the user has since navigated to.
    const { promise, resolve } = deferred()
    getPriceHistory.mockReturnValue(promise)

    const { unmount } = renderDetail(okProduct)
    expect(screen.getByText('Loading price history…')).toBeInTheDocument()

    unmount()

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    resolve([
      { ts: '2026-07-14T00:00:00Z', total_price: 145 },
      { ts: '2026-07-15T00:00:00Z', total_price: 148 },
      { ts: '2026-07-16T00:00:00Z', total_price: 150 },
    ])
    await Promise.resolve()
    await Promise.resolve()

    expect(consoleErrorSpy).not.toHaveBeenCalled()
    consoleErrorSpy.mockRestore()
  })

  it('places the Price History section between the trend badges and the meta block', async () => {
    // D-03, UI-SPEC Layout Notes ordering: header, price, trends,
    // history, meta.
    getPriceHistory.mockResolvedValue([
      { ts: '2026-07-14T00:00:00Z', total_price: 145 },
      { ts: '2026-07-15T00:00:00Z', total_price: 148 },
      { ts: '2026-07-16T00:00:00Z', total_price: 150 },
    ])

    const { container } = renderDetail(okProduct)
    await screen.findByTestId('price-history-chart')

    const text = container.textContent
    expect(text.indexOf('Price History')).toBeGreaterThan(text.indexOf('7d'))
    expect(text.indexOf('Price History')).toBeLessThan(text.indexOf('MSRP:'))
    expect(screen.getByText('Price History').tagName).toBe('H2')
  })
})
