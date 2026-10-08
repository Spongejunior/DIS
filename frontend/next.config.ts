import type { NextConfig } from 'next';

// The existing Flask backend. `python app.py` listens on port 80.
const BACKEND_URL = (process.env.BACKEND_URL || 'http://127.0.0.1:80').replace(/\/$/, '');

const nextConfig: NextConfig = {
  // Each page load is one request to Flask. Strict mode would double it in
  // development and the first request would consume the flash messages.
  reactStrictMode: false,

  // Proxied through the Next.js server so the browser stays on one origin and
  // the Flask session cookie works exactly as before.
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
