const themes = [
  {
    id: "light",
    name: "Light",
    description: "Bright surfaces with clear contrast for daytime use.",
    swatches: ["#f4f7fb", "#ffffff", "#2563eb"],
  },
  {
    id: "dark",
    name: "Dark",
    description: "Low-glare dark surfaces for focused market monitoring.",
    swatches: ["#0b1220", "#151f30", "#60a5fa"],
  },
];

export default function Admin({ theme, onThemeChange }) {
  return (
    <main className="admin-page">
      <header className="admin-page__header">
        <p className="admin-page__eyebrow">WORKSPACE SETTINGS</p>
        <h1>Admin</h1>
        <p>Manage app-wide preferences. More workspace settings can be added here.</p>
      </header>

      <section className="admin-card" aria-labelledby="appearance-heading">
        <div className="admin-card__heading">
          <div>
            <h2 id="appearance-heading">Appearance</h2>
            <p>Choose how the trading terminal looks on this device.</p>
          </div>
        </div>

        <div className="theme-options" role="radiogroup" aria-labelledby="appearance-heading">
          {themes.map((option) => (
            <button
              key={option.id}
              type="button"
              role="radio"
              aria-checked={theme === option.id}
              className={`theme-option${theme === option.id ? " theme-option--selected" : ""}`}
              onClick={() => onThemeChange(option.id)}
            >
              <span className={`theme-preview theme-preview--${option.id}`} aria-hidden="true">
                <span className="theme-preview__sidebar" />
                <span className="theme-preview__content">
                  <span />
                  <span />
                  <span />
                </span>
              </span>
              <span className="theme-option__details">
                <span className="theme-option__title">{option.name}</span>
                <span className="theme-option__description">{option.description}</span>
                <span className="theme-option__swatches" aria-hidden="true">
                  {option.swatches.map((color) => (
                    <span key={color} style={{ backgroundColor: color }} />
                  ))}
                </span>
              </span>
              <span className="theme-option__indicator" aria-hidden="true">
                {theme === option.id ? "Selected" : "Select"}
              </span>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
