import api from "./client";
import type { AuthResponse, User } from "../types";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>("/auth/login", { email, password }),

  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    phone?: string;
  }) => api.post<AuthResponse>("/auth/register", data),

  refresh: (refresh_token: string) =>
    api.post<AuthResponse>("/auth/refresh", { refresh_token }),

  logout: (refresh_token: string) =>
    api.post("/auth/logout", { refresh_token }),

  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }),

  updateProfile: (data: { full_name?: string; phone?: string }) =>
    api.patch<User>("/auth/me", data),

  getProfile: () => api.get<User>("/auth/me"),
};
