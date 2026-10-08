'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { OrgAdminSidebar } from '@/components/sidebar/Sidebar';
import { ChartCanvas } from '@/components/charts/ChartCanvas';
import { FlaskForm, processingOnSubmit } from '@/components/forms/FlaskForm';
import { Field, HiddenTag, Label } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import { pyFloat, round, strftime, text } from '@/lib/utils/format';
import type { FormData_ } from '@/types/api';
import type { GeneratedReport } from '@/types/models';

interface ReportsContext {
  form: FormData_;
  reports: GeneratedReport[];
  disease_labels: string[];
  disease_values: number[];
  /** (disease name, case count) */
  disease_rows: [string, number][];
  location_disease_summary: { location: string; disease_name: string; frequency: number }[];
  trend_labels: string[];
  trend_values: number[];
  veterinarian_summary: {
    full_name: string;
    service_location: string;
    status: string;
    reviewed_predictions_count: number;
    assigned_farmers_count: number;
  }[];
  location_options: string[];
  f_location: string;
  f_animal: string;
  f_days: number;
}

const PALETTE = ['#1a4a2e', '#2c7744', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6', '#10b981', '#6c757d'];

// templates/organization_admin/reports.html
export default function OrgReportsPage() {
  return (
    <FlaskPage<ReportsContext>
      title="Reports & Analytics - Mzimba North VetAssistant"
      sidebar={<OrgAdminSidebar active="reports" />}
    >
      {(ctx) => {
        const f = ctx.form.fields;
        const total = ctx.disease_values.reduce((sum, value) => sum + value, 0);
        const pdfQuery = new URLSearchParams({ location: ctx.f_location, animal_type: ctx.f_animal, days: String(ctx.f_days) });
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
              <h2><i className="bi bi-bar-chart"></i> Reports &amp; Analytics</h2>
              <div className="d-flex gap-2">
                <a href={`${routes.orgReportsPdf}?${pdfQuery}`} className="btn btn-danger">
                  <i className="bi bi-file-earmark-pdf"></i> Export PDF
                </a>
                <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#generateReportModal">
                  <i className="bi bi-plus-circle"></i> Generate Report
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
              <div className="card-body">
                <form className="row g-3 align-items-end" method="GET" action={routes.orgReports} onSubmit={processingOnSubmit}>
                  <div className="col-md-4">
                    <label className="form-label small fw-bold text-muted">Location (Block)</label>
                    <select className="form-select" name="location" defaultValue={ctx.f_location}>
                      <option value="all">All blocks</option>
                      {ctx.location_options.map((location) => <option key={location} value={location}>{location}</option>)}
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label small fw-bold text-muted">Animal Type</label>
                    <select className="form-select" name="animal_type" defaultValue={ctx.f_animal}>
                      <option value="all">All species</option>
                      <option value="cattle">Cattle</option>
                      <option value="goat">Goat</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label small fw-bold text-muted">Period</label>
                    <select className="form-select" name="days" defaultValue={String(ctx.f_days)}>
                      <option value="7">Last 7 days</option>
                      <option value="14">Last 14 days</option>
                      <option value="30">Last 30 days</option>
                      <option value="90">Last 90 days</option>
                      <option value="365">Last year</option>
                    </select>
                  </div>
                  <div className="col-md-2">
                    <button type="submit" className="btn btn-outline-primary w-100"><i className="bi bi-funnel"></i> Apply</button>
                  </div>
                </form>
              </div>
            </div>

            {/* Most Frequent Diseases (trend) */}
            <div className="row g-4 mb-4">
              <div className="col-lg-7">
                <div className="card h-100">
                  <div className="card-header"><h6 className="mb-0">Most Frequent Diseases (Last {ctx.f_days} days)</h6></div>
                  <div className="card-body">
                    {ctx.disease_labels.length > 0 ? (
                      <ChartCanvas
                        id="diseaseChart"
                        height={220}
                        config={{
                          type: 'bar',
                          data: {
                            labels: ctx.disease_labels,
                            datasets: [{ label: 'Cases', data: ctx.disease_values, backgroundColor: PALETTE }],
                          },
                          options: {
                            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                            plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } },
                          },
                        }}
                      />
                    ) : (
                      <p className="text-muted text-center py-5 mb-0">No predictions for the selected filters.</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="col-lg-5">
                <div className="card h-100">
                  <div className="card-header"><h6 className="mb-0">Ranking</h6></div>
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table table-sm">
                        <thead><tr><th>#</th><th>Disease</th><th>Cases</th><th>Share</th></tr></thead>
                        <tbody>
                          {ctx.disease_rows.length > 0 ? (
                            ctx.disease_rows.map(([name, count], index) => (
                              <tr key={name}>
                                <td>{index + 1}</td>
                                <td>{name}</td>
                                <td>{count}</td>
                                <td>{total ? pyFloat(round((count / total) * 100, 1)) : 0}%</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan={4} className="text-center text-muted py-3">No data.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Disease Trend */}
            <div className="card mb-4">
              <div className="card-header"><h6 className="mb-0">Disease Trend Over Time</h6></div>
              <div className="card-body">
                {ctx.trend_labels.length > 0 ? (
                  <ChartCanvas
                    id="trendChart"
                    height={90}
                    config={{
                      type: 'line',
                      data: {
                        labels: ctx.trend_labels,
                        datasets: [{
                          label: 'Predictions', data: ctx.trend_values,
                          borderColor: '#2c7744', backgroundColor: 'rgba(44,119,68,0.15)',
                          fill: true, tension: 0.3,
                        }],
                      },
                      options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                      },
                    }}
                  />
                ) : (
                  <p className="text-muted text-center py-4 mb-0">Not enough data to show a trend for the selected filters.</p>
                )}
              </div>
            </div>

            {/* Available Reports */}
            <div className="card mb-4">
              <div className="card-header">
                <h5 className="mb-0">Generated Reports</h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Report ID</th>
                        <th>Type</th>
                        <th>Period</th>
                        <th>Generated</th>
                        <th>Schedule</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ctx.reports.length > 0 ? (
                        ctx.reports.map((r) => (
                          <tr key={r.id}>
                            <td><strong>{r.report_id}</strong></td>
                            <td><span className="badge bg-primary text-capitalize">{text(r.report_type)}</span></td>
                            <td>
                              {r.period_start ? strftime(r.period_start, '%Y-%m-%d') : '--'}
                              {' '}&ndash;{' '}
                              {r.period_end ? strftime(r.period_end, '%Y-%m-%d') : '--'}
                            </td>
                            <td>{r.generated_at ? strftime(r.generated_at, '%Y-%m-%d %H:%M') : '--'}</td>
                            <td>
                              {r.is_scheduled ? (
                                <span className="badge bg-info text-capitalize">{text(r.schedule_frequency)}</span>
                              ) : (
                                <span className="badge bg-secondary">Once</span>
                              )}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="text-center text-muted py-4">No reports generated yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Dominant disease by location */}
            <div className="row g-4 mb-4">
              <div className="col-12">
                <div className="card h-100">
                  <div className="card-header"><h6 className="mb-0">Dominant Disease by Location (Last {ctx.f_days} days)</h6></div>
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table table-sm">
                        <thead>
                          <tr><th>Location</th><th>Most Common Disease</th><th>Cases</th></tr>
                        </thead>
                        <tbody>
                          {ctx.location_disease_summary.length > 0 ? (
                            ctx.location_disease_summary.map((row, index) => (
                              <tr key={index}>
                                <td>{row.location}</td>
                                <td>{row.disease_name}</td>
                                <td>{row.frequency}</td>
                              </tr>
                            ))
                          ) : (
                            <tr><td colSpan={3} className="text-center text-muted py-3">No data yet.</td></tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Veterinarian performance */}
            <div className="card">
              <div className="card-header"><h5 className="mb-0">Veterinarian Activity</h5></div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-sm table-hover">
                    <thead>
                      <tr>
                        <th>Veterinarian</th>
                        <th>Service Location</th>
                        <th>Status</th>
                        <th>Reviews Completed</th>
                        <th>Assigned Farmers</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ctx.veterinarian_summary.length > 0 ? (
                        ctx.veterinarian_summary.map((v, index) => (
                          <tr key={index}>
                            <td>{v.full_name}</td>
                            <td>{v.service_location}</td>
                            <td><span className={`badge bg-${v.status === 'approved' ? 'success' : 'secondary'} text-capitalize`}>{v.status}</span></td>
                            <td>{v.reviewed_predictions_count}</td>
                            <td>{v.assigned_farmers_count}</td>
                          </tr>
                        ))
                      ) : (
                        <tr><td colSpan={5} className="text-center text-muted py-3">No veterinarians registered yet.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Generate Report Modal */}
            <div className="modal fade" id="generateReportModal" tabIndex={-1}>
              <div className="modal-dialog modal-lg">
                <FlaskForm className="modal-content" action={routes.orgReports}>
                  <HiddenTag form={ctx.form} />
                  <div className="modal-header">
                    <h5 className="modal-title">Generate Report</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div className="modal-body">
                    <div className="row g-3">
                      <div className="col-md-6">
                        <Label field={f.report_name} className="form-label" />
                        <Field field={f.report_name} className="form-control" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.report_type} className="form-label" />
                        <Field field={f.report_type} className="form-select" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.animal_type} className="form-label" />
                        <Field field={f.animal_type} className="form-select" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.output_format} className="form-label" />
                        <Field field={f.output_format} className="form-select" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.period_start} className="form-label" />
                        <Field field={f.period_start} className="form-control" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.period_end} className="form-label" />
                        <Field field={f.period_end} className="form-control" />
                      </div>
                      <div className="col-md-6">
                        <Label field={f.schedule_frequency} className="form-label" />
                        <Field field={f.schedule_frequency} className="form-select" />
                      </div>
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <Field field={f.submit} className="btn btn-primary" />
                  </div>
                </FlaskForm>
              </div>
            </div>
          </>
        );
      }}
    </FlaskPage>
  );
}
