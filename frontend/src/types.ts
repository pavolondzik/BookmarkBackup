export type NodeType = "folder" | "bookmark";
export interface TreeNode {
  id: number;
  node_type: NodeType;
  name: string;
  href?: string | null;
  parent_id?: number | null;
  folder_id?: number | null;
  sort_index?: number | null;
  children: TreeNode[];
}
export type DropTarget =
  | { kind: "folder"; folderId: number | null }
  | {
      kind: "bookmark";
      bookmarkId: number;
      folderId: number | null;
      sortIndex: number;
    };
export interface ExportInfo {
  id: number;
  browser_name: string;
  device_id: number;
  exported_at: string;
  source_format: string;
  source_path: string | null;
}
export interface UserInfo {
  id: number;
  email: string;
}
export interface DeviceInfo {
  id: number;
  name: string;
  user_id: number;
}
export interface ImportResult {
  scanned: number;
  inserted: number;
  skipped_duplicates: number;
}
export interface BookmarkDetail {
  id: number;
  title: string;
  href: string;
  icon_uri: string;
  icon: string | null;
  folder_id: number | null;
}
export type DragItem = {
  type: NodeType;
  id: number;
  folderId?: number | null;
};
