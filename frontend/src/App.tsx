import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import PatientsPage from "./pages/PatientsPage";
import CasesPage from "./pages/CasesPage";
import HospitalsPage from "./pages/HospitalsPage";
import FundingPage from "./pages/FundingPage";
import FollowUpsPage from "./pages/FollowUpsPage";

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
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/hospitals" element={<HospitalsPage />} />
            <Route path="/funding" element={<FundingPage />} />
            <Route path="/follow-ups" element={<FollowUpsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
