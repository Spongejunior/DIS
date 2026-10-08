'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { important } from '@/lib/utils/dom';
import { percent, strftime, text, title, unsnake } from '@/lib/utils/format';
import type { Notification, Prediction, UserBrief, UserLookup } from '@/types/models';

interface FarmerDashboardContext {
  total_reports: number;
  pending_predictions: number;
  recent_predictions: Prediction[];
  notifications: Notification[];
  notification_senders: UserLookup;
  assigned_vets: UserBrief[];
}

function StatCard({ color, label, value, tint, icon }: { color: string; label: string; value: number; tint: string; icon: string }) {
  return (
    <div className="card h-100 border-0 shadow-sm" ref={important({ 'border-left': `4px solid ${color}` })}>
      <div className="card-body">
        <div className="d-flex justify-content-between">
          <div>
            <p className="text-muted small fw-bold text-uppercase mb-1">{label}</p>
            <h3 className="fw-bold mb-0">{value}</h3>
          </div>
          <div className={`${tint} bg-opacity-10 p-2 rounded-3`}>
            <i className={`bi ${icon} fs-4`}></i>
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/farmer/dashboard.html
export default function FarmerDashboardPage() {
  return (
    <FlaskPage<FarmerDashboardContext>
      title="Dashboard - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="solid" active="dashboard" />}
    >
      {(ctx, page) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">Welcome back, {page.user?.username}!</h3>
              <p className="text-muted">Here&apos;s what&apos;s happening on your farm today.</p>
            </div>
            <Link href={routes.symptomForm} className="btn btn-primary shadow-sm">
              <i className="bi bi-plus-lg me-2"></i>New Report
            </Link>
          </div>

          <div className="row g-4 mb-4">
            {/* Stats Cards */}
            <div className="col-md-3">
              <StatCard color="#f59e0b" label="Pending" value={ctx.pending_predictions} tint="bg-warning" icon="bi-hourglass-split text-warning" />
            </div>
            <div className="col-md-3">
              <StatCard color="#10b981" label="Total Reports" value={ctx.total_reports} tint="bg-success" icon="bi-file-earmark-text text-success" />
            </div>
            <div className="col-md-3">
              <StatCard color="#3b82f6" label="Predictions" value={ctx.recent_predictions.length} tint="bg-primary" icon="bi-graph-up text-primary" />
            </div>
            <div className="col-md-3">
              <Link href={routes.farmerNotifications} className="text-decoration-none">
                <StatCard color="#8b5cf6" label="Alerts" value={ctx.notifications.length} tint="bg-info" icon="bi-bell text-info" />
              </Link>
            </div>
          </div>

          <div className="row g-4">
            {/* Recent Predictions */}
            <div className="col-lg-8">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-header bg-white py-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="fw-bold mb-0">Recent Predictions</h5>
                    <Link href={routes.farmerPredictions} className="btn btn-sm btn-light">View All</Link>
                  </div>
                </div>
                <div className="card-body p-0">
                  <div className="table-responsive">
                    <table className="table table-hover align-middle mb-0">
                      <thead className="bg-light">
                        <tr>
                          <th className="px-4 py-3">Animal</th>
                          <th className="py-3">Disease</th>
                          <th className="py-3">Confidence</th>
                          <th className="py-3 text-end px-4">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ctx.recent_predictions.length > 0 ? (
                          ctx.recent_predictions.map((pred) => (
                            <tr key={pred.id}>
                              <td className="px-4">
                                <div className="d-flex align-items-center">
                                  <div className="bg-light p-2 rounded-circle me-3">
                                    <i className="bi bi-activity text-primary"></i>
                                  </div>
                                  <div>
                                    <div className="fw-bold">{pred.symptom_report ? text(pred.symptom_report.animal_name) : '--'}</div>
                                    <div className="small text-muted">{pred.symptom_report ? text(pred.symptom_report.animal_type) : '--'}</div>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span className="badge bg-danger bg-opacity-10 text-danger px-3 py-2 rounded-pill">
                                  {text(pred.disease_name)}
                                </span>
                              </td>
                              <td>
                                <div className="d-flex align-items-center">
                                  <div className="progress flex-grow-1 me-2" style={{ height: '6px' }}>
                                    <div className="progress-bar bg-success" role="progressbar" data-width={percent(pred.confidence)} style={{ width: `${percent(pred.confidence)}%` }}></div>
                                  </div>
                                  <span className="small fw-bold">{percent(pred.confidence)}%</span>
                                </div>
                              </td>
                              <td className="text-end px-4">
                                <button className="btn btn-sm btn-outline-primary rounded-pill px-3">Details</button>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={4} className="text-center py-5">
                              <img src="https://illustrations.popsy.co/gray/data-analysis.svg" alt="No data" style={{ width: '120px' }} className="mb-3" />
                              <p className="text-muted">No recent predictions found.</p>
                              <Link href={routes.symptomForm} className="btn btn-sm btn-primary">Report Symptoms Now</Link>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions & Notifications */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-white py-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="fw-bold mb-0">Notifications</h5>
                    <Link href={routes.farmerNotifications} className="btn btn-sm btn-light">View All</Link>
                  </div>
                </div>
                <div className="card-body p-0">
                  <div className="list-group list-group-flush">
                    {ctx.notifications.length > 0 ? (
                      ctx.notifications.map((note) => {
                        const sender = note.sender_id ? ctx.notification_senders[String(note.sender_id)] : undefined;
                        const dot = note.priority === 'high' || note.priority === 'critical' ? 'danger' : note.priority === 'medium' ? 'warning' : 'primary';
                        return (
                          <Link key={note.id} href={note.action_url || routes.farmerNotifications} className="list-group-item list-group-item-action border-0 px-4 py-3 text-decoration-none">
                            <div className="d-flex align-items-center mb-1">
                              <span className={`badge bg-${dot} rounded-circle p-1 me-2`}></span>
                              <h6 className="fw-bold mb-0 small">{text(note.title)}</h6>
                              <small className="text-muted ms-auto">{note.created_at ? strftime(note.created_at, '%H:%M') : '--'}</small>
                            </div>
                            <div className="small text-muted mb-1">
                              {title(unsnake(note.notification_type))}
                              {sender && <> &middot; from {sender.full_name || sender.username}</>}
                            </div>
                            <p className="text-muted small mb-0">{text(note.message)}</p>
                          </Link>
                        );
                      })
                    ) : (
                      <div className="p-4 text-center">
                        <p className="text-muted mb-0 small">No new notifications.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="card border-0 shadow-sm bg-primary text-white">
                <div className="card-body p-4">
                  <h5 className="fw-bold mb-3">Need Assistance?</h5>
                  <p className="small opacity-75 mb-4">
                    {ctx.assigned_vets.length > 0
                      ? 'Send a message to your assigned veterinarian directly from the platform.'
                      : 'You do not have an assigned veterinarian yet.'}
                  </p>
                  {ctx.assigned_vets.length > 0 && (
                    <div className="small mb-3 opacity-75">
                      Assigned vet{ctx.assigned_vets.length > 1 ? 's' : ''}:{' '}
                      {ctx.assigned_vets.map((vet) => vet.full_name || vet.username).join(', ')}
                    </div>
                  )}
                  <div className="d-grid">
                    <button className="btn btn-light fw-bold" data-bs-toggle="modal" data-bs-target="#vetContactModal" disabled={ctx.assigned_vets.length === 0}>
                      <i className="bi bi-chat-text-fill me-2"></i>Contact Vet
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Modal remains the same but styled */}
          <div className="modal fade" id="vetContactModal" tabIndex={-1}>
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content border-0 shadow">
                <FlaskForm action={routes.contactVet}>
                  <div className="modal-header border-0 pb-0">
                    <h5 className="modal-title fw-bold">Contact Veterinarian</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div className="modal-body p-4">
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Subject</label>
                      <input type="text" name="subject" className="form-control border-0 bg-light" maxLength={200} placeholder="Reason for your message" />
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Your Message</label>
                      <textarea name="message" className="form-control border-0 bg-light" rows={4} placeholder="Describe your concern in detail..." required></textarea>
                    </div>
                  </div>
                  <div className="modal-footer border-0 pt-0">
                    <button type="button" className="btn btn-light px-4" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" className="btn btn-primary px-4">Send Message</button>
                  </div>
                </FlaskForm>
              </div>
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
