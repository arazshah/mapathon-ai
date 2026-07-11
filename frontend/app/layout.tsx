import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";


export const metadata: Metadata = {
  title: {
    default: "مپاتون | هوش مصنوعی مکانی",
    template: "%s | مپاتون",
  },
  description:
    "پرس‌وجوی مکانی به زبان طبیعی و مشاهده نتایج روی نقشه",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <header className="site-header">
          <Link
            href="/"
            className="brand"
            aria-label="صفحه اصلی مپاتون"
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
              <small>
                هوش مصنوعی مکانی
              </small>
            </span>
          </Link>

          <nav aria-label="منوی اصلی">
            <Link href="/">نقشه</Link>
            <Link href="/about">
              درباره مپاتون
            </Link>
          </nav>
        </header>

        {children}
      </body>
    </html>
  );
}
