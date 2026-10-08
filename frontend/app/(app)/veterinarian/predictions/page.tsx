'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm, processingOnSubmit } from '@/components/forms/FlaskForm';
import { routes } from '@/lib/api/routes';
import { capitalize, confidenceColor, percent, pyFloat, round, strftime, text } from '@/lib/utils/format';
import type { Prediction } from '@/types/models';

interface PredictionReviewContext {
  pending_predictions: Prediction[];
  reviewed_predictions: Prediction[];
  f_severity: string;
  f_animal: string;
  f_confidence: string;
}

function PendingCard({ p }: { p: Prediction }) {
  const report = p.symptom_report;
  const conf = percent(p.confidence);
  const severe = p.severity === 'critical' || p.severity === 'severe';
  return (
    <>
      <div className="col-md-4 mb-4">
        <div className="card h-100 border-warning">
          <div className="card-header bg-warning text-dark">
            <div className="d-flex justify-content-between align-items-center">
              <h6 className="mb-0">Review Needed</h6>
              <span className={`badge bg-${severe ? 'danger' : 'secondary'}`}>{capitalize(p.severity)}</span>
            </div>
          </div>
          <div className="card-body">
            <div className="d-flex justify-content-between mb-2">
              <small className="text-muted">Prediction ID: {p.prediction_id}</small>
              <small className="text-muted">{p.predicted_at ? strftime(p.predicted_at, '%Y-%m-%d %H:%M') : ''}</small>
            </div>

            <h6>{text(p.disease_name)}</h6>
            <div className="mb-3">
              <div className="progress" style={{ height: '20px' }}>
                <div className={`progress-bar bg-${confidenceColor(round(p.confidence * 100, 1))}`} data-width={conf} style={{ width: `${conf}%` }}>{conf}% Confidence</div>
              </div>
            </div>

            <div className="mb-3">
              <p className="mb-1"><strong>Farmer:</strong> {report?.farmer ? text(report.farmer.full_name) : '--'}</p>
              <p className="mb-1"><strong>Animal:</strong> {text(report?.animal_name)}</p>
              <p className="mb-1"><strong>Sex / Age:</strong> {report?.animal_sex ? capitalize(report.animal_sex) : '--'} / {report?.animal_age || '--'} months</p>
            </div>

            <div className="mb-3">
              <h6>Reported Symptoms:</h6>
              <div className="d-flex flex-wrap gap-1">
                {report && report.symptoms.length > 0 ? (
                  report.symptoms.map((symptom, index) => <span key={index} className="badge bg-secondary">{symptom}</span>)
                ) : (
                  <span className="text-muted small">None recorded</span>
                )}
              </div>
            </div>

            {p.possible.length > 1 && (
              <div className="mb-3">
                <h6>Other possibilities:</h6>
                <p className="small mb-0">
                  {p.possible.slice(1).map((d) => `${d.disease} (${percent(d.probability)}%)`).join(', ')}
                </p>
              </div>
            )}

            <div className="alert alert-info py-2 mb-0">
              <small><i className="bi bi-thermometer-high"></i> <strong>Temperature:</strong> {report?.temperature ? pyFloat(report.temperature) : '--'}°C</small>
            </div>
          </div>
          <div className="card-footer">
            <div className="d-grid gap-2">
              <Link className="btn btn-primary" href={routes.addTreatment(p.id)}>
                <i className="bi bi-capsule"></i> Add Treatment
              </Link>
              <Link className="btn btn-outline-info" href={routes.predictionDetail(p.id)}>
                <i className="bi bi-eye"></i> View Details
              </Link>
              <button className="btn btn-success" data-bs-toggle="modal" data-bs-target={`#confirmModal${p.id}`}>
                <i className="bi bi-check-circle"></i> Confirm Prediction
              </button>
              <button className="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target={`#modifyModal${p.id}`}>
                <i className="bi bi-pencil"></i> Modify Diagnosis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirm Modal */}
      <div className="modal fade" id={`confirmModal${p.id}`} tabIndex={-1}>
        <div className="modal-dialog">
          <FlaskForm className="modal-content" action={routes.reviewPrediction(p.id)}>
            <input type="hidden" name="action" value="confirm" readOnly />
            <div className="modal-header">
              <h5 className="modal-title">Confirm Prediction</h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div className="modal-body">
              <p>Confirm the AI prediction of <strong>{text(p.disease_name)}</strong> for {text(report?.animal_name)}?</p>
              <p className="small text-muted">A treatment plan will be created and the farmer will be notified.</p>
              <div className="mb-3">
                <label className="form-label">Add Notes (Optional)</label>
                <textarea className="form-control" name="notes" rows={3} placeholder="Add any additional notes..."></textarea>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" className="btn btn-success">Confirm Diagnosis</button>
            </div>
          </FlaskForm>
        </div>
      </div>

      {/* Modify Modal */}
      <div className="modal fade" id={`modifyModal${p.id}`} tabIndex={-1}>
        <div className="modal-dialog">
          <FlaskForm className="modal-content" action={routes.reviewPrediction(p.id)}>
            <input type="hidden" name="action" value="modify" readOnly />
            <div className="modal-header">
              <h5 className="modal-title">Modify Diagnosis</h5>
              <button type="button" className="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div className="modal-body">
              <div className="mb-3">
                <label className="form-label">Revised Diagnosis</label>
                <input type="text" className="form-control" name="diagnosis" defaultValue={text(p.disease_name)} required />
              </div>
              <div className="mb-3">
                <label className="form-label">Notes (Optional)</label>
                <textarea className="form-control" name="notes" rows={3} placeholder="Reason for change..."></textarea>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" className="btn btn-warning">Save Diagnosis</button>
            </div>
          </FlaskForm>
        </div>
      </div>
    </>
  );
}

// templates/veterinarian/prediction_review.html
export default function PredictionReviewPage() {
  return (
    <FlaskPage<PredictionReviewContext>
      title="Review Predictions - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="reviews" />}
    >
      {(ctx) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-clipboard-check"></i> Disease Predictions Review</h2>
            <span className="badge bg-warning text-dark fs-6">{ctx.pending_predictions.length} pending</span>
          </div>

          {/* Filters */}
          <div className="card mb-4">
            <div className="card-body">
              <form className="row g-3 align-items-end" method="GET" action={routes.predictionsReview} onSubmit={processingOnSubmit}>
                <div className="col-md-3">
                  <label className="form-label">Severity</label>
                  <select className="form-select" name="severity" defaultValue={ctx.f_severity}>
                    <option value="all">All severities</option>
                    <option value="critical">Critical</option>
                    <option value="severe">Severe</option>
                    <option value="moderate">Moderate</option>
                    <option value="mild">Mild</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label">Confidence Level</label>
                  <select className="form-select" name="confidence" defaultValue={ctx.f_confidence}>
                    <option value="all">All levels</option>
                    <option value="high">High (&ge;90%)</option>
                    <option value="medium">Medium (70-90%)</option>
                    <option value="low">Low (&lt;70%)</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label">Animal Type</label>
                  <select className="form-select" name="animal_type" defaultValue={ctx.f_animal}>
                    <option value="all">All species</option>
                    <option value="cattle">Cattle</option>
                    <option value="goat">Goat</option>
                  </select>
                </div>
                <div className="col-md-3 d-flex gap-2">
                  <button type="submit" className="btn btn-primary flex-grow-1"><i className="bi bi-funnel"></i> Apply</button>
                  <Link href={routes.predictionsReview} className="btn btn-outline-secondary">Reset</Link>
                </div>
              </form>
            </div>
          </div>

          {/* Pending Reviews */}
          <div className="row">
            {ctx.pending_predictions.length > 0 ? (
              ctx.pending_predictions.map((p) => <PendingCard key={p.id} p={p} />)
            ) : (
              <div className="col-12">
                <div className="alert alert-success">
                  <i className="bi bi-check-circle"></i> No predictions pending review. You&apos;re all caught up!
                </div>
              </div>
            )}
          </div>

          {/* Reviewed Predictions */}
          <div className="card mt-4">
            <div className="card-header">
              <h5 className="mb-0">Recently Reviewed Predictions</h5>
            </div>
            <div className="card-body">
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Farmer</th>
                      <th>Prediction</th>
                      <th>Confidence</th>
                      <th>Your Diagnosis</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ctx.reviewed_predictions.length > 0 ? (
                      ctx.reviewed_predictions.map((p) => (
                        <tr key={p.id}>
                          <td>{p.reviewed_at ? strftime(p.reviewed_at, '%Y-%m-%d') : '--'}</td>
                          <td>{p.symptom_report?.farmer ? text(p.symptom_report.farmer.full_name) : '--'}</td>
                          <td>{text(p.disease_name)}</td>
                          <td>{percent(p.confidence)}%</td>
                          <td>{p.review_status === 'modified' ? `Modified to: ${text(p.disease_name)}` : 'Confirmed'}</td>
                          <td>
                            <span className={`badge bg-${p.review_status === 'confirmed' ? 'success' : 'info'}`}>{capitalize(p.review_status)}</span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="text-center text-muted py-4">No reviewed predictions yet.</td>
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
