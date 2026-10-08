import { Suspense, type ReactNode } from 'react';
import Script from 'next/script';
import { siteMetadata, siteViewport } from '@/lib/site';

export const metadata = siteMetadata;
export const viewport = siteViewport;

// The document from templates/base.html. Stylesheets are linked in the same
// order as before so the cascade is identical.
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Google Fonts: Inter */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />

        {/* Bootstrap 5.3.3 */}
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" />

        {/* Custom Styles */}
        <link rel="stylesheet" href="/static/css/style.css" />
        <link rel="stylesheet" href="/static/css/base.css" />
      </head>
      <body>
        <Suspense>{children}</Suspense>

        {/* Drives the dropdowns, modals and dismissible alerts through data-bs-* attributes */}
        <Script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" strategy="afterInteractive" />
      </body>
    </html>
  );
}
