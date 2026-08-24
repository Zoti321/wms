/** 作业端仅允许仓管员（operator）进入待办流。 */
export function canAccessOperatorApp(roleCode: string | null | undefined): boolean {
  return roleCode === 'operator'
}
