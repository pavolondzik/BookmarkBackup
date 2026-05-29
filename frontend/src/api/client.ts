import type {
  BookmarkDetail,
  DeviceInfo,
  ExportInfo,
  ImportResult,
  TreeNode,
  UserInfo,
} from "../types";

const API = "/api";
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
export function postImport(form: FormData): Promise<ImportResult> {
  return request(`${API}/import`, {
    method: "POST",
    body: form,
  });
}
export function fetchExports(): Promise<ExportInfo[]> {
  return request(`${API}/exports`);
}
export function fetchUsers(): Promise<UserInfo[]> {
  return request(`${API}/users`);
}
export function fetchDevices(userId: number): Promise<DeviceInfo[]> {
  return request(`${API}/devices?user_id=${userId}`);
}
export function fetchExportsForDevice(deviceId: number): Promise<ExportInfo[]> {
  return request(`${API}/exports?device_id=${deviceId}`);
}
export function fetchTree(exportId?: number): Promise<TreeNode[]> {
  const query = exportId ? `?export_id=${exportId}` : "";
  return request(`${API}/tree${query}`);
}
export function updateFolder(
  folderId: number,
  body: { name?: string; parent_id?: number | null },
): Promise<void> {
  return request(`${API}/folders/${folderId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
export function deleteFolder(folderId: number): Promise<void> {
  return request(`${API}/folders/${folderId}`, { method: "DELETE" });
}
export function fetchBookmark(bookmarkId: number): Promise<BookmarkDetail> {
  return request(`${API}/bookmarks/${bookmarkId}`);
}
export function updateBookmark(
  bookmarkId: number,
  body: { title?: string; folder_id?: number | null; sort_index?: number },
): Promise<void> {
  return request(`${API}/bookmarks/${bookmarkId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
export function deleteBookmark(bookmarkId: number): Promise<void> {
  return request(`${API}/bookmarks/${bookmarkId}`, { method: "DELETE" });
}
