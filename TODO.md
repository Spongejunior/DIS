# TODO - Remove hardcoded data + use real DB/model for predictions

## Plan
- [ ] 1) Remove hardcoded default user seeding from `app.py` (sysadmin/orgadmin/vet1/farmer1) and replace with DB-driven bootstrap (or disable auto-seed).
- [ ] 2) Replace `create_prediction(report)` hardcoded disease dictionary/rule-based simulation with a `run_prediction(report)` placeholder interface.
  - [ ] 2.1) Add `MODEL_PREDICTOR` abstraction that will be replaced later by the real model.
  - [ ] 2.2) Ensure prediction output fields saved into `Prediction` come only from model output, not hardcoded lists.
- [ ] 3) Update veterinarian confirm flow to create `Treatment` from DB disease library data (not hardcoded medication/frequency/duration).
- [ ] 4) Replace admin/system hardcoded metrics (accuracy/uptime/api requests/component status, performance breakdown, model update schedules) with DB-derived values or `SystemLog`/`PerformanceMetric` queries.
- [ ] 5) Verify farmer history pages already query `Prediction` rows (so after step 2 they will be “real”).
- [ ] 6) Run application smoke test and ensure prediction history updates in real time.

