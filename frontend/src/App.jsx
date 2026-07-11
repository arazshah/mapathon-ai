import { useState } from "react";
import AboutPage from "./components/AboutPage";
import MapWorkspace from "./components/MapWorkspace";

export default function App() {
  const [page, setPage] = useState("map");

  return (
    <div className="app-shell">
      <header className="app-header">
        <button
          className="brand"
          type="button"
          onClick={() => setPage("map")}
          aria-label="صفحه اصلی مپاتون"
        >
          <span className="brand-mark">م</span>

          <span>
            <strong>مپاتون</strong>
            <small>هوش مکانی فارسی</small>
          </span>
        </button>

        <nav className="main-nav" aria-label="منوی اصلی">
          <button
            type="button"
            className={page === "map" ? "nav-link active" : "nav-link"}
            onClick={() => setPage("map")}
            aria-current={page === "map" ? "page" : undefined}
          >
            نقشه و جست‌وجو
          </button>

          <button
            type="button"
            className={page === "about" ? "nav-link active" : "nav-link"}
            onClick={() => setPage("about")}
            aria-current={page === "about" ? "page" : undefined}
          >
            درباره مپاتون
          </button>
        </nav>

        <div className="header-badge" aria-label="وضعیت سامانه: آنلاین">
          <span aria-hidden="true" />
          آنلاین
        </div>
      </header>

      {page === "about" ? (
        <AboutPage onBack={() => setPage("map")} />
      ) : (
        <MapWorkspace />
      )}
    </div>
  );
}
