'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { AuthCard } from '@/components/layout/AuthCard';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FieldErrors, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_ } from '@/types/api';

function LoginForm({ form }: { form: FormData_ }) {
  const [showPassword, setShowPassword] = useState(false);
  const f = form.fields;

  return (
    <FlaskForm action={routes.login} noValidate>
      <HiddenTag form={form} />

      <div className="mb-3">
        <Label field={f.username} className="form-label small fw-bold text-muted" />
        <div className="input-group">
          <span className="input-group-text border-0 bg-light"><i className="bi bi-person text-muted"></i></span>
          <Field field={f.username} className="form-control border-0 bg-light py-2" placeholder="Example: thokobanda12" />
        </div>
        <div className="form-text">Enter the username you registered with.</div>
        <FieldErrors field={f.username} />
      </div>

      <div className="mb-3">
        <Label field={f.password} className="form-label small fw-bold text-muted" />
        <div className="input-group">
          <span className="input-group-text border-0 bg-light"><i className="bi bi-lock text-muted"></i></span>
          <Field field={f.password} type={showPassword ? 'text' : 'password'} className="form-control border-0 bg-light py-2" placeholder="Enter your password" />
          <button className="btn btn-light border-0 bg-light" type="button" id="togglePassword" onClick={() => setShowPassword((shown) => !shown)}>
            <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'} text-muted`}></i>
          </button>
        </div>
        <div className="form-text">Passwords are case-sensitive.</div>
        <FieldErrors field={f.password} />
      </div>

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div className="form-check">
          <Field field={f.remember} className="form-check-input" />{' '}
          <Label field={f.remember} className="form-check-label small text-muted" />
        </div>
        <Link href={routes.forgotPassword} className="text-primary small fw-bold text-decoration-none">Forgot Password?</Link>
      </div>

      <div className="d-grid">
        <Field field={f.submit} className="btn btn-primary py-2 fw-bold" />
      </div>
    </FlaskForm>
  );
}

// templates/auth/login.html
export default function LoginPage() {
  return (
    <FlaskPage<{ form: FormData_ }> title="Login - Mzimba North VetAssistant">
      {({ form }) => (
        <AuthCard variant="login" heading="Welcome back">
          <LoginForm form={form} />

          <div className="mt-4 pt-3 border-top text-center">
            <p className="text-muted small mb-0">Don&apos;t have an account? <Link href={routes.register} className="text-primary fw-bold text-decoration-none">Create Account</Link></p>
          </div>
        </AuthCard>
      )}
    </FlaskPage>
  );
}
