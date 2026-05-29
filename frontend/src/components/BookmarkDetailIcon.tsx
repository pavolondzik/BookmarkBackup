import { useState } from "react";
import { resolveBookmarkIconSrc } from "../bookmarkIcon";

type Props = {
  href: string | null | undefined;
  icon: string | null | undefined;
  iconUri: string | null | undefined;
  title: string;
};
const iconClass = "size-16 shrink-0 object-contain";
export function BookmarkDetailIcon({ href, icon, iconUri, title }: Props) {
  const [failed, setFailed] = useState(false);
  const src = resolveBookmarkIconSrc(href, icon, iconUri);
  if (!src || failed) {
    return (
      <span
        className="flex size-16 shrink-0 items-center justify-center text-2xl text-muted"
        aria-hidden="true"
      >
        ◇
      </span>
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
