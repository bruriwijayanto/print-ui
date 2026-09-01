import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { JobStatusBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/QueryState";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";

const CANCELABLE_STATUSES = new Set(["PENDING", "PROCESSING"]);

export default function Jobs() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: jobApi.getJobs,
    refetchInterval: 4000,
  });

  const cancelMutation = useMutation({
    mutationFn: (jobId: number) => jobApi.cancelJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;

  const jobs = [...(data ?? [])].sort((a, b) => b.job_id - a.job_id);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold">Jobs</h1>
      <Card>
        <CardContent className="p-0 sm:p-4">
          {jobs.length === 0 ? (
            <EmptyState label="Belum ada print job." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job ID</TableHead>
                  <TableHead>Printer</TableHead>
                  <TableHead>Document</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.job_id}>
                    <TableCell>
                      <Link to={`/jobs/${job.job_id}`} className="font-medium text-primary underline underline-offset-4">
                        #{job.job_id}
                      </Link>
                    </TableCell>
                    <TableCell>{job.printer}</TableCell>
                    <TableCell>{job.document || "-"}</TableCell>
                    <TableCell>{job.user || "-"}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDateTime(job.submitted_at)}</TableCell>
                    <TableCell>
                      <JobStatusBadge status={job.status} />
                    </TableCell>
                    <TableCell>
                      {CANCELABLE_STATUSES.has(job.status) && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={cancelMutation.isPending}
                          onClick={() => cancelMutation.mutate(job.job_id)}
                        >
                          Cancel
                        </Button>
                      )}
                    </TableCell>
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
