# TODO - ChiwetoCare alignment

- [x] Inspect app.py routes and key templates.
- [x] Inspect base.html for broken url_for usage.
- [x] Fix templates/base.html vet_profile url_for syntax.
- [x] Ensure SymptomForm fields in forms.py match what app.py writes to SymptomReport.
- [x] Fix prediction pipeline: model needs integer-encoded categorical features.
      Reconstructed the real encoding into model/feature_encoding.json (the shipped
      global_categorical_encoder.pkl was fit on the wrong values and is unused now).
- [x] Align scikit-learn runtime (1.9.0) with the version the model was trained on,
      fixing the predict_proba AttributeError. Added ML deps to requirements.txt.
- [x] Add animal_sex (a real model feature) to the form, model, DB migration and template.
- [x] Remove hardcoded dummy data and fix unclosed {% if %} blocks in
      farmer/symptom_history.html, farmer/predictions.html, veterinarian/prediction_review.html.
- [x] Wire up the veterinarian Confirm/Modify review actions (real forms -> /api endpoint).
- [x] Seed default farmer1 <-> vet1 assignment so the end-to-end flow works out of the box.
- [x] Verified: py_compile clean, all 30 templates compile, 0 server errors across
      100 role/route checks, full submit -> predict -> vet review -> treatment flow works.

# Multilingual Support (English, Chichewa, Tumbuka)

## Backend foundation (already in place)
- [x] Add `preferred_language` column to User model (default `en`).
- [x] Add `ensure_user_language_column()` migration helper + run on startup.
- [x] Initialize Flask-Babel with `_get_locale()` selector (user -> session -> en).
- [x] Add `/set-language` route to persist language (DB for logged-in, session otherwise).
- [x] Add `inject_i18n` context processor exposing `current_language` + `available_languages`.
- [x] Add i18n config to config.py (LANGUAGES, BABEL_DEFAULT_LOCALE).
- [x] Add Flask-Babel and Babel to requirements.txt.
- [x] Create babel.cfg extraction config.

## Phase 1 - Backend string wrapping
- [ ] app.py: wrap remaining flash messages in `_()`.
- [ ] app.py: wrap notification titles/bodies in `_()`.
- [ ] app.py: wrap DISEASE_INFO recommendations + get_disease_info fallback via `_()` at call time.
- [ ] app.py: wrap org_reports_pdf / PDF metadata strings in `_()`.
- [ ] mail_utils.py: wrap email subjects/bodies in `_()`.
- [ ] pdf_utils.py: wrap PDF section headers/labels/footer in `_()`.

## Phase 2 - Language switcher UI
- [ ] Add 🌐 Language switcher to templates/base.html navbar + wrap navbar/dropdown strings.
- [ ] Add 🌐 Language switcher to templates/landing_files/landing.html + translate strings.

## Phase 3 - Template translations
- [ ] Translate templates/auth/* (login, register, forgot_password, reset_password).
- [ ] Translate templates/errors/* (403, 404, 500).
- [ ] Translate templates/farmer/* (dashboard, symptom_form, symptom_history, predictions,
      prediction_detail, notifications, notification_detail, registration).
- [ ] Translate templates/veterinarian/* (_sidebar, dashboard, communications,
      prediction_review, treatment_suggestions, add_treatment, mortality_reports,
      farmer_mapping, profile).
- [ ] Translate templates/organization_admin/* (_sidebar, dashboard, my_profile,
      user_management, reports).
- [ ] Translate templates/system_admin/* (dashboard, system_logs, performance_report,
      model_updates).

## Phase 4 - Extract, translate, compile
- [ ] Extract strings via `pybabel extract -F babel.cfg -k _l -o messages.pot .`
- [ ] Initialize translation catalogs for chi and tum via `pybabel init`.
- [ ] Fill in Chichewa (chi) and Tumbuka (tum) translations in .po files.
- [ ] Compile catalogs via `pybabel compile -d translations`.
- [ ] Verify app runs: language switcher updates UI immediately, persists per user/session,
      all pages respect the selected language, existing features unbroken.

