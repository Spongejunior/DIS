'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm, processingOnSubmit } from '@/components/forms/FlaskForm';
import { Field, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_ } from '@/types/api';
import type { Treatment } from '@/types/models';

interface TreatmentSuggestionsContext {
  form: FormData_;
  pending_treatments: Treatment[];
  active_treatments: Treatment[];
}

function farmerName(t: Treatment): string {
  // `{{ t.symptom_report.farmer.full_name if ... else '--' }}`
  if (!t.symptom_report?.farmer) return '--';
  return t.symptom_report.farmer.full_name ?? 'None';
}

// templates/veterinarian/treatment_suggestions.html
export default function TreatmentSuggestionsPage() {
  return (
    <FlaskPage<TreatmentSuggestionsContext>
      title="Treatment Suggestions - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="treatments" />}
    >
      {({ form, pending_treatments, active_treatments }) => {
        const f = form.fields;
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2><i className="bi bi-capsule"></i> Treatment Suggestions &amp; Management</h2>
              <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#newTreatmentModal">
                <i className="bi bi-plus-circle"></i> New Treatment Plan
              </button>
            </div>

            {/* Pending Treatment Approvals */}
            <div className="card mb-4">
              <div className="card-header bg-warning">
                <h5 className="mb-0"><i className="bi bi-clock-history"></i> Pending Treatment Approvals</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Case ID</th>
                        <th>Farmer</th>
                        <th>Animal</th>
                        <th>Medication</th>
                        <th>Dosage</th>
                        <th>Duration</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pending_treatments.length > 0 ? (
                        pending_treatments.map((t) => (
                          <tr key={t.id}>
                            <td>{t.symptom_report ? t.symptom_report.report_id : '--'}</td>
                            <td>{farmerName(t)}</td>
                            <td>{t.symptom_report ? t.symptom_report.animal_name ?? 'None' : '--'}</td>
                            <td>{t.medication || '--'}</td>
                            <td>{t.dosage || '--'}</td>
                            <td>{t.duration || '--'}</td>
                            <td>
                              {/* Posts straight to the existing JSON endpoint, as the template did */}
                              <form method="POST" action={routes.approveTreatment(t.id)} className="d-inline" onSubmit={processingOnSubmit}>
                                <button type="submit" className="btn btn-sm btn-success">
                                  <i className="bi bi-check"></i> Approve
                                </button>
                              </form>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="text-center text-muted py-4">
                            <i className="bi bi-inbox"></i> No treatments are awaiting approval.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="row">
              {/* Active Treatments */}
              <div className="col-md-8">
                <div className="card">
                  <div className="card-header">
                    <h5 className="mb-0">Active Treatment Plans</h5>
                  </div>
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead>
                          <tr>
                            <th>Treatment ID</th>
                            <th>Farmer</th>
                            <th>Animal</th>
                            <th>Medication</th>
                            <th>Frequency</th>
                            <th>Duration</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {active_treatments.length > 0 ? (
                            active_treatments.map((t) => (
                              <tr key={t.id}>
                                <td>{t.treatment_id || '--'}</td>
                                <td>{farmerName(t)}</td>
                                <td>{t.symptom_report ? t.symptom_report.animal_name ?? 'None' : '--'}</td>
                                <td>{t.medication || '--'}</td>
                                <td>{t.frequency || '--'}</td>
                                <td>{t.duration || '--'}</td>
                                <td><span className="badge bg-warning">{t.status || '--'}</span></td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={7} className="text-center text-muted py-4">
                                <i className="bi bi-clipboard-x"></i> No active treatment plans.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>

              {/* Treatment Database & Quick Actions */}
              <div className="col-md-4">
                {/* Quick Add Treatment */}
                <div className="card">
                  <div className="card-header">
                    <h5 className="mb-0">Quick Actions</h5>
                  </div>
                  <div className="card-body">
                    <div className="d-grid gap-2">
                      <button className="btn btn-outline-primary" data-bs-toggle="modal" data-bs-target="#newTreatmentModal">
                        <i className="bi bi-plus-circle"></i> New Treatment Plan
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* New Treatment Plan Modal */}
            <div className="modal fade" id="newTreatmentModal" tabIndex={-1}>
              <div className="modal-dialog modal-lg">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">Create New Treatment Plan</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <FlaskForm action={routes.treatmentSuggestions}>
                    <HiddenTag form={form} />
                    <div className="modal-body">
                      <div className="mb-3">
                        <Label field={f.medication} className="form-label" />
                        <Field field={f.medication} className="form-control" />
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.medication_type} className="form-label" />
                          <Field field={f.medication_type} className="form-select" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.route} className="form-label" />
                          <Field field={f.route} className="form-select" />
                        </div>
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-4">
                          <Label field={f.dosage} className="form-label" />
                          <Field field={f.dosage} className="form-control" />
                        </div>
                        <div className="col-md-4">
                          <Label field={f.dosage_per_kg} className="form-label" />
                          <Field field={f.dosage_per_kg} className="form-control" />
                        </div>
                        <div className="col-md-4">
                          <Label field={f.duration} className="form-label" />
                          <Field field={f.duration} className="form-control" />
                        </div>
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.frequency} className="form-label" />
                          <Field field={f.frequency} className="form-select" />
                        </div>
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.milk_withdrawal_days} className="form-label" />
                          <Field field={f.milk_withdrawal_days} className="form-control" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.meat_withdrawal_days} className="form-label" />
                          <Field field={f.meat_withdrawal_days} className="form-control" />
                        </div>
                      </div>

                      <div className="mb-3">
                        <Label field={f.supportive_care} className="form-label" />
                        <Field field={f.supportive_care} className="form-control" rows={3} />
                      </div>

                      <div className="mb-3">
                        <Label field={f.diet_recommendations} className="form-label" />
                        <Field field={f.diet_recommendations} className="form-control" rows={3} />
                      </div>

                      <div className="mb-3 form-check">
                        <Field field={f.follow_up_required} className="form-check-input" />{' '}
                        <Label field={f.follow_up_required} className="form-check-label" />
                      </div>

                      <div className="mb-3">
                        <Label field={f.follow_up_date} className="form-label" />
                        <Field field={f.follow_up_date} className="form-control" />
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
          </>
        );
      }}
    </FlaskPage>
  );
}
