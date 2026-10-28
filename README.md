# Mzimba North VetAssistant

A livestock disease identification and veterinary assistance system for cattle
and goats in Mzimba North, Malawi. A farmer enters an animal's details, body
temperature and symptoms. The system predicts the likely disease with a
machine-learning model, gives the farmer a care plan to contain the illness
while they wait, and sends the case to the farmer's veterinarian, who reviews
it and prescribes treatment.

**Roles:** farmer, veterinarian, organization admin, system admin.

## Project layout

```text
backend/                Django app (JSON only) + database + ML model
  manage.py             Django commands: runserver, migrate, import_sqlite, ...
  vetassistant/         project: settings.py (reads backend/.env: DATABASE_URL, ...), urls.py, wsgi.py
  core/                 the app
    views.py            pages and actions (one view per URL)
    urls.py             page URLs (same paths as the frontend pages)
    bridge.py           serves every view as JSON at /api/v1/page/<path>
    models.py           database models (the existing tables and columns)
    forms.py            forms (validation)
    services.py         access checks, record ids, farmer/vet assignment, notifications, log, email
    prediction.py       prediction pipeline (model, temperature, care plan)
    clinical_guidance.py  temperature check, temperature adjustment, care plans and sources
    locations.py        Mzimba North EPAs and sections
    pdf_utils.py        prediction and report PDFs
    migrations/         database schema (0001) and demo accounts / start-up data (0002)
    management/commands/  import_sqlite (copy SQLite data into PostgreSQL), runserver on port 80
  model/                livestock_disease_model.pkl (stacking ensemble) + feature_encoding.json
  data/                 training data (raw/cattle_goat.xlsx, encoded/encoded_data.csv)
  instance/database.db  old SQLite database (used only when DATABASE_URL is not set)
  Dockerfile            backend container (gunicorn, port 10000)
frontend/               Next.js user interface (see frontend/README.md)
```

## Database

The app stores its data in the PostgreSQL database **`mzimbanorth`**. The
connection is set in `backend/.env`, which is not committed to git because it
holds the password:

```bash
# backend/.env
DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/mzimbanorth
```

Special characters in the password must be URL-encoded (`$` → `%24`,
`@` → `%40`). If `DATABASE_URL` is not set, the app falls back to the SQLite
file `backend/instance/database.db`.

Tables are created and updated by Django's migrations. Run this from
`backend/` after installing or updating the code:

```bash
python manage.py migrate --fake-initial
```

`--fake-initial` lets Django take over a database that the earlier Flask
version created: the tables already exist, so Django records them as created
instead of creating them again. It does nothing on a new, empty database. The
migrations also create the demo accounts and the model version record.

**Setting up on another computer:** create an empty database
(`CREATE DATABASE mzimbanorth;` in psql or pgAdmin), create `backend/.env` as
above, and run `python manage.py migrate`. To bring over existing data from a
SQLite file, run this once from `backend/` afterwards:

```bash
python manage.py import_sqlite --replace                   # from instance/database.db
python manage.py import_sqlite --replace --source other.db
```

The command copies every table in one transaction (all or nothing), checks
the data for anything PostgreSQL would reject before writing, moves the id
counters past the copied ids, and compares row counts. The SQLite file is
only read. It refuses to write into tables that already have data unless
`--replace` is given (`migrate` has already added the demo accounts, so
`--replace` is needed; they are replaced by the copied data).

The data was migrated from SQLite on 2026-10-25. A backup of the SQLite file
from that moment is in `backend/instance/` (`database.sqlite-backup-*.db`, not
committed).

## Running it

PostgreSQL must be running (on Windows it is the `postgresql-x64-18` service).
Then use two terminals:

```bash
# 1. Backend (port 80)
cd backend
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py runserver

# 2. Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Always use the frontend address; it forwards
requests to the backend.

`runserver` uses port 80 by default here. If port 80 is taken, start it on
another port (`python manage.py runserver 8000`) and put
`BACKEND_URL=http://127.0.0.1:8000` in `frontend/.env.local`.

**With Docker (backend only):** the container runs the migrations and then
serves the app with gunicorn. From `backend/`, run
`docker build -t vetassistant-backend .` and
`docker run -p 10000:10000 vetassistant-backend`, then set
`BACKEND_URL=http://127.0.0.1:10000` for the frontend.

**Demo accounts** (created by `migrate`, password `pass123`): `sysadmin`,
`orgadmin`, `vet1`, `farmer1`. Change these passwords before real use. (The
old SQLite file, which also holds these accounts, is still in the repository.)

## How a prediction is made

When a farmer submits the symptom form (`/farmer/symptoms`), `create_prediction`
in `backend/core/prediction.py` runs these steps:

1. **Temperature check.** The reading is compared with the species' normal
   rectal range from the Merck Veterinary Manual: cattle 38.0–39.3 °C, goats
   38.5–39.7 °C. The result is *low*, *normal*, *fever* or *high fever*
   (cattle ≥ 40.5 °C, goats ≥ 41.0 °C). Readings outside 34–43.5 °C are treated
   as a measuring or typing error, are not used, and the farmer is asked to
   measure again.
2. **Fever as a symptom.** If the thermometer shows a fever but the farmer did
   not tick "Fever" or "High fever", that symptom is added to the model input.
3. **Model.** The stacking ensemble (Random Forest + XGBoost + CatBoost,
   combined by logistic regression) predicts one of eight diseases: Anthrax,
   Brucellosis, East Coast Fever, Foot and Mouth Disease, Mastitis, Pneumonia,
   Trypanosomiasis and Worm Infestation.
4. **Temperature adjustment.** The model's probabilities are re-weighted by
   how typical the temperature is for each disease (for example, a high fever
   fits East Coast fever and anthrax, and does not fit worms or brucellosis).
5. **Care plan.** A plan is built for the top disease and saved with the
   prediction (see below).

### Why temperature is handled outside the model

In the training data, the temperature column holds a single value per species
(the middle of the normal range), so the model could never learn from real
readings. The model is given that training value, and the real reading is used
in steps 1, 2 and 4 instead. The weights in step 4 (`TEMPERATURE_LIKELIHOOD` in
`clinical_guidance.py`) are expert estimates based on the clinical descriptions
in the sources below, not values fitted to data. Retraining the model on
records with real thermometer readings would be the long-term improvement.

### Symptom order

The model learned which column (`symptom1` to `symptom7`) each symptom
appeared in, not just which symptoms are present. For example, "diarrhea" is
nearly always in `symptom1` and "drooling" in `symptom5`–`symptom7`. The app
builds 32 likely arrangements from the column statistics stored in
`feature_encoding.json` (`symptom_slot_counts`) and averages the model's
answers over them.

| Input to the model | Accuracy on the training rows |
|---|---|
| Columns exactly as stored in the training data | 99.7% |
| Symptoms in the order the farmer ticked them (old behaviour) | 72.9% |
| Single most likely arrangement | 96.9% |
| Average over 32 arrangements (current) | 98.9% |

These figures are measured on the training data, so real-world accuracy will
be lower. Every training case had 5–7 symptoms; predictions with only 2–3
symptoms are less certain, and the farmer is told so.

## Care plan for the farmer

Every new prediction includes a care plan that the farmer sees on the
predictions page, on the prediction report and in the PDF. It contains:

- **Urgency:** from "within 1–2 days" to "emergency: contact the veterinary
  office immediately". Urgency is raised for a high or low temperature, and
  when a dangerous disease is a close second.
- **Containment steps for the predicted disease:** for example, never opening
  a carcass for suspected anthrax, stopping all animal movement for suspected
  foot-and-mouth disease, tick control for East Coast fever, and milking last
  and discarding milk for mastitis.
- **Steps for every sick animal:** isolation, no movement or sale, water and
  feed, hygiene, and no leftover medicines.
- **Danger signs** that mean the vet must be called immediately.
- **Warnings** when the disease must be reported to the veterinary office
  (WOAH-listed: anthrax, foot-and-mouth disease, brucellosis, East Coast fever,
  trypanosomiasis) or can infect people (anthrax, brucellosis).
- **Sources** for the advice.

The plan never names a medicine or a dose. Prescriptions come only from the
veterinarian. The veterinarian sees the temperature assessment on the
treatment page.

Predictions made before this feature have no care plan and still show their
original one-line recommendation.

### Sources

- Merck Veterinary Manual: [normal rectal temperature ranges](https://www.merckvetmanual.com/multimedia/table/normal-rectal-temperature-ranges), [anthrax](https://www.merckvetmanual.com/generalized-conditions/anthrax/anthrax-in-animals), [theileriases (East Coast fever)](https://www.merckvetmanual.com/circulatory-system/blood-parasites/theileriases), [trypanosomiasis](https://www.merckvetmanual.com/circulatory-system/blood-parasites/trypanosomiasis-in-animals), [mastitis in cattle](https://www.merckvetmanual.com/reproductive-system/mastitis-in-large-animals/mastitis-in-cattle), [bovine respiratory disease](https://www.merckvetmanual.com/respiratory-system/respiratory-diseases-of-cattle/bovine-respiratory-disease-complex), [GI parasites of cattle](https://www.merckvetmanual.com/digestive-system/gastrointestinal-parasites-of-ruminants/gastrointestinal-parasites-of-cattle), [GI parasites of sheep and goats](https://www.merckvetmanual.com/digestive-system/gastrointestinal-parasites-of-ruminants/gastrointestinal-parasites-of-sheep-and-goats)
- WHO: [brucellosis fact sheet](https://www.who.int/news-room/fact-sheets/detail/brucellosis)
- USDA APHIS: [foot-and-mouth disease fact sheet](https://aphis.prod.usda.gov/sites/default/files/2023-11/fs-fmd-general.pdf), [WOAH-listed diseases](https://www.aphis.usda.gov/nvap/reference-guide/emergency-management/woah)
- New Zealand MPI: [FMD advice to farmers](https://www.mpi.govt.nz/biosecurity/pests-and-diseases-not-in-new-zealand/animal-diseases-not-in-nz/foot-and-mouth-disease-response-plans/advice-to-farmers-and-livestock-owners-about-foot-and-mouth-disease)

The care plans are decision support for farmers and do not replace a
veterinarian. Have a veterinarian review the wording in
`clinical_guidance.py` before wider use. The care plan text is in English
only; it is not yet translated into Chichewa or Tumbuka.

## Troubleshooting

- **The backend fails to start with "connection refused" or "password
  authentication failed":** PostgreSQL is not running, or the user/password in
  `backend/.env` is wrong. The username is `postgres`.
- **"relation ... already exists" when running `migrate`:** the database was
  created by the Flask version; run `python manage.py migrate --fake-initial`.
- **"500 – An unexpected error occurred" in the browser:** the frontend shows
  this whenever the backend does not answer properly. Check that
  `python manage.py runserver` is running, and look at its terminal for an
  error.
- **Slow first prediction:** the backend loads the model in the background
  when it starts. On Windows the first load can take a few minutes while the
  ML libraries are scanned; the frontend waits up to 3 minutes.
- **"An Application Control policy has blocked this file":** Windows blocked
  an ML library file. Allow Python in Windows Security (Smart App Control),
  then restart the backend.
- **"Symptoms were saved, but the trained model could not generate a
  prediction":** the reason is recorded in the system logs (system admin →
  Logs, component `model`).
