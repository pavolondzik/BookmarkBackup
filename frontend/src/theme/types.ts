export const THEME_IDS = ["system", "dark", "light", "forest", "grey"] as const;
export type ThemeId = (typeof THEME_IDS)[number];
export type ThemeOption = {
  id: ThemeId;
  label: string;
};
