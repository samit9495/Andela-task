import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test } from "vitest";

import { App } from "./App";
import { mockFetch, renderWithProviders } from "./test/utils";

const incident = {
  id: 1,
  title: "Degradation in payment-api",
  service: "payment-api",
  category: "database",
  severity: "CRITICAL",
  status: "OPEN",
  root_cause: "Database connection pool exhausted",
  summary: "Payment API is failing due to database timeouts.",
  confidence_score: 0.9,
  recommended_actions: ["Increase the connection pool size"],
  runbook_references: [{ slug: "database_timeout", title: "Database Timeout" }],
  created_at: "2026-06-18T10:00:00Z",
  updated_at: "2026-06-18T10:00:00Z",
  resolved_at: null,
  anomalies: [],
};

describe("Incident Center → AI Analysis", () => {
  test("clicking an incident opens its AI analysis", async () => {
    mockFetch({
      "/api/v1/incidents/1": incident,
      "/api/v1/incidents": [incident],
    });

    renderWithProviders(<App />, "/incidents");

    const row = await screen.findByText("Degradation in payment-api");
    await userEvent.click(row);

    expect(await screen.findByRole("heading", { name: /ai analysis/i })).toBeInTheDocument();
    expect(screen.getByText(/Database connection pool exhausted/)).toBeInTheDocument();
    expect(screen.getByText("Increase the connection pool size")).toBeInTheDocument();
  });
});
