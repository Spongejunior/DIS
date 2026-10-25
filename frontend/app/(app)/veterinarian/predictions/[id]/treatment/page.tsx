'use client';

import Link from 'next/link';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { VetSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { TemperatureBadge } from '@/components/predictions/CarePlan';
import { ErrorSummaryItems, Field, HiddenTag, Label, hasErrors } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import { capitalize, percent, text } from '@/lib/utils/format';
import type { FormData_ } from '@/types/api';
import type { Prediction, SymptomReport, Treatment } from '@/types/models';

interface AddTreatmentContext {
  form: FormData_;
  prediction: Prediction;
  report: SymptomReport;
  existing: Treatment | null;
}

const LABEL = 'form-label small fw-bold text-muted';

// templates/veterinarian/add_treatment.html
export default function AddTreatmentPage() {
  return (
    <FlaskPage<AddTreatmentContext>
      title="Treatment Recommendation - Mzimba North VetAssistant"
      sidebar={<VetSidebar active="reviews" />}
    >
      {({ form, prediction, report, existing }) => {
        const f = form.fields;
        return (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
              <div>
                <h3 className="fw-bold mb-0">{existing ? 'Edit' : 'Add'} Treatment Recommendation</h3>
                <p className="text-muted mb-0">{prediction.prediction_id} &middot; {report.report_id}</p>
              </div>
              <div className="d-flex gap-2">
                <Link href={routes.predictionDetail(prediction.id)} className="btn btn-outline-info"><i className="bi bi-eye"></i> View Prediction</Link>
                <Link href={routes.predictionsReview} className="btn btn-light"><i className="bi bi-arrow-left"></i> Back</Link>
              </div>
            </div>

            {/* Case summary */}
            <div className="card border-0 shadow-sm mb-4">
              <div className="card-body">
                <div className="row g-3">
                  <div className="col-md-3"><div className="small text-muted">Animal</div><div className="fw-bold">{text(report.animal_name)} ({capitalize(report.animal_type)})</div></div>
                  <div className="col-md-3"><div className="small text-muted">Predicted Disease</div><div className="fw-bold">{text(prediction.disease_name)}</div></div>
                  <div className="col-md-3"><div className="small text-muted">Confidence</div><div className="fw-bold">{percent(prediction.confidence)}%</div></div>
                  <div className="col-md-3"><div className="small text-muted">Severity</div><div className="fw-bold text-capitalize">{text(prediction.severity)}</div></div>
                  <div className="col-12">
                    <div className="small text-muted">Reported symptoms</div>
                    <div className="d-flex flex-wrap gap-1 mt-1">
                      {report.symptoms.length > 0 ? (
                        report.symptoms.map((symptom, index) => <span key={index} className="badge bg-secondary">{symptom}</span>)
                      ) : (
                        <span className="text-muted small">None recorded</span>
                      )}
                    </div>
                  </div>
                  <div className="col-12">
                    <div className="small text-muted">AI recommended action</div>
                    <div>{prediction.recommendation_text || '--'}</div>
                    {prediction.care_plan && (
                      <div className="mt-2 d-flex flex-wrap gap-2 align-items-center">
                        <TemperatureBadge temperature={prediction.care_plan.temperature} />
                        <span className="small text-muted">{prediction.care_plan.temperature.message}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Treatment form */}
            <FlaskForm action={routes.addTreatment(prediction.id)}>
              <HiddenTag form={form} />
              <div className="card border-0 shadow-sm">
                <div className="card-header bg-white py-3"><h5 className="fw-bold mb-0">Treatment Plan</h5></div>
                <div className="card-body">
                  {hasErrors(form) && (
                    <div className="alert alert-danger small">
                      <ul className="mb-0">
                        <ErrorSummaryItems form={form} />
                      </ul>
                    </div>
                  )}
                  <div className="row g-3">
                    <div className="col-md-6">
                      <Label field={f.medication} className={LABEL} />
                      <Field field={f.medication} className="form-control" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.medication_type} className={LABEL} />
                      <Field field={f.medication_type} className="form-select" />
                    </div>
                    <div className="col-md-4">
                      <Label field={f.dosage} className={LABEL} />
                      <Field field={f.dosage} className="form-control" placeholder="e.g. 10 ml" />
                    </div>
                    <div className="col-md-4">
                      <Label field={f.dosage_per_kg} className={LABEL} />
                      <Field field={f.dosage_per_kg} className="form-control" />
                    </div>
                    <div className="col-md-4">
                      <Label field={f.route} className={LABEL} />
                      <Field field={f.route} className="form-select" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.frequency} className={LABEL} />
                      <Field field={f.frequency} className="form-select" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.duration} className={LABEL} />
                      <Field field={f.duration} className="form-control" placeholder="days" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.milk_withdrawal_days} className={LABEL} />
                      <Field field={f.milk_withdrawal_days} className="form-control" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.meat_withdrawal_days} className={LABEL} />
                      <Field field={f.meat_withdrawal_days} className="form-control" />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.supportive_care} className={LABEL} />
                      <Field field={f.supportive_care} className="form-control" rows={3} />
                    </div>
                    <div className="col-md-6">
                      <Label field={f.diet_recommendations} className={LABEL} />
                      <Field field={f.diet_recommendations} className="form-control" rows={3} />
                    </div>
                    <div className="col-md-6 d-flex align-items-center">
                      <div className="form-check mt-2">
                        <Field field={f.follow_up_required} className="form-check-input" />{' '}
                        <Label field={f.follow_up_required} className="form-check-label" />
                      </div>
                    </div>
                    <div className="col-md-6">
                      <Label field={f.follow_up_date} className={LABEL} />
                      <Field field={f.follow_up_date} className="form-control" />
                    </div>
                  </div>
                </div>
                <div className="card-footer bg-white border-0 d-flex justify-content-end gap-2 p-3">
                  <Link href={routes.predictionsReview} className="btn btn-light">Cancel</Link>
                  <button type="submit" className="btn btn-success"><i className="bi bi-check-circle"></i> Save &amp; Share with Farmer</button>
                </div>
              </div>
            </FlaskForm>
          </>
        );
      }}
    </FlaskPage>
  );
}
