import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { printerApi } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { PrinterStateBadge } from "@/components/StatusBadge";
import { LoadingState, ErrorState, EmptyState } from "@/components/QueryState";
import { Badge } from "@/components/ui/badge";

export default function Printers() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["printers"],
    queryFn: printerApi.getPrinters,
    refetchInterval: 5000,
  });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;

  const printers = data ?? [];

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold">Printers</h1>
      <Card>
        <CardContent className="p-0 sm:p-4">
          {printers.length === 0 ? (
            <EmptyState label="Tidak ada printer terdaftar di CUPS." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Printer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Queue</TableHead>
                  <TableHead>Current Job</TableHead>
                  <TableHead>Accepting Jobs</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {printers.map((printer) => (
                  <TableRow key={printer.name}>
                    <TableCell className="font-medium">{printer.name}</TableCell>
                    <TableCell>
                      <PrinterStateBadge state={printer.state} />
                    </TableCell>
                    <TableCell>{printer.queue_count}</TableCell>
                    <TableCell>{printer.current_job ?? "-"}</TableCell>
                    <TableCell>
                      <Badge variant={printer.accepting_jobs ? "success" : "warning"}>
                        {printer.accepting_jobs ? "Yes" : "No"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/printers/${encodeURIComponent(printer.name)}`}
                        className="text-sm font-medium text-primary underline underline-offset-4"
                      >
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
    </div>
  );
}
