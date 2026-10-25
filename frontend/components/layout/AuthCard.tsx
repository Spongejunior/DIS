import type { ReactNode } from 'react';

interface AuthCardProps {
  /** The login-sized card pinned to the viewport, or the wider scrolling register card. */
  variant: 'login' | 'register';
  heading: string;
  /** Small grey line under the heading. */
  intro?: string;
  children: ReactNode;
}

/** The centred card that the login, register and password pages share. */
export function AuthCard({ variant, heading, intro, children }: AuthCardProps) {
  const login = variant === 'login';
  return (
    <div className={login ? 'auth-wrapper auth-wrapper-fixed' : 'auth-wrapper'}>
      <div className="auth-shell">
        <div className={`card auth-card ${login ? 'auth-card-login auth-card-login-fixed' : 'auth-card-register'} border-0 shadow-lg bg-white`}>
          <div className="p-4 p-md-5">
            <div className="mb-4 text-center">
              <p className="text-uppercase small fw-semibold text-success mb-2" style={{ letterSpacing: '0.06em' }}>Mzimba North VetAssistant</p>
              <h3 className="fw-bold text-dark mb-2">{heading}</h3>
              {intro && <p className="text-muted small mb-0">{intro}</p>}
            </div>

            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
