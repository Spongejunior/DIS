"""Disease prediction: the trained model plus the temperature check and care plan."""
import json
import logging
import threading
from functools import lru_cache

from django.conf import settings

from .clinical_guidance import adjust_for_temperature, assess_temperature, build_care_plan, temperature_symptoms
from .models import Prediction, malawi_now
from .services import create_with_record_id

logger = logging.getLogger(__name__)

SUPPORTED_ANIMAL_TYPES = {'cattle', 'goat'}

MODEL_DIRECTORY = settings.BASE_DIR / 'model'
MODEL_PATH = MODEL_DIRECTORY / 'livestock_disease_model.pkl'
FEATURE_ENCODING_PATH = MODEL_DIRECTORY / 'feature_encoding.json'


@lru_cache(maxsize=1)
def load_prediction_artifacts():
    try:
        import joblib
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            'Prediction dependencies are not installed. Add pandas, joblib, and the model runtime packages to run predictions.'
        ) from exc

    if not MODEL_PATH.exists():
        raise RuntimeError(f'Model file not found: {MODEL_PATH}')
    if not FEATURE_ENCODING_PATH.exists():
        raise RuntimeError(f'Feature encoding file not found: {FEATURE_ENCODING_PATH}')

    model = joblib.load(MODEL_PATH)
    with open(FEATURE_ENCODING_PATH, 'r', encoding='utf-8') as handle:
        encoding = json.load(handle)
    return pd, model, encoding


def warm_up_prediction_model():
    """Load the model when the server starts.

    The first load can take minutes on Windows while the ML libraries' files
    are scanned. Doing it on the first farmer submission made that request
    outlast the frontend proxy, which then showed a 500 page. If loading fails
    here, the next prediction simply tries again (failures are not cached).
    """
    try:
        load_prediction_artifacts()
        logger.info('Prediction model loaded: %s', MODEL_PATH.name)
    except Exception:
        logger.exception('Prediction model could not be loaded at startup')


def start_model_warm_up():
    if not settings.TESTING:
        threading.Thread(target=warm_up_prediction_model, name='model-warm-up', daemon=True).start()


def infer_malawi_season(reference_time=None):
    month = (reference_time or malawi_now()).month
    if month in {11, 12, 1, 2, 3, 4}:
        return 'rainy'
    if month in {5, 6, 7, 8}:
        return 'cold_dry'
    return 'hot_dry'


def normalize_symptom_name(symptom):
    return (symptom or '').strip().lower()


def encode_category(encoding, value):
    """Map a raw categorical string to the integer code the model was trained on.

    Unknown / missing values fall back to the encoder's missing code so the model
    always receives a valid numeric feature."""
    feature_map = encoding['feature_map']
    key = normalize_symptom_name(value)
    return feature_map.get(key, encoding['missing_code'])


SYMPTOM_SLOT_COUNT = 7
SYMPTOM_ARRANGEMENTS = 32


def symptom_slot_arrangements(symptoms, encoding, count=SYMPTOM_ARRANGEMENTS):
    """Return ``count`` likely ways to place the symptoms in the model's
    columns (symptom1..symptom7); the first is the single most likely one.

    The model learned symptom positions, not just which symptoms are present:
    e.g. 'diarrhea' is nearly always in symptom1 and 'drooling' in symptom5-7.
    ``symptom_slot_counts`` in feature_encoding.json holds, per symptom, how
    often it appeared in each column of data/raw/cattle_goat.xlsx.

    The prediction averages the model over all arrangements, so no single
    guess about positions decides the result. On the training rows (with the
    symptom order shuffled): ticked order ~73%, best arrangement only ~97%,
    average of 32 arrangements ~99%. The random draws use a fixed seed, so the
    same report always gets the same prediction.
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    if not symptoms:
        return [[None] * SYMPTOM_SLOT_COUNT]

    slot_counts = encoding.get('symptom_slot_counts', {})
    uniform = [1.0] * SYMPTOM_SLOT_COUNT
    # Small smoothing so a column a symptom never used is unlikely, not impossible.
    weights = {}
    for symptom in symptoms:
        row = np.array(slot_counts.get(symptom, uniform), dtype=float) + 0.5
        weights[symptom] = row / row.sum()

    # Most likely arrangement (if more than seven symptoms, the best seven are kept).
    best = [None] * SYMPTOM_SLOT_COUNT
    cost = -np.log(np.array([weights[symptom] for symptom in symptoms]))
    for symptom_index, slot_index in zip(*linear_sum_assignment(cost)):
        best[slot_index] = symptoms[symptom_index]
    arrangements = [best]

    # Further arrangements drawn in proportion to how often each symptom used each column.
    rng = np.random.default_rng(20240625)
    for _ in range(count - 1):
        slots = [None] * SYMPTOM_SLOT_COUNT
        free = list(range(SYMPTOM_SLOT_COUNT))
        for symptom in rng.permutation(symptoms)[:SYMPTOM_SLOT_COUNT]:
            column_weights = weights[symptom][free]
            chosen = free[rng.choice(len(free), p=column_weights / column_weights.sum())]
            slots[chosen] = str(symptom)
            free.remove(chosen)
        arrangements.append(slots)
    return arrangements


# In the training data the temperature column holds one value per species (the
# midpoint of its normal range), so the model never learned from real readings.
# It gets that value; the real reading is used by clinical_guidance instead.
MODEL_TRAINING_TEMPERATURE = {'cattle': 38.65, 'goat': 39.25}


def build_model_feature_sets(report, temperature_assessment=None):
    """Model inputs for a report: one feature dict per symptom arrangement."""
    symptoms = [normalize_symptom_name(symptom) for symptom in report.get_additional_symptoms_list()]
    symptoms = [symptom for symptom in symptoms if symptom]
    unique_symptoms = list(dict.fromkeys(symptoms))
    if temperature_assessment is not None:
        # A fever on the thermometer becomes the 'fever'/'high fever' symptom the model knows.
        unique_symptoms = temperature_symptoms(unique_symptoms, temperature_assessment)

    pd, _, encoding = load_prediction_artifacts()

    season_key = encoding['season_aliases'].get(
        infer_malawi_season(report.created_at), 'cold'
    )
    sex_value = (report.animal_sex or '').strip().lower() or 'female'
    base = {
        'season': encode_category(encoding, season_key),
        'specie': encode_category(encoding, report.animal_type),
        'sex': encode_category(encoding, sex_value),
        'age(month)': float(report.animal_age or 0),
        'temperature': MODEL_TRAINING_TEMPERATURE.get(report.animal_type, 38.65),
    }
    return [
        {**base, **{f'symptom{index + 1}': encode_category(encoding, slot) for index, slot in enumerate(slots)}}
        for slots in symptom_slot_arrangements(unique_symptoms, encoding)
    ]


def decode_model_label(raw_label, encoding):
    if isinstance(raw_label, str):
        return raw_label
    return encoding['disease_labels'].get(str(int(raw_label)), f'Disease {int(raw_label)}')


def categorize_disease(disease_name):
    disease = (disease_name or '').lower()
    if any(term in disease for term in ('pneumonia', 'respiratory', 'cough')):
        return 'respiratory'
    if any(term in disease for term in ('parasite', 'parasitic', 'worm')):
        return 'parasitic'
    if any(term in disease for term in ('mastitis', 'udder', 'milk')):
        return 'production'
    if any(term in disease for term in ('bloat', 'diarrhea', 'enterotoxemia', 'digest')):
        return 'digestive'
    return 'general'


def confidence_to_severity(confidence):
    if confidence >= 0.9:
        return 'critical'
    if confidence >= 0.75:
        return 'severe'
    if confidence >= 0.6:
        return 'moderate'
    return 'mild'


# Per-disease clinical metadata so each prediction gives distinct, useful guidance
# instead of a single generic recommendation.
DISEASE_INFO = {
    'Anthrax': {
        'category': 'bacterial',
        'severity': 'critical',
        'recommendation': 'Do NOT open or move the carcass. Isolate all animals immediately, restrict movement, and contact your veterinarian and animal-health authorities urgently. Anthrax is zoonotic — avoid direct contact and handling.'
    },
    'Brucellosis': {
        'category': 'reproductive',
        'severity': 'severe',
        'recommendation': 'Isolate affected animals and safely dispose of aborted material. Brucellosis is zoonotic — wear gloves when handling. Arrange veterinary testing of the herd and avoid consuming unpasteurised milk.'
    },
    'East Coast Fever': {
        'category': 'tick-borne',
        'severity': 'critical',
        'recommendation': 'Begin tick control immediately and keep the animal hydrated and sheltered. East Coast Fever progresses fast — seek urgent veterinary treatment for antiparasitic therapy.'
    },
    'Foot and Mouth Disease': {
        'category': 'viral',
        'severity': 'critical',
        'recommendation': 'Quarantine the animal and the whole herd at once — FMD is highly contagious. Disinfect equipment, restrict movement on/off the farm, and report to veterinary authorities immediately.'
    },
    'Mastitis': {
        'category': 'production',
        'severity': 'moderate',
        'recommendation': 'Separate the animal from the milking line and discard affected milk. Keep the udder clean and dry, milk out frequently, and consult your veterinarian for appropriate antibiotic therapy.'
    },
    'Pneumonia': {
        'category': 'respiratory',
        'severity': 'severe',
        'recommendation': 'Move the animal to a warm, dry, well-ventilated shelter away from draughts. Ensure water intake and seek veterinary care promptly for antibiotic treatment.'
    },
    'Trypanosomiasis': {
        'category': 'parasitic',
        'severity': 'severe',
        'recommendation': 'Reduce tsetse-fly exposure and support the animal with good nutrition and rest. Seek veterinary care for trypanocidal treatment as soon as possible.'
    },
    'Worm Infestation': {
        'category': 'parasitic',
        'severity': 'moderate',
        'recommendation': 'Administer an appropriate dewormer as advised by your veterinarian, provide good nutrition, and rotate/clean pastures to reduce re-infection.'
    },
}


def get_disease_info(disease_name):
    return DISEASE_INFO.get(disease_name, {
        'category': categorize_disease(disease_name),
        'severity': 'moderate',
        'recommendation': 'Isolate the animal and wait for veterinarian review and prescription.'
    })


def create_prediction(report):
    if report.animal_type not in SUPPORTED_ANIMAL_TYPES:
        raise ValueError(f'Unsupported animal type for model prediction: {report.animal_type}')

    pd, model, encoding = load_prediction_artifacts()
    temperature = assess_temperature(report.animal_type, report.temperature)
    feature_sets = build_model_feature_sets(report, temperature)
    feature_frame = pd.DataFrame(feature_sets)[encoding['feature_order']]
    features = dict(feature_sets[0])

    # Model probabilities averaged over the symptom arrangements, then
    # re-weighted by how well the thermometer reading fits each disease
    # (see clinical_guidance.adjust_for_temperature).
    if hasattr(model, 'predict_proba'):
        raw_probabilities = model.predict_proba(feature_frame).mean(axis=0)
        model_classes = getattr(model, 'classes_', range(len(raw_probabilities)))
        model_probabilities = {
            decode_model_label(label, encoding): float(probability)
            for label, probability in zip(model_classes, raw_probabilities)
        }
    else:
        model_probabilities = {decode_model_label(model.predict(feature_frame)[0], encoding): 1.0}
    final_probabilities = adjust_for_temperature(model_probabilities, temperature)

    ranked = sorted(final_probabilities, key=final_probabilities.get, reverse=True)
    disease_name = ranked[0]
    confidence = final_probabilities[disease_name]
    possible_diseases = [
        {
            'disease': disease,
            'probability': round(final_probabilities[disease], 4),
            'model_probability': round(model_probabilities[disease], 4),
        }
        for disease in ranked[:3]
    ]

    disease_info = get_disease_info(disease_name)
    care_plan = build_care_plan(disease_name, temperature, confidence, possible_diseases)
    features['temperature_reading'] = report.temperature
    features['temperature_status'] = temperature['status']

    prediction = create_with_record_id(
        Prediction, 'prediction_id', 'PRED',
        symptom_report=report,
        user_id=report.farmer_id,
        disease_name=disease_name,
        disease_category=disease_info['category'],
        confidence=confidence,
        severity=disease_info['severity'],
        recommendation_text=care_plan['summary'] if care_plan['steps'] else disease_info['recommendation'],
        care_plan=json.dumps(care_plan),
        model_version='model.pkl',
        possible_diseases=json.dumps(possible_diseases),
        review_status='pending',
        features_used=json.dumps(features),
    )

    report.status = 'predicted'
    report.save()
    return prediction
