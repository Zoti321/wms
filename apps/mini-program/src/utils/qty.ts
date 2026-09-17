/** 剩余可作业数量（字符串，三位小数）；非正数返回 '0.000'。 */
export function remainQty(plannedOrAllocated: string, done: string): string {
  const planned = Number(plannedOrAllocated)
  const finished = Number(done)
  if (!Number.isFinite(planned) || !Number.isFinite(finished)) {
    return '0.000'
  }
  const remain = planned - finished
  if (remain <= 0) {
    return '0.000'
  }
  return remain.toFixed(3)
}

export function isPositiveQty(qty: string): boolean {
  const n = Number(qty)
  return Number.isFinite(n) && n > 0
}
