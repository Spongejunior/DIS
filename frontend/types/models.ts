// Shapes of the records the Flask views pass to their templates (see models.py).

export type Role = 'farmer' | 'veterinarian' | 'organization_admin' | 'system_admin';

/** A user reduced to the name fields templates display for other people. */
export interface UserBrief {
  id: number;
  username: string;
  full_name: string | null;
}

export interface User extends UserBrief {
  email: string;
  phone: string | null;
  role: Role;
  location: string | null;
  specific_location: string | null;
  farm_name: string | null;
  animal_types: string | null;
  animal_types_list: string[];
  production_focus: string | null;
  registration_date: string | null;
  last_login: string | null;
  is_active: boolean;
  status: string;
  approved_at: string | null;
  rejected_at: string | null;
  preferred_language: string;
}

export type CurrentUser = User;

export interface SymptomReport {
  id: number;
  report_id: string;
  farmer_id: number;
  animal_name: string | null;
  animal_type: string | null;
  animal_sex: string | null;
  animal_age: number | null;
  temperature: number | null;
  additional_symptoms: string | null;
  status: string | null;
  created_at: string | null;
  symptoms: string[];
  farmer: UserBrief | null;
}

export interface PossibleDisease {
  disease: string;
  probability: number;
}

export interface Prediction {
  id: number;
  prediction_id: string;
  disease_name: string | null;
  disease_category: string | null;
  confidence: number;
  severity: string | null;
  predicted_at: string | null;
  recommendation_text: string | null;
  review_status: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
  possible: PossibleDisease[];
  symptom_report: SymptomReport | null;
}

export interface Treatment {
  id: number;
  treatment_id: string | null;
  medication: string | null;
  dosage: string | null;
  frequency: string | null;
  duration: string | null;
  status: string | null;
  symptom_report: SymptomReport | null;
}

export interface MortalityReport {
  id: number;
  report_id: string;
  animal_type: string | null;
  animal_id: string | null;
  animal_name: string | null;
  breed: string | null;
  date_of_death: string | null;
  suspected_cause: string | null;
  was_dairy: boolean | null;
  requires_investigation: boolean | null;
}

export interface Notification {
  id: number;
  user_id: number;
  sender_id: number | null;
  notification_type: string | null;
  title: string | null;
  message: string | null;
  priority: string | null;
  is_read: boolean;
  created_at: string | null;
  action_url: string | null;
}

export interface SystemLog {
  id: number;
  timestamp: string | null;
  level: string | null;
  component: string | null;
  ip_address: string | null;
  message: string | null;
}

export interface GeneratedReport {
  id: number;
  report_id: string;
  report_type: string | null;
  period_start: string | null;
  period_end: string | null;
  generated_at: string | null;
  is_scheduled: boolean | null;
  schedule_frequency: string | null;
}

/** Lookups keyed by user id (JSON object keys are strings). */
export type UserLookup = Record<string, UserBrief>;
