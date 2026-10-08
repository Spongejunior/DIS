'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { routes } from '@/lib/api/routes';
import { capitalize, percent, pyFloat, strftime, text } from '@/lib/utils/format';
import type { Prediction, SymptomReport } from '@/types/models';

interface SymptomHistoryContext {
  /** (report, its prediction or none) */
  reports: [SymptomReport, Prediction | null][];
  page: number;
  per_page: number;
}

function ReportDetailsModal({ report, pred }: { report: SymptomReport; pred: Prediction | null }) {
  return (
    <div className="modal fade" id={`detailsModal${report.id}`} tabIndex={-1}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Report Details: {report.report_id}</h5>
            <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div className="modal-body">
            <div className="row">
              <div className="col-md-6">
                <h6>Animal Information</h6>
                <p className="mb-1"><strong>Name:</strong> {text(report.animal_name)}</p>
                <p className="mb-1"><strong>Type:</strong> {capitalize(report.animal_type)}</p>
                <p className="mb-1"><strong>Sex:</strong> {report.animal_sex ? capitalize(report.animal_sex) : '--'}</p>
                <p className="mb-1"><strong>Age:</strong> {report.animal_age || '--'} months</p>
                <p className="mb-0"><strong>Temperature:</strong> {report.temperature ? pyFloat(report.temperature) : '--'}°C</p>
              </div>
              <div className="col-md-6">
                <h6>Report Information</h6>
                <p className="mb-1"><strong>Date:</strong> {report.created_at ? strftime(report.created_at, '%Y-%m-%d %H:%M') : '--'}</p>
                <p className="mb-1"><strong>Status:</strong> <span className="badge bg-secondary text-capitalize">{text(report.status)}</span></p>
                <p className="mb-0"><strong>Prediction:</strong>{' '}
                  {pred ? `${text(pred.disease_name)} (${percent(pred.confidence)}%)` : 'Awaiting analysis'}
                </p>
              </div>
            </div>
            <hr />
            <h6>Symptoms Reported</h6>
            {report.symptoms.length > 0 ? (
              <ul className="mb-0">
                {report.symptoms.map((symptom, index) => <li key={index}>{symptom}</li>)}
              </ul>
            ) : (
              <p className="text-muted mb-0">No symptoms recorded.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/farmer/symptom_history.html
export default function SymptomHistoryPage() {
  return (
    <FlaskPage<SymptomHistoryContext>
      title="Symptom History - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="outline" active="history" />}
    >
      {({ reports }) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-clock-history"></i> Symptom History &amp; Records</h2>
            <Link href={routes.symptomForm} className="btn btn-primary">
              <i className="bi bi-plus-circle"></i> New Report
            </Link>
          </div>

          {/* Reports Table */}
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Symptom Reports</h5>
            </div>
            <div className="card-body">
              <div className="table-responsive">
                {/* Per-report details modals. The template wrote them between table
                    rows, where the browser moves them out to just before the table. */}
                {reports.map(([report, pred]) => <ReportDetailsModal key={report.id} report={report} pred={pred} />)}

                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th>Report ID</th>
                      <th>Date</th>
                      <th>Animal</th>
                      <th>Symptoms</th>
                      <th>Status</th>
                      <th>Prediction</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.length > 0 ? (
                      reports.map(([report, pred]) => (
                        <tr key={report.id}>
                          <td>{report.report_id}</td>
                          <td>{report.created_at ? strftime(report.created_at, '%Y-%m-%d') : ''}</td>
                          <td>{text(report.animal_name)}</td>
                          <td>{report.additional_symptoms ? report.symptoms.join(', ') : '--'}</td>
                          <td>
                            {report.status === 'reviewed' ? (
                              <span className="badge bg-success">Resolved</span>
                            ) : report.status === 'predicted' ? (
                              <span className="badge bg-secondary">Pending</span>
                            ) : (
                              <span className="badge bg-light text-dark">{text(report.status)}</span>
                            )}
                          </td>
                          <td>{pred ? `${text(pred.disease_name)} (${percent(pred.confidence)}%)` : 'Awaiting Analysis'}</td>
                          <td>
                            <button className="btn btn-sm btn-outline-info" type="button" data-bs-toggle="modal" data-bs-target={`#detailsModal${report.id}`}>
                              <i className="bi bi-eye"></i> View
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="text-center py-5 text-muted">
                          No symptom reports found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
            </div>
          </div>
        </>
      )}
    </FlaskPage>
  );
}
