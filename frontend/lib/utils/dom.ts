/**
 * Inline styles that need `!important` (the templates use them to beat
 * Bootstrap's `.border-0`). React's `style` prop cannot express that, so the
 * declarations are applied through a ref.
 */
export function important(declarations: Record<string, string>) {
  return (element: HTMLElement | null) => {
    if (!element) return;
    for (const [property, value] of Object.entries(declarations)) {
      element.style.setProperty(property, value, 'important');
    }
  };
}

/**
 * From static/js/main.js: when a form is submitted its submit buttons are
 * disabled and show a "Processing..." spinner.
 */
export function showProcessing(form: HTMLFormElement) {
  form.querySelectorAll<HTMLButtonElement>('button[type="submit"]').forEach((button) => {
    button.disabled = true;
    button.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
  });
}

/** Remove what an open Bootstrap modal leaves on <body> when its page is replaced. */
export function clearModalState() {
  document.querySelectorAll('.modal-backdrop').forEach((backdrop) => backdrop.remove());
  document.body.classList.remove('modal-open');
  document.body.style.removeProperty('overflow');
  document.body.style.removeProperty('padding-right');
}

/**
 * From base.html and main.js: five seconds after a page renders, every
 * `.alert` fades out, slides up and leaves the layout.
 */
export function scheduleAlertDismissal(): () => void {
  const timers: number[] = [];
  timers.push(window.setTimeout(() => {
    document.querySelectorAll<HTMLElement>('.alert:not(.alert-permanent)').forEach((alert) => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      timers.push(window.setTimeout(() => {
        alert.style.overflow = 'hidden';
        alert.style.height = `${alert.offsetHeight}px`;
        alert.style.transition = 'height 0.5s, padding 0.5s, margin 0.5s';
        void alert.offsetHeight;
        alert.style.setProperty('height', '0px');
        alert.style.setProperty('padding-top', '0px');
        alert.style.setProperty('padding-bottom', '0px');
        alert.style.setProperty('margin-top', '0px');
        alert.style.setProperty('margin-bottom', '0px');
        timers.push(window.setTimeout(() => {
          alert.style.setProperty('display', 'none', 'important');
        }, 500));
      }, 500));
    });
  }, 5000));
  return () => timers.forEach((timer) => window.clearTimeout(timer));
}
