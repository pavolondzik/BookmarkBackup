import {
  DndContext,
  DragCancelEvent,
  DragEndEvent,
  DragOverEvent,
  PointerSensor,
  pointerWithin,
  useDroppable,
  useSensor,
  useSensors,
  type CollisionDetection,
} from "@dnd-kit/core";
import { useCallback, useState } from "react";
import { getBookmarkInsertPosition } from "../dndInsert";
import type { BookmarkInsertPosition } from "../dndInsert";
import {
  deleteBookmark,
  deleteFolder,
  updateBookmark,
  updateFolder,
} from "../api/client";
import { reorderBookmarkInTree } from "../treeMutations";
import type { DragItem, DropTarget, TreeNode } from "../types";
import { btnSecondaryClass } from "../ui/styles";
import { TreeNodeRow, dragId } from "./TreeNodeRow";

type Props = {
  nodes: TreeNode[];
  onTreeChange: (nodes: TreeNode[]) => void;
  onRefresh: () => void | Promise<void>;
  onSelect: (node: TreeNode) => void;
};

function folderIdsEqual(
  a: number | null | undefined,
  b: number | null | undefined,
): boolean {
  return (a ?? null) === (b ?? null);
}

/** Prefer bookmark drop targets so reorder works inside expanded folders. */
const collisionDetection: CollisionDetection = (args) => {
  const hits = pointerWithin(args);
  if (hits.length === 0) {
    return hits;
  }
  const bookmarkHit = hits.find((hit) =>
    String(hit.id).startsWith("drop-bookmark-"),
  );
  return bookmarkHit ? [bookmarkHit] : hits;
};

export function BookmarkTree({
  nodes,
  onTreeChange,
  onRefresh,
  onSelect,
}: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [insertIndicator, setInsertIndicator] =
    useState<BookmarkInsertPosition | null>(null);
  const [draggingBookmark, setDraggingBookmark] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );
  const { setNodeRef: rootDropRef, isOver: rootIsOver } = useDroppable({
    id: "drop-root",
    data: { kind: "folder", folderId: null } satisfies DropTarget,
  });
  const toggleExpanded = useCallback((node: TreeNode) => {
    const key = dragId(node);
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);
  const expandAll = useCallback(() => {
    setBulkBusy(true);
    requestAnimationFrame(() => {
      const keys = new Set<string>();
      const walk = (items: TreeNode[]) => {
        for (const node of items) {
          if (node.node_type === "folder") {
            keys.add(dragId(node));
            walk(node.children);
          }
        }
      };
      walk(nodes);
      setExpanded(keys);
      requestAnimationFrame(() => setBulkBusy(false));
    });
  }, [nodes]);
  const collapseAll = useCallback(() => {
    setExpanded(new Set());
  }, []);
  const handleRename = async (node: TreeNode) => {
    const nextName = window.prompt(
      node.node_type === "folder" ? "Rename folder" : "Rename bookmark",
      node.name,
    );
    if (!nextName?.trim()) {
      return;
    }
    try {
      if (node.node_type === "folder") {
        await updateFolder(node.id, { name: nextName.trim() });
      } else {
        await updateBookmark(node.id, { title: nextName.trim() });
      }
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    }
  };
  const handleDelete = async (node: TreeNode) => {
    const ok = window.confirm(`Delete ${node.node_type} "${node.name}"?`);
    if (!ok) {
      return;
    }
    try {
      if (node.node_type === "folder") {
        await deleteFolder(node.id);
      } else {
        await deleteBookmark(node.id);
      }
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };
  const handleDragStart = useCallback(
    (event: { active: { data: { current: unknown } } }) => {
      const active = event.active.data.current as DragItem | undefined;
      setDraggingBookmark(active?.type === "bookmark");
      setInsertIndicator(null);
    },
    [],
  );
  const handleDragOver = useCallback((event: DragOverEvent) => {
    setInsertIndicator(getBookmarkInsertPosition(event));
  }, []);
  const handleDragCancel = useCallback((_event: DragCancelEvent) => {
    setInsertIndicator(null);
    setDraggingBookmark(false);
  }, []);
  const handleDragEnd = async (event: DragEndEvent) => {
    setInsertIndicator(null);
    setDraggingBookmark(false);
    const active = event.active.data.current as DragItem | undefined;
    if (!active) {
      return;
    }
    const insertPos =
      active.type === "bookmark" ? getBookmarkInsertPosition(event) : null;
    const overData = event.over?.data.current as DropTarget | undefined;
    try {
      if (active.type === "folder") {
        if (overData?.kind !== "folder") {
          return;
        }
        await updateFolder(active.id, { parent_id: overData.folderId });
        await onRefresh();
        return;
      }
      if (insertPos) {
        const { sortIndex, folderId: targetFolderId } = insertPos;
        const sourceFolderId = active.folderId ?? null;
        const reorderInPlace = folderIdsEqual(sourceFolderId, targetFolderId);
        if (reorderInPlace) {
          const previousTree = nodes;
          const nextTree = reorderBookmarkInTree(
            nodes,
            active.id,
            targetFolderId,
            sortIndex,
          );
          onTreeChange(nextTree);
          try {
            await updateBookmark(active.id, { sort_index: sortIndex });
          } catch (err) {
            onTreeChange(previousTree);
            throw err;
          }
          return;
        }
        await updateBookmark(active.id, {
          folder_id: targetFolderId,
          sort_index: sortIndex,
        });
        await onRefresh();
        return;
      }
      if (overData?.kind === "folder") {
        await updateBookmark(active.id, { folder_id: overData.folderId });
        await onRefresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Move failed");
    }
  };
  const renderNodes = (items: TreeNode[], depth: number): React.ReactNode =>
    items.map((node) => (
      <TreeNodeRow
        key={dragId(node)}
        node={node}
        depth={depth}
        expanded={node.node_type !== "folder" || expanded.has(dragId(node))}
        selectedId={selectedId}
        dropIndicator={
          draggingBookmark &&
          node.node_type === "bookmark" &&
          insertIndicator?.targetBookmarkId === node.id
            ? insertIndicator.position
            : null
        }
        onToggle={toggleExpanded}
        onSelect={(item) => {
          setSelectedId(dragId(item));
          onSelect(item);
        }}
        onRename={handleRename}
        onDelete={handleDelete}
        renderChildren={(folder, childDepth) =>
          renderNodes(folder.children, childDepth)
        }
      />
    ));
  return (
    <DndContext
      sensors={sensors}
      collisionDetection={collisionDetection}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragCancel={handleDragCancel}
      onDragEnd={handleDragEnd}
    >
      <div className="scrollbar-themed flex min-h-0 flex-1 flex-col overflow-auto overflow-anchor-none p-2">
        <div className="p-2">
          <h2 className="m-0 mb-1 text-sm font-semibold">
            Folders & bookmarks
          </h2>
          <p className="m-0 text-xs text-muted">
            Drag onto a folder to move; onto a bookmark to reorder. ✎ rename, ✕
            delete.
          </p>
          <div className="mt-2 flex gap-1.5">
            <button
              type="button"
              className={btnSecondaryClass}
              onClick={expandAll}
              disabled={bulkBusy}
            >
              Expand all
            </button>
            <button
              type="button"
              className={btnSecondaryClass}
              onClick={collapseAll}
              disabled={bulkBusy}
            >
              Collapse all
            </button>
          </div>
        </div>
        {error && <p className="px-2 text-xs text-danger">{error}</p>}
        <div className="relative min-h-0 flex-1">
          {bulkBusy && (
            <div
              className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-overlay"
              aria-hidden="true"
            >
              <span className="spinner" />
            </div>
          )}
          <div
            ref={rootDropRef}
            className={[
              "min-h-[200px] overflow-anchor-none rounded-lg border border-dashed border-transparent p-1",
              rootIsOver && "border-accent bg-accent/10",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {nodes.length === 0 ? (
              <p className="px-2 text-sm text-muted">
                No folders yet. Import bookmarks first.
              </p>
            ) : (
              renderNodes(nodes, 0)
            )}
          </div>
        </div>
      </div>
    </DndContext>
  );
}
