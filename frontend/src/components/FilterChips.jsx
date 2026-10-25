import styles from './FilterChips.module.css'

/**
 * FilterChips — single-select-per-group toggle chips for `product_type`
 * (SEARCH-01, D-13) plus a Set dropdown for `set_name`.
 *
 * The raw product_type values below MUST match
 * `api/services/catalog_service.py` exactly:
 * `VALID_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb",
 * "booster_bundle"}`. No invented values — this component never sends
 * anything the API doesn't accept.
 *
 * Sets are no longer a fixed chip row: the catalog spans well over a
 * hundred sets, so CatalogPage passes the sets it actually loaded (in
 * the API's newest-first order) as `sets`, rendered as a native
 * `<select>`; "All sets" clears the filter.
 *
 * `booster_bundle` gets its own chip, kept visually distinct from
 * `booster_box` (Phase 2 D-06 — meaningfully different price point,
 * must not be conflated).
 */
export const PRODUCT_TYPE_OPTIONS = [
  { value: 'booster_pack', label: 'Booster Pack' },
  { value: 'booster_box', label: 'Booster Box' },
  { value: 'booster_bundle', label: 'Booster Bundle' },
  { value: 'etb', label: 'ETB' },
]

function ChipRow({ options, activeValue, onSelect }) {
  return (
    <div className={styles.chips}>
      {options.map(({ value, label }) => {
        const isActive = value === activeValue
        const className = isActive
          ? `${styles.chip} ${styles['chip--active']}`
          : styles.chip
        return (
          <button
            key={value}
            type="button"
            className={className}
            onClick={() => onSelect(isActive ? null : value)}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

export default function FilterChips({
  productType,
  onProductType,
  sets = [],
  setName,
  onSetName,
}) {
  return (
    <div>
      <ChipRow options={PRODUCT_TYPE_OPTIONS} activeValue={productType} onSelect={onProductType} />
      <select
        aria-label="Set"
        className={styles.select}
        value={setName ?? ''}
        onChange={(event) => onSetName(event.target.value || null)}
      >
        <option value="">All sets</option>
        {sets.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>
    </div>
  )
}
