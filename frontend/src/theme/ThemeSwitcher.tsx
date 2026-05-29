import { themeOptionsForSelect, useTheme } from "./ThemeContext";
import type { ThemeId } from "./types";

const selectClass =
  "rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-foreground focus:border-accent focus:outline-none";
export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  return (
    <label className="flex flex-col items-end gap-1 text-xs text-muted">
      <span>Theme</span>
      <select
        className={selectClass}
        value={theme}
        onChange={(event) => setTheme(event.target.value as ThemeId)}
        aria-label="Color theme"
      >
        {themeOptionsForSelect().map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
