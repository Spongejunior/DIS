'use client';

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { getPage } from '@/lib/api/client';
import { clearModalState } from '@/lib/utils/dom';
import type { BridgeResponse, LoadedPage } from '@/types/api';

interface PageContextValue {
  /** Path and query of the page being shown, as Flask sees it. */
  location: string;
  /** Show a response returned by a form POST (a re-render with errors). */
  showResponse: (response: BridgeResponse) => void;
}

const PageContext = createContext<PageContextValue | null>(null);

export const PageProvider = PageContext.Provider;

export function usePageContext(): PageContextValue {
  const value = useContext(PageContext);
  if (!value) throw new Error('usePageContext must be used inside a FlaskPage');
  return value;
}

/**
 * Loads the current URL from Flask the way the browser used to: the view for
 * this path runs and either sends its template data or a redirect to follow.
 */
export function usePage<C>() {
  const pathname = usePathname();
  const query = useSearchParams().toString();
  const router = useRouter();
  const location = pathname + (query ? `?${query}` : '');

  const [page, setPage] = useState<LoadedPage<C> | null>(null);
  const nonce = useRef(0);

  const showResponse = useCallback((response: BridgeResponse) => {
    if ('redirect' in response) {
      router.replace(response.redirect);
      return;
    }
    clearModalState();
    nonce.current += 1;
    setPage({ ...(response as LoadedPage<C>), nonce: nonce.current });
  }, [router]);

  useEffect(() => {
    let cancelled = false;
    getPage<C>(location).then((response) => {
      if (!cancelled) showResponse(response as BridgeResponse);
    });
    return () => {
      cancelled = true;
    };
  }, [location, showResponse]);

  // A modal left open must not outlive the page that owns it.
  useEffect(() => clearModalState, []);

  return { page, location, showResponse };
}
