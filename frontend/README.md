# Mzimba North VetAssistant: Next.js frontend

The user interface of VetAssistant, built with Next.js (App Router), React and
TypeScript. It replaced the Flask/Jinja templates, which have been removed; it
looks and behaves like them and uses the same Flask backend, database and
login session. Flask no longer renders HTML, so the app is always used through
this frontend.

## Running it

Two processes are needed: the Flask backend and this frontend.

```bash
# 1. Backend, from the backend/ folder (serves on port 80)
cd backend
pip install -r requirements.txt
python app.py

# 2. Frontend, in a second terminal from the frontend/ folder
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Open http://localhost:3000. If Flask runs on another port, say so before
starting the frontend:

```bash
# .env.local
BACKEND_URL=http://127.0.0.1:5000
```

For production: `npm run build` then `npm run start`. `BACKEND_URL` is read at
build time.

Requests forwarded to Flask may take up to 3 minutes before Next.js gives up
(`experimental.proxyTimeout` in `next.config.ts`; the Next.js default is 30
seconds). The first prediction after Flask starts can be slow while the model
loads, and a timeout shows the generic 500 page.

See the [project README](../README.md) for the whole system, including how
predictions and care plans are made.

## How it talks to Flask

The browser only ever talks to the Next.js server, which forwards `/api/*` and
the two PDF downloads to Flask (see `next.config.ts`). Because everything stays
on one origin, the Flask session cookie, CSRF tokens and `remember me` work as
they did before.

Flask has no separate JSON API; `backend/api_bridge.py` exposes the existing views
instead. A request to `/api/v1/page/<path>` runs the Flask view for `<path>`
and returns the data that view prepares for its page as JSON:

```json
{ "template": "farmer/dashboard.html", "context": { ... }, "user": { ... }, "flashes": [["success", "Login successful!"]] }
```

A redirect comes back as `{ "redirect": "/login" }`. Validation, permissions,
flash messages and business rules all stay in the Flask views. The `template`
value is only a page name now.

## Layout

```text
app/(landing)/landing/      the public landing page (own fonts and stylesheet)
app/(app)/                  every page that used templates/base.html
  login, register, forgot-password, reset-password/[token]
  farmer/...                dashboard, symptoms, history, predictions, notifications, profile
  veterinarian/...          dashboard, farmers, predictions, treatments, mortality, communications, profile
  organization/...          dashboard, user_management, reports, profile
  system/...                dashboard, logs, performance, updates
  predictions/[id]          prediction report shared by all roles
  [...slug]                 any other URL, answered by Flask's 404 page
components/layout/          AppShell (navbar, sidebar, flashes), FlaskPage, AuthCard
components/sidebar/         the per-role sidebars
components/forms/           FlaskForm (POST to a Flask view) and WTForms field rendering
components/charts/          Chart.js canvas
components/predictions/     CarePlan: temperature check and containment steps shown with a prediction
lib/api/                    bridge client and the Flask URL table
lib/utils/                  formatting that reproduces the Jinja output, DOM helpers
hooks/usePage.tsx           loads the current URL's data from Flask
types/                      API and model types
public/static/              the existing CSS and images, at their original URLs
```

Each page is one file that replaced one template; the name of the template it
came from is in a comment above the component. URLs are identical to the Flask
routes.

## Styling

Nothing was redesigned. `public/static/css/style.css` and `landing.css` are
copies of the originals, and `base.css` is the inline `<style>` block from
the old `templates/base.html` moved into a file. Bootstrap 5.3.3, Bootstrap Icons,
Font Awesome, the Google fonts and Chart.js load from the same CDN URLs as
before.
