import Link from 'next/link';
import { routes } from '@/lib/api/routes';

interface SidebarItem {
  key: string;
  href: string;
  icon: string;
  label: string;
}

function SidebarNav({ items, active }: { items: SidebarItem[]; active?: string }) {
  return (
    <nav className="nav flex-column">
      {items.map((item) => (
        <Link key={item.key} className={`nav-link ${item.key === active ? 'active' : ''}`} href={item.href}>
          <i className={`bi ${item.icon}`}></i> {item.label}
        </Link>
      ))}
    </nav>
  );
}

// The farmer templates each define their own sidebar and two designs are in
// use. Both are kept so every page shows the menu it showed before.
const FARMER_SOLID: SidebarItem[] = [
  { key: 'dashboard', href: routes.farmerDashboard, icon: 'bi-grid-1x2-fill', label: 'Dashboard' },
  { key: 'symptoms', href: routes.symptomForm, icon: 'bi-clipboard-plus-fill', label: 'Report Symptoms' },
  { key: 'history', href: routes.symptomHistory, icon: 'bi-clock-history', label: 'History' },
  { key: 'predictions', href: routes.farmerPredictions, icon: 'bi-graph-up-arrow', label: 'Predictions' },
  { key: 'notifications', href: routes.farmerNotifications, icon: 'bi-bell-fill', label: 'Notifications' },
  { key: 'profile', href: routes.farmerRegistration, icon: 'bi-person-fill-gear', label: 'Profile' },
];

const FARMER_OUTLINE: SidebarItem[] = [
  { key: 'dashboard', href: routes.farmerDashboard, icon: 'bi-house-door', label: 'Dashboard' },
  { key: 'symptoms', href: routes.symptomForm, icon: 'bi-clipboard-plus', label: 'Report Symptoms' },
  { key: 'history', href: routes.symptomHistory, icon: 'bi-clock-history', label: 'Symptom History' },
  { key: 'predictions', href: routes.farmerPredictions, icon: 'bi-graph-up', label: 'Disease Predictions' },
  { key: 'profile', href: routes.farmerRegistration, icon: 'bi-person-badge', label: 'My Profile' },
];

type FarmerPage = 'dashboard' | 'symptoms' | 'history' | 'predictions' | 'notifications' | 'profile';

export function FarmerSidebar({ active, variant, notifications = true }: {
  active: FarmerPage;
  variant: 'solid' | 'outline';
  /** The symptom form's sidebar has no Notifications entry. */
  notifications?: boolean;
}) {
  let items = variant === 'solid' ? FARMER_SOLID : FARMER_OUTLINE;
  if (!notifications) items = items.filter((item) => item.key !== 'notifications');
  return <SidebarNav items={items} active={active} />;
}

/** templates/veterinarian/_sidebar.html */
const VET: SidebarItem[] = [
  { key: 'dashboard', href: routes.vetDashboard, icon: 'bi-house-door', label: 'Dashboard' },
  { key: 'farmers', href: routes.farmerMapping, icon: 'bi-people', label: 'Farmer Mapping' },
  { key: 'reviews', href: routes.predictionsReview, icon: 'bi-clipboard-check', label: 'Review Predictions' },
  { key: 'communications', href: routes.vetCommunications, icon: 'bi-chat-square-text', label: 'Communications' },
  { key: 'treatments', href: routes.treatmentSuggestions, icon: 'bi-capsule', label: 'Treatment Suggestions' },
  { key: 'mortality', href: routes.mortalityReports, icon: 'bi-graph-down', label: 'Mortality Reports' },
  { key: 'profile', href: routes.vetProfile, icon: 'bi-person-badge', label: 'My Profile' },
];

export function VetSidebar({ active }: {
  active: 'dashboard' | 'farmers' | 'reviews' | 'communications' | 'treatments' | 'mortality' | 'profile';
}) {
  return <SidebarNav items={VET} active={active} />;
}

/** templates/organization_admin/_sidebar.html */
const ORG_ADMIN: SidebarItem[] = [
  { key: 'dashboard', href: routes.orgAdminDashboard, icon: 'bi-grid-1x2-fill', label: 'Dashboard' },
  { key: 'profile', href: routes.orgAdminProfile, icon: 'bi-person-fill-gear', label: 'My Profile' },
  { key: 'users', href: routes.orgAdminUsers, icon: 'bi-people-fill', label: 'User Management' },
  { key: 'reports', href: routes.orgReports, icon: 'bi-bar-chart-line-fill', label: 'Reports & Analytics' },
];

export function OrgAdminSidebar({ active }: { active: 'dashboard' | 'profile' | 'users' | 'reports' }) {
  return <SidebarNav items={ORG_ADMIN} active={active} />;
}

// The system admin dashboard uses different icons and labels from the other
// three system admin pages.
const SYS_ADMIN_DASHBOARD: SidebarItem[] = [
  { key: 'dashboard', href: routes.sysAdminDashboard, icon: 'bi-cpu-fill', label: 'Dashboard' },
  { key: 'logs', href: routes.systemLogs, icon: 'bi-journal-text', label: 'System Logs' },
  { key: 'performance', href: routes.performanceReports, icon: 'bi-bar-chart-line-fill', label: 'Performance' },
  { key: 'updates', href: routes.modelUpdates, icon: 'bi-cloud-arrow-up-fill', label: 'Updates' },
];

const SYS_ADMIN: SidebarItem[] = [
  { key: 'dashboard', href: routes.sysAdminDashboard, icon: 'bi-house-door', label: 'Dashboard' },
  { key: 'logs', href: routes.systemLogs, icon: 'bi-journal-text', label: 'System Logs' },
  { key: 'performance', href: routes.performanceReports, icon: 'bi-speedometer2', label: 'Performance Reports' },
  { key: 'updates', href: routes.modelUpdates, icon: 'bi-cloud-arrow-up', label: 'Model Updates' },
];

export function SysAdminSidebar({ active }: { active: 'dashboard' | 'logs' | 'performance' | 'updates' }) {
  return <SidebarNav items={active === 'dashboard' ? SYS_ADMIN_DASHBOARD : SYS_ADMIN} active={active} />;
}

/** templates/farmer/prediction_detail.html is shared by every role. */
export function PredictionDetailSidebar({ role }: { role: string | undefined }) {
  if (role === 'farmer') {
    return <SidebarNav items={FARMER_SOLID.slice(0, 4)} active="predictions" />;
  }
  if (role === 'veterinarian') {
    return (
      <SidebarNav
        items={[
          { key: 'dashboard', href: routes.vetDashboard, icon: 'bi-grid-1x2-fill', label: 'Dashboard' },
          { key: 'reviews', href: routes.predictionsReview, icon: 'bi-clipboard-check', label: 'Review Predictions' },
          { key: 'farmers', href: routes.farmerMapping, icon: 'bi-people', label: 'Farmers' },
        ]}
      />
    );
  }
  return (
    <SidebarNav items={[{ key: 'dashboard', href: routes.dashboard, icon: 'bi-grid-1x2-fill', label: 'Dashboard' }]} />
  );
}
