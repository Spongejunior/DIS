import type { CurrentUser } from './models';

/** [category, message] exactly as Flask's get_flashed_messages(with_categories=True). */
export type Flash = [string, string];

/** What a Flask view passed to render_template, delivered as JSON by the bridge. */
export interface PagePayload<C = Record<string, unknown>> {
  template: string;
  context: C;
  user: CurrentUser | null;
  flashes: Flash[];
}

export interface RedirectPayload {
  redirect: string;
}

export type BridgeResponse<C = Record<string, unknown>> = PagePayload<C> | RedirectPayload;

/** A rendered response held by the page, with a counter that changes per response. */
export interface LoadedPage<C = Record<string, unknown>> extends PagePayload<C> {
  nonce: number;
}

/** One WTForms field, described with the attributes its widget renders. */
export interface FormFieldData {
  id: string;
  name: string;
  type: string;
  label: string;
  value?: string;
  checked?: boolean;
  /** [value, label, selected] */
  choices?: [string, string, boolean][];
  attrs: Record<string, string | number | boolean>;
  errors: string[];
}

export interface FormData_ {
  fields: Record<string, FormFieldData>;
  errors: Record<string, string[]>;
}
