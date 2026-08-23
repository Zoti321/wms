import { listDictItems } from '@/api/dictionaries'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'

export interface DictOption {
  code: string
  name: string
}

export async function fetchActiveDictOptions(dictType: string): Promise<DictOption[]> {
  const page = await listDictItems({
    dict_type: dictType,
    page: 1,
    page_size: MAX_LIST_PAGE_SIZE,
  })
  return page.items.map((item) => ({ code: item.code, name: item.name }))
}

export function buildDictLabelMap(options: DictOption[]): Map<string, string> {
  const map = new Map<string, string>()
  for (const option of options) {
    map.set(option.code, option.name)
  }
  return map
}

export function dictLabelFromMap(
  map: Map<string, string>,
  code: string,
  fallback: Record<string, string>,
): string {
  return map.get(code) ?? fallback[code] ?? code
}

export async function loadDictLabelMap(
  dictType: string,
  fallback: Record<string, string>,
): Promise<Map<string, string>> {
  try {
    const options = await fetchActiveDictOptions(dictType)
    if (options.length === 0) {
      return buildDictLabelMap(
        Object.entries(fallback).map(([code, name]) => ({ code, name })),
      )
    }
    return buildDictLabelMap(options)
  } catch {
    return buildDictLabelMap(
      Object.entries(fallback).map(([code, name]) => ({ code, name })),
    )
  }
}

export async function loadDictOptionsWithFallback(
  dictType: string,
  fallback: Record<string, string>,
): Promise<DictOption[]> {
  try {
    const options = await fetchActiveDictOptions(dictType)
    if (options.length > 0) {
      return options
    }
  } catch {
    // fallback below
  }
  return Object.entries(fallback).map(([code, name]) => ({ code, name }))
}
