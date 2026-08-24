import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/dictionaries', () => ({
  listDictItems: vi.fn(),
}))

import { listDictItems } from '@/api/dictionaries'
import {
  buildDictLabelMap,
  dictLabelFromMap,
  fetchActiveDictOptions,
  loadDictLabelMap,
  loadDictOptionsWithFallback,
} from '@/utils/dictOptions'

describe('dictOptions', () => {
  beforeEach(() => {
    vi.mocked(listDictItems).mockReset()
  })

  it('fetchActiveDictOptions requests dict_type with max page size', async () => {
    vi.mocked(listDictItems).mockResolvedValue({
      items: [{ id: 1, dict_type: 'inbound_order_type', code: 'purchase', name: '采购入库', sort_order: 1, status: 1 }],
      total: 1,
      page: 1,
      page_size: 100,
    })

    const options = await fetchActiveDictOptions('inbound_order_type')

    expect(listDictItems).toHaveBeenCalledWith({
      dict_type: 'inbound_order_type',
      page: 1,
      page_size: 100,
    })
    expect(options).toEqual([{ code: 'purchase', name: '采购入库' }])
  })

  it('loadDictLabelMap falls back when request fails', async () => {
    vi.mocked(listDictItems).mockRejectedValue(new Error('offline'))

    const map = await loadDictLabelMap('inbound_order_type', {
      purchase: '采购入库',
    })

    expect(dictLabelFromMap(map, 'purchase', {})).toBe('采购入库')
  })

  it('loadDictOptionsWithFallback uses constants when list is empty', async () => {
    vi.mocked(listDictItems).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
    })

    const options = await loadDictOptionsWithFallback('outbound_order_type', {
      sales: '销售出库',
    })

    expect(options).toEqual([{ code: 'sales', name: '销售出库' }])
  })

  it('buildDictLabelMap maps code to name', () => {
    const map = buildDictLabelMap([
      { code: 'a', name: '甲' },
      { code: 'b', name: '乙' },
    ])
    expect(map.get('b')).toBe('乙')
  })
})
