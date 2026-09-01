export type PrinterState = "IDLE" | "PRINTING" | "STOPPED" | "ERROR" | "UNKNOWN";

export interface PrinterSummary {
  name: string;
  description: string;
  state: PrinterState;
  state_message: string;
  accepting_jobs: boolean;
  shared: boolean;
  device_uri: string | null;
  current_job: number | null;
  queue_count: number;
}

export interface PrinterCapabilities {
  media: string[];
  color: boolean;
  duplex: boolean;
  resolution: string[];
  copies_supported: boolean;
  max_copies: number | null;
  page_ranges_supported: boolean;
  orientation_supported: boolean;
}

export interface PrinterDetail extends PrinterSummary {
  location: string | null;
  manufacturer: string | null;
  model: string | null;
  capabilities: PrinterCapabilities;
}
