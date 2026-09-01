import type { ComponentType } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock, Printer, PrinterCheck, XCircle } from "lucide-react";
import { jobApi, printerApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { PrinterStateBadge, JobStatusBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/QueryState";
import { cn, formatDateTime } from "@/lib/utils";

function isToday(isoString: string | null): boolean {
  if (!isoString) return false;
  const date = new Date(isoString);
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
}

export default function Dashboard() {
  const printersQuery = useQuery({
    queryKey: ["printers"],
    queryFn: printerApi.getPrinters,
    refetchInterval: 5000,
  });
  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: jobApi.getJobs,
    refetchInterval: 4000,
  });

  if (printersQuery.isLoading || jobsQuery.isLoading) return <LoadingState />;
  if (printersQuery.isError) return <ErrorState error={printersQuery.error} onRetry={() => printersQuery.refetch()} />;
  if (jobsQuery.isError) return <ErrorState error={jobsQuery.error} onRetry={() => jobsQuery.refetch()} />;

  const printers = printersQuery.data ?? [];
  const jobs = jobsQuery.data ?? [];

  const stats = {
    total: printers.length,
    online: printers.filter((p) => p.state !== "STOPPED" && p.state !== "ERROR").length,
    printing: printers.filter((p) => p.state === "PRINTING").length,
    queued: jobs.filter((j) => j.status === "PENDING" || j.status === "PROCESSING").length,
    completedToday: jobs.filter((j) => j.status === "COMPLETED" && isToday(j.submitted_at)).length,
    failedToday: jobs.filter((j) => j.status === "FAILED" && isToday(j.submitted_at)).length,
  };

  const recentJobs = [...jobs].sort((a, b) => b.job_id - a.job_id).slice(0, 5);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Total Printers" value={stats.total} icon={Printer} tone="indigo" />
        <StatCard label="Online" value={stats.online} icon={CheckCircle2} tone="emerald" />
        <StatCard label="Printing" value={stats.printing} icon={PrinterCheck} tone="blue" />
        <StatCard label="Queued Jobs" value={stats.queued} icon={Clock} tone="amber" />
        <StatCard label="Completed Today" value={stats.completedToday} icon={CheckCircle2} tone="emerald" />
        <StatCard label="Failed Today" value={stats.failedToday} icon={XCircle} tone="red" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Printer Status</CardTitle>
        </CardHeader>
        <CardContent>
          {printers.length === 0 ? (
            <EmptyState label="Belum ada printer terdaftar di CUPS." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Printer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Current Job</TableHead>
                  <TableHead>Queue</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {printers.map((printer) => (
                  <TableRow key={printer.name}>
                    <TableCell className="font-medium">{printer.name}</TableCell>
                    <TableCell>
                      <PrinterStateBadge state={printer.state} />
                    </TableCell>
                    <TableCell>{printer.current_job ?? "-"}</TableCell>
                    <TableCell>{printer.queue_count}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(new Date(printersQuery.dataUpdatedAt).toISOString())}
                    </TableCell>
                    <TableCell>
                      <Link to={`/printers/${encodeURIComponent(printer.name)}`} className="text-sm font-medium text-primary underline underline-offset-4">
                        Detail
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {recentJobs.length === 0 ? (
            <EmptyState label="Belum ada print job." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job</TableHead>
                  <TableHead>Printer</TableHead>
                  <TableHead>Document</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentJobs.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell>
                      <Link to={`/jobs/${job.job_id}`} className="font-medium text-primary underline underline-offset-4">
                        #{job.job_id}
                      </Link>
                    </TableCell>
                    <TableCell>{job.printer}</TableCell>
                    <TableCell>{job.document || "-"}</TableCell>
                    <TableCell>
                      <JobStatusBadge status={job.status} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(job.submitted_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

const TONE_CLASSES: Record<string, string> = {
  indigo: "bg-indigo-50 text-indigo-600",
  emerald: "bg-emerald-50 text-emerald-600",
  blue: "bg-blue-50 text-blue-600",
  amber: "bg-amber-50 text-amber-600",
  red: "bg-red-50 text-red-600",
};

function StatCard({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  icon: ComponentType<{ className?: string }>;
  tone: keyof typeof TONE_CLASSES;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", TONE_CLASSES[tone])}>
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold leading-tight">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}
