// TypeScript interfaces generated from backend API

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: string;
  permissions: Record<string, string>;
  is_active: boolean;
  last_login_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface Patient {
  id: string;
  full_name: string;
  age: number;
  gender: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface Case {
  id: string;
  patient_id: string;
  diagnosis: string;
  status: string;
  priority: string;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface Document {
  id: string;
  case_id: string;
  original_filename: string;
  stored_filename: string;
  file_type: string;
  file_size_bytes: number;
  mime_type: string;
  ocr_status: string;
  ocr_processed_at: string | null;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface Hospital {
  id: string;
  name: string;
  city: string;
  state: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  specialties: string | null;
  has_financial_assistance: boolean;
  rating: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FundingProgram {
  id: string;
  name: string;
  description: string | null;
  provider: string | null;
  program_type: string | null;
  eligibility_criteria: string | null;
  max_amount: number | null;
  min_amount: number | null;
  application_url: string | null;
  deadline: string | null;
  is_active: boolean;
  contact_email: string | null;
  contact_phone: string | null;
}

export interface FollowUp {
  id: string;
  case_id: string;
  scheduled_date: string;
  follow_up_type: string;
  status: string;
  notes: string | null;
  completed_at: string | null;
  completed_by: string | null;
  reminder_sent: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface AIResponse {
  content: string;
  disclaimer: string;
  model: string | null;
}

export interface OCRResult {
  id: string;
  ocr_status: string;
  ocr_text: string | null;
  ocr_processed_at: string | null;
}

export interface DocumentPreview {
  id: string;
  case_id: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  mime_type: string;
  ocr_status: string;
  ocr_text: string | null;
  ocr_processed_at: string | null;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}
