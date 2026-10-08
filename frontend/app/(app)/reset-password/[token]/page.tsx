'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { AuthCard } from '@/components/layout/AuthCard';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FieldErrors, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_ } from '@/types/api';

// templates/auth/reset_password.html
export default function ResetPasswordPage() {
  return (
    <FlaskPage<{ form: FormData_ }> title="Reset Password - Mzimba North VetAssistant">
      {({ form }) => (
        <AuthCard variant="login" heading="Choose a new password" intro="Your reset link is active. Set a new password below.">
          <FlaskForm noValidate>
            <HiddenTag form={form} />

            <div className="mb-3">
              <Label field={form.fields.new_password} className="form-label small fw-bold text-muted" />
              <Field field={form.fields.new_password} className="form-control border-0 bg-light py-2" placeholder="Enter a new password" autoComplete="new-password" />
              <FieldErrors field={form.fields.new_password} />
            </div>

            <div className="mb-4">
              <Label field={form.fields.confirm_new_password} className="form-label small fw-bold text-muted" />
              <Field field={form.fields.confirm_new_password} className="form-control border-0 bg-light py-2" placeholder="Confirm your new password" autoComplete="new-password" />
              <FieldErrors field={form.fields.confirm_new_password} />
            </div>

            <div className="d-grid">
              <Field field={form.fields.submit} className="btn btn-primary py-2 fw-bold" />
            </div>
          </FlaskForm>

          <div className="mt-4 pt-3 border-top text-center">
            <p className="text-muted small mb-0"><Link href={routes.login} className="text-primary fw-bold text-decoration-none">Back to login</Link></p>
          </div>
        </AuthCard>
      )}
    </FlaskPage>
  );
}
