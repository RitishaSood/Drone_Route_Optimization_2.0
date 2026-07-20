import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Link, Outlet, createRootRouteWithContext, useRouter } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { reportLovableError } from "../lib/lovable-error-reporting";
import { ScenarioProvider } from "@/state/scenario";

function NotFoundComponent() {
  return (
    <div className="page">
      <div className="empty-state">
        <h2 style={{ margin: 0 }}>404 - Page not found</h2>
        <p style={{ marginTop: 8 }}>
          <Link to="/simulation">Return to Simulation Setup</Link>
        </p>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();

  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="page">
      <div className="alert alert-error">
        <strong>This page did not load.</strong> {error.message}
      </div>
      <button
        className="btn"
        onClick={() => {
          router.invalidate();
          reset();
        }}
      >
        Try again
      </button>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function TopNav() {
  const [clientIdShort, setClientIdShort] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const value = window.localStorage.getItem("uav.clientId");
    if (value) setClientIdShort(value.slice(0, 8));
  }, []);

  return (
    <nav className="topnav" aria-label="Primary">
      <div className="topnav-inner">
        <div className="topnav-brand">UAV Route Optimization</div>
        <div className="topnav-links">
          <Link to="/simulation" className="topnav-link" activeOptions={{ exact: false }}>
            Simulation
          </Link>
          <Link to="/results" className="topnav-link">
            Results
          </Link>
          <Link to="/drones" className="topnav-link">
            Drone Database
          </Link>
          <Link to="/methodology" className="topnav-link">
            Methodology
          </Link>
          <Link to="/swarm-study" className="topnav-link">
            Swarm Study
          </Link>
        </div>
        <div className="topnav-meta">
          {clientIdShort ? (
            <>
              Client <strong>{clientIdShort}</strong>
            </>
          ) : null}
        </div>
      </div>
    </nav>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <ScenarioProvider>
        <TopNav />
        <Outlet />
      </ScenarioProvider>
    </QueryClientProvider>
  );
}
