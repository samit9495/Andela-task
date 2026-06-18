import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { AIAnalysis } from "./pages/AIAnalysis";
import { IncidentCenter } from "./pages/IncidentCenter";
import { Overview } from "./pages/Overview";
import { Topology } from "./pages/Topology";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="incidents" element={<IncidentCenter />} />
        <Route path="incidents/:id" element={<AIAnalysis />} />
        <Route path="topology" element={<Topology />} />
      </Route>
    </Routes>
  );
}
