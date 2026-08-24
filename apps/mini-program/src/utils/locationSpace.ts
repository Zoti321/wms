import { SPACE_STATUS_LABEL } from '@/constants/labels'
import type { SpaceStatus } from '@/types/api'

export function spaceStatusLabel(status: string | undefined | null): string {
  if (status == null || status === '') {
    return '—'
  }
  return SPACE_STATUS_LABEL[status] ?? status
}

/** 库位状态·冻结不可选；缺省视为可选（由提交时盘点锁等兜底）。 */
export function isLocationSelectable(status: string | undefined | null): boolean {
  return status !== 'frozen'
}

export type { SpaceStatus }
