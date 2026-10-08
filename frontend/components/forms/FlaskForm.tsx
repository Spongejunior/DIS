'use client';

import type { ComponentPropsWithoutRef, FormEvent } from 'react';
import { postForm } from '@/lib/api/client';
import { showProcessing } from '@/lib/utils/dom';
import { usePageContext } from '@/hooks/usePage';

interface FlaskFormProps extends Omit<ComponentPropsWithoutRef<'form'>, 'action' | 'method' | 'onSubmit'> {
  /** Flask URL to post to. Omitted = the current page, like a form without `action`. */
  action?: string;
  /** Ask before submitting (the templates' `onsubmit="return confirm(...)"`). */
  confirmMessage?: string;
}

/**
 * A `<form method="POST">` handled by a Flask view. The fields are posted
 * URL-encoded to the same view as before; a redirect is followed with a full
 * page load, and a re-render (validation errors) replaces the page content.
 */
export function FlaskForm({ action, confirmMessage, children, ...rest }: FlaskFormProps) {
  const { location, showResponse } = usePageContext();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (confirmMessage && !window.confirm(confirmMessage)) return;

    const form = event.currentTarget;
    const submitter = (event.nativeEvent as SubmitEvent).submitter;
    let data: FormData;
    try {
      data = new FormData(form, submitter);
    } catch {
      data = new FormData(form);
    }
    showProcessing(form);

    const response = await postForm<Record<string, unknown>>(action ?? location, data);
    if ('redirect' in response) {
      window.location.assign(response.redirect);
    } else {
      showResponse(response);
    }
  }

  return (
    <form method="POST" action={action} onSubmit={handleSubmit} {...rest}>
      {children}
    </form>
  );
}

/** For plain GET (filter) and native POST forms: keep main.js's "Processing..." buttons. */
export function processingOnSubmit(event: FormEvent<HTMLFormElement>) {
  const form = event.currentTarget;
  // Let the browser collect the form data before the buttons are disabled.
  window.setTimeout(() => showProcessing(form), 0);
}
