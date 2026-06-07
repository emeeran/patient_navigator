import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { patientsApi } from "./index";
import type { Patient } from "../types";

// ── Patient hooks ────────────────────────────────────
export function usePatients(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["patients", params],
    queryFn: async () => (await patientsApi.list(params)).data,
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: ["patient", id],
    queryFn: async () => (await patientsApi.get(id)).data,
    enabled: !!id,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Patient>) => patientsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["patients"] }),
  });
}

export function useUpdatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Patient> }) =>
      patientsApi.update(id, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["patients"] });
      qc.invalidateQueries({ queryKey: ["patient", variables.id] });
    },
  });
}
