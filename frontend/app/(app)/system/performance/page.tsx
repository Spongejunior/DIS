'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { SysAdminSidebar } from '@/components/sidebar/Sidebar';
import { percent, roundInt, thousands } from '@/lib/utils/format';

interface PerformanceContext {
  metrics: {
    response_time: number | null;
    error_rate: number;
    cpu_usage: number | null;
    memory_usage: number | null;
    disk_usage: number | null;
    api_success_rate: number;
  };
  api_performance: { endpoint: string; avg_response: number | null; success_rate: number; requests: number }[];
}

function MetricCard({ color, heading, value, caption }: { color: string; heading: string; value: string; caption: string }) {
  return (
    <div className="col-md-3">
      <div className={`card text-white bg-${color} h-100`}>
        <div className="card-body">
          <h6 className="card-title">{heading}</h6>
          <h2 className="mb-0">{value}</h2>
          <small>{caption}</small>
        </div>
      </div>
    </div>
  );
}

function UsageBar({ label, usage, color, last }: { label: string; usage: number | null; color: string; last?: boolean }) {
  const width = usage !== null ? roundInt(usage * 100) : '0';
  return (
    <div className={last ? 'mb-0' : 'mb-3'}>
      <div className="d-flex justify-content-between small fw-bold">
        <span>{label}</span><span>{usage !== null ? `${roundInt(usage * 100)}%` : 'N/A'}</span>
      </div>
      <div className="progress" style={{ height: '18px' }}>
        <div className={`progress-bar bg-${color}`} data-width={width} style={{ width: `${width}%` }}></div>
      </div>
    </div>
  );
}

function usagePercent(usage: number | null): string {
  return usage !== null ? `${percent(usage)}%` : 'N/A';
}

// templates/system_admin/performance_report.html
export default function PerformanceReportsPage() {
  return (
    <FlaskPage<PerformanceContext>
      title="Performance Reports - Mzimba North VetAssistant"
      sidebar={<SysAdminSidebar active="performance" />}
    >
      {({ metrics, api_performance }) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-speedometer2"></i> System Performance</h2>
            <small className="text-muted">Live host metrics &amp; activity from the last 24 hours</small>
          </div>

          {/* Performance Metrics */}
          <div className="row g-3 mb-4">
            <MetricCard color="primary" heading="CPU Usage" value={usagePercent(metrics.cpu_usage)} caption="Current host load" />
            <MetricCard color="info" heading="Memory Usage" value={usagePercent(metrics.memory_usage)} caption="Current host RAM" />
            <MetricCard color="warning" heading="Disk Usage" value={usagePercent(metrics.disk_usage)} caption="Application volume" />
            <MetricCard color="success" heading="Error Rate (24h)" value={`${percent(metrics.error_rate, 2)}%`} caption={`Success: ${percent(metrics.api_success_rate, 2)}%`} />
          </div>

          {/* Resource Utilization bars */}
          <div className="card mb-4">
            <div className="card-header"><h5 className="mb-0">Resource Utilization</h5></div>
            <div className="card-body">
              <UsageBar label="CPU" usage={metrics.cpu_usage} color="success" />
              <UsageBar label="Memory" usage={metrics.memory_usage} color="info" />
              <UsageBar label="Disk" usage={metrics.disk_usage} color="warning" last />
            </div>
          </div>

          {/* Activity by component (from system logs, last 24h) */}
          <div className="card">
            <div className="card-header"><h5 className="mb-0">Activity by Component (Last 24h)</h5></div>
            <div className="card-body">
              <div className="table-responsive">
                <table className="table table-sm table-hover">
                  <thead>
                    <tr>
                      <th>Component</th>
                      <th>Events</th>
                      <th>Success Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {api_performance.length > 0 ? (
                      api_performance.map((row, index) => (
                        <tr key={index}>
                          <td className="text-capitalize">{row.endpoint}</td>
                          <td>{thousands(row.requests)}</td>
                          <td>{percent(row.success_rate)}%</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="text-center text-muted py-4">No logged activity in the last 24 hours.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
