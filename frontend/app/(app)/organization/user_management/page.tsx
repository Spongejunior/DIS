'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { OrgAdminSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { strftime, unsnake } from '@/lib/utils/format';
import type { User } from '@/types/models';

interface UserManagementContext {
  users_by_status: { pending: User[]; approved: User[]; rejected: User[] };
  total_users: number;
}

/** The template's `user_status_badge` macro. */
function UserStatusBadge({ status }: { status: string }) {
  if (status === 'approved') return <span className="badge bg-success">Approved</span>;
  if (status === 'rejected') return <span className="badge bg-danger">Rejected</span>;
  return <span className="badge bg-warning text-dark">Pending</span>;
}

/** The template's `user_table` macro. */
function UserTable({ heading, users, emptyMessage, currentUserId }: {
  heading: string;
  users: User[];
  emptyMessage: string;
  currentUserId: number | undefined;
}) {
  return (
    <div className="card mb-4">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h5 className="mb-0">{heading}</h5>
        <span className="badge bg-light text-dark">{users.length} users</span>
      </div>
      <div className="card-body">
        {users.length > 0 ? (
          <div className="table-responsive">
            <table className="table table-hover align-middle">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Email</th>
                  <th>Registered</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const isAdmin = user.role === 'organization_admin' || user.role === 'system_admin';
                  return (
                    <tr key={user.id}>
                      <td>
                        <div className="fw-semibold">{user.full_name || user.username}</div>
                        <div className="small text-muted">@{user.username}</div>
                      </td>
                      <td><span className="badge bg-secondary">{unsnake(user.role)}</span></td>
                      <td>{user.email}</td>
                      <td>{user.registration_date ? strftime(user.registration_date, '%d %b %Y %H:%M') : 'N/A'}</td>
                      <td><UserStatusBadge status={user.status} /></td>
                      <td>
                        {user.last_login ? (
                          <small className="text-muted">{strftime(user.last_login, '%d %b %Y %H:%M')}</small>
                        ) : (
                          <small className="text-muted">Never</small>
                        )}
                      </td>
                      <td className="text-end">
                        <div className="d-flex flex-wrap justify-content-end gap-2">
                          {user.status !== 'approved' && !isAdmin && (
                            <FlaskForm action={routes.approveUser(user.id)}>
                              <button type="submit" className="btn btn-sm btn-success">
                                <i className="bi bi-check-circle"></i> Approve
                              </button>
                            </FlaskForm>
                          )}

                          {user.status !== 'rejected' && !isAdmin && (
                            <FlaskForm action={routes.rejectUser(user.id)}>
                              <button type="submit" className="btn btn-sm btn-warning">
                                <i className="bi bi-x-circle"></i> Reject
                              </button>
                            </FlaskForm>
                          )}

                          {user.id !== currentUserId && user.role !== 'system_admin' && (
                            <FlaskForm action={routes.deleteUser(user.id)} confirmMessage={`Delete ${user.username} permanently?`}>
                              <button type="submit" className="btn btn-sm btn-outline-danger">
                                <i className="bi bi-trash"></i> Delete
                              </button>
                            </FlaskForm>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="alert alert-primary mb-0">{emptyMessage}</div>
        )}
      </div>
    </div>
  );
}

function StatCard({ color, heading, value, caption }: { color: string; heading: string; value: number; caption: string }) {
  return (
    <div className="col-md-3">
      <div className={`card text-white bg-${color} h-100`}>
        <div className="card-body">
          <h6 className="card-title">{heading}</h6>
          <h2 className="mb-1">{value}</h2>
          <small>{caption}</small>
        </div>
      </div>
    </div>
  );
}

// templates/organization_admin/user_management.html
export default function UserManagementPage() {
  return (
    <FlaskPage<UserManagementContext>
      title="User Management - Mzimba North VetAssistant"
      sidebar={<OrgAdminSidebar active="users" />}
    >
      {({ users_by_status, total_users }, page) => (
        <>
          <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center mb-4 gap-3">
            <div>
              <h2 className="mb-1"><i className="bi bi-person-check"></i> User Approval Dashboard</h2>
              <p className="text-muted mb-0">Review registrations, approve access, reject requests, and remove accounts when needed.</p>
            </div>
            <div className="btn-group">
              <Link href={routes.orgAdminProfile} className="btn btn-outline-primary">
                <i className="bi bi-person"></i> My Profile
              </Link>
              <Link href={routes.orgReports} className="btn btn-primary">
                <i className="bi bi-file-earmark-bar-graph"></i> Reports
              </Link>
            </div>
          </div>

          <div className="row g-4 mb-4">
            <StatCard color="primary" heading="Total Users" value={total_users} caption="All registered accounts" />
            <StatCard color="warning" heading="Pending Approval" value={users_by_status.pending.length} caption="Waiting for admin review" />
            <StatCard color="success" heading="Approved" value={users_by_status.approved.length} caption="Allowed to log in" />
            <StatCard color="danger" heading="Rejected" value={users_by_status.rejected.length} caption="Declined registrations" />
          </div>

          <UserTable heading="Pending Users" users={users_by_status.pending} emptyMessage="There are no users waiting for approval right now." currentUserId={page.user?.id} />
          <UserTable heading="Approved Users" users={users_by_status.approved} emptyMessage="There are no approved users yet." currentUserId={page.user?.id} />
          <UserTable heading="Rejected Users" users={users_by_status.rejected} emptyMessage="There are no rejected users." currentUserId={page.user?.id} />
        </>
      )}
    </FlaskPage>
  );
}
