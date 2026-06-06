-- Seed roles, users, patients, cases
-- Password: TestPass123! (bcrypt hash below)

INSERT INTO roles (id, name, description, permissions) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'admin', 'Admin', '{"patients":"full","cases":"full","documents":"full","hospitals":"full","funding":"full","followups":"full","ai":"full","reports":"full","users":"full","audit":"full","settings":"full"}'),
  ('a0000000-0000-0000-0000-000000000002', 'navigator', 'Navigator', '{"patients":"full","cases":"full","documents":"full","hospitals":"read","funding":"read","followups":"full","ai":"full","reports":"read"}'),
  ('a0000000-0000-0000-0000-000000000003', 'clinician', 'Clinician', '{"patients":"read","cases":"read","documents":"read","hospitals":"read","funding":"read","followups":"read","ai":"review","reports":"read"}'),
  ('a0000000-0000-0000-0000-000000000004', 'volunteer', 'Volunteer', '{"patients":"read","cases":"read","documents":"none","hospitals":"read","funding":"read","followups":"read"}'),
  ('a0000000-0000-0000-0000-000000000005', 'patient', 'Patient', '{"patients":"own","cases":"own","documents":"own","hospitals":"read","funding":"read","followups":"own"}')
ON CONFLICT (id) DO UPDATE SET permissions = EXCLUDED.permissions;

INSERT INTO users (id, email, password_hash, full_name, role_id, is_active) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'admin@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Test Admin', 'a0000000-0000-0000-0000-000000000001', true),
  ('b0000000-0000-0000-0000-000000000002', 'navigator@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Test Navigator', 'a0000000-0000-0000-0000-000000000002', true),
  ('b0000000-0000-0000-0000-000000000003', 'clinician@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Test Clinician', 'a0000000-0000-0000-0000-000000000003', true),
  ('b0000000-0000-0000-0000-000000000004', 'volunteer@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Test Volunteer', 'a0000000-0000-0000-0000-000000000004', true),
  ('b0000000-0000-0000-0000-000000000005', 'patient@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Test Patient', 'a0000000-0000-0000-0000-000000000005', true),
  ('b0000000-0000-0000-0000-000000000006', 'disabled@test.com', '$2b$12$Ng7gQAqBiHtXKjlFHy4YpujRlE.acMXfkRHHUP585HD9ZeHMliO.K', 'Disabled Navigator', 'a0000000-0000-0000-0000-000000000002', false)
ON CONFLICT (id) DO UPDATE SET password_hash = EXCLUDED.password_hash, is_active = EXCLUDED.is_active, role_id = EXCLUDED.role_id;

INSERT INTO patients (id, full_name, age, gender, phone, email, address, emergency_contact_name, emergency_contact_phone, status, created_by) VALUES
  ('c0000000-0000-0000-0000-000000000001', 'Aarav Mehta', 45, 'male', '+919876543210', 'aarav@example.org', '123 Main St, Mumbai', 'Priya Mehta', '+919876543211', 'active', 'b0000000-0000-0000-0000-000000000002'),
  ('c0000000-0000-0000-0000-000000000002', 'Arun Kumar', 32, 'male', '+919998887776', NULL, NULL, NULL, NULL, 'active', 'b0000000-0000-0000-0000-000000000002'),
  ('c0000000-0000-0000-0000-000000000003', 'Priya Sharma', 28, 'female', '+919112233445', 'priya@example.org', NULL, NULL, NULL, 'active', 'b0000000-0000-0000-0000-000000000002')
ON CONFLICT (id) DO NOTHING;

INSERT INTO cases (id, patient_id, diagnosis, status, priority, notes, created_by) VALUES
  ('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Stage 2B Oral Cancer', 'new', 'high', 'Biopsy confirmed', 'b0000000-0000-0000-0000-000000000002'),
  ('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 'Hypertension', 'under_review', 'medium', NULL, 'b0000000-0000-0000-0000-000000000002'),
  ('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000002', 'Type 2 Diabetes', 'closed', 'low', NULL, 'b0000000-0000-0000-0000-000000000002')
ON CONFLICT (id) DO NOTHING;
