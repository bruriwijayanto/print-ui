import { Badge, type BadgeProps } from "@/components/ui/badge";

const PRINTER_STATE_VARIANT: Record<string, BadgeProps["variant"]> = {
  IDLE: "success",
  PRINTING: "info",
  STOPPED: "warning",
  ERROR: "destructive",
  UNKNOWN: "default",
};

const JOB_STATUS_VARIANT: Record<string, BadgeProps["variant"]> = {
  PENDING: "default",
  PROCESSING: "info",
  COMPLETED: "success",
  CANCELED: "warning",
  FAILED: "destructive",
  UNKNOWN: "default",
};

export function PrinterStateBadge({ state }: { state: string }) {
  return <Badge variant={PRINTER_STATE_VARIANT[state] ?? "default"}>{state}</Badge>;
}

export function JobStatusBadge({ status }: { status: string }) {
  return <Badge variant={JOB_STATUS_VARIANT[status] ?? "default"}>{status}</Badge>;
}
