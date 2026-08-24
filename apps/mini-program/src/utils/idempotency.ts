export function createIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

/**
 * 执行页表单幂等键：字段变更时换新 key，重复确认复用同一 key。
 */
export function nextIdempotencyKey(
  previousKey: string | null,
  fingerprint: string,
  previousFingerprint: string | null,
): { key: string; fingerprint: string } {
  if (previousKey != null && previousFingerprint === fingerprint) {
    return { key: previousKey, fingerprint }
  }
  return { key: createIdempotencyKey(), fingerprint }
}
