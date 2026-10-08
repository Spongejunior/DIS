'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';

// Any other URL: Flask answers with its 404 page, as it always did.
export default function UnknownPage() {
  return <FlaskPage title="Page Not Found" />;
}
