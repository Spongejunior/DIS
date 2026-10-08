'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { OrgAdminSidebar } from '@/components/sidebar/Sidebar';
import { routes } from '@/lib/api/routes';
import { strftime, unsnake } from '@/lib/utils/format';

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="col-md-6">
      <label className="form-label text-muted">{label}</label>
      <div className="form-control bg-light">{value}</div>
    </div>
  );
}

// templates/organization_admin/my_profile.html
export default function OrgAdminProfilePage() {
  return (
    <FlaskPage
      title="My Profile - Mzimba North VetAssistant"
      sidebar={<OrgAdminSidebar active="profile" />}
    >
      {(_ctx, page) => {
        const user = page.user!;
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <div>
                <h2 className="mb-1"><i className="bi bi-person-badge"></i> My Profile</h2>
                <p className="text-muted mb-0">Your organization administrator account details and system access summary.</p>
              </div>
              <Link href={routes.orgAdminDashboard} className="btn btn-outline-primary">
                <i className="bi bi-arrow-left"></i> Back to Dashboard
              </Link>
            </div>

            <div className="row g-4">
              <div className="col-lg-4">
                <div className="card h-100">
                  <div className="card-body text-center">
                    <div className="display-5 text-primary mb-3">
                      <i className="bi bi-person-circle"></i>
                    </div>
                    <h4 className="mb-1">{user.full_name || user.username}</h4>
                    <div className="text-muted mb-3">@{user.username}</div>
                    <span className="badge bg-primary">{unsnake(user.role)}</span>
                  </div>
                </div>
              </div>
              <div className="col-lg-8">
                <div className="card">
                  <div className="card-header">
                    <h5 className="mb-0">Account Information</h5>
                  </div>
                  <div className="card-body">
                    <div className="row g-3">
                      <ReadOnlyField label="Full Name" value={user.full_name || 'Not provided'} />
                      <ReadOnlyField label="Email" value={user.email} />
                      <ReadOnlyField label="Phone" value={user.phone || 'Not provided'} />
                      <ReadOnlyField label="Location" value={user.location || 'Not provided'} />
                      <ReadOnlyField label="Registered" value={user.registration_date ? strftime(user.registration_date, '%d %b %Y') : 'N/A'} />
                      <ReadOnlyField label="Account Status" value={user.is_active ? 'Active' : 'Inactive'} />
                    </div>
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
