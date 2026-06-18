---
name: andela-frontend-react
description: React + Vite + TypeScript + Recharts scaffolding recipe for the 5 dashboard pages. Use when adding a page, component, or chart. Browser MCP for runtime inspection.
---

# Andela Frontend React Scaffold

## Trigger

Use when asked to: add a page, scaffold a component, wire a chart, query the API from the UI, inspect the running dashboard.

## Context

The frontend has exactly 5 pages (Req. doc Component 13):

1. Overview — risk score, active incidents, alerts, services
2. Incident Center — incident list with severity, status, root cause, confidence
3. Topology View — service graph, dependency tree, blast radius
4. Trends — error rate, incident timeline, severity distribution, health
5. AI Analysis — classification, root cause, remediation, executive summary, runbook references

Stack: React 18 + Vite + TypeScript (strict) + Recharts + TanStack Query + React Router. Vitest + RTL for tests.

## Recipe (test-first, per page or component)

### Step 0 — RED: write the smallest behavioral test

```tsx
// frontend/src/components/overview/RiskScoreGauge.test.tsx
import { render, screen } from "@testing-library/react";
import { RiskScoreGauge } from "./RiskScoreGauge";

test("displays the risk score and the Healthy band when score >= 90", () => {
  render(<RiskScoreGauge score={95} />);
  expect(screen.getByText("95")).toBeInTheDocument();
  expect(screen.getByText(/healthy/i)).toBeInTheDocument();
});
```

Run it. Confirm failure. Commit `test: ...`.

### Step 1 — Add the typed API contract (mirror the backend Pydantic schema)

```ts
// frontend/src/types/api.ts
export type Severity = "critical" | "high" | "medium" | "low";
export type IncidentStatus = "open" | "investigating" | "mitigated" | "resolved";

export interface Incident {
  id: number;
  title: string;
  severity: Severity;
  status: IncidentStatus;
  created_at: string;
  resolved_at: string | null;
  root_cause: string | null;
  summary: string | null;
}

export interface RiskScore {
  score: number;          // 0-100
  band: "healthy" | "warning" | "critical";
  generated_at: string;
}
```

### Step 2 — Add the typed fetcher (single boundary that talks to the backend)

```ts
// frontend/src/api/risk.ts
import type { RiskScore } from "../types/api";

export async function getRiskScore(): Promise<RiskScore> {
  const res = await fetch("/api/v1/risk-score");
  if (!res.ok) throw new Error(`risk-score: ${res.status}`);
  return res.json();
}
```

### Step 3 — Add the hook (TanStack Query)

```ts
// frontend/src/hooks/useRiskScore.ts
import { useQuery } from "@tanstack/react-query";
import { getRiskScore } from "../api/risk";

export const useRiskScore = () =>
  useQuery({ queryKey: ["risk-score"], queryFn: getRiskScore, refetchInterval: 30_000 });
```

### Step 4 — Add the component

```tsx
// frontend/src/components/overview/RiskScoreGauge.tsx
interface RiskScoreGaugeProps {
  score: number;
}

export function RiskScoreGauge({ score }: RiskScoreGaugeProps) {
  const band = score >= 90 ? "Healthy" : score >= 70 ? "Warning" : "Critical";
  return (
    <div className={`risk-gauge band-${band.toLowerCase()}`}>
      <span className="risk-score-value">{score}</span>
      <span className="risk-band-label">{band}</span>
    </div>
  );
}
```

Run the test. Green. Commit `feat: ...`.

### Step 5 — Compose into the page

```tsx
// frontend/src/pages/OverviewPage.tsx
import { useRiskScore } from "../hooks/useRiskScore";
import { RiskScoreGauge } from "../components/overview/RiskScoreGauge";

export function OverviewPage() {
  const { data, isLoading, error } = useRiskScore();
  if (isLoading) return <div>Loading…</div>;
  if (error) return <div>Failed to load risk score</div>;
  return <RiskScoreGauge score={data!.score} />;
}
```

### Step 6 — Browser MCP verification

Use the Browser MCP (configured in `.cursor/mcp.json`) to:

1. Visit `http://localhost:5173/`
2. Verify the gauge renders.
3. Verify it refetches every 30s.
4. Capture a screenshot for the deck.

## Recharts patterns

- One chart per Recharts container.
- Chart components receive prepared data; they do not fetch.

```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

interface ErrorRateChartProps {
  data: { t: string; rate: number }[];
}

export function ErrorRateChart({ data }: ErrorRateChartProps) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data}>
        <XAxis dataKey="t" />
        <YAxis />
        <Tooltip />
        <Line dataKey="rate" type="monotone" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

## Anti-patterns

- Fetch in `useEffect`. Use TanStack Query.
- Inline styles for anything but truly one-off rules.
- A 500-line page. Split into components.
- Calling `/api/...` directly from a component — go through `src/api/`.
- Snapshot tests. Behavioral tests only.

## Checklist

- [ ] Failing component test (RED) committed first
- [ ] Types in `src/types/api.ts` mirror the backend Pydantic schema
- [ ] Fetcher in `src/api/<resource>.ts` is the only network boundary
- [ ] TanStack Query hook for server state; no manual loading/error state
- [ ] One component per file, named export, explicit props interface
- [ ] No `any`; strict TS passes
- [ ] Browser MCP run to verify the page renders against a real backend (or MSW)

## See also

- Rule: `.cursor/rules/andela-frontend-react.mdc`
- Rule: `.cursor/rules/andela-testing.mdc`
- Rule: `.cursor/rules/andela-project-map.mdc`
- Skill: `.cursor/skills/andela-tdd-loop/SKILL.md`
