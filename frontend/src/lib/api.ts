import type { HealthStatus } from "@/types/health";
import type { JobCancelResponse, JobDetail, JobSummary } from "@/types/job";
import type { PrinterDetail, PrinterSummary } from "@/types/printer";
import type { PrintOptions, PrintJobResponse } from "@/types/print";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);

  if (!response.ok) {
    let code = "UNKNOWN_ERROR";
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      code = body?.detail?.code ?? code;
      message = body?.detail?.message ?? message;
    } catch {
      // response body wasn't JSON — keep the generic message above.
    }
    throw new ApiError(response.status, code, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const healthApi = {
  get: () => request<HealthStatus>("/health"),
};

export const printerApi = {
  getPrinters: () => request<PrinterSummary[]>("/printers"),
  getPrinter: (name: string) => request<PrinterDetail>(`/printers/${encodeURIComponent(name)}`),
  getPrinterJobs: (name: string) => request<JobSummary[]>(`/printers/${encodeURIComponent(name)}/jobs`),
  pause: (name: string) => request<void>(`/printers/${encodeURIComponent(name)}/pause`, { method: "POST" }),
  resume: (name: string) => request<void>(`/printers/${encodeURIComponent(name)}/resume`, { method: "POST" }),
  enable: (name: string) => request<void>(`/printers/${encodeURIComponent(name)}/enable`, { method: "POST" }),
  disable: (name: string) => request<void>(`/printers/${encodeURIComponent(name)}/disable`, { method: "POST" }),
};

export const jobApi = {
  getJobs: () => request<JobSummary[]>("/jobs"),
  getJob: (jobId: number) => request<JobDetail>(`/jobs/${jobId}`),
  cancelJob: (jobId: number) => request<JobCancelResponse>(`/jobs/${jobId}`, { method: "DELETE" }),
};

export const printApi = {
  printDocument: (file: File, options: PrintOptions) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("printer", options.printer);
    formData.append("copies", String(options.copies));
    if (options.page_ranges) formData.append("page_ranges", options.page_ranges);
    if (options.media) formData.append("media", options.media);
    if (options.orientation) formData.append("orientation", options.orientation);
    if (options.color) formData.append("color", options.color);
    if (options.duplex) formData.append("duplex", options.duplex);

    return request<PrintJobResponse>("/print", { method: "POST", body: formData });
  },
};
