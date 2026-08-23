const CANCEL_REASON_PREFIX = /^\[取消原因: ([^\]]+)\]/

export function parseCancelReasonFromRemark(remark: string | null | undefined): {
  cancelReason: string | null
  userRemark: string | null
} {
  if (!remark) {
    return { cancelReason: null, userRemark: null }
  }

  const match = remark.match(CANCEL_REASON_PREFIX)
  if (!match) {
    return { cancelReason: null, userRemark: remark }
  }

  const cancelReason = match[1]
  const rest = remark.slice(match[0].length).trimStart()
  return { cancelReason, userRemark: rest.length > 0 ? rest : null }
}
