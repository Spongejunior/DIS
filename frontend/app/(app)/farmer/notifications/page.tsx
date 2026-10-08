'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { capitalize, priorityBadge, strftime, text, title, unsnake } from '@/lib/utils/format';
import type { Notification, UserLookup } from '@/types/models';

interface NotificationsContext {
  notifications: Notification[];
  notification_senders: UserLookup;
  unread_count: number;
  total_notifications: number;
  meetings_count: number;
  active_filter: 'all' | 'unread' | 'meeting';
}

// templates/farmer/notifications.html
export default function FarmerNotificationsPage() {
  return (
    <FlaskPage<NotificationsContext>
      title="Notifications - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="solid" active="notifications" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">Notifications</h3>
              <p className="text-muted mb-0">Alerts, meeting schedules, and messages from your veterinarian.</p>
            </div>
            <FlaskForm action={routes.markFarmerNotificationsRead}>
              <button type="submit" className="btn btn-outline-primary" disabled={!ctx.unread_count}>
                <i className="bi bi-check2-all me-2"></i>Mark All Read
              </button>
            </FlaskForm>
          </div>

          <div className="row g-4 mb-4">
            <div className="col-md-4">
              <Link href={`${routes.farmerNotifications}?filter=all`} className="text-decoration-none">
                <div className={`card border-0 shadow-sm h-100 ${ctx.active_filter === 'all' ? 'border border-primary' : ''}`}>
                  <div className="card-body">
                    <div className="text-muted small fw-bold text-uppercase mb-2">Total Notifications</div>
                    <div className="display-6 fw-bold">{ctx.total_notifications}</div>
                  </div>
                </div>
              </Link>
            </div>
            <div className="col-md-4">
              <Link href={`${routes.farmerNotifications}?filter=unread`} className="text-decoration-none">
                <div className={`card border-0 shadow-sm h-100 ${ctx.active_filter === 'unread' ? 'border border-warning' : ''}`}>
                  <div className="card-body">
                    <div className="text-muted small fw-bold text-uppercase mb-2">Unread</div>
                    <div className="display-6 fw-bold text-warning">{ctx.unread_count}</div>
                  </div>
                </div>
              </Link>
            </div>
            <div className="col-md-4">
              <Link href={`${routes.farmerNotifications}?filter=meeting`} className="text-decoration-none">
                <div className={`card border-0 shadow-sm h-100 ${ctx.active_filter === 'meeting' ? 'border border-primary' : ''}`}>
                  <div className="card-body">
                    <div className="text-muted small fw-bold text-uppercase mb-2">Meetings Scheduled</div>
                    <div className="display-6 fw-bold text-primary">{ctx.meetings_count}</div>
                  </div>
                </div>
              </Link>
            </div>
          </div>

          <div className="card border-0 shadow-sm">
            <div className="card-header bg-white py-3">
              <div className="d-flex justify-content-between align-items-center">
                <h5 className="fw-bold mb-0">
                  {ctx.active_filter === 'unread' ? 'Unread Notifications' : ctx.active_filter === 'meeting' ? 'Meeting Notifications' : 'All Notifications'}
                </h5>
                {ctx.active_filter !== 'all' && (
                  <Link href={routes.farmerNotifications} className="btn btn-sm btn-light">Show All</Link>
                )}
              </div>
            </div>
            <div className="card-body p-0">
              <div className="list-group list-group-flush">
                {ctx.notifications.length > 0 ? (
                  ctx.notifications.map((note) => {
                    const sender = note.sender_id ? ctx.notification_senders[String(note.sender_id)] : undefined;
                    return (
                      <Link key={note.id} href={routes.farmerNotificationDetail(note.id)} className="list-group-item list-group-item-action border-0 px-4 py-3 text-decoration-none">
                        <div className="d-flex justify-content-between align-items-start gap-3">
                          <div>
                            <div className="fw-semibold">{text(note.title)}</div>
                            <div className="small text-muted mb-1">
                              {title(unsnake(note.notification_type))}
                              {sender && <> &middot; from {sender.full_name || sender.username}</>}
                              {!note.is_read && <> &middot; <span className="text-warning fw-semibold">Unread</span></>}
                            </div>
                          </div>
                          <span className={`badge bg-${priorityBadge(note.priority)}`}>
                            {capitalize(note.priority)}
                          </span>
                        </div>
                        <p className="text-muted mb-1 mt-2">{text(note.message)}</p>
                        <div className="small text-muted">{note.created_at ? strftime(note.created_at, '%d %b %Y %H:%M') : '--'}</div>
                      </Link>
                    );
                  })
                ) : (
                  <div className="p-5 text-center text-muted">No notifications yet.</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
