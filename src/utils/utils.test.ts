import { describe, it, expect } from 'vitest'
import { clamp, assertNonNullable } from '@/utils/guards'
import { formatTime, formatRelativeTime, truncate } from '@/utils/format'
import { debounce } from '@/utils/debounce'

describe('guards', () => {
  it('clamp should constrain value within range', () => {
    expect(clamp(5, 0, 10)).toBe(5)
    expect(clamp(-5, 0, 10)).toBe(0)
    expect(clamp(15, 0, 10)).toBe(10)
    expect(clamp(0, 0, 0)).toBe(0)
  })

  it('assertNonNullable should throw for null/undefined', () => {
    expect(() => assertNonNullable(null)).toThrow()
    expect(() => assertNonNullable(undefined)).toThrow()
    expect(() => assertNonNullable('hello')).not.toThrow()
    expect(() => assertNonNullable(0)).not.toThrow()
  })
})

describe('format', () => {
  it('formatTime should return HH:MM', () => {
    const result = formatTime(new Date('2026-04-05T14:23:00'))
    expect(result).toMatch(/^\d{2}:\d{2}$/)
  })

  it('formatRelativeTime should return Chinese relative time', () => {
    const now = new Date()
    const justNow = new Date(now.getTime() - 30_000).toISOString()
    expect(formatRelativeTime(justNow)).toBe('刚刚')

    const minsAgo = new Date(now.getTime() - 5 * 60_000).toISOString()
    expect(formatRelativeTime(minsAgo)).toContain('分钟前')
  })

  it('truncate should cut long text', () => {
    expect(truncate('hello world', 5)).toBe('hello…')
    expect(truncate('hi', 10)).toBe('hi')
    expect(truncate('abc', 3)).toBe('abc')
  })
})

describe('debounce', () => {
  it('should debounce function calls', async () => {
    let count = 0
    const fn = debounce(() => { count++ }, 50)

    fn()
    fn()
    fn()

    expect(count).toBe(0)

    await new Promise((r) => setTimeout(r, 70))
    expect(count).toBe(1)
  })
})
