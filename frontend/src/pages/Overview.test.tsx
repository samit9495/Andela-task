import { screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { Overview } from "./Overview";
import { mockFetch, renderWithProviders } from "../test/utils";

describe("Overview", () => {
  test("shows the platform risk score and band", async () => {
    mockFetch({
      "/metrics": {
        total_events: 120,
        events_by_level: { ERROR: 40 },
        monitored_services: 3,
        total_incidents: 2,
        total_alerts: 5,
        risk_score: 72.5,
      },
      "/api/v1/risk-score": {
        score: 72.5,
        status: "Warning",
        error_penalty: 10,
        alert_penalty: 5,
        incident_penalty: 12.5,
      },
    });

    renderWithProviders(<Overview />);

    expect(await screen.findByText("Warning")).toBeInTheDocument();
    expect(await screen.findByText(/72\.5/)).toBeInTheDocument();
    expect(await screen.findByText("120")).toBeInTheDocument();
  });
});
