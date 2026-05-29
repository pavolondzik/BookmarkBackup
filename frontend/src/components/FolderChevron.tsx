type Props = {
  expanded: boolean;
};

/** SVG chevron — avoids Windows emoji rendering of ▶/▼ (blue square background). */
export function FolderChevron({ expanded }: Props) {
  return (
    <svg
      className={[
        "size-3 shrink-0 text-muted transition-transform duration-150",
        expanded ? "rotate-90" : "",
      ].join(" ")}
      viewBox="0 0 12 12"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M4 2.5 8.5 6 4 9.5V2.5z" />
    </svg>
  );
}
