'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import { strftime, text } from '@/lib/utils/format';
import type { FormData_ } from '@/types/api';

interface FarmerProfileContext {
  form: FormData_;
  assigned_vets: { full_name: string | null; phone: string | null; email: string }[];
}

// templates/farmer/registration.html
export default function FarmerProfilePage() {
  return (
    <FlaskPage<FarmerProfileContext>
      title="My Profile - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="outline" active="profile" />}
    >
      {({ form, assigned_vets }, page) => {
        const user = page.user!;
        const f = form.fields;
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2><i className="bi bi-person-badge"></i> Farmer Profile &amp; Registration Details</h2>
              <button className="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editProfileModal">
                <i className="bi bi-pencil"></i> Edit Profile
              </button>
            </div>

            <div className="row">
              <div className="col-md-4">
                {/* Profile Card */}
                <div className="card mb-4">
                  <div className="card-body text-center">
                    <div className="mb-3">
                      <i className="bi bi-person-circle" style={{ fontSize: '4rem', color: '#6c757d' }}></i>
                    </div>
                    <h4>{user.username}</h4>
                    <p className="text-muted">Farmer</p>
                    <div className="badge bg-primary mb-3">Registered Member</div>
                    <p><i className="bi bi-calendar-check"></i> Member since: March 2023</p>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="card">
                  <div className="card-header">
                    <h6 className="mb-0">Account Statistics</h6>
                  </div>
                  <div className="card-body">
                    <div className="d-flex justify-content-between mb-2">
                      <span>Total Reports:</span>
                      <strong>15</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Animals Registered:</span>
                      <strong>8</strong>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Predictions Made:</span>
                      <strong>12</strong>
                    </div>
                    <div className="d-flex justify-content-between">
                      <span>Vet Consultations:</span>
                      <strong>5</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-md-8">
                {/* Profile Details */}
                <div className="card mb-4">
                  <div className="card-header">
                    <h5 className="mb-0">Registration Details</h5>
                  </div>
                  <div className="card-body">
                    <div className="row mb-3">
                      <div className="col-md-6">
                        <label className="form-label"><strong>Full Name</strong></label>
                        <p>{user.full_name || 'Not provided'}</p>
                      </div>
                      <div className="col-md-6">
                        <label className="form-label"><strong>Email Address</strong></label>
                        <p>{user.email}</p>
                      </div>
                    </div>
                    <div className="row mb-3">
                      <div className="col-md-6">
                        <label className="form-label"><strong>Phone Number</strong></label>
                        <p>{user.phone || 'Not provided'}</p>
                      </div>
                      <div className="col-md-6">
                        <label className="form-label"><strong>Registration Date</strong></label>
                        <p>{strftime(user.registration_date, '%B %d, %Y')}</p>
                      </div>
                    </div>
                    <div className="row mb-3">
                      <div className="col-md-12">
                        <label className="form-label"><strong>Farm Address/Location</strong></label>
                        <p>{user.location || 'Not provided'}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Farm Information */}
                <div className="card mb-4">
                  <div className="card-header">
                    <h5 className="mb-0">Farm &amp; Animal Information</h5>
                  </div>
                  <div className="card-body">
                    <div className="row mb-3">
                      <div className="col-md-12">
                        <label className="form-label"><strong>Farm Name</strong></label>
                        <p>{user.farm_name || 'Not provided'}</p>
                      </div>
                    </div>
                    <div className="row mb-3">
                      <div className="col-md-6">
                        <label className="form-label"><strong>Primary Animal Types</strong></label>
                        <div className="d-flex flex-wrap gap-2">
                          {user.animal_types ? (
                            user.animal_types.split(',').map((animalType, index) => (
                              <span key={index} className="badge bg-secondary text-capitalize">{animalType}</span>
                            ))
                          ) : (
                            <span className="text-muted small">None specified</span>
                          )}
                        </div>
                      </div>
                      <div className="col-md-6">
                        <label className="form-label"><strong>Production Focus</strong></label>
                        <p className="text-capitalize">{user.production_focus || 'Not provided'}</p>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-md-12">
                        <label className="form-label"><strong>Assigned Veterinarians</strong></label>
                        {assigned_vets.length > 0 ? (
                          assigned_vets.map((vet, index) => (
                            <div key={index} className="alert alert-info py-2 mb-2">
                              <i className="bi bi-person-heart"></i> <strong>{text(vet.full_name)}</strong><br />
                              <small>Phone: {vet.phone || 'N/A'} | Email: {vet.email}</small>
                            </div>
                          ))
                        ) : (
                          <div className="alert alert-light py-2 border">
                            <small className="text-muted">No veterinarian assigned yet.</small>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Settings */}
                <div className="card">
                  <div className="card-header">
                    <h5 className="mb-0">Account Settings</h5>
                  </div>
                  <div className="card-body">
                    <div className="list-group">
                      <a href="#" className="list-group-item list-group-item-action" data-bs-toggle="modal" data-bs-target="#changePasswordModal">
                        <i className="bi bi-key"></i> Change Password
                      </a>
                      <a href="#" className="list-group-item list-group-item-action">
                        <i className="bi bi-bell"></i> Notification Settings
                      </a>
                      <a href="#" className="list-group-item list-group-item-action">
                        <i className="bi bi-shield-check"></i> Privacy Settings
                      </a>
                      <a href="#" className="list-group-item list-group-item-action text-danger">
                        <i className="bi bi-trash"></i> Deactivate Account
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Edit Profile Modal */}
            <div className="modal fade" id="editProfileModal" tabIndex={-1}>
              <div className="modal-dialog modal-lg">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">Edit Profile</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <FlaskForm action={routes.farmerRegistration}>
                    <HiddenTag form={form} />
                    <div className="modal-body">
                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.full_name} className="form-label" />
                          <Field field={f.full_name} className="form-control" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.email} className="form-label" />
                          <Field field={f.email} className="form-control" />
                        </div>
                      </div>
                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.phone} className="form-label" />
                          <Field field={f.phone} className="form-control" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.farm_name} className="form-label" />
                          <Field field={f.farm_name} className="form-control" />
                        </div>
                      </div>
                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.animal_types} className="form-label" />
                          <Field field={f.animal_types} className="form-select" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.production_focus} className="form-label" />
                          <Field field={f.production_focus} className="form-select" />
                        </div>
                      </div>
                      <div className="mb-3">
                        <Label field={f.location} className="form-label" />
                        <Field field={f.location} className="form-select" />
                      </div>
                    </div>
                    <div className="modal-footer">
                      <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                      <Field field={f.submit} className="btn btn-primary" />
                    </div>
                  </FlaskForm>
                </div>
              </div>
            </div>

            {/* Change Password Modal */}
            <div className="modal fade" id="changePasswordModal" tabIndex={-1}>
              <div className="modal-dialog">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">Change Password</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div className="modal-body">
                    <form>
                      <div className="mb-3">
                        <label className="form-label">Current Password</label>
                        <input type="password" className="form-control" />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">New Password</label>
                        <input type="password" className="form-control" />
                      </div>
                      <div className="mb-3">
                        <label className="form-label">Confirm New Password</label>
                        <input type="password" className="form-control" />
                      </div>
                    </form>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" className="btn btn-primary">Update Password</button>
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
