import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { ApiError } from "@/lib/api";

export function LoadingState({ label = "Memuat data..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof ApiError ? error.message : "Terjadi kesalahan tak terduga.";
  const code = error instanceof ApiError ? error.code : undefined;

  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 py-16 text-center">
      <AlertTriangle className="h-6 w-6 text-destructive" />
      <p className="text-sm font-medium text-destructive">{message}</p>
      {code && <p className="text-xs text-muted-foreground">Kode: {code}</p>}
      {onRetry && (
        <button onClick={onRetry} className="mt-2 text-sm font-medium text-primary underline underline-offset-4">
          Coba lagi
        </button>
      )}
    </div>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-muted-foreground">
      <Inbox className="h-6 w-6" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
