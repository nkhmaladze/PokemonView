import { describe, expect, it } from 'vitest'
import { formatRelativeTime } from './relativeTime'

describe('formatRelativeTime', () => {
  it('returns an hour-based relative string for a timestamp ~2 hours ago', () => {
    const iso = new Date(Date.now() - 2 * 3600 * 1000).toISOString()
    expect(formatRelativeTime(iso)).toContain('hour')
  })

  it('returns a day-based relative string for a timestamp ~3 days ago', () => {
    const iso = new Date(Date.now() - 3 * 86400 * 1000).toISOString()
    expect(formatRelativeTime(iso)).toContain('day')
  })

  it('returns a seconds-based relative string for a timestamp within the last minute', () => {
    const iso = new Date(Date.now() - 30 * 1000).toISOString()
    expect(formatRelativeTime(iso)).toContain('second')
  })
})
