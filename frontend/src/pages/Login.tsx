import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { KeyRound } from "lucide-react";
import { ApiError, authApi } from "@/lib/api";
import { getApiKey, setApiKey } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (getApiKey()) {
    const redirectTo = (location.state as { from?: string } | null)?.from ?? "/";
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const { token } = await authApi.login(username, password);
      setApiKey(token);
      const redirectTo = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Username atau password salah.");
      } else if (err instanceof ApiError && err.status === 429) {
        setError("Terlalu banyak percobaan. Coba lagi dalam beberapa menit.");
      } else {
        setError("Tidak dapat menghubungi server. Coba lagi.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center gap-2 text-center">
          <KeyRound className="h-8 w-8 text-primary" />
          <CardTitle className="text-base text-foreground">CUPS Print Manager</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                autoFocus
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={isSubmitting || !username || !password}>
              {isSubmitting ? "Memeriksa..." : "Masuk"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
