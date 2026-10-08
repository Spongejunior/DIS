'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { SysAdminSidebar } from '@/components/sidebar/Sidebar';
import { routes } from '@/lib/api/routes';
import { important } from '@/lib/utils/dom';
import { capitalize, percent, roundInt, strftime, text, thousands, unsnake } from '@/lib/utils/format';
import type { SystemLog } from '@/types/models';

interface SysDashboardContext {
  uptime: number;
  active_users: number;
  api_requests: number;
  system_alerts: SystemLog[];
  component_status: Record<string, string>;
  cpu_usage: number | null;
  memory_usage: number | null;
  disk_usage: number | null;
}

function StatCard({ color, label, value, tint, icon }: { color: string; label: string; value: string | number; tint: string; icon: string }) {
  return (
    <div className="col-md-3">
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
    </div>
  );
}

function ResourceBar({ label, usage, color }: { label: string; usage: number | null; color: string }) {
  const width = usage !== null ? roundInt(usage) : '0';
  return (
    <div className="col-md-4">
      <div className="small fw-bold mb-1 d-flex justify-content-between">
        <span>{label}</span>
        <span>{usage !== null ? `${roundInt(usage)}%` : 'N/A'}</span>
      </div>
      <div className="progress rounded-pill" style={{ height: '8px' }}>
        <div className={`progress-bar bg-${color}`} data-width={width} style={{ width: `${width}%` }}></div>
      </div>
    </div>
  );
}

function runSystemDiagnostic() {
  alert('System diagnostic initiated. Results will be logged.');
}

function backupSystem() {
  if (confirm('Create full system backup?')) {
    alert('System backup started.');
  }
}

// templates/system_admin/dashboard.html
export default function SysAdminDashboardPage() {
  return (
    <FlaskPage<SysDashboardContext>
      title="System Admin - Mzimba North VetAssistant"
      sidebar={<SysAdminSidebar active="dashboard" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h3 className="fw-bold mb-0 text-dark">System Infrastructure</h3>
              <p className="text-muted">Real-time monitoring and management of core services.</p>
            </div>
            <div className="btn-group shadow-sm">
              <button className="btn btn-outline-primary px-3" onClick={runSystemDiagnostic}>
                <i className="bi bi-activity me-1"></i> Diagnostic
              </button>
              <button className="btn btn-primary px-3" onClick={backupSystem}>
                <i className="bi bi-shield-check me-1"></i> Backup
              </button>
            </div>
          </div>

          <div className="row g-4 mb-4">
            <StatCard color="#10b981" label="System Uptime" value={`${percent(ctx.uptime)}%`} tint="bg-success" icon="bi-clock-history text-success" />
            <StatCard color="#3b82f6" label="Active Users" value={ctx.active_users} tint="bg-primary" icon="bi-people text-primary" />
            <StatCard color="#f59e0b" label="API Requests" value={thousands(ctx.api_requests)} tint="bg-warning" icon="bi-lightning-charge text-warning" />
            <StatCard color="#ef4444" label="Errors (24h)" value={ctx.system_alerts.length} tint="bg-danger" icon="bi-bug text-danger" />
          </div>

          <div className="row g-4">
            {/* Component Status */}
            <div className="col-lg-8">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-header bg-white py-3">
                  <h5 className="fw-bold mb-0">Component Health</h5>
                </div>
                <div className="card-body">
                  <div className="row g-4">
                    {Object.entries(ctx.component_status).map(([component, status]) => (
                      <div key={component} className="col-md-6">
                        <div className="p-3 border rounded-4 d-flex align-items-center justify-content-between">
                          <div className="d-flex align-items-center">
                            <div className="bg-light p-2 rounded-3 me-3">
                              <i className="bi bi-hdd-network text-secondary"></i>
                            </div>
                            <span className="fw-bold text-capitalize small">{unsnake(component)}</span>
                          </div>
                          <span className={`badge bg-${status === 'running' ? 'success' : status === 'degraded' ? 'warning' : 'danger'} px-3 rounded-pill`}>
                            {status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5">
                    <h6 className="fw-bold mb-3 small text-muted text-uppercase">Resource Allocation</h6>
                    <div className="row g-4">
                      <ResourceBar label="CPU Usage" usage={ctx.cpu_usage} color="success" />
                      <ResourceBar label="Memory Usage" usage={ctx.memory_usage} color="info" />
                      <ResourceBar label="Disk Space" usage={ctx.disk_usage} color="warning" />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* System Alerts */}
            <div className="col-lg-4">
              <div className="card border-0 shadow-sm h-100">
                <div className="card-header bg-white py-3">
                  <h5 className="fw-bold mb-0">Critical Events</h5>
                </div>
                <div className="card-body p-0">
                  <div className="list-group list-group-flush">
                    {ctx.system_alerts.length > 0 ? (
                      ctx.system_alerts.map((alertLog) => (
                        <div key={alertLog.id} className="list-group-item border-0 px-4 py-3">
                          <div className="d-flex align-items-center mb-1">
                            <span className="badge bg-danger p-1 rounded-circle me-2"></span>
                            <h6 className="fw-bold mb-0 small">{capitalize(alertLog.component)} Error</h6>
                            <small className="text-muted ms-auto">{strftime(alertLog.timestamp, '%H:%M')}</small>
                          </div>
                          <p className="text-muted mb-0 small">{text(alertLog.message)}</p>
                        </div>
                      ))
                    ) : (
                      <div className="p-5 text-center">
                        <i className="bi bi-shield-check fs-1 text-success opacity-50 mb-3 d-block"></i>
                        <p className="text-muted small">No critical events in the last 24 hours.</p>
                      </div>
                    )}
                  </div>
                </div>
                <div className="card-footer bg-white border-0 p-3">
                  <Link href={routes.systemLogs} className="btn btn-light w-100 btn-sm fw-bold">View Full Logs</Link>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
