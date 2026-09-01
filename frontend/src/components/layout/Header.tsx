import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export function Header() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.get,
    refetchInterval: 5000,
  });

  const connected = !isError && data?.status === "ok";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card/80 px-4 backdrop-blur md:px-6">
      <div className="text-sm font-semibold md:hidden">CUPS Print Manager</div>
      <div className="ml-auto flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs font-medium">
        <span className="relative flex h-2 w-2">
          {connected && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          )}
          <span className={cn("relative inline-flex h-2 w-2 rounded-full", connected ? "bg-emerald-500" : "bg-destructive")} />
        </span>
        <span className="text-muted-foreground">{connected ? "CUPS connected" : "CUPS disconnected"}</span>
      </div>
    </header>
  );
}
