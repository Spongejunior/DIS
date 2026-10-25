'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { CarePlan } from '@/components/predictions/CarePlan';
import { routes } from '@/lib/api/routes';
import { capitalize, confidenceColor, percent, round, strftime, text } from '@/lib/utils/format';
import type { Prediction } from '@/types/models';

function reviewBadge(status: string | null): string {
  if (status === 'confirmed') return 'success';
  return status === 'modified' ? 'info' : 'secondary';
}

function LatestPrediction({ latest }: { latest: Prediction }) {
  const others = latest.possible;
  return (
    <div className="card mb-4">
      <div className="card-header bg-warning text-dark">
        <h5 className="mb-0"><i className="bi bi-exclamation-triangle"></i> Latest Prediction Requiring Attention</h5>
      </div>
      <div className="card-body">
        <div className="alert alert-warning mb-0">
          <div className="d-flex">
            <div className="flex-shrink-0">
              <i className="bi bi-thermometer-high" style={{ fontSize: '2rem' }}></i>
            </div>
            <div className="flex-grow-1 ms-3">
              <h5>AI Prediction: {text(latest.disease_name)}</h5>
              <p>
                <strong>Confidence:</strong> {percent(latest.confidence)}%{' '}
                <span className="ms-2">| <strong>Report ID:</strong> {text(latest.symptom_report?.report_id)}</span>{' '}
                <span className="ms-2">| <strong>Animal:</strong> {text(latest.symptom_report?.animal_name)}</span>
              </p>
              {others.length > 1 && (
                <p className="mb-1"><strong>Other possibilities:</strong>{' '}
                  {others.slice(1).map((d) => `${d.disease} (${percent(d.probability)}%)`).join(', ')}
                </p>
              )}
              {latest.care_plan ? (
                <div className="bg-white rounded p-3 text-dark mb-2">
                  <CarePlan plan={latest.care_plan} compact />
                  <Link href={routes.predictionDetail(latest.id)} className="small">Full care plan, danger signs and sources</Link>
                </div>
              ) : (
                <p>
                  <strong>Recommended Action:</strong>{' '}
                  {latest.recommendation_text || 'Isolate the animal and wait for veterinarian review and prescription.'}
                </p>
              )}
              <div className="mt-2">
                <span className={`badge bg-${reviewBadge(latest.review_status)}`}>
                  Review: {capitalize(latest.review_status)}
                </span>{' '}
                <span className="badge bg-dark">Severity: {capitalize(latest.severity)}</span>
              </div>
              <div className="mt-3">
                <Link href={routes.predictionDetail(latest.id)} className="btn btn-sm btn-primary">
                  <i className="bi bi-eye"></i> View Full Report
                </Link>{' '}
                <a href={routes.predictionPdf(latest.id)} className="btn btn-sm btn-outline-danger">
                  <i className="bi bi-file-earmark-pdf"></i> Download PDF
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// templates/farmer/predictions.html
export default function FarmerPredictionsPage() {
  return (
    <FlaskPage<{ predictions: Prediction[] }>
      title="Disease Predictions - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="outline" active="predictions" />}
    >
      {({ predictions }) => (
        <>
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2><i className="bi bi-graph-up"></i> Disease Predictions &amp; Recommendations</h2>
            <div>
              <button className="btn btn-outline-secondary" onClick={() => window.print()}>
                <i className="bi bi-printer"></i> Print Report
              </button>
            </div>
          </div>

          {predictions.length === 0 ? (
            <div className="alert alert-info" role="alert">
              <i className="bi bi-info-circle"></i> No predictions yet.{' '}
              <Link href={routes.symptomForm} className="alert-link">Submit a symptom report</Link> to receive an AI-powered disease prediction.
            </div>
          ) : (
            <>
              {/* Latest Prediction */}
              <LatestPrediction latest={predictions[0]} />

              {/* Prediction History */}
              <div className="card">
                <div className="card-header">
                  <h5 className="mb-0">Prediction History</h5>
                </div>
                <div className="card-body">
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Animal</th>
                          <th>Prediction</th>
                          <th>Confidence</th>
                          <th>Review Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {predictions.map((p) => {
                          const conf = percent(p.confidence);
                          return (
                            <tr key={p.id}>
                              <td>{p.predicted_at ? strftime(p.predicted_at, '%Y-%m-%d') : '--'}</td>
                              <td>{text(p.symptom_report?.animal_name)}</td>
                              <td>{text(p.disease_name)}</td>
                              <td style={{ minWidth: '140px' }}>
                                <div className="progress" style={{ height: '20px' }}>
                                  <div className={`progress-bar bg-${confidenceColor(round(p.confidence * 100, 1))}`} data-width={conf} style={{ width: `${conf}%` }}>{conf}%</div>
                                </div>
                              </td>
                              <td>
                                {p.review_status === 'confirmed' ? (
                                  <span className="badge bg-success">Confirmed</span>
                                ) : p.review_status === 'modified' ? (
                                  <span className="badge bg-info">Modified</span>
                                ) : (
                                  <span className="badge bg-secondary">Pending Review</span>
                                )}
                              </td>
                              <td className="text-nowrap">
                                <Link href={routes.predictionDetail(p.id)} className="btn btn-sm btn-outline-info" title="View detail"><i className="bi bi-eye"></i></Link>{' '}
                                <a href={routes.predictionPdf(p.id)} className="btn btn-sm btn-outline-danger" title="Download PDF"><i className="bi bi-file-earmark-pdf"></i></a>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </FlaskPage>
  );
}
