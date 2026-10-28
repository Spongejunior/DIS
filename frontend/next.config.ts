import type { NextConfig } from 'next';

// The Django backend. `python manage.py runserver` listens on port 80.
const BACKEND_URL = (process.env.BACKEND_URL || 'http://127.0.0.1:80').replace(/\/$/, '');

const nextConfig: NextConfig = {
  // Each page load is one request to the backend. Strict mode would double it in
  // development and the first request would consume the flash messages.
  reactStrictMode: false,

  // How long to wait for the backend before failing a proxied request (default 30s).
  // A prediction can be slow while the model loads for the first time.
  experimental: {
    proxyTimeout: 180_000,
  },

  // Proxied through the Next.js server so the browser stays on one origin and
  // the backend's session cookie works as a same-site cookie.
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${BACKEND_URL}/api/:path*` },
      { source: '/predictions/:id/pdf', destination: `${BACKEND_URL}/predictions/:id/pdf` },
      { source: '/organization/reports/pdf', destination: `${BACKEND_URL}/organization/reports/pdf` },
      { source: '/set-language', destination: `${BACKEND_URL}/set-language` },
    ];
  },
};

export default nextConfig;
