import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Library from "./pages/Library";
import PromptDetail from "./pages/PromptDetail";
import Builder from "./pages/Builder";
import Assistant from "./pages/Assistant";
import Workflows from "./pages/Workflows";
import AnalyticsPage from "./pages/Analytics";
import Governance from "./pages/Governance";
import Audit from "./pages/Audit";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/library" element={<Library />} />
        <Route path="/prompts/:id" element={<PromptDetail />} />
        <Route path="/builder" element={<Builder />} />
        <Route path="/builder/:id" element={<Builder />} />
        <Route path="/assistant" element={<Assistant />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/governance" element={<Governance />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}