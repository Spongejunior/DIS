import type { BridgeResponse, PagePayload } from '@/types/api';

/** Flask route that runs the view for a page path and answers with JSON. */
export const BRIDGE_PREFIX = '/api/v1/page';

function bridgeUrl(pathWithQuery: string): string {
  const [path, query] = pathWithQuery.split(/\?(.*)/s);
  const cleanPath = path === '/' ? '' : path.replace(/\/$/, '');
  return BRIDGE_PREFIX + cleanPath + (query ? `?${query}` : '');
}

function serverError(): PagePayload {
  return { template: 'errors/500.html', context: {}, user: null, flashes: [] };
}

async function request<C>(pathWithQuery: string, init?: RequestInit): Promise<BridgeResponse<C>> {
  try {
    const response = await fetch(bridgeUrl(pathWithQuery), {
      credentials: 'same-origin',
      cache: 'no-store',
      ...init,
      headers: { Accept: 'application/json', ...init?.headers },
    });
    const body = await response.json();
    if (body && (typeof body.redirect === 'string' || typeof body.template === 'string')) {
      return body as BridgeResponse<C>;
    }
  } catch {
    // Network failure or a non-JSON reply (e.g. the backend is down).
  }
  return serverError() as BridgeResponse<C>;
}

/** GET a page: runs the same Flask view the old URL ran. */
export function getPage<C>(pathWithQuery: string): Promise<BridgeResponse<C>> {
  return request<C>(pathWithQuery);
}

/** POST a form to a Flask view, URL-encoded like a normal HTML form. */
export function postForm<C>(pathWithQuery: string, data: FormData): Promise<BridgeResponse<C>> {
  const body = new URLSearchParams();
  data.forEach((value, key) => {
    if (typeof value === 'string') body.append(key, value);
  });
  return request<C>(pathWithQuery, { method: 'POST', body });
}
