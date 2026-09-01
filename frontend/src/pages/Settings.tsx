import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, ErrorState } from "@/components/QueryState";

export default function Settings() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.get,
    refetchInterval: 5000,
  });

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6">
      <h1 className="text-lg font-semibold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Connection</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : (
            <>
              <Row label="Backend API">
                <Badge variant={data?.status === "ok" ? "success" : "destructive"}>{data?.status}</Badge>
              </Row>
              <Row label="CUPS Server">
                <Badge variant={data?.cups === "connected" ? "success" : "destructive"}>{data?.cups}</Badge>
              </Row>
              <Row label="Printers Detected">
                <span>{data?.printers ?? "-"}</span>
              </Row>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm text-muted-foreground">
          <p>CUPS Print Manager — Web UI &amp; REST API untuk mengelola printer melalui CUPS.</p>
          <p>
            Autentikasi API key (<code className="rounded bg-muted px-1 py-0.5 text-xs">PRINT_API_KEY</code>) belum
            diberlakukan pada UI ini — akan ditambahkan pada fase keamanan berikutnya.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      {children}
    </div>
  );
}
