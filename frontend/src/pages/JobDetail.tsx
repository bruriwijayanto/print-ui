import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Circle, XCircle } from "lucide-react";
import { jobApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { JobStatusBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState } from "@/components/QueryState";
import { cn, formatDateTime } from "@/lib/utils";

const CANCELABLE_STATUSES = new Set(["PENDING", "PROCESSING"]);

export default function JobDetail() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const numericJobId = Number(jobId);

  const jobQuery = useQuery({
    queryKey: ["job", numericJobId],
    queryFn: () => jobApi.getJob(numericJobId),
    refetchInterval: 4000,
  });

  const cancelMutation = useMutation({
    mutationFn: () => jobApi.cancelJob(numericJobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", numericJobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  if (jobQuery.isLoading) return <LoadingState />;
  if (jobQuery.isError) return <ErrorState error={jobQuery.error} onRetry={() => jobQuery.refetch()} />;

  const job = jobQuery.data!;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => navigate("/jobs")}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h1 className="text-lg font-semibold">Job #{job.job_id}</h1>
        <JobStatusBadge status={job.status} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <Timeline status={job.status} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Detail</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Printer</dt>
          <dd>{job.printer}</dd>
          <dt className="text-muted-foreground">Document</dt>
          <dd>{job.document || "-"}</dd>
          <dt className="text-muted-foreground">Owner</dt>
          <dd>{job.owner || job.user || "-"}</dd>
          <dt className="text-muted-foreground">Submitted At</dt>
          <dd>{formatDateTime(job.submitted_at)}</dd>
          <dt className="text-muted-foreground">Started At</dt>
          <dd>{formatDateTime(job.started_at)}</dd>
          <dt className="text-muted-foreground">Completed At</dt>
          <dd>{formatDateTime(job.completed_at)}</dd>
          {Object.keys(job.options).length > 0 && (
            <>
              <dt className="text-muted-foreground">Options</dt>
              <dd>
                {Object.entries(job.options)
                  .map(([key, value]) => `${key}=${value}`)
                  .join(", ")}
              </dd>
            </>
          )}
          {job.error && (
            <>
              <dt className="text-destructive">Error</dt>
              <dd className="text-destructive">{job.error}</dd>
            </>
          )}
        </CardContent>
      </Card>

      {CANCELABLE_STATUSES.has(job.status) && (
        <Button variant="destructive" disabled={cancelMutation.isPending} onClick={() => cancelMutation.mutate()}>
          Cancel Job
        </Button>
      )}
    </div>
  );
}

function Timeline({ status }: { status: string }) {
  const failed = status === "FAILED" || status === "CANCELED";
  const steps = failed
    ? [
        { label: "Submitted", done: true },
        { label: "Queued", done: true },
        { label: status === "CANCELED" ? "Canceled" : "Failed", done: true, isEnd: true, error: true },
      ]
    : [
        { label: "Submitted", done: true },
        { label: "Queued", done: true },
        { label: "Printing", done: status === "PROCESSING" || status === "COMPLETED" },
        { label: "Completed", done: status === "COMPLETED", isEnd: true },
      ];

  return (
    <ol className="flex flex-col gap-4">
      {steps.map((step, index) => (
        <li key={step.label} className="flex items-center gap-3">
          {"error" in step && step.error ? (
            <XCircle className="h-5 w-5 text-destructive" />
          ) : step.done ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          ) : (
            <Circle className="h-5 w-5 text-muted-foreground" />
          )}
          <span className={cn("text-sm", step.done ? "font-medium" : "text-muted-foreground")}>{step.label}</span>
          {index < steps.length - 1 && <span className="text-muted-foreground">&rarr;</span>}
        </li>
      ))}
    </ol>
  );
}
