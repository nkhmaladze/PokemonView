import styles from './FilterChips.module.css'

/**
 * FilterChips — single-select-per-group toggle chips for `product_type`
 * and `set_name` (SEARCH-01, D-13 plus the discretionary set chip row).
 *
 * The raw values below MUST match `api/services/catalog_service.py`
 * exactly: `VALID_PRODUCT_TYPES = {"booster_pack", "booster_box",
 * "etb", "booster_bundle"}` and `SET_ORDER = ["Pitch Black",
 * "Chaos Rising", "Perfect Order", "Ascended Heroes"]`. No invented
 * values — this component never sends anything the API doesn't accept.
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

export const SET_OPTIONS = [
  { value: 'Pitch Black', label: 'Pitch Black' },
  { value: 'Chaos Rising', label: 'Chaos Rising' },
  { value: 'Perfect Order', label: 'Perfect Order' },
  { value: 'Ascended Heroes', label: 'Ascended Heroes' },
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

export default function FilterChips({ productType, onProductType, setName, onSetName }) {
  return (
    <div>
      <ChipRow options={PRODUCT_TYPE_OPTIONS} activeValue={productType} onSelect={onProductType} />
      <ChipRow options={SET_OPTIONS} activeValue={setName} onSelect={onSetName} />
    </div>
  )
}
