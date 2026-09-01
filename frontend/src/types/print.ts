export interface PrintOptions {
  printer: string;
  copies: number;
  page_ranges?: string;
  media?: string;
  orientation?: string;
  color?: string;
  duplex?: string;
}

export interface PrintJobResponse {
  success: boolean;
  job_id: number;
  printer: string;
  filename: string;
  status: string;
}
