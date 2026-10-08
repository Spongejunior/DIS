// Formatting helpers that reproduce what the Jinja templates printed, so the
// React pages show the same text the Flask-rendered pages did.

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

/**
 * Python's strftime for the ISO strings the backend sends. The value is read
 * field by field (no Date object) so the browser's timezone never shifts it.
 */
export function strftime(iso: string | null | undefined, format: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(iso ?? '');
  if (!match) return '';
  const [, year, month, day, hour = '00', minute = '00', second = '00'] = match;
  const monthName = MONTHS[Number(month) - 1] ?? '';
  const tokens: Record<string, string> = {
    Y: year, m: month, d: day, H: hour, M: minute, S: second,
    B: monthName, b: monthName.slice(0, 3),
  };
  return format.replace(/%([YmdHMSBb])/g, (_, token: string) => tokens[token]);
}

/** How Jinja prints a Python float: whole numbers keep a trailing ".0". */
export function pyFloat(value: number): string {
  return Number.isInteger(value) ? value.toFixed(1) : String(value);
}

/** Jinja's `|round(n)` (result is still a float). */
export function round(value: number, digits = 0): number {
  // toFixed rounds the number's exact binary value, as Python's round() does
  // (so 0.15 becomes 0.1, not 0.2).
  const rounded = value.toFixed(digits);
  // An exact tie goes to the even digit in Python (0.25 -> 0.2); toFixed rounds it up.
  const exact = value.toFixed(digits + 40);
  const kept = exact.slice(0, exact.length - 40);
  const isTie = /^50*$/.test(exact.slice(-40));
  if (isTie && Number(kept.slice(-1)) % 2 === 0) return Number(kept);
  return Number(rounded);
}

/** `{{ (x * 100)|round(1) }}` */
export function percent(fraction: number, digits = 1): string {
  return pyFloat(round(fraction * 100, digits));
}

/** `{{ x|round(0)|int }}` */
export function roundInt(value: number): string {
  return value.toFixed(0);
}

/** `{{ "{:,}".format(n) }}` */
export function thousands(value: number): string {
  return value.toLocaleString('en-US');
}

/** How Jinja prints a value: None becomes the text "None". */
export function text(value: unknown): string {
  return value === null || value === undefined ? 'None' : String(value);
}

/** Jinja's `|capitalize`. */
export function capitalize(value: unknown): string {
  const s = text(value);
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

/** Jinja's `|title`. */
export function title(value: unknown): string {
  return text(value).toLowerCase().replace(/(^|[\s\-(\[{<])(\S)/g, (_, pre: string, ch: string) => pre + ch.toUpperCase());
}

/** `{{ value|replace('_', ' ') }}` */
export function unsnake(value: unknown): string {
  return text(value).replaceAll('_', ' ');
}

/** `{{ value or fallback }}` */
export function or<T>(value: T | null | undefined | '' | 0 | false, fallback: string): T | string {
  return value ? value : fallback;
}

/** Badge colour used for notification priority across the templates. */
export function priorityBadge(priority: string | null, mediumClass = 'warning text-dark'): string {
  if (priority === 'high' || priority === 'critical') return 'danger';
  return priority === 'medium' ? mediumClass : 'primary';
}

/** Progress-bar colour used for prediction confidence across the templates. */
export function confidenceColor(confidencePercent: number): string {
  if (confidencePercent >= 75) return 'success';
  return confidencePercent >= 50 ? 'info' : 'warning';
}
