import type { CarePlan as CarePlanData, TemperatureAssessment } from '@/types/models';

const URGENCY_COLOR: Record<CarePlanData['urgency'], string> = {
  emergency: 'danger',
  urgent: 'warning',
  soon: 'info',
  routine: 'secondary',
};

const TEMPERATURE_COLOR: Record<TemperatureAssessment['status'], string> = {
  high_fever: 'danger',
  fever: 'warning',
  low: 'danger',
  implausible: 'secondary',
  normal: 'success',
  unknown: 'secondary',
};

/** Thermometer reading compared with the species' normal range. */
export function TemperatureBadge({ temperature }: { temperature: TemperatureAssessment }) {
  return (
    <span className={`badge bg-${TEMPERATURE_COLOR[temperature.status]} px-3 py-2`}>
      <i className="bi bi-thermometer-half"></i> {temperature.label}
      {temperature.value !== null && ` (${temperature.value} °C)`}
    </span>
  );
}

/**
 * Containment steps the farmer follows while waiting for the veterinarian's
 * prescription. `compact` shows only the summary and the disease steps.
 */
export function CarePlan({ plan, compact = false }: { plan: CarePlanData; compact?: boolean }) {
  return (
    <div>
      <div className={`alert alert-${URGENCY_COLOR[plan.urgency]} d-flex align-items-start gap-2 mb-3`}>
        <i className="bi bi-alarm fs-5"></i>
        <div>
          <div className="fw-bold">{plan.urgency_label}</div>
          <div>{plan.summary}</div>
        </div>
      </div>

      <div className="d-flex flex-wrap gap-2 mb-3">
        <TemperatureBadge temperature={plan.temperature} />
        {plan.notifiable && (
          <span className="badge bg-danger px-3 py-2"><i className="bi bi-megaphone"></i> Notifiable: report to the veterinary office</span>
        )}
        {plan.zoonotic && (
          <span className="badge bg-dark px-3 py-2"><i className="bi bi-person-exclamation"></i> Can infect people</span>
        )}
      </div>
      <p className="small text-muted">{plan.temperature.message}</p>

      {plan.warnings.map((warning, index) => (
        <div key={index} className="alert alert-light border small py-2"><i className="bi bi-exclamation-circle text-danger"></i> {warning}</div>
      ))}

      {plan.steps.length > 0 && (
        <>
          <h6 className="fw-bold mt-3">While you wait for the veterinarian</h6>
          <ol className="mb-3">
            {plan.steps.map((step, index) => <li key={index} className="mb-1">{step}</li>)}
          </ol>
        </>
      )}

      {!compact && (
        <>
          <h6 className="fw-bold">For every sick animal</h6>
          <ul className="mb-3">
            {plan.general_steps.map((step, index) => <li key={index} className="mb-1">{step}</li>)}
          </ul>

          <h6 className="fw-bold text-danger">Call the veterinarian immediately if</h6>
          <ul className="mb-3">
            {plan.danger_signs.map((sign, index) => <li key={index} className="mb-1">{sign}</li>)}
          </ul>

          <p className="small text-muted mb-1"><i className="bi bi-info-circle"></i> {plan.disclaimer}</p>
          <p className="small text-muted mb-0">
            Sources:{' '}
            {plan.sources.map((source, index) => (
              <span key={source.url}>
                {index > 0 && '; '}
                <a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a>
              </span>
            ))}
          </p>
        </>
      )}
    </div>
  );
}
