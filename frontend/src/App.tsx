import React from "react";
import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";
import {
  Cpu,
  Settings,
  AlertTriangle,
  BarChart2,
  Database,
} from "lucide-react";
import { lazy, Suspense } from "react";

const ExecutiveDashboard = lazy(() => import("./pages/ExecutiveDashboard"));
const FleetRegistry = lazy(() => import("./pages/FleetRegistry"));
const MachineTwin = lazy(() => import("./pages/MachineTwin"));
const AlertIntelligence = lazy(() => import("./pages/AlertIntelligence"));
const HistoricalAnalytics = lazy(() => import("./pages/HistoricalAnalytics"));

const PageLoading = () => (
  <div className="flex h-full items-center justify-center bg-[#0d0f12] text-gray-400">
    <div className="text-center space-y-2 font-mono text-xs">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
      <p className="tracking-widest uppercase">Loading Control Panel...</p>
    </div>
  </div>
);

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0d0f12] text-gray-200 font-mono">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#11141a] border-r border-border flex flex-col justify-between flex-shrink-0">
        <div>
          {/* Logo Section */}
          <div className="p-6 border-b border-border flex items-center gap-2.5">
            <Database className="h-6 w-6 text-primary" />
            <div>
              <h2 className="text-sm font-bold tracking-wider text-white uppercase">
                AutoForge
              </h2>
              <span className="text-[9px] text-muted-foreground uppercase">
                Industrial Intelligence
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${isActive ? "bg-primary text-white font-bold" : "text-gray-400 hover:bg-[#1c222c] hover:text-white"}`
              }
            >
              <Cpu className="h-4 w-4" />
              <span>Executive Dashboard</span>
            </NavLink>
            <NavLink
              to="/machines"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${isActive ? "bg-primary text-white font-bold" : "text-gray-400 hover:bg-[#1c222c] hover:text-white"}`
              }
            >
              <Settings className="h-4 w-4" />
              <span>Machine Registry</span>
            </NavLink>
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${isActive ? "bg-primary text-white font-bold" : "text-gray-400 hover:bg-[#1c222c] hover:text-white"}`
              }
            >
              <AlertTriangle className="h-4 w-4" />
              <span>Alert Intelligence</span>
            </NavLink>
            <NavLink
              to="/analytics"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${isActive ? "bg-primary text-white font-bold" : "text-gray-400 hover:bg-[#1c222c] hover:text-white"}`
              }
            >
              <BarChart2 className="h-4 w-4" />
              <span>Intelligence Center</span>
            </NavLink>
          </nav>
        </div>

        {/* Footer/Identity */}
        <div className="p-4 border-t border-border bg-[#0d0f12]/30 text-xs text-muted-foreground space-y-1">
          <p className="font-semibold tracking-wider">PROD CONTROL v0.3.0</p>
          <p className="text-[10px] text-muted-foreground/80">DB STATUS: ATHENA OK</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
}

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Suspense fallback={<PageLoading />}>
            <Routes>
              <Route path="/" element={<ExecutiveDashboard />} />
              <Route path="/machines" element={<FleetRegistry />} />
              <Route path="/machine/:id" element={<MachineTwin />} />
              <Route path="/alerts" element={<AlertIntelligence />} />
              <Route path="/analytics" element={<HistoricalAnalytics />} />
            </Routes>
          </Suspense>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}
