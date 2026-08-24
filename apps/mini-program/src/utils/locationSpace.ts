export type SpaceStatus = 'idle' | 'occupied' | 'frozen'

const SPACE_STATUS_LABEL: Record<SpaceStatus, string> = {
  idle: '空闲',
  occupied: '占用',
  frozen: '冻结',
}

export function spaceStatusLabel(status: string | undefined | null): string {
  if (status == null || status === '') {
    return '—'
  }
  if (status in SPACE_STATUS_LABEL) {
    return SPACE_STATUS_LABEL[status as SpaceStatus]
  }
  return status
}

/** 库位状态·冻结不可选；缺省视为可选（由提交时盘点锁等兜底）。 */
export function isLocationSelectable(status: string | undefined | null): boolean {
  return status !== 'frozen'
}
