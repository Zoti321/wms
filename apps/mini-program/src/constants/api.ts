/**
 * 列表查询 `page_size` 上限，与 `services/wms-api/app/shared/pagination.py` 的
 * `MAX_PAGE_SIZE` 保持一致。下拉选项等「一次拉全」场景勿超过此值，否则 API 返回 422。
 */
export const MAX_LIST_PAGE_SIZE = 100
