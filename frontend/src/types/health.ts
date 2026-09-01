export interface HealthStatus {
  status: "ok" | "degraded";
  cups: "connected" | "disconnected";
  printers?: number;
}
