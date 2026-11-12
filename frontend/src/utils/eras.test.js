import { describe, expect, it } from 'vitest'
import { ERAS, eraForDate } from './eras'

describe('eraForDate', () => {
  it.each([
    // newest sets: TCGplayer codes ME03..ME06 and "ME: 30th Celebration"
    ['2026-11-06', 'Mega Evolution'], // Delta Reign
    ['2026-09-16', 'Mega Evolution'], // 30th Celebration
    ['2025-09-26', 'Mega Evolution'], // Mega Evolution
    ['2025-07-18', 'Scarlet & Violet'], // Black Bolt / White Flare
    ['2023-03-31', 'Scarlet & Violet'], // Scarlet & Violet base
    ['2023-01-20', 'Sword & Shield'], // Crown Zenith
    ['2020-02-07', 'Sword & Shield'],
    ['2019-11-01', 'Sun & Moon'], // Cosmic Eclipse
    ['2017-02-03', 'Sun & Moon'],
    ['2016-11-02', 'XY'], // Evolutions
    ['2014-02-05', 'XY'],
    ['2013-11-06', 'Black & White'], // Legendary Treasures
    ['2011-04-25', 'Black & White'],
    ['2011-02-09', 'HeartGold SoulSilver'], // Call of Legends
    ['2010-02-10', 'HeartGold SoulSilver'],
    ['2009-11-04', 'Diamond & Pearl / Platinum'], // Arceus
    ['2007-05-23', 'Diamond & Pearl / Platinum'],
    ['2007-02-01', 'EX'], // EX Power Keepers
    ['2003-06-18', 'EX'],
    ['2003-05-12', 'e-Card'], // Skyridge
    ['2002-09-15', 'e-Card'], // Expedition
    ['2002-05-24', 'Classic'], // Legendary Collection
    ['1999-01-09', 'Classic'], // Base Set
  ])('%s is in %s', (date, label) => {
    expect(eraForDate(date)).toBe(label)
  })

  it('reads the date part of a full ISO timestamp', () => {
    expect(eraForDate('2026-11-06T00:00:00+00:00')).toBe('Mega Evolution')
  })

  it('returns null when the date is missing or not a date', () => {
    expect(eraForDate(null)).toBeNull()
    expect(eraForDate(undefined)).toBeNull()
    expect(eraForDate('')).toBeNull()
    expect(eraForDate('soon')).toBeNull()
  })

  it('puts dates before the first era in the oldest era', () => {
    expect(eraForDate('1998-12-31')).toBe('Classic')
  })
})

describe('ERAS', () => {
  it('lists eras newest first, each starting earlier than the one before', () => {
    const starts = ERAS.map((era) => era.from)
    expect(starts).toEqual([...starts].sort().reverse())
    expect(new Set(starts).size).toBe(starts.length)
  })
})
