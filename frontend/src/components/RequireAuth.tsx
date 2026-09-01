import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getApiKey } from "@/lib/auth";

export function RequireAuth() {
  const location = useLocation();

  if (!getApiKey()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
