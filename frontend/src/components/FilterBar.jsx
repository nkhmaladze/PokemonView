import styles from './FilterBar.module.css'

/**
 * FilterBar — the Type, Era and Set dropdowns, plus a live "Showing X of Y"
 * line with a "Clear filters" button.
 *
 * The raw product_type values below MUST match
 * `api/services/catalog_service.py` exactly:
 * `VALID_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb",
 * "booster_bundle"}`. No invented values — this component never sends
 * anything the API doesn't accept.
 *
 * Purely presentational: CatalogPage owns the filter state and decides which
 * eras exist and which sets are on offer. `setGroups` is that list of sets,
 * `[{ era, sets: [name, ...] }]`. With no era chosen the Set dropdown shows
 * the groups under era headings (130+ sets are hard to scan flat); once an
 * era is chosen CatalogPage passes only that era's group and the headings
 * are dropped.
 *
 * `booster_bundle` stays its own type, distinct from `booster_box`
 * (meaningfully different price point, must not be conflated).
 */
export const PRODUCT_TYPE_OPTIONS = [
  { value: 'booster_pack', label: 'Booster Pack' },
  { value: 'booster_box', label: 'Booster Box' },
  { value: 'booster_bundle', label: 'Booster Bundle' },
  { value: 'etb', label: 'ETB' },
]

function Dropdown({ label, value, onChange, children }) {
  const className = value ? `${styles.select} ${styles['select--active']}` : styles.select
  return (
    <select
      aria-label={label}
      className={className}
      value={value ?? ''}
      onChange={(event) => onChange(event.target.value || null)}
    >
      {children}
    </select>
  )
}

export default function FilterBar({
  productType,
  onProductType,
  era,
  onEra,
  eras = [],
  setGroups = [],
  setName,
  onSetName,
  shown,
  total,
  hasFilters,
  onClear,
}) {
  const grouped = !era

  return (
    <div className={styles.bar}>
      <div className={styles.selects}>
        <Dropdown label="Type" value={productType} onChange={onProductType}>
          <option value="">All types</option>
          {PRODUCT_TYPE_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Dropdown>

        <Dropdown label="Era" value={era} onChange={onEra}>
          <option value="">All eras</option>
          {eras.map((label) => (
            <option key={label} value={label}>
              {label}
            </option>
          ))}
        </Dropdown>

        <Dropdown label="Set" value={setName} onChange={onSetName}>
          <option value="">All sets</option>
          {setGroups.map((group) =>
            grouped ? (
              <optgroup key={group.era} label={group.era}>
                {group.sets.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </optgroup>
            ) : (
              group.sets.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))
            )
          )}
        </Dropdown>
      </div>

      <div className={styles.summary}>
        <p className={styles.count} role="status">
          {`Showing ${shown} of ${total} ${total === 1 ? 'product' : 'products'}`}
        </p>
        {hasFilters && (
          <button type="button" className={styles.clear} onClick={onClear}>
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}
