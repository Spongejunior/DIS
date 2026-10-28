import type { Metadata, Viewport } from 'next';

const NAME = 'Mzimba North VetAssistant';
const DESCRIPTION =
  'Intelligent livestock disease identification and veterinary assistance system for Mzimba North.';

// The <head> tags shared by templates/base.html and templates/landing_files/landing.html.
export const siteMetadata: Metadata = {
  title: NAME,
  applicationName: NAME,
  description: DESCRIPTION,
  openGraph: { siteName: NAME, title: NAME, description: DESCRIPTION, type: 'website' },
};

export const siteViewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#1a4a2e',
};
