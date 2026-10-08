'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { routes } from '@/lib/api/routes';
import { capitalize, priorityBadge, strftime, text } from '@/lib/utils/format';
import type { Notification, UserBrief, UserLookup } from '@/types/models';

interface CommunicationsContext {
  incoming_messages: Notification[];
  sent_alerts: Notification[];
  scheduled_meetings: Notification[];
  message_senders: UserLookup;
  alert_recipients: UserLookup;
  meeting_recipients: UserLookup;
}

function personName(person: UserBrief | undefined): string {
  return person ? person.full_name || person.username : 'Assigned farmer';
}

function sentAt(note: Notification): string {
  return note.created_at ? strftime(note.created_at, '%d %b %Y %H:%M') : '--';
}

function Column({ heading, empty, children }: { heading: string; empty: string; children: ReactNode[] }) {
  return (
    <div className="col-lg-4">
      <div className="card border-0 shadow-sm h-100">
        <div className="card-header bg-white py-3">
          <h5 className="fw-bold mb-0">{heading}</h5>
        </div>
        <div className="card-body p-0">
          <div className="list-group list-group-flush">
            {children.length > 0 ? children : <div className="p-4 text-center text-muted">{empty}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/veterinarian/communications.html
export default function VetCommunicationsPage() {
  return (
    <FlaskPage<CommunicationsContext>
      title="Communications - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="communications" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-3 mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">Communications</h3>
              <p className="text-muted mb-0">Review incoming farmer messages, sent alerts, and scheduled meetings.</p>
            </div>
            <div className="btn-group">
              <Link href={routes.vetDashboard} className="btn btn-outline-secondary">
                <i className="bi bi-arrow-left me-2"></i>Back to Dashboard
              </Link>
            </div>
          </div>

          <div className="row g-4 mb-4">
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body">
                  <div className="text-muted small fw-bold text-uppercase mb-2">Incoming Messages</div>
                  <div className="display-6 fw-bold">{ctx.incoming_messages.length}</div>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body">
                  <div className="text-muted small fw-bold text-uppercase mb-2">Sent Alerts</div>
                  <div className="display-6 fw-bold text-primary">{ctx.sent_alerts.length}</div>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-body">
                  <div className="text-muted small fw-bold text-uppercase mb-2">Scheduled Meetings</div>
                  <div className="display-6 fw-bold text-success">{ctx.scheduled_meetings.length}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="row g-4">
            <Column heading="Incoming Farmer Messages" empty="No farmer messages yet.">
              {ctx.incoming_messages.map((note) => (
                <div key={note.id} className="list-group-item border-0 px-4 py-3">
                  <div className="fw-semibold">{text(note.title)}</div>
                  <div className="small text-muted mb-1">
                    From {personName(note.sender_id ? ctx.message_senders[String(note.sender_id)] : undefined)}
                  </div>
                  <p className="text-muted mb-1">{text(note.message)}</p>
                  <div className="small text-muted">{sentAt(note)}</div>
                </div>
              ))}
            </Column>

            <Column heading="Sent Alerts" empty="No alerts sent yet.">
              {ctx.sent_alerts.map((note) => (
                <div key={note.id} className="list-group-item border-0 px-4 py-3">
                  <div className="d-flex justify-content-between align-items-start gap-2">
                    <div>
                      <div className="fw-semibold">{text(note.title)}</div>
                      <div className="small text-muted">To {personName(ctx.alert_recipients[String(note.user_id)])}</div>
                    </div>
                    <span className={`badge bg-${priorityBadge(note.priority)}`}>
                      {capitalize(note.priority)}
                    </span>
                  </div>
                  <p className="text-muted mb-1 mt-2">{text(note.message)}</p>
                  <div className="small text-muted">{sentAt(note)}</div>
                </div>
              ))}
            </Column>

            <Column heading="Scheduled Meetings" empty="No meetings scheduled yet.">
              {ctx.scheduled_meetings.map((note) => (
                <div key={note.id} className="list-group-item border-0 px-4 py-3">
                  <div className="fw-semibold">{text(note.title)}</div>
                  <div className="small text-muted mb-1">With {personName(ctx.meeting_recipients[String(note.user_id)])}</div>
                  <p className="text-muted mb-1">{text(note.message)}</p>
                  <div className="small text-muted">{sentAt(note)}</div>
                </div>
              ))}
            </Column>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
