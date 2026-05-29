import type { ThemeOption } from "./types";
/** System is always listed first in the theme picker. */
const OTHER_THEMES: ThemeOption[] = [
  { id: "dark", label: "Dark" },
  { id: "light", label: "Light" },
  { id: "grey", label: "Grey" },
  { id: "forest", label: "Forest" },
];
export const THEME_OPTIONS: ThemeOption[] = [
  { id: "system", label: "System" },
  ...OTHER_THEMES,
];
export function themeOptionsForSelect(): ThemeOption[] {
  return THEME_OPTIONS;
}
export function isThemeId(value: string): value is ThemeOption["id"] {
  return THEME_OPTIONS.some((theme) => theme.id === value);
}
