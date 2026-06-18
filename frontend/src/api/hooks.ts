import { useQuery } from "@tanstack/react-query";

import { apiGet } from "./client";
import type { Alert, Incident, Metrics, RiskScore, Topology } from "../types";

const REFETCH_MS = 5000;

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: () => apiGet<Metrics>("/metrics"),
    refetchInterval: REFETCH_MS,
  });
}

export function useRiskScore() {
  return useQuery({
    queryKey: ["risk-score"],
    queryFn: () => apiGet<RiskScore>("/api/v1/risk-score"),
    refetchInterval: REFETCH_MS,
  });
}

export function useIncidents() {
  return useQuery({
    queryKey: ["incidents"],
    queryFn: () => apiGet<Incident[]>("/api/v1/incidents"),
    refetchInterval: REFETCH_MS,
  });
}

export function useIncident(id: number) {
  return useQuery({
    queryKey: ["incident", id],
    queryFn: () => apiGet<Incident>(`/api/v1/incidents/${id}`),
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: () => apiGet<Alert[]>("/api/v1/alerts"),
    refetchInterval: REFETCH_MS,
  });
}

export function useTopology() {
  return useQuery({
    queryKey: ["topology"],
    queryFn: () => apiGet<Topology>("/api/v1/topology"),
    refetchInterval: REFETCH_MS,
  });
}
