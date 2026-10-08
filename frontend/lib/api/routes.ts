// URLs of the Flask views, mirroring url_for() in the templates. The Next.js
// pages live at the same paths.
export const routes = {
  landing: '/landing',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  logout: '/logout',
  dashboard: '/dashboard',

  farmerDashboard: '/farmer/dashboard',
  farmerNotifications: '/farmer/notifications',
  farmerNotificationDetail: (id: number) => `/farmer/notifications/${id}`,
  markFarmerNotificationsRead: '/farmer/notifications/mark-all-read',
  contactVet: '/farmer/contact-vet',
  symptomForm: '/farmer/symptoms',
  symptomHistory: '/farmer/symptoms/history',
  farmerPredictions: '/farmer/predictions',
  farmerRegistration: '/farmer/profile',

  predictionDetail: (id: number) => `/predictions/${id}`,
  predictionPdf: (id: number) => `/predictions/${id}/pdf`,

  vetDashboard: '/veterinarian/dashboard',
  vetCommunications: '/veterinarian/communications',
  sendFarmerAlert: '/veterinarian/alerts/send',
  scheduleFarmerMeeting: '/veterinarian/meetings/schedule',
  vetProfile: '/veterinarian/profile',
  farmerMapping: '/veterinarian/farmers',
  predictionsReview: '/veterinarian/predictions',
  treatmentSuggestions: '/veterinarian/treatments',
  addTreatment: (id: number) => `/veterinarian/predictions/${id}/treatment`,
  mortalityReports: '/veterinarian/mortality',

  orgAdminDashboard: '/organization/dashboard',
  orgAdminProfile: '/organization/profile',
  orgAdminUsers: '/organization/user_management',
  approveUser: (id: number) => `/organization/users/${id}/approve`,
  rejectUser: (id: number) => `/organization/users/${id}/reject`,
  deleteUser: (id: number) => `/organization/users/${id}/delete`,
  orgReports: '/organization/reports',
  orgReportsPdf: '/organization/reports/pdf',

  sysAdminDashboard: '/system/dashboard',
  systemLogs: '/system/logs',
  performanceReports: '/system/performance',
  modelUpdates: '/system/updates',

  // Existing JSON endpoints
  reviewPrediction: (id: number) => `/api/predictions/${id}/review`,
  approveTreatment: (id: number) => `/api/treatments/${id}/approve`,
} as const;
