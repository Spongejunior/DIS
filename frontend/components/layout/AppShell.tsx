'use client';

import { useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { routes } from '@/lib/api/routes';
import { scheduleAlertDismissal } from '@/lib/utils/dom';
import { unsnake } from '@/lib/utils/format';
import type { LoadedPage } from '@/types/api';
import type { CurrentUser } from '@/types/models';

function profileHref(user: CurrentUser): string {
  if (user.role === 'farmer') return routes.farmerRegistration;
  if (user.role === 'veterinarian') return routes.vetProfile;
  if (user.role === 'organization_admin') return routes.orgAdminProfile;
  return '#';
}

interface AppShellProps {
  page: LoadedPage<unknown>;
  title: string;
  sidebar?: ReactNode;
  children: ReactNode;
}

/** The page frame from templates/base.html: navbar, sidebar, flash messages, content. */
export function AppShell({ page, title, sidebar, children }: AppShellProps) {
  const user = page.user;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.title = title;
  }, [title]);

  useEffect(() => scheduleAlertDismissal(), [page.nonce]);

  return (
    <>
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg fixed-top">
        <div className="container-fluid">
          <button className="btn d-lg-none me-2" type="button" id="sidebarToggle" onClick={() => setSidebarOpen((open) => !open)}>
            <i className="bi bi-list fs-4"></i>
          </button>

          <Link className="navbar-brand" href={routes.dashboard}>
            <span className="brand-text">
              <span className="brand-region">Mzimba North</span>
              <span className="brand-name">VetAssistant</span>
            </span>
          </Link>

          <div className="ms-auto d-flex align-items-center">
            {user ? (
              <div className="user-menu">
                <div className="user-info d-none d-sm-block">
                  <span className="user-name">{user.full_name || user.username}</span>
                  <span className="role-badge">{unsnake(user.role)}</span>
                </div>
                <div className="dropdown">
                  <a href="#" className="d-block link-dark text-decoration-none dropdown-toggle" id="dropdownUser" data-bs-toggle="dropdown" aria-expanded="false">
                    <i className="bi bi-person-circle fs-3 text-secondary"></i>{' '}
                  </a>
                  <ul className="dropdown-menu dropdown-menu-end shadow border-0 mt-3" aria-labelledby="dropdownUser">
                    <li>
                      {profileHref(user) === '#' ? (
                        <a className="dropdown-item py-2" href="#"><i className="bi bi-person me-2"></i> Profile</a>
                      ) : (
                        <Link className="dropdown-item py-2" href={profileHref(user)}><i className="bi bi-person me-2"></i> Profile</Link>
                      )}
                    </li>
                    <li><a className="dropdown-item py-2" href="#"><i className="bi bi-gear me-2"></i> Settings</a></li>
                    <li><hr className="dropdown-divider" /></li>
                    <li><Link className="dropdown-item py-2 text-danger" href={routes.logout} prefetch={false}><i className="bi bi-box-arrow-right me-2"></i> Logout</Link></li>
                  </ul>
                </div>
              </div>
            ) : (
              <Link href={routes.login} className="btn btn-primary btn-sm">Sign In</Link>
            )}
          </div>
        </div>
      </nav>

      <div className={`main-wrapper ${user ? 'has-sidebar' : ''}`}>
        {user && (
          <aside className={`sidebar${sidebarOpen ? ' show' : ''}`} id="sidebar">
            <div className="d-flex flex-column h-100">
              {sidebar}

              <div className="mt-auto pt-4 border-top">
                <div className="p-3 bg-light rounded-3 small text-muted">
                  <i className="bi bi-info-circle me-1"></i> System v2.1.4
                </div>
              </div>
            </div>
          </aside>
        )}

        {/* Content: remounted for every response, like a fresh page render */}
        <main className="page-content" key={page.nonce}>
          <div className="container-fluid p-0">
            {page.flashes.map(([category, message], index) => (
              <div key={index} className={`alert alert-${category !== 'message' ? category : 'info'} alert-dismissible fade show`} role="alert">
                {message}
                <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            ))}

            {children}
          </div>
        </main>
      </div>
    </>
  );
}
