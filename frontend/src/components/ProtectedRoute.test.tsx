import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../contexts/AuthContext";
import ProtectedRoute from "./ProtectedRoute";

function renderWithProviders(ui: React.ReactElement, { route = "/" } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("redirects to /login when not authenticated", () => {
    renderWithProviders(
      <ProtectedRoute>
        <div>Secret content</div>
      </ProtectedRoute>
    );
    // The child content should NOT be rendered
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    // Pre-seed a token so isAuthenticated is true
    localStorage.setItem("access_token", "test-token");
    localStorage.setItem(
      "user",
      JSON.stringify({ id: 1, email: "test@test.com", full_name: "Test", role: "admin" })
    );

    renderWithProviders(
      <ProtectedRoute>
        <div>Secret content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText("Secret content")).toBeInTheDocument();

    // Clean up
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  });
});
