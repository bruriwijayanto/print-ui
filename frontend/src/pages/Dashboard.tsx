import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { jobApi, printerApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { PrinterStateBadge, JobStatusBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/QueryState";
import { formatDateTime } from "@/lib/utils";

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
        <StatCard label="Total Printers" value={stats.total} />
        <StatCard label="Online" value={stats.online} />
        <StatCard label="Printing" value={stats.printing} />
        <StatCard label="Queued Jobs" value={stats.queued} />
        <StatCard label="Completed Today" value={stats.completedToday} />
        <StatCard label="Failed Today" value={stats.failedToday} />
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

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent className="pt-0 text-2xl font-semibold">{value}</CardContent>
    </Card>
  );
}
