import { routes } from '@/lib/api/routes';

// templates/landing_files/landing.html
export default function LandingPage() {
  return (
    <div className="landing-shell">
      <header className="site-header">
        <div className="brand">
          <div className="brand-mark">
            <img src="/static/images/logo.svg" alt="Mzimba North VetAssistant logo" />
          </div>
          <div>
            <h1>Mzimba North VetAssistant</h1>
            <p>Livestock disease identification &amp; veterinary assistance</p>
          </div>
        </div>

        <nav className="site-nav" aria-label="Primary">
          <a href="#features">Features</a>
          <a href="#impact">Impact</a>
          <a href="#about">About</a>
        </nav>

        <div className="header-actions">
          <a href={routes.login} className="btn btn-outline">Login</a>
          <a href={routes.register} className="btn btn-primary">Sign Up</a>
        </div>
      </header>

      <main>
        <section className="hero-section">
          {/* Text block: top of the left column */}
          <div className="hero-copy">
            <span className="hero-kicker"><i className=""></i> Spot symptoms earlier. Act faster.</span>
            <h2>Smart disease identification for <span className="accent-text">cattle &amp; goats</span></h2>
            <p>
              Mzimba North VetAssistant is an intelligent livestock disease identification and veterinary
              assistance system for farmers and veterinary officers in Mzimba North. Report an animal&apos;s
              symptoms, receive a disease prediction, and get guidance from your veterinary officer.
            </p>

            <div className="hero-actions">
              <a href={routes.register} className="btn btn-primary">Get Started <i className="fa-solid fa-arrow-right"></i></a>
              <a href={routes.login} className="btn btn-soft">Open Dashboard</a>
            </div>

            <div className="hero-highlights">
              <span className="highlight-chip"><i className="fa-solid fa-bolt"></i> Fast symptom reporting</span>
              <span className="highlight-chip"><i className="fa-solid fa-stethoscope"></i> Quick vet review</span>
              <span className="highlight-chip"><i className="fa-solid fa-mobile-screen"></i> Works across devices</span>
            </div>
          </div>

          {/* Two cards: bottom-left, bottoms aligned with the image to form the L */}
          <div className="hero-cards">
            <div className="goat-card-floating">
              <div className="goat-card-image">
                <img src="/static/images/goat.jpg" alt="Goat receiving care" />
              </div>
              <div className="goat-card-badge"><i className="fa-solid fa-heart-pulse"></i> Goat care</div>
            </div>

            <div className="hero-card hero-card-flow">
              <p className="metric-label">Average response flow</p>
              <div className="metric-row">
                <strong>Report</strong>
                <i className="fa-solid fa-arrow-right-long"></i>
                <span>Review</span>
                <i className="fa-solid fa-arrow-right-long"></i>
                <strong>Treat</strong>
              </div>
              <div className="metric-bar"><span></span></div>
              <small>Designed for farm-to-vet coordination.</small>
            </div>
          </div>

          {/* Main image: the tall right side of the L */}
          <div className="hero-visual">
            <div className="hero-card hero-card-main">
              <img src="https://cdn.phototourl.com/free/2026-06-24-a9d92bbe-d728-4a4d-9c7d-1614cb350cb6.jpg" alt="Healthy livestock in a green field" />
            </div>
          </div>
        </section>

        <section className="feature-section" id="features">
          <div className="section-heading">
            <span className="eyebrow">What the platform helps you do</span>
            <h3>Built to help both farmers and veterinarian officers to reduce losses due to delayed treatment .</h3>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon"><i className="fa-solid fa-brain"></i></div>
              <h4>AI-powered prediction support</h4>
              <p>Capture symptoms and receive structured disease predictions that help users prioritize the next step.</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon"><i className="fa-solid fa-user-doctor"></i></div>
              <h4>Veterinary collaboration</h4>
              <p>Enable veterinarians to review cases, suggest treatment, and follow up with mapped farmers.</p>
            </article>
            <article className="feature-card">
              <div className="feature-icon"><i className="fa-solid fa-chart-line"></i></div>
              <h4>Operational visibility</h4>
              <p>Give administrators dashboards and reporting views that show user activity and prediction workload.</p>
            </article>
          </div>
        </section>

        <section className="impact-section" id="impact">
          <div className="impact-card">
            <div className="section-heading section-heading-light">
              <span className="eyebrow">Why teams choose Mzimba North VetAssistant</span>
              <h3>A simpler path from symptoms to action.</h3>
            </div>

            <div className="stats-grid">
              <div className="stat-tile">
                <strong>24/7</strong>
                <span>Platform availability for field access</span>
              </div>
              <div className="stat-tile">
                <strong>Role-based</strong>
                <span>Farmer, vet, and admin workflows</span>
              </div>
              <div className="stat-tile">
                <strong>Faster</strong>
                <span>Case review and treatment coordination</span>
              </div>
              <div className="stat-tile">
                <strong>Mobile-ready</strong>
                <span>Responsive access from smaller screens</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer" id="about">
        <div className="footer-grid">
          <div>
            <h3>Mzimba North VetAssistant</h3>
            <p>
              An intelligent livestock disease identification and veterinary assistance system for farmers and veterinary officers in Mzimba North, Malawi.
            </p>
          </div>
          <div>
            <h4>Explore</h4>
            <ul>
              <li><a href="#features">Features</a></li>
              <li><a href="#impact">Impact</a></li>
              <li><a href={routes.login}>Login</a></li>
            </ul>
          </div>
          <div>
            <h4>Contact</h4>
            <ul>
              <li><i className="fa-solid fa-envelope"></i> josebanda2705@gmail.com</li>
              <li><i className="fa-solid fa-phone"></i> +265 999 231 915</li>
              <li><i className="fa-solid fa-location-dot"></i> Luwinga, Mzuzu City</li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>© 2026 Mzimba North VetAssistant.</p>
        </div>
      </footer>
    </div>
  );
}
