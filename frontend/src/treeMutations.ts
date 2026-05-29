import type { TreeNode } from "./types";

export function findBookmarkNode(
  tree: TreeNode[],
  bookmarkId: number,
): TreeNode | null {
  for (const node of tree) {
    if (node.node_type === "bookmark" && node.id === bookmarkId) {
      return node;
    }
    if (node.node_type === "folder") {
      const found = findBookmarkNode(node.children, bookmarkId);
      if (found) {
        return found;
      }
    }
  }
  return null;
}
function reorderBookmarksInChildren(
  children: TreeNode[],
  bookmarkId: number,
  toIndex: number,
): TreeNode[] {
  const folders = children.filter((node) => node.node_type === "folder");
  const bookmarks = children.filter((node) => node.node_type === "bookmark");
  const fromIndex = bookmarks.findIndex((node) => node.id === bookmarkId);
  if (fromIndex < 0) {
    return children;
  }
  const nextBookmarks = [...bookmarks];
  const [moved] = nextBookmarks.splice(fromIndex, 1);
  const insertAt = Math.max(0, Math.min(toIndex, nextBookmarks.length));
  nextBookmarks.splice(insertAt, 0, moved);
  const reindexed = nextBookmarks.map((node, index) => ({
    ...node,
    sort_index: index,
  }));
  return [...folders, ...reindexed];
}
export function reorderBookmarkInTree(
  tree: TreeNode[],
  bookmarkId: number,
  folderId: number | null,
  toIndex: number,
): TreeNode[] {
  if (folderId === null) {
    return reorderBookmarksInChildren(tree, bookmarkId, toIndex);
  }
  return tree.map((node) => {
    if (node.node_type !== "folder") {
      return node;
    }
    if (node.id === folderId) {
      return {
        ...node,
        children: reorderBookmarksInChildren(
          node.children,
          bookmarkId,
          toIndex,
        ),
      };
    }
    return {
      ...node,
      children: reorderBookmarkInTree(
        node.children,
        bookmarkId,
        folderId,
        toIndex,
      ),
    };
  });
}
