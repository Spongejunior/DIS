'use client';

import { useMemo, type ReactNode } from 'react';
import { PageProvider, usePage } from '@/hooks/usePage';
import { ErrorPage, errorTitle } from '@/components/errors/ErrorPage';
import { AppShell } from './AppShell';
import type { LoadedPage } from '@/types/api';

interface FlaskPageProps<C> {
  /** The template's {% block title %} */
  title: string | ((context: C, page: LoadedPage<C>) => string);
  /** The template's {% block sidebar %} */
  sidebar?: ReactNode | ((page: LoadedPage<C>) => ReactNode);
  /** The template's {% block content %} */
  children?: (context: C, page: LoadedPage<C>) => ReactNode;
}

/**
 * A page that used to be a Jinja template extending base.html. It asks Flask
 * for the data of the current URL and renders it inside the shared frame.
 * Nothing is shown until the response arrives, as with a server-rendered page.
 */
export function FlaskPage<C = Record<string, never>>({ title, sidebar, children }: FlaskPageProps<C>) {
  const { page, location, showResponse } = usePage<C>();
  const contextValue = useMemo(() => ({ location, showResponse }), [location, showResponse]);

  if (!page) return null;

  if (page.template.startsWith('errors/')) {
    return (
      <AppShell page={page} title={errorTitle(page.template)}>
        <ErrorPage template={page.template} authenticated={page.user !== null} />
      </AppShell>
    );
  }

  return (
    <PageProvider value={contextValue}>
      <AppShell
        page={page}
        title={typeof title === 'function' ? title(page.context, page) : title}
        sidebar={typeof sidebar === 'function' ? sidebar(page) : sidebar}
      >
        {children?.(page.context, page)}
      </AppShell>
    </PageProvider>
  );
}
