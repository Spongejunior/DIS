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
