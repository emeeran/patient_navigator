import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./contexts/AuthContext";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import LoadingSpinner from "./components/LoadingSpinner";
import { queryClient } from "./lib/queryClient";

// Login page is always needed — keep as static import
import LoginPage from "./pages/LoginPage";

// Lazy-load all other route pages for code splitting
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const PatientsPage = lazy(() => import("./pages/PatientsPage"));
const PatientDetailPage = lazy(() => import("./pages/PatientDetailPage"));
const CasesPage = lazy(() => import("./pages/CasesPage"));
const CaseDetailPage = lazy(() => import("./pages/CaseDetailPage"));
const HospitalsPage = lazy(() => import("./pages/HospitalsPage"));
const HospitalDetailPage = lazy(() => import("./pages/HospitalDetailPage"));
const FundingPage = lazy(() => import("./pages/FundingPage"));
const FundingDetailPage = lazy(() => import("./pages/FundingDetailPage"));
const FollowUpsPage = lazy(() => import("./pages/FollowUpsPage"));
const AIAssistantPage = lazy(() => import("./pages/AIAssistantPage"));
const AdminUsersPage = lazy(() => import("./pages/AdminUsersPage"));
const AuditLogPage = lazy(() => import("./pages/AuditLogPage"));
const ScraperPage = lazy(() => import("./pages/ScraperPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
            <Suspense fallback={<LoadingSpinner />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/patients" element={<PatientsPage />} />
                  <Route path="/patients/:patientId" element={<PatientDetailPage />} />
                  <Route path="/cases" element={<CasesPage />} />
                  <Route path="/cases/:caseId" element={<CaseDetailPage />} />
                  <Route path="/hospitals" element={<HospitalsPage />} />
                  <Route path="/hospitals/:hospitalId" element={<HospitalDetailPage />} />
                  <Route path="/funding" element={<FundingPage />} />
                  <Route path="/funding/:fundingId" element={<FundingDetailPage />} />
                  <Route path="/follow-ups" element={<FollowUpsPage />} />
                  <Route path="/ai-assistant" element={<AIAssistantPage />} />
                  <Route path="/admin/users" element={<AdminUsersPage />} />
                  <Route path="/admin/data-scraper" element={<ScraperPage />} />
                  <Route path="/admin/audit-log" element={<AuditLogPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
