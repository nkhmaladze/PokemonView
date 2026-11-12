import { useMemo, useState } from 'react'
import { useLoaderData } from 'react-router'
import styles from './CatalogPage.module.css'
import SearchBar from '../components/SearchBar'
import FilterBar from '../components/FilterBar'
import ProductRow from '../components/ProductRow'
import { ERAS, eraForDate } from '../utils/eras'

// Sets whose release date is missing are listed under this heading in the Set
// dropdown. It is not a real era, so it is never offered in the Era dropdown.
const OTHER_ERA = 'Other'

/**
 * CatalogPage — the browse route (`/`).
 *
 * The full catalog array is fetched exactly once by the route loader
 * (wired in the router) and read here via useLoaderData(). All search-text
 * and type/era/set filtering happens against that already-loaded array
 * in-memory via useMemo — the loader is never re-invoked in response to
 * typing or dropdown changes (no per-keystroke network call).
 *
 * A product's era comes from its release date (utils/eras.js). The Era
 * dropdown only offers eras that have products, and choosing one narrows the
 * Set dropdown to that era's sets; choosing an era that does not contain the
 * currently chosen set clears the set so the list can never be empty because
 * of two filters that contradict each other.
 *
 * Renders one ProductRow per visible product as a single flat,
 * continuous list in the loader's given order — no per-set section
 * headers or tabs — or the "No products found" empty state when
 * the combined filter matches nothing. A table header above the rows says
 * the bold price includes shipping; each row's grey line is labelled "item".
 */
export default function CatalogPage() {
  const products = useLoaderData()
  const [query, setQuery] = useState('')
  const [productType, setProductType] = useState(null)
  const [era, setEra] = useState(null)
  const [setName, setSetName] = useState(null)

  const entries = useMemo(
    () => products.map((product) => ({ product, era: eraForDate(product.release_date) })),
    [products]
  )

  // First-seen order of the loader array = the API's newest-set-first order.
  const eraBySet = useMemo(() => {
    const map = new Map()
    for (const { product, era: productEra } of entries) {
      if (!map.has(product.set_name)) map.set(product.set_name, productEra)
    }
    return map
  }, [entries])

  const eras = useMemo(
    () => ERAS.map((candidate) => candidate.label).filter((label) => entries.some((e) => e.era === label)),
    [entries]
  )

  const setGroups = useMemo(() => {
    const groups = new Map()
    for (const [name, setEraLabel] of eraBySet) {
      const label = setEraLabel ?? OTHER_ERA
      if (era && label !== era) continue
      if (!groups.has(label)) groups.set(label, [])
      groups.get(label).push(name)
    }
    return [...ERAS.map((candidate) => candidate.label), OTHER_ERA]
      .filter((label) => groups.has(label))
      .map((label) => ({ era: label, sets: groups.get(label) }))
  }, [eraBySet, era])

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return entries
      .filter(({ product, era: productEra }) => {
        if (productType && product.product_type !== productType) return false
        if (era && productEra !== era) return false
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
      .map(({ product }) => product)
  }, [entries, query, productType, era, setName])

  const hasFilters = Boolean(query.trim() || productType || era || setName)

  function chooseEra(next) {
    setEra(next)
    if (next && setName && eraBySet.get(setName) !== next) setSetName(null)
  }

  function clearFilters() {
    setQuery('')
    setProductType(null)
    setEra(null)
    setSetName(null)
  }

  return (
    <div className={styles.catalog}>
      <h1 className={styles.title}>PokemonView Catalog</h1>
      <div className={styles.controls}>
        <SearchBar value={query} onChange={setQuery} />
        <FilterBar
          productType={productType}
          onProductType={setProductType}
          era={era}
          onEra={chooseEra}
          eras={eras}
          setGroups={setGroups}
          setName={setName}
          onSetName={setSetName}
          shown={visible.length}
          total={products.length}
          hasFilters={hasFilters}
          onClear={clearFilters}
        />
      </div>
      {visible.length === 0 ? (
        <div className={styles.empty}>
          <h2>No products found</h2>
          <p>Try a different search term, or clear your filters to see the full catalog.</p>
        </div>
      ) : (
        <div className={styles.results}>
          <div className={styles.head}>
            <span>Product</span>
            <span>Price with shipping</span>
          </div>
          <div className={styles.list}>
            {visible.map((product) => (
              <ProductRow key={product.id} product={product} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
