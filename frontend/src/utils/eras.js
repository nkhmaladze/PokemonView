/**
 * Card eras, newest first. The catalog has no era field, so an era is
 * worked out from a product's `release_date`: the first era whose `from`
 * date is on or before it. The newest era is open-ended, so a set released
 * after the last known one lands there until a new era is added (one line).
 *
 * `from` is the first day of the month a series opened in, not the exact
 * release date, so a set slipping a few days never changes its era.
 * Boundaries follow the series each set belongs to: Black Bolt / White Flare
 * (July 2025) are Scarlet & Violet; Mega Evolution starts in September 2025
 * and covers every set after it (TCGplayer codes ME03 to ME06 and the
 * 30th Celebration).
 */
export const ERAS = [
  { label: 'Mega Evolution', from: '2025-09-01' },
  { label: 'Scarlet & Violet', from: '2023-03-01' },
  { label: 'Sword & Shield', from: '2020-02-01' },
  { label: 'Sun & Moon', from: '2017-02-01' },
  { label: 'XY', from: '2014-02-01' },
  { label: 'Black & White', from: '2011-04-01' },
  { label: 'HeartGold SoulSilver', from: '2010-01-01' },
  { label: 'Diamond & Pearl / Platinum', from: '2007-05-01' },
  { label: 'EX', from: '2003-06-01' },
  { label: 'e-Card', from: '2002-09-01' },
  { label: 'Classic', from: '1999-01-01' },
]

const DATE_PREFIX = /^\d{4}-\d{2}-\d{2}/

/**
 * The era label for a `release_date` ("YYYY-MM-DD", or a full ISO
 * timestamp), or null when there is no usable date. Dates before the first
 * era belong to the oldest one.
 */
export function eraForDate(releaseDate) {
  if (typeof releaseDate !== 'string' || !DATE_PREFIX.test(releaseDate)) return null
  const day = releaseDate.slice(0, 10)
  const era = ERAS.find((candidate) => day >= candidate.from)
  return era ? era.label : ERAS[ERAS.length - 1].label
}
