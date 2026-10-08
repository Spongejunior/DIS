'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { AuthCard } from '@/components/layout/AuthCard';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FieldErrors, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_, FormFieldData } from '@/types/api';

const LABEL = 'form-label small fw-bold text-muted';
const INPUT = 'form-control border-0 bg-light py-2';
const SELECT = 'form-select border-0 bg-light py-2';

function TextColumn({ field, hint, column = 'col-md-6', autoComplete = 'off', errors = true }: {
  field: FormFieldData;
  hint: string;
  column?: string;
  autoComplete?: string;
  errors?: boolean;
}) {
  return (
    <div className={column}>
      <Label field={field} className={LABEL} />
      <Field field={field} className={INPUT} placeholder="" autoComplete={autoComplete} />
      <div className="form-text">{hint}</div>
      {errors && <FieldErrors field={field} />}
    </div>
  );
}

function RegisterForm({ form }: { form: FormData_ }) {
  const f = form.fields;
  // The farm fields are only shown while "Farmer" is the selected role.
  const [role, setRole] = useState(f.role.choices?.find((choice) => choice[2])?.[0] ?? '');

  return (
    <FlaskForm action={routes.register} noValidate autoComplete="off">
      <HiddenTag form={form} />

      <div className="row g-3">
        <TextColumn field={f.full_name} hint="Enter your first and last name." />
        <TextColumn field={f.email} hint="Use an email you can access." />

        <TextColumn field={f.username} hint="Pick a simple username for login." />
        <TextColumn field={f.phone} hint="Malawi mobile number is best." />

        <TextColumn field={f.password} hint="Mix letters and numbers if possible." autoComplete="new-password" />
        <TextColumn field={f.confirm_password} hint="Must match the password above." autoComplete="new-password" />

        <div className="col-md-6">
          <Label field={f.role} className={LABEL} />
          <select
            id="role-select"
            name={f.role.name}
            className={SELECT}
            autoComplete="off"
            required={Boolean(f.role.attrs.required)}
            value={role}
            onChange={(event) => setRole(event.target.value)}
          >
            {f.role.choices?.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <div className="form-text">Choose whether you are a farmer or veterinarian.</div>
          <FieldErrors field={f.role} />
        </div>
        <div className="col-md-6">
          <Label field={f.location} className={LABEL} />
          <Field field={f.location} className={SELECT} autoComplete="off" />
          <div className="form-text">Pick the block your are in.</div>
          <FieldErrors field={f.location} />
        </div>

        <TextColumn field={f.specific_location} column="col-12" hint="Add a village, street, landmark, block, or trading centre." />

        <div id="farmer-fields" style={{ display: role === 'farmer' ? 'flex' : 'none' }} className="row g-3 mt-1">
          <TextColumn field={f.farm_name} hint="Only for farmer accounts." errors={false} />
          <div className="col-md-6">
            <Label field={f.animal_types} className={LABEL} />
            <Field field={f.animal_types} className={SELECT} autoComplete="off" />
            <div className="form-text">Choose the animals you mainly keep.</div>
          </div>
          <div className="col-md-6">
            <Label field={f.production_focus} className={LABEL} />
            <Field field={f.production_focus} className={SELECT} autoComplete="off" />
            <div className="form-text">Example: dairy, meat, or breeding.</div>
          </div>
        </div>
      </div>

      <div className="d-grid mt-4">
        <Field field={f.submit} className="btn btn-primary py-2 fw-bold" />
      </div>
    </FlaskForm>
  );
}

// templates/auth/register.html
export default function RegisterPage() {
  return (
    <FlaskPage<{ form: FormData_ }> title="Register - Mzimba North VetAssistant">
      {({ form }) => (
        <AuthCard variant="register" heading="Create your account" intro="New accounts require admin approval before full access.">
          <div className="auth-tip small text-muted mb-4">
            Use your real name, active phone number and location.
          </div>

          <RegisterForm form={form} />

          <div className="mt-4 pt-3 border-top text-center">
            <p className="text-muted small mb-0">Already have an account? <Link href={routes.login} className="text-primary fw-bold text-decoration-none">Sign In</Link></p>
          </div>
        </AuthCard>
      )}
    </FlaskPage>
  );
}
