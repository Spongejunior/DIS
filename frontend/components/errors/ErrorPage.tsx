import Link from 'next/link';
import { routes } from '@/lib/api/routes';

const ERRORS: Record<string, { title: string; code: string; message: string; button: string }> = {
  'errors/404.html': { title: 'Page Not Found', code: '404', message: 'The page you requested could not be found.', button: 'Go Back' },
  'errors/403.html': { title: 'Access Denied', code: '403', message: 'You do not have permission to access this page.', button: 'Return' },
  'errors/500.html': { title: 'Server Error', code: '500', message: 'An unexpected error occurred while processing the request.', button: 'Return' },
};

export function errorTitle(template: string): string {
  return (ERRORS[template] ?? ERRORS['errors/500.html']).title;
}

/** templates/errors/404.html, 403.html and 500.html */
export function ErrorPage({ template, authenticated }: { template: string; authenticated: boolean }) {
  const error = ERRORS[template] ?? ERRORS['errors/500.html'];
  return (
    <div className="row justify-content-center mt-5">
      <div className="col-md-8 col-lg-6">
        <div className="card shadow-sm">
          <div className="card-body text-center p-5">
            <h1 className="display-5 mb-3">{error.code}</h1>
            <p className="lead">{error.message}</p>
            <Link href={authenticated ? routes.dashboard : routes.login} className="btn btn-primary">{error.button}</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
