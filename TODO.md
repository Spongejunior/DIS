# Organization Admin Dashboard Replacement Plan

## Steps to Complete:

- [ ] Step 1: Create this TODO.md file ✅
- [x] Step 2: Update {% block sidebar %} with new design using Font Awesome icons and green active state matching project theme (#2c7744)
- [x] Step 3: Update {% block styles %} with glassmorphism CSS and hovers
- [x] Step 4: Replace {% block content %} with new Bootstrap-based layout:
  | Section | Use Dynamic Data |
  |---------|------------------|
  | KPI Cards | total_farmers, active_predictions, total_veterinarians, system_accuracy |
  | Performance Overview | Progress bars with accuracy/system_accuracy |
  | Recent Activities | Loop recent_logs |
  | Regional Overview | Static Mzuzu 42 |
  | Quick Actions | url_for to existing routes |
- [x] Step 5: Use edit_file on templetes/organization_admin/dashboard.html
- [x] Step 6: Test with: `python app.py` (login orgadmin/pass123, go to /organization/dashboard)
- [x] Step 7: Updated ✅
- [x] Step 8: Complete

