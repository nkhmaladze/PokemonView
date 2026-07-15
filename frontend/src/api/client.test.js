import { describe, it, expect, vi, afterEach } from 'vitest'
import { getProducts, getProductDetail } from './client'

function mockFetchOnce({ ok, status = 200, body }) {
  return vi.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok,
    status,
    json: () => Promise.resolve(body),
  })
}

describe('api/client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('getProducts() with no args requests exactly /products and resolves to the parsed JSON array', async () => {
    const products = [{ id: 'abc', display_name: 'Booster Box' }]
    mockFetchOnce({ ok: true, body: products })

    const result = await getProducts()

    expect(global.fetch).toHaveBeenCalledWith('/products')
    expect(result).toEqual(products)
  })

  it('getProducts({ product_type }) requests /products?product_type=booster_box via URLSearchParams', async () => {
    mockFetchOnce({ ok: true, body: [] })

    await getProducts({ product_type: 'booster_box' })

    expect(global.fetch).toHaveBeenCalledWith('/products?product_type=booster_box')
  })

  it('getProductDetail("some-id") requests exactly /products/some-id and resolves to the parsed detail object', async () => {
    const detail = { id: 'some-id', display_name: 'Elite Trainer Box' }
    mockFetchOnce({ ok: true, body: detail })

    const result = await getProductDetail('some-id')

    expect(global.fetch).toHaveBeenCalledWith('/products/some-id')
    expect(result).toEqual(detail)
  })

  it('rejects with an Error whose message is the API error string when the response is not ok', async () => {
    mockFetchOnce({ ok: false, status: 404, body: { error: 'not_found' } })

    await expect(getProductDetail('missing-id')).rejects.toThrow('not_found')
  })

  it('falls back to "Request failed: <status>" when the error body is unparseable', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('not json')),
    })

    await expect(getProductDetail('broken')).rejects.toThrow('Request failed: 500')
  })
})
