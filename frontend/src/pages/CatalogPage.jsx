import { useMemo, useState } from 'react'
import { useLoaderData } from 'react-router'
import styles from './CatalogPage.module.css'
import SearchBar from '../components/SearchBar'
import FilterChips from '../components/FilterChips'
import ProductRow from '../components/ProductRow'

/**
 * CatalogPage — the browse route (`/`), SEARCH-01, D-02/D-14.
 *
 * The full catalog array is fetched exactly once by the route loader
 * (wired in 06-07) and read here via useLoaderData(). All search-text
 * and product_type/set_name chip filtering happens against that
 * already-loaded array in-memory via useMemo — the loader is never
 * re-invoked in response to typing or chip clicks (no per-keystroke
 * network call, D-14).
 *
 * Renders one ProductRow per visible product as a single flat,
 * continuous list in the loader's given order — no per-set section
 * headers or tabs (D-02) — or the "No products found" empty state when
 * the combined filter matches nothing.
 */
export default function CatalogPage() {
  const products = useLoaderData()
  const [query, setQuery] = useState('')
  const [productType, setProductType] = useState(null)
  const [setName, setSetName] = useState(null)

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return products.filter((product) => {
      if (productType && product.product_type !== productType) return false
      if (setName && product.set_name !== setName) return false
      if (
        q &&
        !product.display_name.toLowerCase().includes(q) &&
        !product.set_name.toLowerCase().includes(q)
      ) {
        return false
      }
      return true
    })
  }, [products, query, productType, setName])

  return (
    <div className={styles.catalog}>
      <h1 className={styles.title}>PokemonView Catalog</h1>
      <SearchBar value={query} onChange={setQuery} />
      <FilterChips
        productType={productType}
        onProductType={setProductType}
        setName={setName}
        onSetName={setSetName}
      />
      {visible.length === 0 ? (
        <div className={styles.empty}>
          <h2>No products found</h2>
          <p>Try a different search term, or clear your filters to see the full catalog.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {visible.map((product) => (
            <ProductRow key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}
