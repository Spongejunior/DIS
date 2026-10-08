'use client';

import type { CSSProperties } from 'react';
import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { important } from '@/lib/utils/dom';
import { capitalize, priorityBadge, strftime, text } from '@/lib/utils/format';
import type { MortalityReport, Notification, UserBrief, UserLookup } from '@/types/models';

interface VetDashboardContext {
  assigned_farmers: number;
  assigned_farmer_list: UserBrief[];
  pending_reviews: number;
  active_treatments: number;
  recent_mortality: MortalityReport[];
  farmer_messages: Notification[];
  message_senders: UserLookup;
  sent_alerts_count: number;
  scheduled_meetings_count: number;
}

function StatCard({ color, label, value, tintClass, tintStyle, iconClass, iconStyle }: {
  color: string;
  label: string;
  value: number;
  tintClass: string;
  tintStyle?: CSSProperties;
  iconClass: string;
  iconStyle?: CSSProperties;
}) {
  return (
    <div className="card h-100 border-0 shadow-sm" ref={important({ 'border-left': `4px solid ${color}` })}>
      <div className="card-body">
        <div className="d-flex justify-content-between">
          <div>
            <p className="text-muted small fw-bold text-uppercase mb-1">{label}</p>
            <h3 className="fw-bold mb-0">{value}</h3>
          </div>
          <div className={`${tintClass} bg-opacity-10 p-2 rounded-3`} style={tintStyle}>
            <i className={`bi ${iconClass} fs-4`} style={iconStyle}></i>
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/veterinarian/dashboard.html
export default function VetDashboardPage() {
  return (
    <FlaskPage<VetDashboardContext>
      title="Vet Dashboard - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="dashboard" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">Veterinary Workspace</h3>
              <p className="text-muted">Monitor and review health reports from your assigned farmers.</p>
            </div>
            <div className="btn-group shadow-sm">
              <Link href={routes.vetProfile} className="btn btn-outline-secondary">
                <i className="bi bi-person-circle me-2"></i>My Profile
              </Link>
              <Link href={routes.predictionsReview} className="btn btn-primary">
                <i className="bi bi-eye me-2"></i>Review Cases
              </Link>
            </div>
          </div>

          <div className="row g-4 mb-4">
            {/* Stats Cards */}
            <div className="col-md-3">
              <StatCard color="#ef4444" label="Pending Reviews" value={ctx.pending_reviews} tintClass="bg-danger" iconClass="bi-exclamation-circle text-danger" />
            </div>
            <div className="col-md-3">
              <StatCard color="#3b82f6" label="Assigned Farmers" value={ctx.assigned_farmers} tintClass="bg-primary" iconClass="bi-people text-primary" />
            </div>
            <div className="col-md-3">
              <StatCard color="#10b981" label="Active Treatments" value={ctx.active_treatments} tintClass="bg-success" iconClass="bi-capsule text-success" />
            </div>
            <div className="col-md-3">
              <StatCard
                color="#6366f1"
                label="Mortality Reports"
                value={ctx.recent_mortality.length}
                tintClass="bg-indigo"
                tintStyle={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
                iconClass="bi-activity text-indigo"
                iconStyle={{ color: '#6366f1' }}
              />
            </div>
          </div>

          <div className="row g-4">
            {/* Urgent Cases */}
            <div className="col-lg-8">
              <div className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-white py-3">
                  <h5 className="fw-bold mb-0">High Priority Reviews</h5>
                </div>
                <div className="card-body p-0">
                  <div className="list-group list-group-flush">
                    {ctx.pending_reviews > 0 ? (
                      <div className="p-4 text-center">
                        <i className="bi bi-clipboard-pulse fs-1 text-muted opacity-25 mb-3 d-block"></i>
                        <p className="text-muted mb-3">You have {ctx.pending_reviews} cases awaiting your expert review.</p>
                        <Link href={routes.predictionsReview} className="btn btn-primary px-4 rounded-pill">Start Reviewing</Link>
                      </div>
                    ) : (
                      <div className="p-5 text-center">
                        <i className="bi bi-check-circle-fill text-success fs-1 mb-3 d-block"></i>
                        <h6 className="fw-bold">All caught up!</h6>
                        <p className="text-muted small">No pending predictions require your attention right now.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="card border-0 shadow-sm">
                <div className="card-header bg-white py-3">
                  <h5 className="fw-bold mb-0">Recent Mortality Reports</h5>
                </div>
                <div className="card-body p-0">
                  <div className="table-responsive">
                    <table className="table table-hover align-middle mb-0">
                      <thead className="bg-light">
                        <tr>
                          <th className="px-4 py-3">Animal</th>
                          <th className="py-3">Cause (Suspected)</th>
                          <th className="py-3">Date</th>
                          <th className="py-3 text-end px-4">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ctx.recent_mortality.length > 0 ? (
                          ctx.recent_mortality.map((report) => (
                            <tr key={report.id}>
                              <td className="px-4">
                                <div className="fw-bold">{text(report.animal_name)}</div>
                                <div className="small text-muted">{capitalize(report.animal_type)}{report.breed && <> &middot; {report.breed}</>}</div>
                              </td>
                              <td>
                                <span className="text-danger small fw-bold">{text(report.suspected_cause)}</span>
                                {report.requires_investigation && (
                                  <>{' '}<span className="badge bg-warning text-dark ms-1">Investigate</span></>
                                )}
                              </td>
                              <td>{report.date_of_death ? strftime(report.date_of_death, '%Y-%m-%d') : '--'}</td>
                              <td className="text-end px-4">
                                <Link href={routes.mortalityReports} className="btn btn-sm btn-light">View Report</Link>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={4} className="text-center py-4 text-muted small">No recent mortality reports.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions & Stats */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-white py-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="fw-bold mb-0">Farmer Messages</h5>
                    <Link href={routes.vetCommunications} className="btn btn-sm btn-light">Open Inbox</Link>
                  </div>
                </div>
                <div className="card-body p-0">
                  <div className="list-group list-group-flush">
                    {ctx.farmer_messages.length > 0 ? (
                      ctx.farmer_messages.map((note) => {
                        const sender = note.sender_id ? ctx.message_senders[String(note.sender_id)] : undefined;
                        return (
                          <div key={note.id} className="list-group-item border-0 px-4 py-3">
                            <div className="d-flex justify-content-between align-items-start gap-2">
                              <div>
                                <div className="fw-semibold small">{text(note.title)}</div>
                                <div className="text-muted small">
                                  From {sender ? sender.full_name || sender.username : 'Assigned farmer'}
                                </div>
                              </div>
                              <span className={`badge bg-${priorityBadge(note.priority)}`}>
                                {capitalize(note.priority)}
                              </span>
                            </div>
                            <p className="text-muted small mb-0 mt-2">{text(note.message)}</p>
                            <div className="small text-muted mt-2">{note.created_at ? strftime(note.created_at, '%d %b %Y %H:%M') : '--'}</div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="p-4 text-center">
                        <p className="text-muted mb-0 small">No farmer messages yet.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-white py-3">
                  <h5 className="fw-bold mb-0">Quick Actions</h5>
                </div>
                <div className="card-body">
                  <div className="d-grid gap-2">
                    <Link href={routes.predictionsReview} className="btn btn-outline-primary text-start px-3 py-2">
                      <i className="bi bi-clipboard-check me-2"></i> Review Predictions
                    </Link>
                    <Link href={routes.farmerMapping} className="btn btn-outline-primary text-start px-3 py-2">
                      <i className="bi bi-people me-2"></i> Manage Farmers
                    </Link>
                    <Link href={routes.treatmentSuggestions} className="btn btn-outline-primary text-start px-3 py-2">
                      <i className="bi bi-capsule me-2"></i> Suggest Treatments
                    </Link>
                    <Link href={routes.mortalityReports} className="btn btn-outline-primary text-start px-3 py-2">
                      <i className="bi bi-graph-down me-2"></i> New Mortality Report
                    </Link>
                    <Link href={routes.vetProfile} className="btn btn-outline-primary text-start px-3 py-2">
                      <i className="bi bi-person-badge me-2"></i> Edit Profile
                    </Link>
                  </div>
                </div>
              </div>

              <div className="card border-0 shadow-sm bg-dark text-white">
                <div className="card-body p-4">
                  <div className="d-flex align-items-center mb-3">
                    <div className="bg-primary p-2 rounded-3 me-3">
                      <i className="bi bi-megaphone-fill fs-4"></i>
                    </div>
                    <h5 className="fw-bold mb-0">Farmer Alerts</h5>
                  </div>
                  <p className="small opacity-75 mb-4">Send health alerts or advice to all your assigned farmers at once.</p>
                  <div className="small opacity-75 mb-3">Sent alerts: {ctx.sent_alerts_count} | Meetings: {ctx.scheduled_meetings_count}</div>
                  <div className="d-grid gap-2">
                    <button className="btn btn-primary fw-bold py-2" data-bs-toggle="modal" data-bs-target="#newAnnouncement">
                      Create Broadcast
                    </button>
                    <button className="btn btn-outline-light fw-bold py-2" data-bs-toggle="modal" data-bs-target="#scheduleMeetingModal">
                      Schedule Meeting
                    </button>
                    <Link href={routes.vetCommunications} className="btn btn-light fw-bold py-2">
                      View Sent Alerts
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Send Announcement Modal */}
          <div className="modal fade" id="newAnnouncement" tabIndex={-1}>
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content border-0 shadow">
                <FlaskForm action={routes.sendFarmerAlert}>
                  <div className="modal-header border-0 pb-0">
                    <h5 className="modal-title fw-bold">Broadcast to Farmers</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div className="modal-body p-4">
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Recipients</label>
                      <input type="text" className="form-control border-0 bg-light py-2" value="All Assigned Farmers" readOnly />
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Subject</label>
                      <input type="text" name="subject" className="form-control border-0 bg-light" maxLength={200} placeholder="Example: Urgent disease prevention advice" />
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Alert Level</label>
                      <div className="d-flex gap-2">
                        <input type="radio" className="btn-check" name="priority" id="level1" value="low" defaultChecked />
                        <label className="btn btn-outline-info btn-sm flex-grow-1" htmlFor="level1">Info</label>
                        <input type="radio" className="btn-check" name="priority" id="level2" value="high" />
                        <label className="btn btn-outline-warning btn-sm flex-grow-1" htmlFor="level2">Warning</label>
                        <input type="radio" className="btn-check" name="priority" id="level3" value="critical" />
                        <label className="btn btn-outline-danger btn-sm flex-grow-1" htmlFor="level3">Critical</label>
                      </div>
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Message</label>
                      <textarea name="message" className="form-control border-0 bg-light" rows={4} placeholder="Enter your message here..." required></textarea>
                    </div>
                  </div>
                  <div className="modal-footer border-0 pt-0">
                    <button type="button" className="btn btn-light px-4" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" className="btn btn-primary px-4">Send Broadcast</button>
                  </div>
                </FlaskForm>
              </div>
            </div>
          </div>

          <div className="modal fade" id="scheduleMeetingModal" tabIndex={-1}>
            <div className="modal-dialog modal-dialog-centered">
              <div className="modal-content border-0 shadow">
                <FlaskForm action={routes.scheduleFarmerMeeting}>
                  <div className="modal-header border-0 pb-0">
                    <h5 className="modal-title fw-bold">Schedule Meeting</h5>
                    <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div className="modal-body p-4">
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Assigned Farmer</label>
                      <select name="farmer_id" className="form-select border-0 bg-light" required defaultValue="">
                        <option value="">Select farmer</option>
                        {ctx.assigned_farmer_list.map((farmer) => (
                          <option key={farmer.id} value={farmer.id}>{farmer.full_name || farmer.username}</option>
                        ))}
                      </select>
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Meeting Title</label>
                      <input type="text" name="title" className="form-control border-0 bg-light" maxLength={200} placeholder="Example: Farm health follow-up" />
                    </div>
                    <div className="row g-3">
                      <div className="col-md-6">
                        <label className="form-label fw-bold small text-muted">Date</label>
                        <input type="date" name="meeting_date" className="form-control border-0 bg-light" required />
                      </div>
                      <div className="col-md-6">
                        <label className="form-label fw-bold small text-muted">Time</label>
                        <input type="time" name="meeting_time" className="form-control border-0 bg-light" required />
                      </div>
                    </div>
                    <div className="mt-3 mb-3">
                      <label className="form-label fw-bold small text-muted">Location</label>
                      <input type="text" name="location" className="form-control border-0 bg-light" placeholder="Village, clinic, or farm address" required />
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small text-muted">Notes</label>
                      <textarea name="notes" className="form-control border-0 bg-light" rows={3} placeholder="What should the farmer prepare or bring?"></textarea>
                    </div>
                  </div>
                  <div className="modal-footer border-0 pt-0">
                    <button type="button" className="btn btn-light px-4" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" className="btn btn-primary px-4">Schedule Meeting</button>
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
