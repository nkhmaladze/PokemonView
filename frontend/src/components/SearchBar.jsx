import styles from './SearchBar.module.css'

/**
 * SearchBar — controlled, instant, no-debounce free-text search input
 * (SEARCH-01, D-12/D-14).
 *
 * Purely controlled: owns no internal state, fires `onChange` with the
 * raw typed string on every keystroke, no submit button. `CatalogPage`
 * (06-05) owns the actual filter state and applies it in-memory against
 * the already-loaded catalog — this component never fetches and never
 * debounces.
 */
export default function SearchBar({ value, onChange }) {
  return (
    <input
      type="text"
      className={styles.search}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder="Search by product name or set…"
      aria-label="Search products"
    />
  )
}
