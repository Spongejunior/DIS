import type { FormData_, FormFieldData } from '@/types/api';

// WTForms renders HTML attribute names; React wants the camelCase property.
const ATTRIBUTE_NAMES: Record<string, string> = {
  maxlength: 'maxLength',
  minlength: 'minLength',
  readonly: 'readOnly',
  autocomplete: 'autoComplete',
};

/** Attributes the template passed when rendering the field. */
interface ExtraProps {
  id?: string;
  className?: string;
  placeholder?: string;
  autoComplete?: string;
  type?: string;
  rows?: number;
}

function widgetProps(field: FormFieldData, extra: ExtraProps): Record<string, unknown> {
  const attrs: Record<string, unknown> = {};
  for (const [name, value] of Object.entries(field.attrs)) {
    attrs[ATTRIBUTE_NAMES[name] ?? name] = value;
  }
  return { id: field.id, name: field.name, ...attrs, ...extra };
}

/** `{{ form.field(class="...", placeholder="...") }}` */
export function Field({ field, ...extra }: { field: FormFieldData } & ExtraProps) {
  const props = widgetProps(field, extra);

  if (field.type === 'select') {
    const selected = field.choices?.find((choice) => choice[2])?.[0];
    return (
      <select {...props} defaultValue={selected}>
        {field.choices?.map(([value, label]) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>
    );
  }
  if (field.type === 'textarea') {
    return <textarea {...props} defaultValue={field.value} />;
  }
  if (field.type === 'checkbox') {
    return <input {...props} type="checkbox" value={field.value} defaultChecked={field.checked} />;
  }
  if (field.type === 'submit') {
    return <input {...props} type="submit" value={field.value} />;
  }
  return <input type={field.type} {...props} defaultValue={field.value} />;
}

/** `{{ form.field.label(class="...") }}` */
export function Label({ field, className }: { field: FormFieldData; className?: string }) {
  return <label className={className} htmlFor={field.id}>{field.label}</label>;
}

/** `{{ form.hidden_tag() }}` */
export function HiddenTag({ form }: { form: FormData_ }) {
  return (
    <>
      {Object.values(form.fields)
        .filter((field) => field.type === 'hidden')
        .map((field) => (
          <input key={field.name} id={field.id} name={field.name} type="hidden" value={field.value ?? ''} readOnly />
        ))}
    </>
  );
}

/** `{% for error in form.field.errors %}<div class="text-danger small mt-1">...` */
export function FieldErrors({ field }: { field: FormFieldData }) {
  return (
    <>
      {field.errors.map((error, index) => (
        <div key={index} className="text-danger small mt-1">{error}</div>
      ))}
    </>
  );
}

/** `{% for field, errors in form.errors.items() %}<li>Label: error</li>` */
export function ErrorSummaryItems({ form }: { form: FormData_ }) {
  return (
    <>
      {Object.entries(form.errors).flatMap(([name, errors]) =>
        errors.map((error, index) => (
          <li key={`${name}-${index}`}>{form.fields[name]?.label}: {error}</li>
        )),
      )}
    </>
  );
}

export function hasErrors(form: FormData_): boolean {
  return Object.keys(form.errors).length > 0;
}

/** For forms inside a modal: after a failed submit the modal is closed, so the errors are listed on the page. */
export function FormErrorAlert({ form, title }: { form: FormData_; title: string }) {
  if (!hasErrors(form)) return null;
  return (
    <div className="alert alert-danger border-0 shadow-sm mb-4">
      <h6 className="fw-bold"><i className="bi bi-exclamation-triangle-fill me-1"></i> {title}</h6>
      <ul className="mb-0 small">
        <ErrorSummaryItems form={form} />
      </ul>
    </div>
  );
}
