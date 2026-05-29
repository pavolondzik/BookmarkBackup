import { useState } from "react";
import { resolveBookmarkIconSrc } from "../bookmarkIcon";

type Props = {
  href: string | null | undefined;
  icon: string | null | undefined;
  iconUri: string | null | undefined;
  title: string;
};
const iconClass =
  "size-16 shrink-0 rounded-lg border border-border bg-foreground/5 object-contain";
export function BookmarkDetailIcon({ href, icon, iconUri, title }: Props) {
  const [failed, setFailed] = useState(false);
  const src = resolveBookmarkIconSrc(href, icon, iconUri);
  if (!src || failed) {
    return (
      <div
        className={`${iconClass} flex items-center justify-center text-2xl text-muted`}
        aria-hidden="true"
      >
        <span>◇</span>
      </div>
    );
  }
  return (
    <img
      className={iconClass}
      src={src}
      alt={title}
      onError={() => setFailed(true)}
    />
  );
}
