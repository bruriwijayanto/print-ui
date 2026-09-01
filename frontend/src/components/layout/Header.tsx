import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, XCircle } from "lucide-react";
import { healthApi } from "@/lib/api";

export function Header() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.get,
    refetchInterval: 5000,
  });

  const connected = !isError && data?.status === "ok";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4 md:px-6">
      <div className="text-sm font-medium md:hidden">CUPS Print Manager</div>
      <div className="ml-auto flex items-center gap-2 text-sm">
        {connected ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span className="text-muted-foreground">CUPS connected</span>
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 text-destructive" />
            <span className="text-muted-foreground">CUPS disconnected</span>
          </>
        )}
      </div>
    </header>
  );
}
