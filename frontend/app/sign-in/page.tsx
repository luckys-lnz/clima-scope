"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertCircle, Cloud, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService } from "@/lib/services/authService";
import { cn } from "@/lib/utils";
import type { LoginData } from "@/lib/models/auth";

const INPUT_CLASSNAME =
  "h-11 rounded-xl border border-slate-300 bg-white shadow-sm caret-slate-900 focus-visible:bg-white focus-visible:border-sky-600 focus-visible:ring-2 focus-visible:ring-sky-500/40";

  export default function SignIn() {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginData>({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      if (!formData.email || !formData.password)
        throw new Error("Please fill in all fields");
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email))
        throw new Error("Please enter a valid email address");

      await authService.login(formData);

      setFormData({ email: "", password: "" });
      setShowPassword(false);
      router.push("/dashboard");
    } catch (err: any) {
      console.error("Login error:", err);
      setFormData((prev) => ({ ...prev, password: "" }));

      if (err.message.includes("Invalid login")) {
        setError("Invalid email or password");
      } else if (err.message.includes("Email not confirmed")) {
        setError("Please confirm your email before logging in");
      } else {
        setError(err.message || "An error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-7xl items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-sm font-medium transition-opacity hover:opacity-80"
            >
              <span className="text-lg font-semibold tracking-wide">
                Clima Scope
              </span>
            </Link>
            <h1 className="mt-8 text-3xl font-semibold tracking-tight">
              Welcome back
            </h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Sign in to continue with your county forecasts, report workflows,
              and dashboard activity.
            </p>
          </div>

          <section className="rounded-[28px] border border-border/40 bg-card px-6 py-8 shadow-[0_24px_80px_rgba(0,0,0,0.45)] sm:px-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4">
                  <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                  <p className="text-sm leading-6 text-red-700">{error}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@organization.com"
                  className={INPUT_CLASSNAME}
                  required
                  disabled={isLoading}
                  autoComplete="email"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <Label htmlFor="password">Password</Label>
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    disabled={isLoading}
                  >
                    {showPassword ? "Hide password" : "Show password"}
                  </button>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter your password"
                    className={cn(INPUT_CLASSNAME, "pr-12")}
                    required
                    disabled={isLoading}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 inline-flex items-center justify-center px-3 text-slate-500 transition-colors hover:text-slate-900"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="h-11 w-full rounded-xl bg-sky-600 text-white hover:bg-sky-700"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                    Signing in...
                  </span>
                ) : (
                  "Sign In"
                )}
              </Button>
            </form>

            <div className="mt-6 space-y-4 text-center">
              <p className="text-sm text-muted-foreground">
                Don&apos;t have an account?{" "}
                <Link
                  href="/sign-up"
                  className="font-semibold text-accent-blue transition-colors hover:text-accent-blue/80"
                >
                  Create one
                </Link>
              </p>
              <Link
                href="/forgot-password"
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                Forgot your password?
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
