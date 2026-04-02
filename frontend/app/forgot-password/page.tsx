"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/lib/supabaseClient";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success">("idle");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Enter your work email to receive a reset link");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      if (typeof window === "undefined") {
        throw new Error("Unable to send reset link from this device");
      }

      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (error) throw error;
      setStatus("success");
    } catch (err: any) {
      setError(err.message || "Unable to send reset instructions. Please try again.");
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
                Back to login
              </Link>
            </div>
            <div className="text-center">
              <h1 className="text-lg font-semibold">Forgot password</h1>
              <p className="text-sm text-muted-foreground">Recover your account password</p>
            </div>
          </header>

          <section className="rounded-[28px] border border-border/40 bg-card px-6 py-8 shadow-[0_24px_80px_rgba(0,0,0,0.45)] sm:px-8">
            <p className="text-sm text-muted-foreground">
              Enter the email associated with your account and we will send a link to reset your password.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {error && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}
              {status === "success" && (
                <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                  We sent a password reset email. Check your inbox and follow the instructions.
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="forgot-email">Work email</Label>
                <Input
                  id="forgot-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@organization.com"
                  className="h-11 rounded-xl border border-slate-300 bg-white shadow-sm"
                  disabled={isLoading || status === "success"}
                  required
                  autoComplete="email"
                />
              </div>

              <Button type="submit" className="h-11 w-full rounded-xl bg-sky-600 text-white hover:bg-sky-700" disabled={isLoading || status === "success"}>
                {isLoading ? "Sending link..." : "Send reset link"}
              </Button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
