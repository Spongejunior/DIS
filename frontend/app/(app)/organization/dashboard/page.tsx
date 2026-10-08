'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { OrgAdminSidebar } from '@/components/sidebar/Sidebar';
import { ChartCanvas } from '@/components/charts/ChartCanvas';
import { routes } from '@/lib/api/routes';
import { strftime, text } from '@/lib/utils/format';
import type { SystemLog } from '@/types/models';

interface OrgDashboardContext {
  total_farmers: number;
  total_veterinarians: number;
  active_predictions: number;
  system_accuracy: number | null;
  recent_logs: SystemLog[];
  location_labels: string[];
  location_values: number[];
}

function StatCard({ color, heading, value, caption, icon }: { color: string; heading: string; value: string | number; caption: string; icon: string }) {
  return (
    <div className="col-md-6 col-xl-3">
      <div className={`card stat-card text-white bg-${color} h-100`}>
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h6 className="card-title">{heading}</h6>
              <h2 className="mb-1">{value}</h2>
              <small>{caption}</small>
            </div>
            <i className={`bi ${icon}`} style={{ fontSize: '2rem' }}></i>
          </div>
        </div>
      </div>
    </div>
  );
}

function logBadge(level: string | null): string {
  if (level === 'critical' || level === 'error') return 'danger';
  return level === 'warning' ? 'warning text-dark' : 'success';
}

// templates/organization_admin/dashboard.html
export default function OrgAdminDashboardPage() {
  return (
    <FlaskPage<OrgDashboardContext>
      title="Organization Admin Dashboard - Mzimba North VetAssistant"
      sidebar={<OrgAdminSidebar active="dashboard" />}
    >
      {(ctx, page) => {
        const accuracy = ctx.system_accuracy !== null ? `${(ctx.system_accuracy * 100).toFixed(1)}%` : 'N/A';
        const accuracyWidth = ctx.system_accuracy !== null ? (ctx.system_accuracy * 100).toFixed(0) : '0';
        return (
          <>
            <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center mb-4 gap-3">
              <div>
                <h2 className="mb-1"><i className="bi bi-speedometer2"></i> Organization Admin Dashboard</h2>
                <p className="text-muted mb-0">Monitor user activity, predictions, and core system health from one place.</p>
              </div>
              <div className="btn-group">
                <Link href={routes.orgReports} className="btn btn-outline-primary">
                  <i className="bi bi-bar-chart"></i> View Reports
                </Link>
                <Link href={routes.orgAdminUsers} className="btn btn-primary">
                  <i className="bi bi-people"></i> Manage Users
                </Link>
              </div>
            </div>

            <div className="row g-4 mb-4">
              <StatCard color="primary" heading="Farmers" value={ctx.total_farmers} caption="Registered farmer accounts" icon="bi-person-hearts" />
              <StatCard color="success" heading="Veterinarians" value={ctx.total_veterinarians} caption="Active veterinary users" icon="bi-shield-plus" />
              <StatCard color="warning" heading="Active Predictions" value={ctx.active_predictions} caption="Awaiting follow-up or review" icon="bi-activity" />
              <StatCard color="info" heading="System Accuracy" value={accuracy} caption="Latest tracked prediction accuracy" icon="bi-graph-up-arrow" />
            </div>

            <div className="row g-4">
              <div className="col-lg-7">
                <div className="card mb-4">
                  <div className="card-header d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Farmer Distribution (Mzuzu Areas)</h5>
                  </div>
                  <div className="card-body">
                    <ChartCanvas
                      id="locationChart"
                      height={250}
                      config={{
                        type: 'bar',
                        data: {
                          labels: ctx.location_labels,
                          datasets: [{
                            label: 'Number of Farmers',
                            data: ctx.location_values,
                            backgroundColor: 'rgba(26, 74, 46, 0.7)',
                            borderColor: 'rgba(26, 74, 46, 1)',
                            borderWidth: 1,
                            borderRadius: 5,
                          }],
                        },
                        options: {
                          responsive: true,
                          maintainAspectRatio: false,
                          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                          plugins: { legend: { display: false } },
                        },
                      }}
                    />
                  </div>
                </div>

                <div className="card h-100">
                  <div className="card-header d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Operational Snapshot</h5>
                    <span className="badge bg-light text-dark">{page.user?.username}</span>
                  </div>
                  <div className="card-body">
                    <div className="mb-4">
                      <div className="d-flex justify-content-between mb-1">
                        <span>Prediction accuracy</span>
                        <strong>{accuracy}</strong>
                      </div>
                      <div className="progress" style={{ height: '10px' }}>
                        <div className="progress-bar bg-success" role="progressbar" data-width={accuracyWidth} style={{ width: `${accuracyWidth}%` }}></div>
                      </div>
                    </div>
                    <div className="row text-center g-3">
                      <div className="col-md-4">
                        <div className="border rounded-3 p-3 h-100">
                          <div className="text-muted small mb-1">Users Monitored</div>
                          <div className="fs-4 fw-bold">{ctx.total_farmers + ctx.total_veterinarians}</div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="border rounded-3 p-3 h-100">
                          <div className="text-muted small mb-1">Recent Logs</div>
                          <div className="fs-4 fw-bold">{ctx.recent_logs.length}</div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="border rounded-3 p-3 h-100">
                          <div className="text-muted small mb-1">Review Focus</div>
                          <div className="fs-4 fw-bold">{ctx.active_predictions}</div>
                        </div>
                      </div>
                    </div>

                    <hr />

                    <div className="row g-3">
                      <div className="col-md-6">
                        <Link href={routes.orgAdminProfile} className="btn btn-outline-secondary w-100 quick-action-btn">
                          <i className="bi bi-person-badge"></i> Open Profile
                        </Link>
                      </div>
                      <div className="col-md-6">
                        <Link href={routes.orgAdminUsers} className="btn btn-outline-secondary w-100 quick-action-btn">
                          <i className="bi bi-people"></i> Review Users
                        </Link>
                      </div>
                      <div className="col-md-6">
                        <Link href={routes.orgReports} className="btn btn-outline-primary w-100 quick-action-btn">
                          <i className="bi bi-file-earmark-bar-graph"></i> Analytics Reports
                        </Link>
                      </div>
                      <div className="col-md-6">
                        {/* A plain link: it reloads this page, which is what "Refresh" did */}
                        <a href={routes.orgAdminDashboard} className="btn btn-outline-primary w-100 quick-action-btn">
                          <i className="bi bi-arrow-repeat"></i> Refresh Overview
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-lg-5">
                <div className="card h-100">
                  <div className="card-header">
                    <h5 className="mb-0">Recent System Activity</h5>
                  </div>
                  <div className="card-body">
                    {ctx.recent_logs.length > 0 ? (
                      <div className="list-group list-group-flush">
                        {ctx.recent_logs.map((log) => (
                          <div key={log.id} className="list-group-item px-0">
                            <div className="d-flex justify-content-between align-items-start gap-3">
                              <div>
                                <div className="fw-semibold text-capitalize">{log.component || 'system'}</div>
                                <div className="small text-muted">{text(log.message)}</div>
                              </div>
                              <div className="text-end">
                                <span className={`badge bg-${logBadge(log.level)} text-uppercase`}>
                                  {log.level || 'info'}
                                </span>
                                <div className="small text-muted mt-1">{strftime(log.timestamp, '%d %b %Y %H:%M')}</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="alert alert-primary mb-0">
                        No recent system logs are available yet.
                      </div>
                    )}
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
