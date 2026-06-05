import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import PatientsPage from "./pages/PatientsPage";
import CasesPage from "./pages/CasesPage";
import CaseDetailPage from "./pages/CaseDetailPage";
import PatientDetailPage from "./pages/PatientDetailPage";
import HospitalDetailPage from "./pages/HospitalDetailPage";
import FundingDetailPage from "./pages/FundingDetailPage";
import HospitalsPage from "./pages/HospitalsPage";
import FundingPage from "./pages/FundingPage";
import FollowUpsPage from "./pages/FollowUpsPage";
import AIAssistantPage from "./pages/AIAssistantPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AuditLogPage from "./pages/AuditLogPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
            <Route path="/admin/audit-log" element={<AuditLogPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
