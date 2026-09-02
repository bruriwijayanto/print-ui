import type { HealthStatus } from "@/types/health";
import type { JobCancelResponse, JobDetail, JobSummary } from "@/types/job";
import type { PrinterDetail, PrinterSummary } from "@/types/printer";
import type { PrintOptions, PrintJobResponse } from "@/types/print";
import { clearApiKey, getApiKey } from "@/lib/auth";

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
  const headers = new Headers(init?.headers);
  const apiKey = getApiKey();
  if (apiKey) headers.set("Authorization", `Bearer ${apiKey}`);

  const response = await fetch(`/api${path}`, { ...init, headers });

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

    if (response.status === 401) {
      // Stored key is missing/invalid/rotated — force a fresh login rather
      // than leaving the SPA stuck making requests that will never succeed.
      clearApiKey();
      if (location.pathname !== "/login") location.assign("/login");
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

export const authApi = {
  login: (username: string, password: string) =>
    request<{ token: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    }),
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
