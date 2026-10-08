'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { routes } from '@/lib/api/routes';
import { capitalize, priorityBadge, strftime, text, title, unsnake } from '@/lib/utils/format';
import type { Notification, UserBrief } from '@/types/models';

interface NotificationDetailContext {
  notification: Notification;
  sender: UserBrief | null;
}

// templates/farmer/notification_detail.html
export default function FarmerNotificationDetailPage() {
  return (
    <FlaskPage<NotificationDetailContext>
      title="Notification Detail - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="solid" active="notifications" />}
    >
      {({ notification, sender }) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">{text(notification.title)}</h3>
              <p className="text-muted mb-0">Notification details and full message.</p>
            </div>
            <Link href={routes.farmerNotifications} className="btn btn-outline-secondary">
              <i className="bi bi-arrow-left me-2"></i>Back to Notifications
            </Link>
          </div>

          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <div className="row g-4 mb-3">
                <div className="col-md-4">
                  <div className="small text-muted fw-bold text-uppercase mb-1">Type</div>
                  <div>{title(unsnake(notification.notification_type))}</div>
                </div>
                <div className="col-md-4">
                  <div className="small text-muted fw-bold text-uppercase mb-1">Priority</div>
                  <div>
                    <span className={`badge bg-${priorityBadge(notification.priority)}`}>
                      {capitalize(notification.priority)}
                    </span>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="small text-muted fw-bold text-uppercase mb-1">Received</div>
                  <div>{notification.created_at ? strftime(notification.created_at, '%d %b %Y %H:%M') : '--'}</div>
                </div>
              </div>

              <div className="mb-3">
                <div className="small text-muted fw-bold text-uppercase mb-1">From</div>
                <div>{sender ? sender.full_name || sender.username : 'System'}</div>
              </div>

              <div>
                <div className="small text-muted fw-bold text-uppercase mb-2">Message</div>
                <div className="p-3 bg-light rounded-3">{text(notification.message)}</div>
              </div>
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
