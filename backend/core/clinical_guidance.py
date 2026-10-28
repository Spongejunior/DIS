"""Clinical rules that sit next to the machine-learning model.

The stacking ensemble in model/livestock_disease_model.pkl cannot learn from
body temperature: in its training data (data/raw/cattle_goat.xlsx) temperature
is the same normal range for every animal of a species. This module brings the
farmer's thermometer reading into the prediction and builds the care plan the
farmer follows while waiting for the veterinarian's prescription.

1. ``assess_temperature`` compares the reading with the species' normal rectal
   range (Merck Veterinary Manual) and classifies it as low / normal / fever /
   high fever.
2. ``temperature_symptoms`` adds "fever" or "high fever" to the model input
   when the thermometer shows it but the farmer did not tick it. These are
   symptoms the model did learn from.
3. ``adjust_for_temperature`` re-weights the model's disease probabilities by
   how typical that temperature is for each disease (a Bayes update with the
   weights in TEMPERATURE_LIKELIHOOD). The weights are expert estimates taken
   from the clinical descriptions in the sources below, not fitted to data.
4. ``build_care_plan`` returns containment steps, danger signs, reporting
   duties and sources. It never recommends a medicine or dose: prescribing is
   left to the veterinarian.

The guidance supports, and does not replace, a veterinarian.
"""

SOURCES = {
    'merck_temperature': {
        'title': 'Merck Veterinary Manual: Normal rectal temperature ranges',
        'url': 'https://www.merckvetmanual.com/multimedia/table/normal-rectal-temperature-ranges',
    },
    'merck_anthrax': {
        'title': 'Merck Veterinary Manual: Anthrax in animals',
        'url': 'https://www.merckvetmanual.com/generalized-conditions/anthrax/anthrax-in-animals',
    },
    'merck_theileriosis': {
        'title': 'Merck Veterinary Manual: Theileriases (East Coast fever)',
        'url': 'https://www.merckvetmanual.com/circulatory-system/blood-parasites/theileriases',
    },
    'merck_trypanosomiasis': {
        'title': 'Merck Veterinary Manual: Trypanosomiasis in animals',
        'url': 'https://www.merckvetmanual.com/circulatory-system/blood-parasites/trypanosomiasis-in-animals',
    },
    'merck_mastitis': {
        'title': 'Merck Veterinary Manual: Mastitis in cattle',
        'url': 'https://www.merckvetmanual.com/reproductive-system/mastitis-in-large-animals/mastitis-in-cattle',
    },
    'merck_brd': {
        'title': 'Merck Veterinary Manual: Bovine respiratory disease complex',
        'url': 'https://www.merckvetmanual.com/respiratory-system/respiratory-diseases-of-cattle/bovine-respiratory-disease-complex',
    },
    'merck_worms_cattle': {
        'title': 'Merck Veterinary Manual: Gastrointestinal parasites of cattle',
        'url': 'https://www.merckvetmanual.com/digestive-system/gastrointestinal-parasites-of-ruminants/gastrointestinal-parasites-of-cattle',
    },
    'merck_worms_goats': {
        'title': 'Merck Veterinary Manual: Gastrointestinal parasites of sheep and goats',
        'url': 'https://www.merckvetmanual.com/digestive-system/gastrointestinal-parasites-of-ruminants/gastrointestinal-parasites-of-sheep-and-goats',
    },
    'who_brucellosis': {
        'title': 'WHO fact sheet: Brucellosis',
        'url': 'https://www.who.int/news-room/fact-sheets/detail/brucellosis',
    },
    'usda_fmd': {
        'title': 'USDA APHIS: Foot-and-mouth disease fact sheet',
        'url': 'https://aphis.prod.usda.gov/sites/default/files/2023-11/fs-fmd-general.pdf',
    },
    'mpi_fmd': {
        'title': 'NZ Ministry for Primary Industries: FMD advice to farmers',
        'url': 'https://www.mpi.govt.nz/biosecurity/pests-and-diseases-not-in-new-zealand/animal-diseases-not-in-nz/foot-and-mouth-disease-response-plans/advice-to-farmers-and-livestock-owners-about-foot-and-mouth-disease',
    },
    'woah_list': {
        'title': 'WOAH-listed (notifiable) diseases (USDA APHIS summary)',
        'url': 'https://www.aphis.usda.gov/nvap/reference-guide/emergency-management/woah',
    },
}

# Normal rectal temperature in °C (Merck Veterinary Manual). Cattle use the
# dairy-cow range; the lower alarm limit allows for beef/zebu cattle, whose
# range starts at 36.7 °C.
TEMPERATURE_RANGES = {
    'cattle': {'normal': (38.0, 39.3), 'low_below': 37.5, 'high_fever_from': 40.5},
    'goat': {'normal': (38.5, 39.7), 'low_below': 38.0, 'high_fever_from': 41.0},
}
# Readings outside this window are almost certainly a measuring or typing error.
PLAUSIBLE_TEMPERATURE = (34.0, 43.5)

# How typical each temperature band is for each disease: roughly
# P(band | disease). Higher means "this temperature fits the disease".
#   Anthrax: abrupt fever up to 41.5 °C; can drop below normal near death.
#   East Coast fever: high fever is the hallmark sign.
#   Foot and mouth: fever up to ~41 °C early, often normal once blisters burst.
#   Pneumonia: usually febrile.
#   Trypanosomiasis: fever comes and goes.
#   Mastitis: fever only in severe (systemic) cases.
#   Brucellosis: abortion without fever is typical.
#   Worms: no fever; low temperature only when anaemia is severe.
TEMPERATURE_LIKELIHOOD = {
    'Anthrax':                {'low': 0.15, 'normal': 0.10, 'fever': 0.30, 'high_fever': 0.45},
    'East Coast Fever':       {'low': 0.05, 'normal': 0.10, 'fever': 0.30, 'high_fever': 0.55},
    'Foot and Mouth Disease': {'low': 0.05, 'normal': 0.30, 'fever': 0.35, 'high_fever': 0.30},
    'Pneumonia':              {'low': 0.05, 'normal': 0.20, 'fever': 0.40, 'high_fever': 0.35},
    'Trypanosomiasis':        {'low': 0.05, 'normal': 0.35, 'fever': 0.40, 'high_fever': 0.20},
    'Mastitis':               {'low': 0.05, 'normal': 0.50, 'fever': 0.33, 'high_fever': 0.12},
    'Brucellosis':            {'low': 0.05, 'normal': 0.70, 'fever': 0.20, 'high_fever': 0.05},
    'Worm Infestation':       {'low': 0.15, 'normal': 0.65, 'fever': 0.15, 'high_fever': 0.05},
}

FEVER_SYMPTOMS = {'fever', 'high fever'}


def assess_temperature(species, temperature):
    """Classify a rectal temperature reading for cattle or goats."""
    ranges = TEMPERATURE_RANGES.get((species or '').lower(), TEMPERATURE_RANGES['cattle'])
    low, high = ranges['normal']
    result = {
        'value': temperature,
        'normal_range': [low, high],
        'status': 'unknown',
        'label': 'Not recorded',
        'message': 'No temperature was recorded. Measure it rectally with a thermometer and tell the veterinarian.',
    }
    if temperature is None:
        return result

    value = float(temperature)
    if not PLAUSIBLE_TEMPERATURE[0] <= value <= PLAUSIBLE_TEMPERATURE[1]:
        result.update(
            status='implausible',
            label='Check reading',
            message=(f'{value:.1f} °C is outside what a live animal can have. Measure again rectally '
                     f'(normal is {low}–{high} °C); the reading was not used for the prediction.'),
        )
    elif value < ranges['low_below']:
        result.update(
            status='low',
            label='Below normal',
            message=(f'{value:.1f} °C is below normal ({low}–{high} °C). A low temperature in a sick animal '
                     'can mean shock or a dying animal. Keep it warm and call the veterinarian now.'),
        )
    elif value <= high:
        result.update(
            status='normal',
            label='Normal',
            message=f'{value:.1f} °C is within the normal range ({low}–{high} °C).',
        )
    elif value < ranges['high_fever_from']:
        result.update(
            status='fever',
            label='Fever',
            message=f'{value:.1f} °C is a fever (normal is {low}–{high} °C).',
        )
    else:
        result.update(
            status='high_fever',
            label='High fever',
            message=(f'{value:.1f} °C is a high fever (normal is {low}–{high} °C). '
                     'High fever points to a serious infection; contact the veterinarian today.'),
        )
    return result


def temperature_symptoms(symptoms, assessment):
    """Return the symptom list with fever added when the thermometer shows it."""
    symptoms = list(symptoms)
    if FEVER_SYMPTOMS.intersection(symptoms):
        return symptoms
    if assessment['status'] == 'fever':
        return symptoms + ['fever']
    if assessment['status'] == 'high_fever':
        return symptoms + ['high fever']
    return symptoms


def adjust_for_temperature(probabilities, assessment):
    """Re-weight {disease: probability} by how well the temperature fits each disease."""
    band = assessment['status']
    if band not in ('low', 'normal', 'fever', 'high_fever'):
        return dict(probabilities)
    weighted = {
        disease: probability * TEMPERATURE_LIKELIHOOD.get(disease, {}).get(band, 0.25)
        for disease, probability in probabilities.items()
    }
    total = sum(weighted.values())
    if total <= 0:
        return dict(probabilities)
    return {disease: value / total for disease, value in weighted.items()}


GENERAL_STEPS = [
    'Separate the sick animal from the rest of the herd: its own pen or shade, with its own water and feed.',
    'Do not sell, slaughter, lend or move the animal, and do not take it to the market or dip tank until the veterinarian has seen it.',
    'Give clean drinking water at all times and good quality feed or fresh grass.',
    'Wash your hands with soap after touching the animal, and use a separate pair of shoes or wash your boots when leaving its pen.',
    'Do not give leftover or borrowed medicines and do not share needles between animals. Wait for the veterinarian\'s prescription.',
    'Check the other animals morning and evening, and record the temperature of the sick animal twice a day for the veterinarian.',
]

DANGER_SIGNS = [
    'The animal goes down and cannot get up, or breathes with its mouth open.',
    'Blood comes from the nose, mouth or anus, or an animal dies suddenly.',
    'The temperature goes above 41 °C or drops below normal.',
    'Other animals in the herd start showing the same signs.',
]

# Containment steps per disease, used while the farmer waits for the vet.
DISEASE_GUIDANCE = {
    'Anthrax': {
        'urgency': 'emergency',
        'notifiable': True,
        'zoonotic': True,
        'summary': 'Possible anthrax: do not touch, open or move a carcass, keep people and animals away, and report to the veterinary office immediately.',
        'steps': [
            'Never open, skin or cut a dead animal. Air turns anthrax bacteria into spores that stay in the soil for decades.',
            'Do not eat, sell or give away meat, milk or hides from sick or suddenly dead animals.',
            'Keep people, dogs and other animals away from the carcass and the place it died. Cover it to keep scavengers and flies off.',
            'Move the rest of the herd away from where the animal fell, onto a different grazing area.',
            'Wear gloves and cover cuts if you must be near the animal; wash well with soap afterwards.',
            'Report to the veterinary office now. Anthrax is a notifiable disease and the officer will arrange safe burning or deep burial and vaccination.',
            'If a person has a skin sore, fever or diarrhoea after contact, they should go to the health centre and mention anthrax.',
        ],
        'sources': ['merck_anthrax', 'woah_list'],
    },
    'Foot and Mouth Disease': {
        'urgency': 'emergency',
        'notifiable': True,
        'zoonotic': False,
        'summary': 'Possible foot and mouth disease: stop all animal movement on and off the farm and report to the veterinary office today.',
        'steps': [
            'Keep the whole herd at home. FMD spreads very fast between cloven-hoofed animals (cattle, goats, sheep, pigs).',
            'Do not let visitors, traders or other farmers\' animals onto the farm; keep animals away from shared grazing and water points.',
            'Clean boots, tools and vehicles before leaving the farm.',
            'Give soft feed and plenty of water: mouth blisters make eating painful. Keep sick animals on soft, dry ground.',
            'Write down where animals moved in the last two weeks; the veterinary officer will ask.',
            'Report to the veterinary office today. FMD is a notifiable disease.',
        ],
        'sources': ['usda_fmd', 'mpi_fmd', 'woah_list'],
    },
    'East Coast Fever': {
        'urgency': 'urgent',
        'notifiable': True,
        'zoonotic': False,
        'summary': 'Possible East Coast fever: start tick control on the whole herd, keep the animal sheltered and get the veterinarian quickly. It progresses fast.',
        'steps': [
            'Remove ticks from the sick animal (look in the ears, under the tail and around the udder) and destroy them; do not crush them with bare hands.',
            'Treat the whole herd against ticks with the dip or spray the extension office uses, and keep to the dipping schedule.',
            'Keep the sick animal in shade, sheltered from rain, with water and feed close by.',
            'Watch for swollen lymph nodes, breathing difficulty and froth at the nose: these mean it is getting worse.',
            'Call the veterinarian quickly. East Coast fever can kill within days, and treatment works best early.',
        ],
        'sources': ['merck_theileriosis', 'woah_list'],
    },
    'Trypanosomiasis': {
        'urgency': 'urgent',
        'notifiable': True,
        'zoonotic': False,
        'summary': 'Possible trypanosomiasis: protect the animal from tsetse and biting flies, support it with good feed and water, and get the veterinarian.',
        'steps': [
            'Keep animals away from bush and river areas where tsetse flies live, especially during the hottest hours.',
            'Protect animals from biting flies; use the fly control (pour-on or spray) recommended by the extension office.',
            'Give good feed and clean water and let the animal rest; the disease causes anaemia and weight loss.',
            'Use a new or sterilised needle for each animal when animals are injected.',
            'Ask the veterinarian to test the animal; the fever comes and goes, so record the temperature twice a day.',
        ],
        'sources': ['merck_trypanosomiasis', 'woah_list'],
    },
    'Brucellosis': {
        'urgency': 'soon',
        'notifiable': True,
        'zoonotic': True,
        'summary': 'Possible brucellosis: isolate the animal, handle any aborted foetus and afterbirth with gloves, and do not drink its raw milk. People can catch it.',
        'steps': [
            'Keep the animal apart from pregnant animals, especially during and after giving birth or aborting.',
            'Wear gloves to handle an aborted foetus, afterbirth or birth fluids; bury them deep or burn them, and disinfect the area.',
            'Do not drink raw milk or eat fresh cheese from this animal. Boil all milk before drinking.',
            'Do not let dogs eat afterbirths or aborted foetuses.',
            'Ask the veterinarian to test the herd. Brucellosis is notifiable, and anyone with a long-lasting fever after contact should visit the health centre.',
        ],
        'sources': ['who_brucellosis', 'woah_list'],
    },
    'Mastitis': {
        'urgency': 'soon',
        'notifiable': False,
        'zoonotic': False,
        'summary': 'Possible mastitis: milk this animal last, throw away its milk, keep the udder clean and dry, and wait for the veterinarian\'s treatment plan.',
        'steps': [
            'Milk the affected animal last, after the healthy ones, so the infection does not spread on hands or equipment.',
            'Milk the affected quarter out completely and often, and discard that milk. Do not feed it to calves or sell it.',
            'Wash your hands before milking and dry the teats with a clean cloth for each animal.',
            'Keep bedding and the resting area clean and dry.',
            'Call the veterinarian, who will decide whether antibiotics are needed and how long milk must be withheld.',
        ],
        'sources': ['merck_mastitis'],
    },
    'Pneumonia': {
        'urgency': 'urgent',
        'notifiable': False,
        'zoonotic': False,
        'summary': 'Possible pneumonia: move the animal to a dry, sheltered, well-aired place away from the herd and get the veterinarian promptly.',
        'steps': [
            'House the animal somewhere dry and sheltered from wind and rain, but with fresh air (not a closed, smoky or dusty room).',
            'Keep it away from the other animals; coughing spreads the infection.',
            'Make sure it keeps drinking; place water and soft feed within easy reach.',
            'Avoid stress: no long walks, work or crowding until it recovers.',
            'Call the veterinarian promptly; pneumonia usually needs prescribed antibiotics.',
        ],
        'sources': ['merck_brd'],
    },
    'Worm Infestation': {
        'urgency': 'soon',
        'notifiable': False,
        'zoonotic': False,
        'summary': 'Possible worm infestation: give good feed and water, move the herd to cleaner grazing, and let the veterinarian choose the dewormer and dose.',
        'steps': [
            'Check the inside of the lower eyelid: pale or white instead of pink means anaemia. Tell the veterinarian.',
            'Give good feed and clean water so the animal can recover strength.',
            'Move the herd to grazing that has not been used recently, and avoid wet, muddy grazing near water.',
            'Remove dung from pens and keep feed and water troughs clean.',
            'Ask the veterinarian to choose the dewormer and dose; wrong or repeated dewormers make worms resistant.',
        ],
        'sources': ['merck_worms_cattle', 'merck_worms_goats'],
    },
}

DEFAULT_GUIDANCE = {
    'urgency': 'soon',
    'notifiable': False,
    'zoonotic': False,
    'summary': 'Isolate the animal and wait for veterinarian review and prescription.',
    'steps': [],
    'sources': [],
}

URGENCY_ORDER = ['routine', 'soon', 'urgent', 'emergency']
URGENCY_LABELS = {
    'routine': 'Routine: mention it at the next veterinary visit',
    'soon': 'Contact the veterinarian within 1–2 days',
    'urgent': 'Contact the veterinarian today',
    'emergency': 'Emergency: contact the veterinary office immediately',
}


def _raise_urgency(current, minimum):
    return max(current, minimum, key=URGENCY_ORDER.index)


def build_care_plan(disease_name, assessment, confidence, possible_diseases):
    """Everything the farmer should do while waiting for the vet's prescription."""
    guidance = DISEASE_GUIDANCE.get(disease_name, DEFAULT_GUIDANCE)
    urgency = guidance['urgency']
    if assessment['status'] in ('high_fever', 'low'):
        urgency = _raise_urgency(urgency, 'urgent')

    warnings = []
    # A notifiable or zoonotic disease that is a close second still needs the
    # precaution, even if it is not the top prediction.
    for item in possible_diseases[1:]:
        other = DISEASE_GUIDANCE.get(item['disease'])
        if other and item['probability'] >= 0.15 and (other['notifiable'] or other['zoonotic']):
            warnings.append(
                f"{item['disease']} is also possible ({item['probability'] * 100:.0f}%): {other['summary']}"
            )
            urgency = _raise_urgency(urgency, 'urgent')
    if confidence < 0.5:
        warnings.append('The prediction is uncertain. Tick every symptom you see and make sure the veterinarian examines the animal.')

    source_keys = ['merck_temperature'] + list(guidance['sources'])
    return {
        'disease': disease_name,
        'summary': guidance['summary'],
        'urgency': urgency,
        'urgency_label': URGENCY_LABELS[urgency],
        'notifiable': guidance['notifiable'],
        'zoonotic': guidance['zoonotic'],
        'temperature': assessment,
        'steps': guidance['steps'],
        'general_steps': GENERAL_STEPS,
        'danger_signs': DANGER_SIGNS,
        'warnings': warnings,
        'sources': [SOURCES[key] for key in dict.fromkeys(source_keys)],
        'disclaimer': ('These steps help contain the illness until the veterinarian arrives. '
                       'They are not a prescription; medicines and doses come from the veterinarian.'),
    }
