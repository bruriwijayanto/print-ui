import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, FileText, UploadCloud } from "lucide-react";
import { printApi, printerApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { LoadingState, ErrorState } from "@/components/QueryState";
import { ApiError } from "@/lib/api";
import { formatFileSize } from "@/lib/utils";
import type { PrinterDetail } from "@/types/printer";

const ACCEPTED_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.txt";

export default function Print() {
  const [searchParams] = useSearchParams();
  const printersQuery = useQuery({ queryKey: ["printers"], queryFn: printerApi.getPrinters });

  const [printer, setPrinter] = useState(searchParams.get("printer") ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [copies, setCopies] = useState(1);
  const [pageRanges, setPageRanges] = useState("");
  const [media, setMedia] = useState("");
  const [orientation, setOrientation] = useState("");
  const [color, setColor] = useState("");
  const [duplex, setDuplex] = useState("");
  const [dragActive, setDragActive] = useState(false);

  const printerDetailQuery = useQuery({
    queryKey: ["printer", printer],
    queryFn: () => printerApi.getPrinter(printer),
    enabled: !!printer,
  });

  useEffect(() => {
    if (!printer && printersQuery.data && printersQuery.data.length > 0) {
      setPrinter(printersQuery.data[0].name);
    }
  }, [printer, printersQuery.data]);

  const printMutation = useMutation({
    mutationFn: () =>
      printApi.printDocument(file!, {
        printer,
        copies,
        page_ranges: pageRanges || undefined,
        media: media || undefined,
        orientation: orientation || undefined,
        color: color || undefined,
        duplex: duplex || undefined,
      }),
  });

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  if (printMutation.isSuccess) {
    const result = printMutation.data;
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
        <CheckCircle2 className="h-10 w-10 text-emerald-600" />
        <h1 className="text-lg font-semibold">Print job submitted</h1>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">Printer</dt>
          <dd>{result.printer}</dd>
          <dt className="text-muted-foreground">Job</dt>
          <dd>#{result.job_id}</dd>
          <dt className="text-muted-foreground">Status</dt>
          <dd className="capitalize">{result.status}</dd>
        </dl>
        <div className="flex gap-2">
          <Link to={`/jobs/${result.job_id}`} className="text-sm font-medium text-primary underline underline-offset-4">
            View Job
          </Link>
          <Button variant="outline" size="sm" onClick={() => printMutation.reset()}>
            Print Another
          </Button>
        </div>
      </div>
    );
  }

  if (printersQuery.isLoading) return <LoadingState />;
  if (printersQuery.isError) return <ErrorState error={printersQuery.error} onRetry={() => printersQuery.refetch()} />;

  const printers = printersQuery.data ?? [];
  const detail: PrinterDetail | undefined = printerDetailQuery.data;

  const handleFiles = (files: FileList | null) => {
    if (files && files[0]) setFile(files[0]);
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <h1 className="text-lg font-semibold">Print Document</h1>

      <Card>
        <CardHeader>
          <CardTitle>Upload File</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              dragActive ? "border-primary bg-accent" : "border-border"
            }`}
          >
            <UploadCloud className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Drag & drop file di sini, atau</p>
            <label className="cursor-pointer text-sm font-medium text-primary underline underline-offset-4">
              Choose File
              <input
                type="file"
                accept={ACCEPTED_EXTENSIONS}
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
            </label>
            <p className="text-xs text-muted-foreground">PDF, PNG, JPG, JPEG, TXT</p>
          </div>

          {file && (
            <div className="flex items-center gap-3 rounded-md border border-border p-3">
              {previewUrl && file.type.startsWith("image/") ? (
                <img src={previewUrl} alt="preview" className="h-14 w-14 rounded object-cover" />
              ) : (
                <FileText className="h-8 w-8 text-muted-foreground" />
              )}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)} &middot; {file.type || "unknown type"}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Options</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="printer">Printer</Label>
            <Select id="printer" value={printer} onChange={(e) => setPrinter(e.target.value)}>
              {printers.map((p) => (
                <option key={p.name} value={p.name} disabled={!p.accepting_jobs}>
                  {p.name} {!p.accepting_jobs ? "(not accepting jobs)" : ""}
                </option>
              ))}
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="copies">Copies</Label>
            <Input
              id="copies"
              type="number"
              min={1}
              max={999}
              value={copies}
              onChange={(e) => setCopies(Number(e.target.value) || 1)}
            />
          </div>

          {detail?.capabilities.page_ranges_supported && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pages">Pages (mis. 1-3,5)</Label>
              <Input id="pages" value={pageRanges} onChange={(e) => setPageRanges(e.target.value)} placeholder="Semua halaman" />
            </div>
          )}

          {detail && detail.capabilities.media.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="media">Paper</Label>
              <Select id="media" value={media} onChange={(e) => setMedia(e.target.value)}>
                <option value="">Default</option>
                {detail.capabilities.media.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </Select>
            </div>
          )}

          {detail?.capabilities.orientation_supported && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="orientation">Orientation</Label>
              <Select id="orientation" value={orientation} onChange={(e) => setOrientation(e.target.value)}>
                <option value="">Default</option>
                <option value="3">Portrait</option>
                <option value="4">Landscape</option>
              </Select>
            </div>
          )}

          {detail?.capabilities.color && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="color">Color</Label>
              <Select id="color" value={color} onChange={(e) => setColor(e.target.value)}>
                <option value="">Default</option>
                <option value="color">Color</option>
                <option value="monochrome">Monochrome</option>
              </Select>
            </div>
          )}

          {detail?.capabilities.duplex && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="duplex">Duplex</Label>
              <Select id="duplex" value={duplex} onChange={(e) => setDuplex(e.target.value)}>
                <option value="">Default</option>
                <option value="one-sided">One-sided</option>
                <option value="two-sided-long-edge">Two-sided (long edge)</option>
                <option value="two-sided-short-edge">Two-sided (short edge)</option>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {printMutation.isError && (
        <p className="text-sm text-destructive">
          {printMutation.error instanceof ApiError ? printMutation.error.message : "Gagal mengirim print job."}
        </p>
      )}

      <Button
        size="lg"
        disabled={!file || !printer || printMutation.isPending}
        onClick={() => printMutation.mutate()}
      >
        {printMutation.isPending ? "Mengirim..." : "PRINT DOCUMENT"}
      </Button>
    </div>
  );
}
