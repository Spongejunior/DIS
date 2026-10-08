'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { AuthCard } from '@/components/layout/AuthCard';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FieldErrors, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_ } from '@/types/api';

// templates/auth/forgot_password.html
export default function ForgotPasswordPage() {
  return (
    <FlaskPage<{ form: FormData_ }> title="Forgot Password - Mzimba North VetAssistant">
      {({ form }) => (
        <AuthCard variant="login" heading="Reset your password" intro="Enter your username or email and we will prepare a reset link.">
          <FlaskForm action={routes.forgotPassword} noValidate>
            <HiddenTag form={form} />

            <div className="mb-4">
              <Label field={form.fields.identity} className="form-label small fw-bold text-muted" />
              <div className="input-group">
                <span className="input-group-text border-0 bg-light"><i className="bi bi-person-lines-fill text-muted"></i></span>
                <Field field={form.fields.identity} className="form-control border-0 bg-light py-2" placeholder="Username or email address" />
              </div>
              <div className="form-text">Use the same username or email you registered with.</div>
              <FieldErrors field={form.fields.identity} />
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
