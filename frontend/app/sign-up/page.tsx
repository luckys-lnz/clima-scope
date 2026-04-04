"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle,
  Eye,
  EyeOff,
  FileText,
  MapPinned,
  Send,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { GoogleLogo } from "@/components/icons/google-logo";
import { authService } from "@/lib/services/authService";
import { cn } from "@/lib/utils";
import type { SignUpData } from "@/lib/models/auth";

import type { Session as SupabaseSession } from "@supabase/auth-js";
import { supabase } from "@/lib/supabaseClient";

const INPUT_CLASSNAME = "h-11 rounded-xl";

const SELECT_CLASSNAME =
  "flex h-11 w-full rounded-xl border border-input bg-transparent px-3 py-2 text-sm text-foreground shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50";

const PASSWORD_REQUIREMENTS = [
  { key: "length", label: "At least 8 characters" },
  { key: "uppercase", label: "One uppercase letter" },
  { key: "lowercase", label: "One lowercase letter" },
  { key: "number", label: "One number" },
  { key: "special", label: "One special character" },
] as const;

type PasswordRequirementKey = (typeof PASSWORD_REQUIREMENTS)[number]["key"];

function getPasswordChecks(
  password: string,
): Record<PasswordRequirementKey, boolean> {
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function getPasswordStrength(password: string) {
  const checks = getPasswordChecks(password);
  const metRequirements = Object.values(checks).filter(Boolean).length;
  const bonusPoint = password.length >= 12 ? 1 : 0;
  const score = Math.min(metRequirements + bonusPoint, 5);

  if (!password) {
    return {
      checks,
      progress: 0,
      label: "Start typing a password",
      textClass: "text-slate-500",
      indicatorClass: "**:data-[slot=progress-indicator]:bg-slate-400",
    };
  }

  if (score <= 2) {
    return {
      checks,
      progress: 25,
      label: "Weak password",
      textClass: "text-red-500",
      indicatorClass: "**:data-[slot=progress-indicator]:bg-red-500",
    };
  }

  if (score === 3) {
    return {
      checks,
      progress: 55,
      label: "Fair password",
      textClass: "text-amber-500",
      indicatorClass: "**:data-[slot=progress-indicator]:bg-amber-500",
    };
  }

  if (score === 4) {
    return {
      checks,
      progress: 78,
      label: "Strong password",
      textClass: "text-sky-600",
      indicatorClass: "**:data-[slot=progress-indicator]:bg-sky-500",
    };
  }

  return {
    checks,
    progress: 100,
    label: "Very strong password",
    textClass: "text-emerald-600",
    indicatorClass: "**:data-[slot=progress-indicator]:bg-emerald-500",
  };
}

export default function SignUp() {
  const router = useRouter();
  const [formData, setFormData] = useState<
    SignUpData & { confirmPassword: string }
  >({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    organization: "",
    county: "",
    phone: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const syncOAuthSession = async (session?: SupabaseSession | null) => {
    if (!session || authService.hasStoredSession()) {
      return;
    }

    try {
      await authService.initializeSessionFromOAuth(session);
      router.replace("/dashboard");
    } catch (err) {
      console.error("OAuth session initialization failed:", err);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const checkStoredSession = async () => {
      if (!isMounted || authService.hasStoredSession()) {
        return;
      }

      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Failed to read OAuth session:", error);
        return;
      }

      if (data?.session) {
        await syncOAuthSession(data.session);
      }
    };

    void checkStoredSession();

    const { data: listener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === "SIGNED_IN") {
          void syncOAuthSession(session);
        }
      },
    );

    return () => {
      isMounted = false;
      listener?.subscription.unsubscribe();
    };
  }, [router]);

  const passwordStrength = getPasswordStrength(formData.password);
  const passwordsMatch =
    Boolean(formData.password) &&
    Boolean(formData.confirmPassword) &&
    formData.password === formData.confirmPassword;
  const confirmPasswordHasValue = Boolean(formData.confirmPassword);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validateForm = (): string | null => {
    if (
      !formData.full_name ||
      !formData.email ||
      !formData.password ||
      !formData.confirmPassword ||
      !formData.organization ||
      !formData.county
    ) {
      return "Please fill in all required fields";
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      return "Please enter a valid email address";
    }

    if (formData.password.length < 8) {
      return "Password must be at least 8 characters";
    }

    const checks = getPasswordChecks(formData.password);
    if (
      !checks.uppercase ||
      !checks.lowercase ||
      !checks.number ||
      !checks.special
    ) {
      return "Password must contain uppercase, lowercase, numeric, and special characters";
    }

    if (formData.password !== formData.confirmPassword) {
      return "Passwords do not match";
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      await authService.signup({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        organization: formData.organization,
        county: formData.county,
        phone: formData.phone || undefined,
      });

      setSuccess(
        "Account created! Please check your email to confirm your account. The confirmation link expires in 24 hours.",
      );

      setFormData({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        organization: "",
        county: "",
        phone: "",
      });
      setShowPassword(false);
      setShowConfirmPassword(false);
    } catch (err: any) {
      const msg = err.message.toLowerCase();
      if (
        msg.includes("already registered") ||
        msg.includes("already exists")
      ) {
        setError("An account with this email already exists. Please sign in.");
      } else if (msg.includes("weak") || msg.includes("password")) {
        setError(
          "Password does not meet security requirements. Please use a stronger password.",
        );
      } else if (msg.includes("rate limit") || msg.includes("too many")) {
        setError("Too many attempts. Please wait a few minutes and try again.");
      } else if (msg.includes("network") || msg.includes("fetch")) {
        setError("Network error. Please check your connection and try again.");
      } else {
        setError(
          err.message ||
            "An error occurred during registration. Please try again.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    if (isLoading) return;

    setError("");
    setIsLoading(true);

    try {
      if (typeof window === "undefined") {
        throw new Error("Unable to start Google sign-up");
      }

      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      });

      if (error) throw error;
    } catch (err: any) {
      setError(
        err.message || "Unable to continue with Google. Please try again.",
      );
      setIsLoading(false);
    }
  };

  const kenyanCounties = [
    "Mombasa",
    "Kwale",
    "Kilifi",
    "Tana River",
    "Lamu",
    "Taita Taveta",
    "Garissa",
    "Wajir",
    "Mandera",
    "Marsabit",
    "Isiolo",
    "Meru",
    "Tharaka Nithi",
    "Embu",
    "Kitui",
    "Machakos",
    "Makueni",
    "Nyandarua",
    "Nyeri",
    "Kirinyaga",
    "Murang'a",
    "Kiambu",
    "Turkana",
    "West Pokot",
    "Samburu",
    "Trans Nzoia",
    "Uasin Gishu",
    "Elgeyo Marakwet",
    "Nandi",
    "Baringo",
    "Laikipia",
    "Nakuru",
    "Narok",
    "Kajiado",
    "Kericho",
    "Bomet",
    "Kakamega",
    "Vihiga",
    "Bungoma",
    "Busia",
    "Siaya",
    "Kisumu",
    "Homa Bay",
    "Migori",
    "Kisii",
    "Nyamira",
    "Nairobi",
  ].sort();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-7xl items-center px-4 py-8">
        <div className="grid w-full overflow-hidden rounded-[28px] border border-border/40 bg-card shadow-[0_32px_120px_rgba(0,0,0,0.45)] lg:grid-cols-[1.1fr_0.9fr]">
          <section className="relative overflow-hidden border-b border-border/40 bg-secondary/30 px-7 py-8 sm:px-9 lg:border-b-0 lg:border-r lg:px-12 lg:py-12">
            <div className="relative z-10">
              <div className="relative flex items-center justify-center">
                <Link
                  href="/sign-in"
                  className="absolute left-0 inline-flex items-center gap-1 text-sm font-semibold text-sky-600 transition-colors hover:text-sky-700"
                >
                  <ArrowLeft className="size-4" />
                  Back to login
                </Link>
                <Link
                  href="/"
                  className="inline-flex items-center justify-center"
                >
                  <Image
                    src="/logo.png"
                    alt="Clima Scope"
                    width={180}
                    height={52}
                    className="h-10 w-auto brightness-0 invert"
                    priority
                  />
                </Link>
              </div>

              <div className="mt-10 max-w-lg space-y-5">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-accent-blue">
                  County Setup
                </p>
                <h1 className="text-4xl font-semibold leading-tight">
                  Create an account built for county reporting operations.
                </h1>
                <p className="text-base leading-7 text-muted-foreground">
                  Set up a workspace for your county team, secure your report
                  workflow, and start generating structured weather outputs with
                  the right regional context from day one.
                </p>
              </div>

              <div className="mt-10 grid gap-4">
                {[
                  {
                    icon: MapPinned,
                    title: "County-aware setup",
                    description:
                      "Tie the account to the county your team supports so dashboards and workflows start in the right context.",
                  },
                  {
                    icon: FileText,
                    title: "Operational reporting",
                    description:
                      "Prepare weekly outputs, county summaries, and distribution-ready material in one place.",
                  },
                  {
                    icon: Send,
                    title: "Distribution readiness",
                    description:
                      "Keep email delivery, automation, and review workflows aligned with the team responsible for the report.",
                  },
                ].map((item) => {
                  const Icon = item.icon;

                  return (
                    <div
                      key={item.title}
                      className="rounded-2xl border border-border/40 bg-background/40 p-4"
                    >
                      <div className="flex items-start gap-4">
                        <div className="rounded-xl bg-accent-blue/10 p-2 text-accent-blue">
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <h2 className="text-sm font-semibold">
                            {item.title}
                          </h2>
                          <p className="mt-1 text-sm leading-6 text-muted-foreground">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="bg-card px-6 py-8 sm:px-8 lg:px-10 lg:py-12">
            <div className="mx-auto w-full max-w-md">
              <div className="mb-8 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-3xl font-semibold tracking-tight">
                    Create your workspace
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Use your work details so county dashboards, reporting
                    workflows, and forecast operations are configured correctly.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <Button
                  type="button"
                  className="h-11 w-full rounded-xl border border-sky-600 bg-transparent text-sky-600 transition hover:bg-sky-600 hover:text-white"
                  onClick={handleGoogleSignUp}
                  disabled={isLoading}
                >
                  <span className="flex items-center justify-center gap-2">
                    <GoogleLogo />
                    Continue with Google
                  </span>
                </Button>
                <div className="relative flex items-center justify-center text-xs text-muted-foreground">
                  <span className="absolute inset-x-0 h-px bg-border/60" />
                  <span className="bg-card px-3 text-sm">
                    or continue with email
                  </span>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4">
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                    <p className="text-sm leading-6 text-red-700">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="flex items-start gap-3 rounded-2xl border border-green-200 bg-green-50 p-4">
                    <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
                    <div>
                      <p className="text-sm font-medium text-green-700">
                        {success}
                      </p>
                      <p className="mt-1 text-xs text-green-600">
                        Keep this tab open until you've clicked the confirmation
                        link in your email.
                      </p>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="full_name">
                    Full Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="full_name"
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    placeholder="John Doe"
                    className={INPUT_CLASSNAME}
                    required
                    disabled={isLoading}
                    autoComplete="name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email <span className="text-red-500">*</span>
                  </Label>
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

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <Label htmlFor="password">
                      Password <span className="text-red-500">*</span>
                    </Label>
                    <span
                      className={cn(
                        "text-xs font-semibold",
                        passwordStrength.textClass,
                      )}
                    >
                      {passwordStrength.label}
                    </span>
                  </div>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Create a secure password"
                      className={cn(INPUT_CLASSNAME, "pr-12")}
                      required
                      minLength={8}
                      disabled={isLoading}
                      autoComplete="new-password"
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
                  <Progress
                    value={passwordStrength.progress}
                    className={cn(
                      "h-2 bg-slate-100 **:data-[slot=progress-indicator]:transition-transform",
                      passwordStrength.indicatorClass,
                    )}
                  />
                  <div className="grid gap-2 rounded-2xl border border-border/40 bg-background/40 p-3 sm:grid-cols-2">
                    {PASSWORD_REQUIREMENTS.map((requirement) => {
                      const isMet = passwordStrength.checks[requirement.key];

                      return (
                        <div
                          key={requirement.key}
                          className={cn(
                            "flex items-center gap-2 text-xs transition-colors",
                            isMet
                              ? "text-emerald-400"
                              : "text-muted-foreground",
                          )}
                        >
                          <span
                            className={cn(
                              "flex size-4 items-center justify-center rounded-full border",
                              isMet
                                ? "border-emerald-500 bg-emerald-500/10"
                                : "border-border/60 bg-transparent",
                            )}
                          >
                            {isMet && <Check className="size-3" />}
                          </span>
                          <span>{requirement.label}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <Label htmlFor="confirmPassword">
                      Confirm Password <span className="text-red-500">*</span>
                    </Label>
                    {confirmPasswordHasValue && (
                      <span
                        className={cn(
                          "text-xs font-semibold",
                          passwordsMatch
                            ? "text-emerald-600"
                            : "text-amber-500",
                        )}
                      >
                        {passwordsMatch
                          ? "Passwords match"
                          : "Passwords do not match"}
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Re-enter your password"
                      className={cn(INPUT_CLASSNAME, "pr-12")}
                      required
                      minLength={8}
                      disabled={isLoading}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((prev) => !prev)}
                      className="absolute inset-y-0 right-0 inline-flex items-center justify-center px-3 text-slate-500 transition-colors hover:text-slate-900"
                      aria-label={
                        showConfirmPassword
                          ? "Hide confirm password"
                          : "Show confirm password"
                      }
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </button>
                  </div>
                  {confirmPasswordHasValue && !passwordsMatch && (
                    <p className="text-xs text-amber-600">
                      Make sure both password fields are identical before
                      submitting.
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="organization">
                    Organization <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="organization"
                    type="text"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    placeholder="Kenya Meteorological Department"
                    className={INPUT_CLASSNAME}
                    required
                    disabled={isLoading}
                    autoComplete="organization"
                  />
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="county">
                      County <span className="text-red-500">*</span>
                    </Label>
                    <select
                      id="county"
                      name="county"
                      value={formData.county}
                      onChange={handleChange}
                      className={SELECT_CLASSNAME}
                      disabled={isLoading}
                      required
                    >
                      <option value="" className="bg-white text-slate-500">
                        Select county
                      </option>
                      {kenyanCounties.map((county) => (
                        <option
                          key={county}
                          value={county}
                          className="bg-white text-slate-950"
                        >
                          {county}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+254 712 345 678"
                      className={INPUT_CLASSNAME}
                      disabled={isLoading}
                      autoComplete="tel"
                    />
                  </div>
                </div>

                <div className="rounded-2xl border border-border/40 bg-background/40 p-4 text-xs leading-6 text-muted-foreground">
                  Use a unique password. County selection is required so the
                  right location context, dashboard scope, and report workflow
                  are attached to your account immediately.
                </div>

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="h-11 w-full rounded-xl bg-sky-600 text-white hover:bg-sky-700"
                >
                  {isLoading ? "Creating account..." : "Create Account"}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                  href="/sign-in"
                  className="font-semibold text-accent-blue transition-colors hover:text-accent-blue/80"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
