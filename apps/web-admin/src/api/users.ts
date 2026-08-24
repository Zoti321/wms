import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  AssignRoleRequest,
  CreateUserRequest,
  Paginated,
  PlatformUser,
  ResetPasswordRequest,
} from '@/types/api'

export interface UserListQuery {
  page?: number
  page_size?: number
}

export async function listUsers(query: UserListQuery = {}): Promise<Paginated<PlatformUser>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<PlatformUser>>>('/users', { params: query }),
  )
}

export async function createUser(payload: CreateUserRequest): Promise<PlatformUser> {
  return requestData(apiClient.post<ApiEnvelope<PlatformUser>>('/users', payload))
}

export async function deactivateUser(userId: number): Promise<PlatformUser> {
  return requestData(
    apiClient.post<ApiEnvelope<PlatformUser>>(`/users/${userId}/deactivate`),
  )
}

export async function resetUserPassword(
  userId: number,
  payload: ResetPasswordRequest,
): Promise<PlatformUser> {
  return requestData(
    apiClient.post<ApiEnvelope<PlatformUser>>(`/users/${userId}/reset-password`, payload),
  )
}

export async function assignUserRole(
  userId: number,
  payload: AssignRoleRequest,
): Promise<PlatformUser> {
  return requestData(
    apiClient.patch<ApiEnvelope<PlatformUser>>(`/users/${userId}/role`, payload),
  )
}
