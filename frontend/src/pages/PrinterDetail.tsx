import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pause, Play, Send, ShieldCheck, ShieldOff } from "lucide-react";
import { printerApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PrinterStateBadge, JobStatusBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/QueryState";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { formatDateTime } from "@/lib/utils";

export default function PrinterDetail() {
  const { printerName = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const printerQuery = useQuery({
    queryKey: ["printer", printerName],
    queryFn: () => printerApi.getPrinter(printerName),
    refetchInterval: 5000,
  });

  const jobsQuery = useQuery({
    queryKey: ["printer-jobs", printerName],
    queryFn: () => printerApi.getPrinterJobs(printerName),
    refetchInterval: 4000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["printer", printerName] });
    queryClient.invalidateQueries({ queryKey: ["printers"] });
  };

  const pauseMutation = useMutation({ mutationFn: () => printerApi.pause(printerName), onSuccess: invalidate });
  const resumeMutation = useMutation({ mutationFn: () => printerApi.resume(printerName), onSuccess: invalidate });
  const enableMutation = useMutation({ mutationFn: () => printerApi.enable(printerName), onSuccess: invalidate });
  const disableMutation = useMutation({ mutationFn: () => printerApi.disable(printerName), onSuccess: invalidate });

  if (printerQuery.isLoading) return <LoadingState />;
  if (printerQuery.isError) return <ErrorState error={printerQuery.error} onRetry={() => printerQuery.refetch()} />;

  const printer = printerQuery.data!;
  const isStopped = printer.state === "STOPPED";
  const pending = pauseMutation.isPending || resumeMutation.isPending || enableMutation.isPending || disableMutation.isPending;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => navigate("/printers")}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h1 className="text-lg font-semibold">{printer.name}</h1>
        <PrinterStateBadge state={printer.state} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Informasi Printer</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <Field label="Description" value={printer.description || "-"} />
            <Field label="Location" value={printer.location || "-"} />
            <Field label="State Message" value={printer.state_message || "-"} />
            <Field label="Device URI" value={printer.device_uri || "-"} mono />
            <Field label="Manufacturer" value={printer.manufacturer || "-"} />
            <Field label="Model" value={printer.model || "-"} />
            <Field label="Accepting Jobs" value={printer.accepting_jobs ? "Yes" : "No"} />
            <Field label="Shared" value={printer.shared ? "Yes" : "No"} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Capabilities</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Badge variant={printer.capabilities.color ? "success" : "outline"}>
                {printer.capabilities.color ? "Color" : "No Color"}
              </Badge>
              <Badge variant={printer.capabilities.duplex ? "success" : "outline"}>
                {printer.capabilities.duplex ? "Duplex" : "Simplex only"}
              </Badge>
              {printer.capabilities.copies_supported && (
                <Badge variant="outline">
                  Max copies: {printer.capabilities.max_copies ?? "?"}
                </Badge>
              )}
              {printer.capabilities.page_ranges_supported && <Badge variant="outline">Page ranges</Badge>}
              {printer.capabilities.orientation_supported && <Badge variant="outline">Orientation</Badge>}
            </div>
            {printer.capabilities.media.length > 0 && (
              <Field label="Paper" value={printer.capabilities.media.join(", ")} />
            )}
            {printer.capabilities.resolution.length > 0 && (
              <Field label="Resolution" value={printer.capabilities.resolution.join(", ")} />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Link to={`/print?printer=${encodeURIComponent(printer.name)}`} className={buttonVariants()}>
            <Send className="h-4 w-4" />
            Print
          </Link>
          {isStopped ? (
            <Button variant="secondary" disabled={pending} onClick={() => resumeMutation.mutate()}>
              <Play className="h-4 w-4" />
              Resume
            </Button>
          ) : (
            <Button variant="secondary" disabled={pending} onClick={() => pauseMutation.mutate()}>
              <Pause className="h-4 w-4" />
              Pause
            </Button>
          )}
          {printer.accepting_jobs ? (
            <Button variant="outline" disabled={pending} onClick={() => disableMutation.mutate()}>
              <ShieldOff className="h-4 w-4" />
              Disable
            </Button>
          ) : (
            <Button variant="outline" disabled={pending} onClick={() => enableMutation.mutate()}>
              <ShieldCheck className="h-4 w-4" />
              Enable
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Jobs on this printer</CardTitle>
        </CardHeader>
        <CardContent>
          {jobsQuery.isLoading ? (
            <LoadingState />
          ) : jobsQuery.isError ? (
            <ErrorState error={jobsQuery.error} onRetry={() => jobsQuery.refetch()} />
          ) : (jobsQuery.data ?? []).length === 0 ? (
            <EmptyState label="Belum ada job untuk printer ini." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job</TableHead>
                  <TableHead>Document</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobsQuery.data!.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell>
                      <Link to={`/jobs/${job.job_id}`} className="font-medium text-primary underline underline-offset-4">
                        #{job.job_id}
                      </Link>
                    </TableCell>
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

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={mono ? "break-all font-mono text-xs" : ""}>{value}</dd>
    </>
  );
}
