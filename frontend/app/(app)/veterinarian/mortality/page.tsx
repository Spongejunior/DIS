'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { Field, FormErrorAlert, HiddenTag, Label } from '@/components/forms/Field';
import { capitalize, strftime } from '@/lib/utils/format';
import type { FormData_ } from '@/types/api';
import type { MortalityReport } from '@/types/models';

interface MortalityContext {
  form: FormData_;
  recent_reports: MortalityReport[];
  monthly_count: number;
}

function StatCard({ color, heading, value, caption }: { color: string; heading: string; value: number; caption: string }) {
  return (
    <div className="col-md-3">
      <div className={`card text-white bg-${color}`}>
        <div className="card-body text-center">
          <h5 className="card-title">{heading}</h5>
          <h2 className="mb-0">{value}</h2>
          <small>{caption}</small>
        </div>
      </div>
    </div>
  );
}

// templates/veterinarian/mortality_reports.html
export default function MortalityReportsPage() {
  return (
    <FlaskPage<MortalityContext>
      title="Mortality Reports - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="mortality" />}
    >
      {({ form, recent_reports, monthly_count }) => {
        const f = form.fields;
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2><i className="bi bi-graph-down"></i> Mortality Reports &amp; Analysis</h2>
              <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#newMortalityReportModal">
                <i className="bi bi-plus-circle"></i> New Mortality Report
              </button>
            </div>

            <FormErrorAlert form={form} title="The mortality report was not saved. Please correct the following:" />

            {/* Mortality Statistics */}
            <div className="row mb-4">
              <StatCard color="danger" heading="Last 30 Days" value={monthly_count} caption="Mortality Cases" />
              <StatCard color="warning" heading="Recent Reports" value={recent_reports.length} caption="On record" />
              <StatCard color="info" heading="Require Investigation" value={recent_reports.filter((r) => r.requires_investigation).length} caption="flagged cases" />
              <StatCard color="success" heading="Dairy Animals" value={recent_reports.filter((r) => r.was_dairy).length} caption="among recent" />
            </div>

            <div className="row">
              {/* Recent Mortality Reports */}
              <div className="col-md-12">
                <div className="card">
                  <div className="card-header bg-danger text-white">
                    <h5 className="mb-0">Recent Mortality Reports</h5>
                  </div>
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Report ID</th>
                            <th>Date</th>
                            <th>Animal</th>
                            <th>Type</th>
                            <th>Suspected Cause</th>
                            <th>Investigation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recent_reports.length > 0 ? (
                            recent_reports.map((r) => (
                              <tr key={r.id}>
                                <td>{r.report_id}</td>
                                <td>{r.date_of_death ? strftime(r.date_of_death, '%Y-%m-%d') : '--'}</td>
                                <td>{r.animal_name || r.animal_id || '--'}</td>
                                <td>{r.animal_type ? capitalize(r.animal_type) : '--'}</td>
                                <td>{r.suspected_cause ? capitalize(r.suspected_cause) : '--'}</td>
                                <td>
                                  {r.requires_investigation ? (
                                    <span className="badge bg-warning">Required</span>
                                  ) : (
                                    <span className="badge bg-success">Not needed</span>
                                  )}
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={6} className="text-center text-muted py-4">
                                No mortality reports recorded yet.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* New Mortality Report Modal */}
            <div className="modal fade" id="newMortalityReportModal" tabIndex={-1}>
              <div className="modal-dialog modal-lg">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">New Mortality Report</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <FlaskForm>
                    <HiddenTag form={form} />
                    <div className="modal-body">
                      <div className="mb-3">
                        <Label field={f.farmer} className="form-label" />
                        <Field field={f.farmer} className="form-select" />
                        {(f.farmer.choices?.length ?? 0) <= 1 && (
                          <div className="form-text">You have no assigned farmers yet.</div>
                        )}
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.animal_type} className="form-label" />
                          <Field field={f.animal_type} className="form-select" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.date_of_death} className="form-label" />
                          <Field field={f.date_of_death} className="form-control" />
                        </div>
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.age} className="form-label" />
                          <Field field={f.age} className="form-control" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.time_of_death} className="form-label" />
                          <Field field={f.time_of_death} className="form-control" />
                        </div>
                      </div>

                      <div className="mb-3">
                        <Label field={f.suspected_cause} className="form-label" />
                        <Field field={f.suspected_cause} className="form-select" />
                      </div>

                      <div className="mb-3">
                        <Label field={f.symptoms_before_death} className="form-label" />
                        <Field field={f.symptoms_before_death} className="form-control" rows={3} />
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.was_predicted} className="form-label" />
                          <Field field={f.was_predicted} className="form-select" />
                        </div>
                        <div className="col-md-6">
                          <Label field={f.treatment_provided} className="form-label" />
                          <Field field={f.treatment_provided} className="form-select" />
                        </div>
                      </div>

                      <div className="row mb-3">
                        <div className="col-md-6">
                          <Label field={f.last_milk_production} className="form-label" />
                          <Field field={f.last_milk_production} className="form-control" />
                        </div>
                      </div>

                      <div className="mb-3">
                        <Label field={f.lab_results} className="form-label" />
                        <Field field={f.lab_results} className="form-control" rows={2} />
                      </div>

                      <div className="mb-3">
                        <Label field={f.additional_notes} className="form-label" />
                        <Field field={f.additional_notes} className="form-control" rows={3} />
                      </div>

                      <div className="form-check mb-2">
                        <Field field={f.was_dairy} className="form-check-input" />{' '}
                        <Label field={f.was_dairy} className="form-check-label" />
                      </div>

                      <div className="form-check mb-2">
                        <Field field={f.lab_samples_taken} className="form-check-input" />{' '}
                        <Label field={f.lab_samples_taken} className="form-check-label" />
                      </div>

                      <div className="form-check mb-3">
                        <Field field={f.requires_investigation} className="form-check-input" />{' '}
                        <Label field={f.requires_investigation} className="form-check-label" />
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
