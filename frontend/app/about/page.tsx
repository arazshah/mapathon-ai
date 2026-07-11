import Link from "next/link";

export const metadata = {
  title: "درباره مپاتون",
  description:
    "درباره سامانه هوش مصنوعی مکانی مپاتون و آراز شاه‌کرمی",
};

export default function AboutPage() {
  return (
    <main className="about-page">
      <div className="about-background" />

      <nav className="about-nav">
        <Link
          href="/"
          className="brand"
          aria-label="بازگشت به مپاتون"
        >
          <span className="brand-symbol">
            <svg
              viewBox="0 0 32 32"
              aria-hidden="true"
            >
              <path d="M16 3.5a10 10 0 0 0-10 10c0 7.9 10 15 10 15s10-7.1 10-15a10 10 0 0 0-10-10Z" />
              <circle
                cx="16"
                cy="13.5"
                r="3.5"
              />
            </svg>
          </span>

          <span>
            <strong>مپاتون</strong>
            <small>هوش مصنوعی مکانی</small>
          </span>
        </Link>

        <Link
          href="/"
          className="back-link"
        >
          بازگشت به نقشه
          <span>←</span>
        </Link>
      </nav>

      <article className="about-content">
        <header className="about-hero">
          <span className="about-badge">
            درباره مپاتون
          </span>

          <h1>
            پرسیدن به زبان انسان،
            <br />
            دیدن پاسخ روی نقشه
          </h1>

          <p>
            مپاتون بستری برای تبدیل
            پرس‌وجوهای زبان طبیعی به
            اطلاعات، تحلیل‌ها و پاسخ‌های
            قابل مشاهده روی نقشه است.
          </p>
        </header>

        <section className="about-grid">
          <div className="about-card featured">
            <span className="card-index">
              ۰۱
            </span>

            <h2>مپاتون چیست؟</h2>

            <p>
              مپاتون تلاش می‌کند تعامل با
              داده‌های مکانی را ساده‌تر و
              انسانی‌تر کند. به‌جای کار با
              ابزارهای پیچیده، کافی است سؤال
              خود را به فارسی بنویسید؛ مانند
              پیدا کردن مکان‌ها، نزدیک‌ترین
              خدمات، مسیریابی یا تحلیل
              اطلاعات جغرافیایی.
            </p>

            <div className="feature-tags">
              <span>جست‌وجوی مکانی</span>
              <span>مسیریابی هوشمند</span>
              <span>زبان طبیعی فارسی</span>
              <span>تحلیل جغرافیایی</span>
            </div>
          </div>

          <div className="about-card">
            <span className="card-index">
              ۰۲
            </span>

            <h2>چشم‌انداز</h2>

            <p>
              هدف مپاتون ایجاد یک رابط عمومی،
              ساده و توسعه‌پذیر برای دسترسی
              هوشمند به داده‌های مکانی است؛
              سامانه‌ای که با بازخورد کاربران
              و مشارکت متخصصان GIS روزبه‌روز
              دقیق‌تر و کاربردی‌تر شود.
            </p>
          </div>
        </section>

        <section className="creator-section">
          <div className="creator-visual">
            <div className="creator-avatar">
              <span>آش</span>
            </div>

            <div className="creator-orbit orbit-one" />
            <div className="creator-orbit orbit-two" />
          </div>

          <div className="creator-copy">
            <span className="about-badge">
              طراح و توسعه‌دهنده
            </span>

            <h2>آراز شاه‌کرمی</h2>

            <h3>
              Geospatial AI Engineer
            </h3>

            <p>
              مپاتون توسط آراز شاه‌کرمی،
              برنامه‌نویس و مهندس هوش مصنوعی
              مکانی، طراحی و توسعه داده شده
              است. تمرکز او بر ترکیب هوش
              مصنوعی، داده‌های جغرافیایی و
              تجربه کاربری برای ساخت ابزارهای
              مکانی قابل‌فهم و کاربردی است.
            </p>

            <div className="creator-actions">
              <a
                href="https://araz.me"
                target="_blank"
                rel="noopener noreferrer"
                className="primary-link"
              >
                مشاهده وب‌سایت آراز
                <span>↗</span>
              </a>

              <a
                href="https://www.coffeebede.com/arazshah"
                target="_blank"
                rel="noopener noreferrer"
                className="support-link"
              >
                حمایت از پروژه
              </a>
            </div>
          </div>
        </section>

        <section className="about-cta">
          <div>
            <span>آماده تجربه هستید؟</span>
            <h2>
              سؤال مکانی خود را بنویسید.
            </h2>
          </div>

          <Link href="/">
            ورود به مپاتون
            <span>←</span>
          </Link>
        </section>
      </article>

      <footer className="about-footer">
        <span>
          © مپاتون — ساخته‌شده با تمرکز بر
          هوش مصنوعی مکانی
        </span>

        <a
          href="https://araz.me"
          target="_blank"
          rel="noopener noreferrer"
        >
          araz.me
        </a>
      </footer>
    </main>
  );
}
