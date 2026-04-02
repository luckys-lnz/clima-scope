"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowLeft, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/lib/supabaseClient";
import { authService } from "@/lib/services/authService";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSession, setHasSession] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession();
      setHasSession(Boolean(data?.session));
    };

    void checkSession();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasSession) {
      setError("This reset link has expired. Request a new link from the sign-in page.");
      return;
    }

    if (!password || !confirmPassword) {
      setError("Please enter and confirm your new password");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw error;

      const { data: sessionData } = await supabase.auth.getSession();
      if (!sessionData?.session) {
        throw new Error("Unable to confirm your session");
      }

      await authService.initializeSessionFromOAuth(sessionData.session);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Unable to reset your password. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-4xl items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <header className="mb-6 space-y-2 px-6">
            <div>
              <Link
                href="/sign-in"
                className="inline-flex items-center gap-1 text-sm font-semibold text-sky-600 transition-colors hover:text-sky-700"
              >
                <ArrowLeft className="size-4" />
                Back to sign in
              </Link>
            </div>
            <div className="text-center">
              <h1 className="text-lg font-semibold">Reset password</h1>
              <p className="text-sm text-muted-foreground">Set a secure password for your Clima Scope account.</p>
            </div>
          </header>

          <section className="rounded-[28px] border border-border/40 bg-card px-6 py-8 shadow-[0_24px_80px_rgba(0,0,0,0.45)] sm:px-8">
            {error && (
              <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                {error}
              </div>
            )}

            {!hasSession && (
              <p className="text-sm text-muted-foreground">
                We could not detect a password reset session. Please request a fresh link from the sign-in page.
              </p>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <Label htmlFor="new-password">New password</Label>
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    disabled={isLoading}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="h-11 rounded-xl border border-slate-300 bg-white shadow-sm"
                    disabled={isLoading || !hasSession}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 inline-flex items-center justify-center px-3 text-slate-500 transition-colors hover:text-slate-900"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    disabled={isLoading}
                  >
                    {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <Label htmlFor="confirm-password">Confirm password</Label>
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    className="text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    disabled={isLoading}
                  >
                    {showConfirmPassword ? "Hide" : "Show"}
                  </button>
                </div>
                <div className="relative">
                  <Input
                    id="confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    className="h-11 rounded-xl border border-slate-300 bg-white shadow-sm"
                    disabled={isLoading || !hasSession}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 inline-flex items-center justify-center px-3 text-slate-500 transition-colors hover:text-slate-900"
                    aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                    disabled={isLoading}
                  >
                    {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="h-11 w-full rounded-xl bg-sky-600 text-white hover:bg-sky-700"
                disabled={isLoading || !hasSession}
              >
                {isLoading ? "Saving new password..." : "Save new password"}
              </Button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
