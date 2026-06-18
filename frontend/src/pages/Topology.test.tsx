import { screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { Topology } from "./Topology";
import { mockFetch, renderWithProviders } from "../test/utils";

describe("Topology", () => {
  test("renders services and flags impacted ones", async () => {
    mockFetch({
      "/api/v1/topology": {
        nodes: [
          { service: "payment-api", depends_on: ["postgres"], impacted: true },
          { service: "postgres", depends_on: [], impacted: false },
        ],
        edges: [{ source: "payment-api", target: "postgres" }],
      },
    });

    renderWithProviders(<Topology />);

    expect(await screen.findByText("payment-api")).toBeInTheDocument();
    expect(screen.getByText("postgres")).toBeInTheDocument();
    expect(screen.getByText("impacted")).toBeInTheDocument();
  });
});
