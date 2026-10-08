'use client';

import { useRef, useState } from 'react';
import { FlaskPage } from '@/components/layout/FlaskPage';
import { FarmerSidebar } from '@/components/sidebar/Sidebar';
import { FlaskForm } from '@/components/forms/FlaskForm';
import { ErrorSummaryItems, Field, HiddenTag, Label, hasErrors } from '@/components/forms/Field';
import { routes } from '@/lib/api/routes';
import type { FormData_ } from '@/types/api';

const COMMON_SYMPTOMS = [
  'Abnormal milk', 'Abortion', 'Anemia', 'Bleeding from orifices', 'Blisters in mouth', 'Bloating', 'Blood in stool',
  'Coughing', 'Dark feces', 'Dehydration', 'Diarrhea', 'Difficulty breathing', 'Difficulty walking', 'Drooling',
  'Excessive salivation', 'Eye discharge', 'Fever', 'Hair loss', 'High fever', 'High pulse rate', 'Lameness',
  'Loss of appetite', 'Mouth sores', 'Nasal discharge', 'Pain in udder', 'Rapid breathing', 'Reduced fertility',
  'Reduced milk production', 'Restlessness', 'Retained placenta', 'Rough coat', 'Shivering', 'Skin lesions',
  'Sudden death', 'Sunken eyes', 'Swollen joints', 'Swollen lymph nodes', 'Swollen udder', 'Weakness',
  'Weight loss',
];

const PAGE_STYLES = `
.step-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: white;
    border: 2px solid #e2e8f0;
    color: #94a3b8;
    transition: all 0.3s ease;
}
.step-item.active .step-circle {
    background: var(--primary-light);
    border-color: var(--primary-light);
    color: white;
    box-shadow: 0 0 0 4px rgba(44, 119, 68, 0.15);
}
.step-item.completed .step-circle {
    background: #10b981;
    border-color: #10b981;
    color: white;
}
.transition-all {
    transition: all 0.4s ease;
}
.symptom-tag-card {
    background: white;
    cursor: pointer;
    border-color: #f1f5f9;
}
.symptom-tag-card:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
}
.symptom-tag-card.active {
    background: #ecfdf5;
    border-color: #10b981;
    color: #065f46;
}
.cursor-pointer {
    cursor: pointer;
}
`;

const LABEL = 'form-label small fw-bold text-muted';
const INPUT = 'form-control border-0 bg-light py-2';
const SELECT = 'form-select border-0 bg-light py-2';

const STEPS = ['Animal Info', 'Symptoms', 'Review'];

function SymptomWizard({ form }: { form: FormData_ }) {
  const f = form.fields;
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [review, setReview] = useState({ type: '', sex: '', temp: '' });

  function fieldValue(selector: string): string {
    return wrapperRef.current?.querySelector<HTMLInputElement | HTMLSelectElement>(selector)?.value ?? '';
  }

  function goToStep(next: number) {
    // Basic validation for Step 1
    if (next === 2) {
      if (!fieldValue('select[name="animal_type"]')) {
        alert('Please select a specie.');
        return;
      }
      if (!fieldValue('select[name="animal_sex"]')) {
        alert('Please select the animal sex.');
        return;
      }
      if (!fieldValue('input[name="temperature"]')) {
        alert('Please enter the body temperature (°C). It is required for the prediction.');
        wrapperRef.current?.querySelector<HTMLInputElement>('#field-temperature')?.focus();
        return;
      }
    }

    if (next === 3) {
      setReview({
        type: fieldValue('select[name="animal_type"]'),
        sex: fieldValue('select[name="animal_sex"]'),
        temp: fieldValue('input[name="temperature"]'),
      });
    }
    setStep(next);
    window.scrollTo(0, 0);
  }

  function toggleSymptom(symptom: string) {
    setSelected((current) =>
      current.includes(symptom) ? current.filter((item) => item !== symptom) : [...current, symptom],
    );
  }

  const query = search.trim().toLowerCase();
  const visibleSymptoms = COMMON_SYMPTOMS.filter((symptom) => !query || symptom.toLowerCase().includes(query));
  // Review lists the symptoms in the order they appear in the grid.
  const selectedInOrder = COMMON_SYMPTOMS.filter((symptom) => selected.includes(symptom));

  return (
    <div className="container-tight py-4" style={{ maxWidth: '800px', margin: '0 auto' }} ref={wrapperRef}>
      <div className="mb-4">
        <h3 className="fw-bold mb-1">Report Animal Symptoms</h3>
        <p className="text-muted">Fill in the details below to receive an AI-powered health prediction.</p>
      </div>

      {/* Stepper */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-body p-4">
          <div className="d-flex justify-content-between position-relative">
            {STEPS.map((label, index) => {
              const number = index + 1;
              const state = `${number < step ? ' completed' : ''}${number === step ? ' active' : ''}`;
              return (
                <div key={label} className={`step-item text-center${state}`} id={`step${number}-indicator`} style={{ zIndex: 2, width: '120px' }}>
                  <div className="step-circle mx-auto mb-2 d-flex align-items-center justify-content-center fw-bold">{number}</div>
                  <div className="small fw-bold">{label}</div>
                </div>
              );
            })}
            {/* Progress Line */}
            <div className="position-absolute top-50 start-0 translate-middle-y w-100 bg-light" style={{ height: '2px', zIndex: 1 }}>
              <div id="step-progress" className="bg-primary h-100 transition-all" style={{ width: `${((step - 1) / 2) * 100}%` }}></div>
            </div>
          </div>
        </div>
      </div>

      {hasErrors(form) && (
        <div className="alert alert-danger border-0 shadow-sm mb-4">
          <h6 className="fw-bold"><i className="bi bi-exclamation-triangle-fill me-1"></i> Please correct the following:</h6>
          <ul className="mb-0 small">
            <ErrorSummaryItems form={form} />
          </ul>
        </div>
      )}

      <FlaskForm action={routes.symptomForm} id="symptomForm">
        <HiddenTag form={form} />

        {/* Step 1: Animal Info */}
        <div className={`step-content${step === 1 ? '' : ' d-none'}`} id="step1">
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-4">Animal Details</h5>
              <div className="row g-3">
                <div className="col-md-6">
                  <Label field={f.animal_type} className={LABEL} />
                  <Field field={f.animal_type} className={SELECT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.animal_sex} className={LABEL} />
                  <Field field={f.animal_sex} className={SELECT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.animal_age} className={LABEL} />
                  <Field field={f.animal_age} className={INPUT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.animal_weight} className={LABEL} />
                  <Field field={f.animal_weight} className={INPUT} />
                </div>
              </div>

              <h5 className="fw-bold mb-3 mt-4">Vital Signs</h5>
              <div className="row g-3">
                <div className="col-md-6">
                  <Label field={f.temperature} className={LABEL} />{' '}
                  <span className="text-danger">*</span>
                  <Field field={f.temperature} className={INPUT} id="field-temperature" placeholder="e.g. 39.0" />
                  <div className="form-text small">Required — normal range is about 38–40°C.</div>
                </div>
                <div className="col-md-6">
                  <Label field={f.appetite} className={LABEL} />
                  <Field field={f.appetite} className={SELECT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.rumen_movement} className={LABEL} />
                  <Field field={f.rumen_movement} className={SELECT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.stool_consistency} className={LABEL} />
                  <Field field={f.stool_consistency} className={SELECT} />
                </div>
                <div className="col-md-6">
                  <Label field={f.milk_production} className={LABEL} />
                  <Field field={f.milk_production} className={SELECT} />
                </div>
              </div>
            </div>
            <div className="card-footer bg-white border-0 p-4 pt-0 text-end">
              <button type="button" className="btn btn-primary px-4 py-2" onClick={() => goToStep(2)}>
                Next: Symptoms <i className="bi bi-arrow-right ms-1"></i>
              </button>
            </div>
          </div>
        </div>

        {/* Step 2: Symptoms */}
        <div className={`step-content${step === 2 ? '' : ' d-none'}`} id="step2">
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-4">Select Observed Symptoms</h5>

              <div className="mb-4">
                <label className="form-label small fw-bold text-muted d-block mb-3">Common Signs</label>
                <div className="mb-3">
                  <div className="input-group">
                    <span className="input-group-text border-0 bg-light">
                      <i className="bi bi-search text-muted"></i>
                    </span>
                    <input
                      type="text"
                      id="symptomSearch"
                      className="form-control border-0 bg-light py-2"
                      placeholder="Search symptoms like fever, cough, diarrhea..."
                      autoComplete="off"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                  </div>
                  <div className="form-text small">Type to quickly find and select symptoms.</div>
                </div>
                <div className="row g-3" id="symptomGrid">
                  {COMMON_SYMPTOMS.map((symptom) => {
                    const active = selected.includes(symptom);
                    return (
                      <div key={symptom} className={`col-md-4 symptom-option${visibleSymptoms.includes(symptom) ? '' : ' d-none'}`} data-symptom={symptom.toLowerCase()}>
                        <div
                          className={`symptom-tag-card p-2 rounded-3 text-center border cursor-pointer transition-all small fw-medium${active ? ' active' : ''}`}
                          onClick={() => toggleSymptom(symptom)}
                          data-value={symptom}
                        >
                          {symptom}
                          <input type="checkbox" name="symptoms" value={symptom} className="d-none" title={symptom} checked={active} readOnly />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div id="symptomSearchEmpty" className={`text-center text-muted small py-3${visibleSymptoms.length === 0 ? '' : ' d-none'}`}>
                  No symptoms matched your search.
                </div>
              </div>
            </div>
            <div className="card-footer bg-white border-0 p-4 pt-0 d-flex justify-content-between">
              <button type="button" className="btn btn-light px-4 py-2" onClick={() => goToStep(1)}>
                <i className="bi bi-arrow-left me-1"></i> Back
              </button>
              <button type="button" className="btn btn-primary px-4 py-2" onClick={() => goToStep(3)}>
                Next: Review <i className="bi bi-arrow-right ms-1"></i>
              </button>
            </div>
          </div>
        </div>

        {/* Step 3: Review */}
        <div className={`step-content${step === 3 ? '' : ' d-none'}`} id="step3">
          <div className="card border-0 shadow-sm">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-4">Review Your Report</h5>

              <div className="bg-light rounded-4 p-4 mb-4">
                <div className="row g-4">
                  <div className="col-6">
                    <div className="small text-muted mb-1">Specie</div>
                    <div className="fw-bold text-capitalize" id="review-type">{review.type || '--'}</div>
                  </div>
                  <div className="col-3">
                    <div className="small text-muted mb-1">Sex</div>
                    <div className="fw-bold text-capitalize" id="review-sex">{review.sex || '--'}</div>
                  </div>
                  <div className="col-3">
                    <div className="small text-muted mb-1">Temp (°C)</div>
                    <div className="fw-bold" id="review-temp">{review.temp || '--'}</div>
                  </div>
                  <div className="col-12">
                    <div className="small text-muted mb-1">Selected Symptoms</div>
                    <div className="d-flex flex-wrap gap-2 mt-2" id="review-symptoms">
                      {selectedInOrder.length > 0 ? (
                        selectedInOrder.map((symptom) => (
                          <span key={symptom} className="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2 rounded-pill">{symptom}</span>
                        ))
                      ) : (
                        <span className="text-muted small italic">None selected</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="alert alert-primary d-flex align-items-center border-0 small">
                <i className="bi bi-info-circle-fill me-2 fs-5"></i>
                By submitting, our AI will analyze these symptoms against thousands of veterinary records to provide a prediction.
              </div>
            </div>
            <div className="card-footer bg-white border-0 p-4 pt-0 d-flex justify-content-between">
              <button type="button" className="btn btn-light px-4 py-2" onClick={() => goToStep(2)}>
                <i className="bi bi-arrow-left me-1"></i> Back
              </button>
              <button type="submit" className="btn btn-success px-5 py-2 fw-bold shadow-sm">
                Submit &amp; Predict <i className="bi bi-magic ms-1"></i>
              </button>
            </div>
          </div>
        </div>
      </FlaskForm>

      <style>{PAGE_STYLES}</style>
    </div>
  );
}

// templates/farmer/symptom_form.html
export default function SymptomFormPage() {
  return (
    <FlaskPage<{ form: FormData_ }>
      title="Report Symptoms - Mzimba North VetAssistant"
      sidebar={<FarmerSidebar variant="solid" active="symptoms" notifications={false} />}
    >
      {({ form }) => <SymptomWizard form={form} />}
    </FlaskPage>
  );
}
