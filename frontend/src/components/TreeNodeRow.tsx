import type { KeyboardEvent, MouseEvent, ReactNode } from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { DragItem, DropTarget, TreeNode } from "../types";
import { FolderChevron } from "./FolderChevron";

type Props = {
  node: TreeNode;
  depth: number;
  expanded: boolean;
  selectedId: string | null;
  dropIndicator?: "before" | "after" | null;
  onToggle: (node: TreeNode) => void;
  onSelect: (node: TreeNode) => void;
  onRename: (node: TreeNode) => void;
  onDelete: (node: TreeNode) => void;
  renderChildren: (node: TreeNode, depth: number) => ReactNode;
};

export function dragId(node: TreeNode): string {
  return `${node.node_type}:${node.id}`;
}

export function TreeNodeRow({
  node,
  depth,
  expanded,
  selectedId,
  dropIndicator = null,
  onToggle,
  onSelect,
  onRename,
  onDelete,
  renderChildren,
}: Props) {
  const id = dragId(node);
  const isFolder = node.node_type === "folder";
  const selected = selectedId === id;
  const dragData: DragItem =
    node.node_type === "bookmark"
      ? { type: "bookmark", id: node.id, folderId: node.folder_id ?? null }
      : { type: "folder", id: node.id };
  const {
    attributes,
    listeners,
    setNodeRef: dragRef,
    transform,
    isDragging,
  } = useDraggable({
    id,
    data: dragData,
  });
  const { setNodeRef: folderDropRef, isOver: folderOver } = useDroppable({
    id: `drop-folder-${node.id}`,
    disabled: !isFolder,
    data: { kind: "folder", folderId: node.id } satisfies DropTarget,
  });
  const { setNodeRef: bookmarkDropRef } = useDroppable({
    id: `drop-bookmark-${node.id}`,
    disabled: isFolder,
    data: {
      kind: "bookmark",
      bookmarkId: node.id,
      folderId: node.folder_id ?? null,
      sortIndex: node.sort_index ?? 0,
    } satisfies DropTarget,
  });
  const indentPx = depth * 14 + 8;
  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    paddingLeft: `${indentPx}px`,
  };
  const rowClass = [
    "group flex cursor-grab select-none items-center gap-1.5 py-1 pr-1",
    folderOver && "rounded-md outline outline-1 outline-accent",
    !isFolder && "text-foreground/85",
  ]
    .filter(Boolean)
    .join(" ");
  const labelClass = ["tree-row-label", selected && "is-selected"]
    .filter(Boolean)
    .join(" ");
  const insertLineClass =
    "pointer-events-none relative z-20 my-0.5 mr-3 h-1 rounded-sm bg-accent shadow-[0_0_8px_var(--app-insert-glow)]";

  const toggleFolder = (event: MouseEvent | KeyboardEvent) => {
    event.stopPropagation();
    onToggle(node);
  };

  const rowContent = (
    <div ref={dragRef} style={style} className={rowClass}>
      {isFolder ? (
        <span
          role="button"
          tabIndex={0}
          className="tree-folder-toggle"
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse folder" : "Expand folder"}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={toggleFolder}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              toggleFolder(event);
            }
          }}
        >
          <FolderChevron expanded={expanded} />
        </span>
      ) : (
        <span className="inline-block w-5 shrink-0 text-center text-muted">
          •
        </span>
      )}
      <div
        className={labelClass}
        {...listeners}
        {...attributes}
        onClick={() => onSelect(node)}
      >
        <span
          className="min-w-0 flex-1 truncate text-sm"
          title={node.href ?? node.name}
        >
          {node.name}
        </span>
        <span className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            type="button"
            className="cursor-pointer border-0 bg-transparent px-0.5 text-muted hover:text-foreground focus:outline-none"
            onClick={(event) => {
              event.stopPropagation();
              onRename(node);
            }}
          >
            ✎
          </button>
          <button
            type="button"
            className="cursor-pointer border-0 bg-transparent px-0.5 text-muted hover:text-foreground focus:outline-none"
            onClick={(event) => {
              event.stopPropagation();
              onDelete(node);
            }}
          >
            ✕
          </button>
        </span>
      </div>
    </div>
  );
  if (isFolder) {
    return (
      <div>
        <div ref={folderDropRef}>{rowContent}</div>
        {expanded && node.children.length > 0 && (
          <div className="children-enter">
            {renderChildren(node, depth + 1)}
          </div>
        )}
      </div>
    );
  }
  return (
    <div ref={bookmarkDropRef}>
      {dropIndicator === "before" && (
        <div
          className={insertLineClass}
          style={{ marginLeft: `${indentPx}px` }}
          aria-hidden="true"
        />
      )}
      {rowContent}
      {dropIndicator === "after" && (
        <div
          className={insertLineClass}
          style={{ marginLeft: `${indentPx}px` }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
