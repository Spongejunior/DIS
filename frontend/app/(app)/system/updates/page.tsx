'use client';

import { FlaskPage } from '@/components/layout/FlaskPage';
import { SysAdminSidebar } from '@/components/sidebar/Sidebar';
import { capitalize, percent, strftime, thousands } from '@/lib/utils/format';

interface ModelUpdatesContext {
  available_updates: {
    id: string;
    version: string;
    type: string;
    size: number | null;
    status: string;
    accuracy: number | null;
    deployment_date: string | null;
  }[];
}

// templates/system_admin/model_updates.html
export default function ModelUpdatesPage() {
  return (
    <FlaskPage<ModelUpdatesContext>
      title="Model Updates - Mzimba North VetAssistant"
      sidebar={<SysAdminSidebar active="updates" />}
    >
      {({ available_updates }) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-cloud-arrow-up"></i> Prediction Model Versions</h2>
          </div>

          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Registered Models</h5>
            </div>
            <div className="card-body">
              <div className="table-responsive">
                <table className="table table-hover align-middle">
                  <thead>
                    <tr>
                      <th>Version</th>
                      <th>Algorithm</th>
                      <th>Accuracy</th>
                      <th>Training Samples</th>
                      <th>Deployed</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {available_updates.length > 0 ? (
                      available_updates.map((m) => (
                        <tr key={m.id}>
                          <td className="fw-bold">{m.version}</td>
                          <td>{m.type}</td>
                          <td>{m.accuracy !== null ? `${percent(m.accuracy)}%` : '--'}</td>
                          <td>{m.size !== null ? thousands(m.size) : '--'}</td>
                          <td>{m.deployment_date ? strftime(m.deployment_date, '%Y-%m-%d') : '--'}</td>
                          <td>
                            <span className={`badge bg-${m.status === 'production' ? 'success' : m.status === 'staging' ? 'info' : 'secondary'}`}>
                              {capitalize(m.status)}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="text-center text-muted py-5">No model versions registered yet.</td>
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
