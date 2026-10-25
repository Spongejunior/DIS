'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { PredictionDetailSidebar } from '@/components/sidebar/Sidebar';
import { ChartCanvas } from '@/components/charts/ChartCanvas';
import { CarePlan, TemperatureBadge } from '@/components/predictions/CarePlan';
import { routes } from '@/lib/api/routes';
import { capitalize, confidenceColor, percent, pyFloat, round, strftime, text } from '@/lib/utils/format';
import type { PossibleDisease, Prediction, SymptomReport } from '@/types/models';

interface PredictionDetailContext {
  prediction: Prediction;
  report: SymptomReport;
  possible_diseases: PossibleDisease[];
}

// templates/farmer/prediction_detail.html (shared by farmers, veterinarians and admins)
export default function PredictionDetailPage() {
  return (
    <FlaskPage<PredictionDetailContext>
      title={({ prediction }) => `Prediction ${prediction.prediction_id} - Mzimba North VetAssistant`}
      sidebar={(page) => <PredictionDetailSidebar role={page.user?.role} />}
    >
      {({ prediction, report, possible_diseases }, page) => {
        const conf = percent(prediction.confidence);
        const severe = prediction.severity === 'critical' || prediction.severity === 'severe';
        const reviewColor = prediction.review_status === 'confirmed' ? 'success' : prediction.review_status === 'modified' ? 'info' : 'secondary';
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
              <div>
                <h3 className="fw-bold mb-0">Prediction Report</h3>
                <p className="text-muted mb-0">{prediction.prediction_id} &middot; Report {report.report_id}</p>
              </div>
              <div className="d-flex gap-2">
                {page.user?.role === 'veterinarian' && (
                  <Link href={routes.addTreatment(prediction.id)} className="btn btn-primary">
                    <i className="bi bi-capsule"></i> Add Treatment
                  </Link>
                )}
                <a href={routes.predictionPdf(prediction.id)} className="btn btn-danger">
                  <i className="bi bi-file-earmark-pdf"></i> Download PDF
                </a>
                <a href="#" className="btn btn-light" onClick={(event) => { event.preventDefault(); window.history.back(); }}><i className="bi bi-arrow-left"></i> Back</a>
              </div>
            </div>

            <div className="row g-4">
              {/* Result */}
              <div className="col-lg-7">
                <div className="card border-0 shadow-sm h-100">
                  <div className="card-header bg-white py-3"><h5 className="fw-bold mb-0">AI Prediction</h5></div>
                  <div className="card-body">
                    <div className="d-flex align-items-center mb-3">
                      <div className="bg-light rounded-circle p-3 me-3"><i className="bi bi-activity fs-3 text-primary"></i></div>
                      <div>
                        <h2 className="fw-bold mb-0">{text(prediction.disease_name)}</h2>
                        <div className="text-muted">{capitalize(prediction.disease_category)} condition</div>
                      </div>
                    </div>

                    <div className="mb-2 d-flex justify-content-between small fw-bold">
                      <span>Confidence</span><span>{conf}%</span>
                    </div>
                    <div className="progress mb-3" style={{ height: '22px' }}>
                      <div className={`progress-bar bg-${confidenceColor(round(prediction.confidence * 100, 1))}`} data-width={conf} style={{ width: `${conf}%` }}>{conf}%</div>
                    </div>

                    <div className="d-flex gap-2 flex-wrap">
                      <span className={`badge bg-${severe ? 'danger' : 'secondary'} px-3 py-2`}>Severity: {capitalize(prediction.severity)}</span>
                      <span className={`badge bg-${reviewColor} px-3 py-2`}>Vet review: {capitalize(prediction.review_status)}</span>
                      {prediction.care_plan && <TemperatureBadge temperature={prediction.care_plan.temperature} />}
                      <span className="badge bg-light text-dark px-3 py-2">{prediction.predicted_at ? strftime(prediction.predicted_at, '%Y-%m-%d %H:%M') : '--'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Possible diseases chart */}
              <div className="col-lg-5">
                <div className="card border-0 shadow-sm h-100">
                  <div className="card-header bg-white py-3"><h6 className="fw-bold mb-0">Top Possible Conditions</h6></div>
                  <div className="card-body">
                    {possible_diseases.length > 0 ? (
                      <ChartCanvas
                        id="possibleChart"
                        height={200}
                        config={{
                          type: 'bar',
                          data: {
                            labels: possible_diseases.map((d) => d.disease),
                            datasets: [{
                              label: 'Probability (%)',
                              data: possible_diseases.map((d) => +(d.probability * 100).toFixed(1)),
                              backgroundColor: ['#1a4a2e', '#2c7744', '#f59e0b', '#3b82f6', '#ef4444'].slice(0, possible_diseases.length),
                            }],
                          },
                          options: {
                            indexAxis: 'y',
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: { x: { beginAtZero: true, max: 100 } },
                          },
                        }}
                      />
                    ) : (
                      <p className="text-muted text-center py-4 mb-0">No probability breakdown available.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Animal info */}
              <div className="col-lg-5">
                <div className="card border-0 shadow-sm h-100">
                  <div className="card-header bg-white py-3"><h6 className="fw-bold mb-0">Animal &amp; Case</h6></div>
                  <div className="card-body">
                    <dl className="row mb-0 small">
                      <dt className="col-6 text-muted">Animal</dt><dd className="col-6">{text(report.animal_name)}</dd>
                      <dt className="col-6 text-muted">Species</dt><dd className="col-6 text-capitalize">{text(report.animal_type)}</dd>
                      <dt className="col-6 text-muted">Sex</dt><dd className="col-6 text-capitalize">{report.animal_sex || '--'}</dd>
                      <dt className="col-6 text-muted">Age (months)</dt><dd className="col-6">{report.animal_age !== null ? report.animal_age : '--'}</dd>
                      <dt className="col-6 text-muted">Temperature</dt><dd className="col-6">{report.temperature !== null ? pyFloat(report.temperature) : '--'}&deg;C</dd>
                      <dt className="col-6 text-muted">Status</dt><dd className="col-6 text-capitalize">{text(report.status)}</dd>
                    </dl>
                  </div>
                </div>
              </div>

              {/* Symptoms */}
              <div className="col-lg-7">
                <div className="card border-0 shadow-sm h-100">
                  <div className="card-header bg-white py-3"><h6 className="fw-bold mb-0">Reported Symptoms</h6></div>
                  <div className="card-body">
                    {report.symptoms.length > 0 ? (
                      <div className="d-flex flex-wrap gap-2">
                        {report.symptoms.map((symptom, index) => <span key={index} className="badge bg-secondary px-3 py-2">{symptom}</span>)}
                      </div>
                    ) : (
                      <p className="text-muted mb-0">No symptoms recorded.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Recommendation */}
              <div className="col-12">
                <div className="card border-0 shadow-sm">
                  <div className="card-header bg-white py-3"><h6 className="fw-bold mb-0"><i className="bi bi-lightbulb text-warning"></i> {prediction.care_plan ? 'Care Plan Until the Veterinarian Arrives' : 'Recommended Action'}</h6></div>
                  <div className="card-body">
                    {prediction.care_plan ? (
                      <CarePlan plan={prediction.care_plan} />
                    ) : (
                      <p className="mb-0">{prediction.recommendation_text || 'Isolate the animal and wait for veterinarian review and prescription.'}</p>
                    )}
                    {prediction.review_notes && (
                      <>
                        <hr />
                        <p className="mb-0"><strong>Veterinarian notes:</strong> {prediction.review_notes}</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-muted small mt-3">
              <i className="bi bi-info-circle"></i> This AI-generated prediction supports — but does not replace — professional veterinary diagnosis.
            </p>
          </>
        );
      }}
    </FlaskPage>
  );
}
