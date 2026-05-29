export function resolveBookmarkIconSrc(
  href: string | null | undefined,
  icon: string | null | undefined,
  iconUri: string | null | undefined,
): string | null {
  const embedded = icon?.trim();
  if (embedded?.startsWith("data:image")) {
    return embedded;
  }
  const uri = iconUri?.trim();
  if (uri?.startsWith("http://") || uri?.startsWith("https://")) {
    return uri;
  }
  if (!href) {
    return null;
  }
  try {
    const host = new URL(href).hostname;
    if (host) {
      return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=64`;
    }
  } catch {
    return null;
  }
  return null;
}
