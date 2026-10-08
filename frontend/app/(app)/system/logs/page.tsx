'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { SysAdminSidebar } from '@/components/sidebar/Sidebar';
import { processingOnSubmit } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { strftime, text, thousands } from '@/lib/utils/format';
import type { SystemLog } from '@/types/models';

interface SystemLogsContext {
  logs: SystemLog[];
  total_logs: number;
  error_count: number;
  warning_count: number;
  current_level: string;
  current_component: string;
  current_time_range: string;
}

const PAGE_STYLES = `
.log-entry { margin-bottom: 5px; padding: 3px 0; border-bottom: 1px solid #333; }
.log-entry.info { color: #17a2b8; }
.log-entry.warning { color: #ffc107; }
.log-entry.error, .log-entry.critical { color: #dc3545; }
.log-entry.debug { color: #6c757d; }
.log-time { color: #6c757d; margin-right: 10px; }
.log-level { margin-right: 10px; font-size: 10px; }
.log-component { color: #20c997; margin-right: 10px; }
`;

function levelBadge(level: string | null): string {
  if (level === 'error' || level === 'critical') return 'danger';
  if (level === 'warning') return 'warning';
  return level === 'debug' ? 'secondary' : 'info';
}

// templates/system_admin/system_logs.html
export default function SystemLogsPage() {
  return (
    <FlaskPage<SystemLogsContext>
      title="System Logs - Mzimba North VetAssistant"
      sidebar={<SysAdminSidebar active="logs" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-journal-text"></i> System Logs &amp; Monitoring</h2>
          </div>

          {/* Log Filters */}
          <div className="card mb-4">
            <div className="card-body">
              <form className="row g-3" method="GET" action={routes.systemLogs} onSubmit={processingOnSubmit}>
                <div className="col-md-3">
                  <label className="form-label">Log Level</label>
                  <select className="form-select" name="level" defaultValue={ctx.current_level}>
                    <option value="all">All Levels</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                    <option value="critical">Critical</option>
                    <option value="debug">Debug</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label">Component</label>
                  <select className="form-select" name="component" defaultValue={ctx.current_component}>
                    <option value="all">All Components</option>
                    <option value="web">Web Server</option>
                    <option value="api">API Gateway</option>
                    <option value="db">Database</option>
                    <option value="model">Prediction Model</option>
                    <option value="prediction">Prediction</option>
                    <option value="auth">Authentication</option>
                    <option value="review">Review</option>
                    <option value="mortality">Mortality</option>
                    <option value="system">System</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label">Time Range</label>
                  <select className="form-select" name="time_range" defaultValue={ctx.current_time_range}>
                    <option value="1h">Last 1 hour</option>
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label">&nbsp;</label>
                  <button type="submit" className="btn btn-primary w-100">
                    <i className="bi bi-filter"></i> Apply Filters
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Log Statistics */}
          <div className="row mb-4">
            <div className="col-md-4">
              <div className="card">
                <div className="card-body text-center">
                  <h6>Logs Shown</h6>
                  <h4 className="text-primary">{thousands(ctx.total_logs)}</h4>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card">
                <div className="card-body text-center">
                  <h6>Errors</h6>
                  <h4 className="text-danger">{ctx.error_count}</h4>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card">
                <div className="card-body text-center">
                  <h6>Warnings</h6>
                  <h4 className="text-warning">{ctx.warning_count}</h4>
                </div>
              </div>
            </div>
          </div>

          {/* Log Viewer */}
          <div className="card mb-4">
            <div className="card-header">
              <h5 className="mb-0">Log Entries</h5>
            </div>
            <div className="card-body">
              <div className="log-container" style={{ height: '480px', overflowY: 'auto', backgroundColor: '#1e1e1e', color: '#d4d4d4', padding: '15px', borderRadius: '5px', fontFamily: "'Courier New', monospace", fontSize: '12px' }}>
                {ctx.logs.length > 0 ? (
                  ctx.logs.map((log) => (
                    <div key={log.id} className={`log-entry ${text(log.level)}`}>
                      <span className="log-time">[{log.timestamp ? strftime(log.timestamp, '%Y-%m-%d %H:%M:%S') : '--'}]</span>{' '}
                      <span className={`log-level badge bg-${levelBadge(log.level)}`}>{(log.level || 'info').toUpperCase()}</span>{' '}
                      <span className="log-component">[{(log.component || 'system').toUpperCase()}]</span>{' '}
                      <span className="log-message">{text(log.message)}{log.ip_address && ` (IP ${log.ip_address})`}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted py-5">No log entries match the selected filters.</div>
                )}
              </div>
            </div>
          </div>

          <style>{PAGE_STYLES}</style>
        </>
      )}
    </FlaskPage>
  );
}
