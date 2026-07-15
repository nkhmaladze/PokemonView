/**
 * formatRelativeTime — converts an ISO-8601 timestamp into a human "X ago"
 * string via the native Intl.RelativeTimeFormat API (PRICE-02, D-09).
 *
 * No date library dependency (no date-fns/dayjs/moment) — the native
 * browser API is sufficient for a single "time ago" string. Consumes
 * ISO strings directly (e.g. current_price.as_of from the API), no
 * reparsing beyond the native Date constructor.
 */

const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

const UNITS = [
  ['year', 31536000],
  ['month', 2592000],
  ['week', 604800],
  ['day', 86400],
  ['hour', 3600],
  ['minute', 60],
  ['second', 1],
]

export function formatRelativeTime(isoString) {
  const diffSeconds = (new Date(isoString).getTime() - Date.now()) / 1000

  if (!Number.isFinite(diffSeconds)) return 'an unknown time'

  for (const [unit, secondsInUnit] of UNITS) {
    if (Math.abs(diffSeconds) >= secondsInUnit || unit === 'second') {
      return rtf.format(Math.round(diffSeconds / secondsInUnit), unit)
    }
  }
}
