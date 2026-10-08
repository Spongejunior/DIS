import type { ReactNode } from 'react';
import { siteMetadata, siteViewport } from '@/lib/site';

export const metadata = siteMetadata;
export const viewport = siteViewport;

// The document from templates/landing_files/landing.html, which does not
// extend base.html and loads its own fonts and stylesheet.
export default function LandingLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Noto+Sans:wght@300;400;500;600;700&display=swap" />
        <link rel="stylesheet" href="/static/css/landing.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
      </head>
      <body>{children}</body>
    </html>
  );
}
