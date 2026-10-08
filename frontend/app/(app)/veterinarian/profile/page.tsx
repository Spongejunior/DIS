'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FieldErrors, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import { strftime, unsnake } from '@/lib/utils/format';
import type { FormData_ } from '@/types/api';

interface VetProfileContext {
  form: FormData_;
  assigned_farmers_count: number;
  pending_reviews: number;
  active_treatments: number;
  mortality_reports_count: number;
}

// templates/veterinarian/profile.html
export default function VetProfilePage() {
  return (
    <FlaskPage<VetProfileContext>
      title="Veterinarian Profile - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="profile" />}
    >
      {(ctx, page) => {
        const user = page.user!;
        const f = ctx.form.fields;
        return (
          <>
            <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-3 mb-4">
              <div>
                <h3 className="fw-bold mb-1 text-dark">Veterinarian Profile</h3>
                <p className="text-muted mb-0">Review your account details and update the contact information farmers rely on.</p>
              </div>
              <Link href={routes.vetDashboard} className="btn btn-outline-primary">
                <i className="bi bi-arrow-left me-2"></i>Back to Dashboard
              </Link>
            </div>

            <div className="row g-4">
              <div className="col-xl-4">
                <div className="card border-0 shadow-sm h-100">
                  <div className="card-body p-4">
                    <div className="text-center mb-4">
                      <div className="display-4 text-primary mb-3">
                        <i className="bi bi-person-badge-fill"></i>
                      </div>
                      <h4 className="fw-bold mb-1">{user.full_name || user.username}</h4>
                      <p className="text-muted mb-2">@{user.username}</p>
                      <span className="badge bg-primary-subtle text-primary text-uppercase">{unsnake(user.role)}</span>
                    </div>

                    <div className="border rounded-4 p-3 bg-light mb-4">
                      <div className="small text-muted mb-1">Primary service area</div>
                      <div className="fw-semibold">{user.location || 'Not provided yet'}</div>
                      <div className="small text-muted">{user.specific_location || 'Specific street or facility not set'}</div>
                    </div>

                    <div className="row g-3 text-center">
                      <div className="col-6">
                        <div className="border rounded-4 p-3 h-100">
                          <div className="small text-muted text-uppercase">Farmers</div>
                          <div className="fs-4 fw-bold text-primary">{ctx.assigned_farmers_count}</div>
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="border rounded-4 p-3 h-100">
                          <div className="small text-muted text-uppercase">Pending Reviews</div>
                          <div className="fs-4 fw-bold text-danger">{ctx.pending_reviews}</div>
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="border rounded-4 p-3 h-100">
                          <div className="small text-muted text-uppercase">Treatments</div>
                          <div className="fs-4 fw-bold text-success">{ctx.active_treatments}</div>
                        </div>
                      </div>
                      <div className="col-6">
                        <div className="border rounded-4 p-3 h-100">
                          <div className="small text-muted text-uppercase">Mortality Reports</div>
                          <div className="fs-4 fw-bold" style={{ color: '#6366f1' }}>{ctx.mortality_reports_count}</div>
                        </div>
                      </div>
                    </div>

                    <hr className="my-4" />

                    <div className="small text-muted mb-2">Account summary</div>
                    <div className="mb-2"><strong>Email:</strong> {user.email}</div>
                    <div className="mb-2"><strong>Phone:</strong> {user.phone || 'Not provided'}</div>
                    <div className="mb-2"><strong>Joined:</strong> {user.registration_date ? strftime(user.registration_date, '%d %b %Y') : 'N/A'}</div>
                    <div><strong>Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</div>
                  </div>
                </div>
              </div>

              <div className="col-xl-8">
                <div className="card border-0 shadow-sm">
                  <div className="card-header bg-white border-0 pt-4 px-4">
                    <h5 className="fw-bold mb-1">Edit Profile</h5>
                    <p className="text-muted small mb-0">Keep your contact and location details current so farmers and administrators can reach you.</p>
                  </div>
                  <div className="card-body p-4 pt-3">
                    <FlaskForm action={routes.vetProfile}>
                      <HiddenTag form={ctx.form} />

                      <div className="row g-3">
                        <div className="col-md-6">
                          <Label field={f.full_name} className="form-label fw-semibold" />
                          <Field field={f.full_name} className="form-control" />
                          <FieldErrors field={f.full_name} />
                        </div>
                        <div className="col-md-6">
                          <label className="form-label fw-semibold">Username</label>
                          <input type="text" className="form-control bg-light" value={user.username} disabled readOnly />
                          <div className="form-text">Username is fixed for now.</div>
                        </div>

                        <div className="col-md-6">
                          <Label field={f.email} className="form-label fw-semibold" />
                          <Field field={f.email} className="form-control" />
                          <FieldErrors field={f.email} />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.phone} className="form-label fw-semibold" />
                          <Field field={f.phone} className="form-control" />
                          <FieldErrors field={f.phone} />
                        </div>

                        <div className="col-12">
                          <Label field={f.location} className="form-label fw-semibold" />
                          <Field field={f.location} className="form-select" />
                          <FieldErrors field={f.location} />
                        </div>

                        <div className="col-12">
                          <Label field={f.specific_location} className="form-label fw-semibold" />
                          <Field field={f.specific_location} className="form-control" placeholder="Clinic, street, landmark, or office location" />
                          <FieldErrors field={f.specific_location} />
                        </div>
                      </div>

                      <div className="d-flex flex-column flex-sm-row gap-2 justify-content-end mt-4">
                        <Link href={routes.vetDashboard} className="btn btn-light">Cancel</Link>
                        <Field field={f.submit} className="btn btn-primary px-4" />
                      </div>
                    </FlaskForm>
                  </div>
                </div>
              </div>
            </div>
          </>
        );
      }}
    </FlaskPage>
  );
}
