export function initialTheme(): "light" | "dark" {
  try {
    const saved = localStorage.getItem("ghosttab-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* Storage may be disabled. */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}
