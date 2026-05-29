import type { Active, Over } from "@dnd-kit/core";
import type { DragItem, DropTarget } from "./types";

export type BookmarkInsertPosition = {
  targetBookmarkId: number;
  position: "before" | "after";
  folderId: number | null;
  sortIndex: number;
};

type DragRects = {
  active: Active;
  over: Over | null;
};

export function getBookmarkInsertPosition(
  event: DragRects,
): BookmarkInsertPosition | null {
  const active = event.active.data.current as DragItem | undefined;
  if (!active || active.type !== "bookmark") {
    return null;
  }

  const over = event.over;
  if (!over) {
    return null;
  }

  const overData = over.data.current as DropTarget | undefined;
  if (!overData || overData.kind !== "bookmark") {
    return null;
  }

  if (active.id === overData.bookmarkId) {
    return null;
  }

  let sortIndex = overData.sortIndex;
  let position: "before" | "after" = "before";
  const overRect = over.rect;
  const translated = event.active.rect.current.translated;
  if (overRect && translated) {
    const pointerY = translated.top + translated.height / 2;
    const mid = overRect.top + overRect.height / 2;
    if (pointerY > mid) {
      position = "after";
      sortIndex += 1;
    }
  }

  return {
    targetBookmarkId: overData.bookmarkId,
    position,
    folderId: overData.folderId,
    sortIndex,
  };
}
