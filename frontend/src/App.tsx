import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchBookmark,
  fetchDevices,
  fetchExportsForDevice,
  fetchTree,
  fetchUsers,
  postImport,
} from "./api/client";
import { AutoResizeTextarea } from "./components/AutoResizeTextarea";
import { BookmarkDetailIcon } from "./components/BookmarkDetailIcon";
import { FolderChevron } from "./components/FolderChevron";
import { BookmarkTree } from "./components/BookmarkTree";
import { ThemeSwitcher } from "./theme/ThemeSwitcher";
import type {
  BookmarkDetail,
  DeviceInfo,
  ExportInfo,
  TreeNode,
  UserInfo,
} from "./types";
import {
  btnPrimaryClass,
  btnSecondaryClass,
  cardClass,
  fileInputClass,
  inputClass,
  selectClass,
} from "./ui/styles";

const DEFAULT_IMPORT_PATHS = [
  "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Bookmarks",
  "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Bookmarks",
  "%APPDATA%\\Opera Software\\Opera Stable\\Default\\Bookmarks",
  "%APPDATA%\\Opera Software\\Opera GX Stable\\Default\\Bookmarks",
  "# Firefox: no Chromium Bookmarks file — export HTML from Library > Bookmarks",
  "# Internet Explorer: export Favorites to a .htm file (Favorites folder is not one file)",
  "# Safari (macOS): export HTML from File > Export Bookmarks",
].join("\n");

export default function App() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [userId, setUserId] = useState<number | undefined>();
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [deviceId, setDeviceId] = useState<number | undefined>();
  const [exports, setExports] = useState<ExportInfo[]>([]);
  const [exportId, setExportId] = useState<number | undefined>();
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [selected, setSelected] = useState<TreeNode | null>(null);
  const [bookmarkDetail, setBookmarkDetail] = useState<BookmarkDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importBusy, setImportBusy] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [importExpanded, setImportExpanded] = useState(true);
  const [importPaths, setImportPaths] = useState(DEFAULT_IMPORT_PATHS);
  const [sidebarWidth, setSidebarWidth] = useState(380);
  const minSidebarWidth = 380;
  const resizingRef = useRef<{
    startX: number;
    startWidth: number;
  } | null>(null);
  const load = useCallback(
    async (opts?: {
      userId?: number;
      deviceId?: number;
      exportId?: number;
    }) => {
      setLoading(true);
      setError(null);
      try {
        const userList = await fetchUsers();
        setUsers(userList);
        const activeUserId = opts?.userId ?? userId ?? userList[0]?.id;
        setUserId(activeUserId);
        if (!activeUserId) {
          setDevices([]);
          setExports([]);
          setTree([]);
          setDeviceId(undefined);
          setExportId(undefined);
          return;
        }
        const deviceList = await fetchDevices(activeUserId);
        setDevices(deviceList);
        const activeDeviceId = opts?.deviceId ?? deviceId ?? deviceList[0]?.id;
        setDeviceId(activeDeviceId);
        if (!activeDeviceId) {
          setExports([]);
          setTree([]);
          setExportId(undefined);
          return;
        }
        const exportList = await fetchExportsForDevice(activeDeviceId);
        setExports(exportList);
        const activeExportId = opts?.exportId ?? exportId ?? exportList[0]?.id;
        setExportId(activeExportId);
        setSelected(null);
        setBookmarkDetail(null);
        if (activeExportId) {
          setTree(await fetchTree(activeExportId));
        } else {
          setTree([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    },
    [deviceId, exportId, userId],
  );
  const refreshTree = useCallback(async () => {
    if (!exportId) {
      return;
    }
    try {
      setTree(await fetchTree(exportId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh tree");
    }
  }, [exportId]);
  useEffect(() => {
    void load();
  }, [load]);
  const handleSelect = useCallback((node: TreeNode) => {
    setSelected(node);
    if (node.node_type !== "bookmark") {
      setBookmarkDetail(null);
      return;
    }
    void fetchBookmark(node.id)
      .then(setBookmarkDetail)
      .catch(() => setBookmarkDetail(null));
  }, []);
  const folderPathFor = (node: TreeNode): string => {
    const folders = new Map<number, TreeNode>();
    const walk = (items: TreeNode[]) => {
      for (const item of items) {
        if (item.node_type === "folder") {
          folders.set(item.id, item);
          walk(item.children);
        }
      }
    };
    walk(tree);
    const startFolderId =
      node.node_type === "bookmark" ? (node.folder_id ?? null) : node.id;
    if (!startFolderId) {
      return "";
    }
    const parts: string[] = [];
    let currentId: number | null | undefined = startFolderId;
    while (currentId != null) {
      const folder = folders.get(currentId);
      if (!folder) break;
      parts.push(folder.name);
      currentId = folder.parent_id ?? null;
    }
    return parts.reverse().join(" / ");
  };
  const onImport = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setImportBusy(true);
    setImportMessage(null);
    setError(null);
    try {
      const form = new FormData(event.currentTarget);
      const result = await postImport(form);
      setImportMessage("Import completed. Refreshing…");
      await load();
      setImportMessage(
        `Imported ${result.inserted}/${result.scanned}, skipped ${result.skipped_duplicates} duplicate(s).`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImportBusy(false);
    }
  };
  const labelClass = "flex flex-col gap-1 text-xs text-muted";
  return (
    <div className="flex h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-border bg-surface/90 backdrop-blur-md">
        <div className="flex items-end justify-between gap-4 px-4 py-3">
          <div className="flex items-end gap-2">
            <a
              href="https://github.com/pavolondzik/BookmarkBackup"
              className="mb-0.5 inline-flex shrink-0 text-muted transition-colors hover:text-foreground"
              aria-label="GitHub"
            >
              <svg
                className="size-9"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
            <div>
              <h1 className="m-0 text-base font-semibold">Bookmark Backup</h1>
              <span className="mt-0.5 block text-xs text-muted">
                {users.find((u) => u.id === userId)?.email ?? "—"}
              </span>
            </div>
          </div>
          <div className="flex items-end gap-3">
            <div className="flex items-end gap-3">
              <label className={labelClass}>
                User
                <select
                  className={selectClass}
                  value={userId ?? ""}
                  onChange={(event) => {
                    const nextUserId = Number(event.target.value);
                    void load({
                      userId: nextUserId,
                      deviceId: undefined,
                      exportId: undefined,
                    });
                  }}
                >
                  {users.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.email}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                Device
                <select
                  className={selectClass}
                  value={deviceId ?? ""}
                  onChange={(event) => {
                    const nextDeviceId = Number(event.target.value);
                    void load({ deviceId: nextDeviceId, exportId: undefined });
                  }}
                >
                  {devices.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                Export
                <select
                  className={selectClass}
                  value={exportId ?? ""}
                  onChange={(event) => {
                    const id = Number(event.target.value);
                    void load({ exportId: id });
                  }}
                >
                  {exports.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.browser_name} —{" "}
                      {new Date(item.exported_at).toLocaleString()}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className={btnPrimaryClass}
                onClick={() => void load()}
              >
                Refresh
              </button>
            </div>
            <ThemeSwitcher />
          </div>
        </div>
      </header>
      <div className="flex min-h-0 flex-1 overflow-hidden">
        <aside
          className="flex min-h-0 min-w-[320px] flex-col border-r border-border bg-surface"
          style={{ width: `${sidebarWidth}px` }}
        >
          {loading ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-2">
              <span className="spinner" />
              <p className="text-sm text-muted">Loading bookmarks…</p>
            </div>
          ) : (
            <BookmarkTree
              nodes={tree}
              onTreeChange={setTree}
              onRefresh={refreshTree}
              onSelect={handleSelect}
            />
          )}
        </aside>
        <div
          className="splitter"
          role="separator"
          aria-orientation="vertical"
          tabIndex={0}
          onPointerDown={(event) => {
            if (event.button !== 0) return;
            resizingRef.current = {
              startX: event.clientX,
              startWidth: sidebarWidth,
            };
            (event.currentTarget as HTMLDivElement).setPointerCapture(
              event.pointerId,
            );
          }}
          onPointerMove={(event) => {
            if (!resizingRef.current) return;
            const delta = event.clientX - resizingRef.current.startX;
            const next = Math.max(
              minSidebarWidth,
              resizingRef.current.startWidth + delta,
            );
            setSidebarWidth(next);
          }}
          onPointerUp={() => {
            resizingRef.current = null;
          }}
          onPointerCancel={() => {
            resizingRef.current = null;
          }}
        />
        <main className="scrollbar-themed min-h-0 flex-1 overflow-auto p-6">
          <h2 className="m-0 mb-4 text-lg font-semibold">Details</h2>
          {error && <p className="px-2 text-sm text-danger">{error}</p>}
          <section className={cardClass}>
            <h3 className="m-0 mb-3 text-base font-medium">Bookmark</h3>
            {selected?.node_type === "bookmark" ? (
              <div className="flex items-start gap-4">
                <div className="flex min-w-0 flex-1 flex-col gap-2">
                  <div className="grid grid-cols-[80px_1fr] items-start gap-3">
                    <span className="text-sm text-muted">Title</span>
                    <span className="break-words text-sm">{selected.name}</span>
                  </div>
                  <div className="grid grid-cols-[80px_1fr] items-start gap-3">
                    <span className="text-sm text-muted">URL</span>
                    <a
                      className="break-all text-sm text-accent"
                      href={selected.href ?? ""}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {selected.href}
                    </a>
                  </div>
                  <div className="grid grid-cols-[80px_1fr] items-start gap-3">
                    <span className="text-sm text-muted">Folder</span>
                    <span className="break-words text-sm">
                      {folderPathFor(selected) || "(root)"}
                    </span>
                  </div>
                </div>
                <BookmarkDetailIcon
                  href={bookmarkDetail?.href ?? selected.href}
                  icon={bookmarkDetail?.icon}
                  iconUri={bookmarkDetail?.icon_uri}
                  title={selected.name}
                />
              </div>
            ) : (
              <p className="text-sm text-muted">
                Select a bookmark in the tree to see details.
              </p>
            )}
          </section>
          <section className={cardClass}>
            <div className="flex items-center justify-between gap-2">
              <h3 className="m-0 text-base font-medium">Import bookmarks</h3>
              <button
                type="button"
                className={btnSecondaryClass}
                aria-expanded={importExpanded}
                aria-controls="import-section-content"
                onClick={() => setImportExpanded((open) => !open)}
              >
                <FolderChevron expanded={importExpanded} />
              </button>
            </div>
            {importExpanded && (
              <div id="import-section-content" className="mt-3">
                {importMessage && (
                  <p className="mb-3 text-sm text-success">{importMessage}</p>
                )}
                <form className="flex flex-col gap-3" onSubmit={onImport}>
                  <div className="grid grid-cols-2 gap-3">
                    <label className={labelClass}>
                      User email
                      <input
                        className={inputClass}
                        name="user_email"
                        defaultValue={
                          users.find((u) => u.id === userId)?.email ??
                          "local@bookmark-backup"
                        }
                      />
                    </label>
                    <label className={labelClass}>
                      Device name
                      <input
                        className={inputClass}
                        name="device_name"
                        defaultValue={
                          devices.find((d) => d.id === deviceId)?.name ??
                          "local-device"
                        }
                      />
                    </label>
                  </div>
                  <label className={labelClass}>
                    Upload file(s)
                    <input
                      className={fileInputClass}
                      name="files"
                      type="file"
                      multiple
                      onChange={(event) => {
                        if (
                          event.target.files &&
                          event.target.files.length > 0
                        ) {
                          setImportPaths("");
                        }
                      }}
                    />
                  </label>
                  <label className={labelClass}>
                    Or local path(s), one per line
                    <AutoResizeTextarea
                      className={`${inputClass} font-mono text-xs`}
                      name="paths"
                      value={importPaths}
                      onChange={(event) => setImportPaths(event.target.value)}
                    />
                  </label>
                  <button
                    type="submit"
                    className={`${btnPrimaryClass} self-start`}
                    disabled={importBusy}
                  >
                    {importBusy ? "Importing…" : "Import"}
                  </button>
                </form>
                <p className="mt-3 text-sm text-muted">
                  Tip: the backend supports Chromium JSON `Bookmarks` files and
                  Netscape HTML exports.
                </p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
