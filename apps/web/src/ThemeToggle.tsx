import { useEffect, useState } from "react";

import { initialTheme } from "./theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState(initialTheme);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("ghosttab-theme", theme);
    } catch {
      /* In-memory choice still works. */
    }
  }, [theme]);
  return (
    <button
      className="theme-toggle"
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      <span aria-hidden="true">{theme === "light" ? "☾" : "☀"}</span>
      <span>{theme === "light" ? "Dark" : "Light"}</span>
    </button>
  );
}
