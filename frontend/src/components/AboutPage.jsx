const externalLinkProps = {
  target: "_blank",
  rel: "noopener noreferrer",
};

const socialLinks = [
  {
    label: "وب‌سایت",
    value: "araz.me",
    href: "https://araz.me",
    icon: "↗",
  },
  {
    label: "گیت‌هاب",
    value: "github.com/arazshah",
    href: "https://github.com/arazshah",
    icon: "GH",
  },
  {
    label: "لینکدین",
    value: "in/araz-shahkarami",
    href: "https://www.linkedin.com/in/araz-shahkarami",
    icon: "in",
  },
  {
    label: "اینستاگرام",
    value: "@araz.me",
    href: "https://instagram.com/araz.me",
    icon: "◎",
  },
];

const expertise = [
  "Geospatial AI",
  "GIS و سنجش از دور",
  "هوش مصنوعی و LLM",
  "مهندسی نرم‌افزار",
  "داده‌های مکانی",
  "متن‌باز",
];

export default function AboutPage({ onBack }) {
  return (
    <main className="about-page">
      <section className="about-card" aria-labelledby="about-title">
        <button className="back-button" type="button" onClick={onBack}>
          <span aria-hidden="true">→</span>
          بازگشت به نقشه
        </button>

        <header className="about-hero">
          <div className="about-kicker">درباره مپاتون</div>

          <h1 id="about-title">
            هوش مکانی، با زبان ساده و روی نقشه
          </h1>

          <p className="about-lead">
            مپاتون یک دستیار هوشمند مکانی فارسی است که پرس‌وجوهای زبان
            طبیعی را به جست‌وجو، مسیر، تحلیل جغرافیایی و پاسخ‌های قابل
            مشاهده روی نقشه تبدیل می‌کند.
          </p>

          <div className="about-status-row" aria-label="ویژگی‌های اصلی مپاتون">
            <span>
              <i aria-hidden="true" />
              فعال و در حال توسعه
            </span>
            <span>فارسی و راست‌به‌چپ</span>
            <span>متمرکز بر داده‌های مکانی ایران</span>
          </div>
        </header>

        <div className="about-grid">
          <article>
            <div className="about-icon" aria-hidden="true">⌕</div>
            <h2>جست‌وجوی فارسی</h2>
            <p>
              مکان، مسیر یا نیاز مکانی خود را همان‌طور که در گفت‌وگوی
              روزمره بیان می‌کنید، به فارسی بنویسید.
            </p>
          </article>

          <article>
            <div className="about-icon" aria-hidden="true">⌖</div>
            <h2>نمایش روی نقشه</h2>
            <p>
              نتایج جست‌وجو، نقاط مهم، مسیرها و اطلاعات جغرافیایی
              به‌شکلی واضح و قابل فهم روی نقشه نمایش داده می‌شوند.
            </p>
          </article>

          <article>
            <div className="about-icon" aria-hidden="true">✦</div>
            <h2>تحلیل هوشمند</h2>
            <p>
              مپاتون با ترکیب هوش مصنوعی، داده‌های مکانی و ابزارهای
              مسیریابی، پاسخ‌های کاربردی‌تر و متناسب با موقعیت ارائه می‌دهد.
            </p>
          </article>
        </div>

        <section className="about-mission" aria-labelledby="mission-title">
          <div>
            <span className="section-eyebrow">چشم‌انداز پروژه</span>
            <h2 id="mission-title">دسترسی عمومی‌تر به اطلاعات مکانی</h2>
          </div>

          <p>
            هدف مپاتون ایجاد یک رابط ساده، عمومی و توسعه‌پذیر برای کار با
            داده‌های جغرافیایی است؛ رابطی که بدون نیاز به شناخت ابزارهای
            تخصصی GIS، پرسش انسان را درک کند و پاسخ را به‌صورت بصری روی
            نقشه نشان دهد.
          </p>
        </section>

        <section className="creator-section" aria-labelledby="creator-title">
          <div className="creator-heading">
            <div className="author-avatar" aria-hidden="true">آ</div>

            <div>
              <span className="section-eyebrow">طراح و توسعه‌دهنده اصلی</span>
              <h2 id="creator-title">آراز شاه‌کرمی</h2>
              <strong>مهندس هوش مصنوعی مکانی</strong>
              <small lang="en">Geospatial AI Engineer</small>
            </div>
          </div>

          <p className="creator-bio">
            آراز شاه‌کرمی مهندس هوش مصنوعی مکانی با بیش از ۱۳ سال تجربه
            در فناوری اطلاعات و دارای کارشناسی ارشد GIS و سنجش از دور است.
            تمرکز او بر ترکیب هوش مصنوعی، داده‌های جغرافیایی، مهندسی
            نرم‌افزار و تجربه کاربری برای ساخت ابزارهای مکانی قابل فهم،
            متن‌باز و کاربردی است.
          </p>

          <div className="expertise-list" aria-label="حوزه‌های تخصصی">
            {expertise.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>

          <div className="social-links">
            {socialLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                aria-label={`${link.label} آراز شاه‌کرمی`}
                {...externalLinkProps}
              >
                <span className="social-icon" aria-hidden="true">
                  {link.icon}
                </span>

                <span className="social-content">
                  <small>{link.label}</small>
                  <strong dir="ltr">{link.value}</strong>
                </span>

                <span className="social-arrow" aria-hidden="true">↖</span>
              </a>
            ))}

            <a
              href="mailto:araz.shah@gmail.com"
              aria-label="ارسال ایمیل به آراز شاه‌کرمی"
            >
              <span className="social-icon" aria-hidden="true">@</span>

              <span className="social-content">
                <small>ایمیل</small>
                <strong dir="ltr">araz.shah [at] gmail [dot] com</strong>
              </span>

              <span className="social-arrow" aria-hidden="true">←</span>
            </a>
          </div>
        </section>

        <footer className="about-footer">
          <div>
            <strong>از توسعه مپاتون حمایت کنید</strong>
            <span>
              اگر مپاتون برایتان مفید است، می‌توانید از ادامه توسعه آن
              حمایت کنید.
            </span>
          </div>

          <a
            className="support-button"
            href="https://www.coffeebede.com/arazshah"
            aria-label="حمایت از توسعه مپاتون"
            {...externalLinkProps}
          >
            حمایت از مپاتون
          </a>
        </footer>
      </section>
    </main>
  );
}
