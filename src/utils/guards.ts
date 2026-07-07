export function isNonNullable<T>(value: T): value is NonNullable<T> {
  return value !== null && value !== undefined
}

export function assertNonNullable<T>(
  value: T,
  message = 'Value is null or undefined',
): asserts value is NonNullable<T> {
  if (value === null || value === undefined) {
    throw new Error(message)
  }
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}
