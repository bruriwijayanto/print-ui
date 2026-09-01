import { Route, Routes } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { RequireAuth } from "@/components/RequireAuth";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Printers from "@/pages/Printers";
import PrinterDetail from "@/pages/PrinterDetail";
import Print from "@/pages/Print";
import Jobs from "@/pages/Jobs";
import JobDetail from "@/pages/JobDetail";
import Settings from "@/pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="printers" element={<Printers />} />
          <Route path="printers/:printerName" element={<PrinterDetail />} />
          <Route path="print" element={<Print />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="jobs/:jobId" element={<JobDetail />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Route>
    </Routes>
  );
}
