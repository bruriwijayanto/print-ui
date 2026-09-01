export type JobStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "CANCELED" | "FAILED" | "UNKNOWN";

export interface JobSummary {
  job_id: number;
  printer: string;
  document: string;
  user: string;
  submitted_at: string | null;
  status: JobStatus;
}

export interface JobDetail extends JobSummary {
  owner: string;
  started_at: string | null;
  completed_at: string | null;
  options: Record<string, string>;
  error: string | null;
}

export interface JobCancelResponse {
  success: boolean;
  job_id: number;
  status: string;
}
