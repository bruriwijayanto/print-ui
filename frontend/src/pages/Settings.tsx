import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { healthApi } from "@/lib/api";
import { clearApiKey } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingState, ErrorState } from "@/components/QueryState";

export default function Settings() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.get,
    refetchInterval: 5000,
  });

  const handleLogout = () => {
    clearApiKey();
    navigate("/login", { replace: true });
  };

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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
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
