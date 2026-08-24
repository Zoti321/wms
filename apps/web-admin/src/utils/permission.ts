export function hasPermission(
  permissions: readonly string[],
  required: string,
): boolean {
  return permissions.includes(required)
}

export function hasAnyPermission(
  permissions: readonly string[],
  required: readonly string[],
): boolean {
  return required.some((perm) => permissions.includes(perm))
}

export function hasAllPermissions(
  permissions: readonly string[],
  required: readonly string[],
): boolean {
  return required.every((perm) => permissions.includes(perm))
}
