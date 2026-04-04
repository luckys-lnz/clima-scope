"use client";
import type { Session as SupabaseSession } from "@supabase/auth-js";
import Link from "next/link";
import Image from "next/image";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  BarChart3,
  FileText,
  Archive,
  Upload,
  Settings,
  CreditCard,
  MapPin,
  Menu,
  X,
  LogOut,
  CheckCircle2,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { DashboardOverview } from "@/components/ui-panels/dashboard-overview";
import { ManualGeneration } from "@/components/ui-panels/manual-generation";
import { ReportArchive } from "@/components/ui-panels/report-archive";
import { CountyDetail } from "@/components/ui-panels/county-detail";
import { SystemConfiguration } from "@/components/ui-panels/system-configuration";
import { DataUpload } from "@/components/data-upload";
import { StatusPanel } from "@/components/ui/status-panel";
import { bootstrapService } from "@/lib/services/bootstrapService";
import { authService } from "@/lib/services/authService";
import { subscriptionService } from "@/lib/services/subscriptionService";
import { useAuth } from "@/hooks/useAuth";
import type { User } from "@/lib/models/auth";
import { supabase } from "@/lib/supabaseClient";

type Screen = "dashboard" | "generate" | "archive" | "config" | "upload";
type LogoutPhase = "idle" | "submitting" | "success";
type LogoutOverlayPhase = Exclude<LogoutPhase, "idle">;

const LOGOUT_REDIRECT_DELAY_MS = 1400 as const;
const LOGOUT_PANEL_CONTENT = {
  submitting: {
    icon: LogOut,
    title: "Signing out",
    description: "Finishing up. You'll be redirected shortly.",
  },
  success: {
    icon: CheckCircle2,
    title: "Signed out",
    description: "You're logged out. Redirecting to the home page.",
  },
} as const satisfies Record<
  LogoutOverlayPhase,
  Readonly<{
    icon: LucideIcon;
    title: string;
    description: string;
  }>
>;

const getDisplayName = (user: User | null): string => {
  const name = user?.full_name?.trim();
  if (name) return name;

  const email = user?.email?.trim();
  if (!email) return "User";

  const localPart = email.split("@")[0]?.trim();
  return localPart || "User";
};

const getAvatarLabel = (user: User | null): string => {
  const displayName = getDisplayName(user);
  if (!displayName || displayName === "User") return "U";

  const words = displayName
    .split(/\s+/)
    .map((word) => word.trim())
    .filter(Boolean);

  if (words.length >= 2) {
    return `${words[0][0] ?? ""}${words[1][0] ?? ""}`.toUpperCase();
  }

  return (words[0]?.slice(0, 2) || "U").toUpperCase();
};

export default function Dashboard() {
  const {
    user: sessionUser,
    access_token: token,
    isLoading: authLoading,
    logout,
  } = useAuth();
  const [currentScreen, setCurrentScreen] = useState<Screen>("dashboard");
  const [visitedScreens, setVisitedScreens] = useState<Screen[]>(["dashboard"]);
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [bootstrappedToken, setBootstrappedToken] = useState<string | null>(
    null,
  );
  const [logoutPhase, setLogoutPhase] = useState<LogoutPhase>("idle");
  const logoutRedirectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLoggingOut = logoutPhase === "submitting";
  const isLogoutOverlayVisible = logoutPhase !== "idle";
  const logoutPanel =
    logoutPhase === "idle" ? null : LOGOUT_PANEL_CONTENT[logoutPhase];

  const syncOAuthSession = useCallback(
    async (session?: SupabaseSession | null) => {
      if (!session || authService.hasStoredSession()) {
        return;
      }

      try {
        await authService.initializeSessionFromOAuth(session);
      } catch (err) {
        console.error("OAuth session initialization failed:", err);
      }
    },
    [],
  );

  const redirectToLanding = useCallback((): void => {
    window.location.replace("/");
  }, []);

  const scheduleLandingRedirect = useCallback((): void => {
    if (logoutRedirectRef.current) {
      globalThis.clearTimeout(logoutRedirectRef.current);
    }
    logoutRedirectRef.current = globalThis.setTimeout(
      redirectToLanding,
      LOGOUT_REDIRECT_DELAY_MS,
    );
  }, [redirectToLanding]);

  useEffect(() => {
    if (authLoading) return;

    if (!token) {
      if (logoutPhase !== "idle") {
        return;
      }
      window.location.replace("/sign-in");
      return;
    }

    if (token !== bootstrappedToken) {
      setBootstrappedToken(token);
      void bootstrapService.primeDashboardData(token);
    }
  }, [authLoading, token, bootstrappedToken, logoutPhase]);

  useEffect(() => {
    if (authLoading || !token) return;

    let cancelled = false;

    const enforceSubscriptionGate = async () => {
      try {
        const state = await subscriptionService.getMySubscription(token);
        if (cancelled) return;

        if (state.access_status === "payment_required") {
          window.location.replace("/pricing?reason=trial-expired");
        }
      } catch {
        // Keep dashboard usable on transient network errors.
      }
    };

    void enforceSubscriptionGate();

    return () => {
      cancelled = true;
    };
  }, [authLoading, token]);

  useEffect(() => {
    return () => {
      if (logoutRedirectRef.current) {
        globalThis.clearTimeout(logoutRedirectRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const initializeOAuthSession = async (): Promise<void> => {
      if (typeof window === "undefined") return;

      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Failed to read OAuth session:", error);
        return;
      }

      if (data?.session) {
        await syncOAuthSession(data.session);
      }
    };

    void initializeOAuthSession();

    const { data: listener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === "SIGNED_IN") {
          void syncOAuthSession(session);
        }
      },
    );

    return () => {
      listener?.subscription.unsubscribe();
    };
  }, [syncOAuthSession]);

  const handleLogout = async () => {
    if (logoutPhase !== "idle") return;
    setUserMenuOpen(false);
    setLogoutPhase("submitting");
    try {
      await logout();
    } finally {
      setLogoutPhase("success");
      scheduleLandingRedirect();
    }
  };

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3 },
    { id: "generate", label: "Generate Report", icon: FileText },
    { id: "archive", label: "Report Archive", icon: Archive },
    { id: "upload", label: "Data Upload", icon: Upload },
    { id: "config", label: "Settings", icon: Settings },
  ];

  const navigateTo = (screen: Screen) => {
    setCurrentScreen(screen);
    setVisitedScreens((prev) =>
      prev.includes(screen) ? prev : [...prev, screen],
    );
  };

  const renderPanel = (screen: Screen, node: ReactNode) => {
    if (!visitedScreens.includes(screen)) return null;
    return (
      <div className={currentScreen === screen ? "block" : "hidden"}>
        {node}
      </div>
    );
  };

  const getTitle = (screen: string) => {
    const titles: Record<string, string> = {
      dashboard: "Dashboard",
      generate: "Generate Report",
      archive: "Report Archive",
      config: "Settings",
      upload: "Data Upload",
    };
    return titles[screen] || "Dashboard";
  };

  return (
    <div className="relative h-screen bg-background">
      {isLogoutOverlayVisible && logoutPanel ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background">
          <div className="w-full max-w-md rounded-lg border border-border/60 bg-card/95 p-6 shadow-2xl">
            <StatusPanel
              icon={logoutPanel.icon}
              title={logoutPanel.title}
              description={logoutPanel.description}
            />
          </div>
        </div>
      ) : (
        <div className="flex h-full">
          {/* Mobile overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-30 bg-black/50 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <aside
            className={`fixed left-0 top-0 h-full w-64 bg-sidebar border-r border-border transform transition-transform md:relative md:translate-x-0 z-40 ${
              sidebarOpen ? "translate-x-0" : "-translate-x-full"
            }`}
          >
            <div className="flex items-center gap-3 px-6 py-6 border-b border-border">
              <MapPin className="w-6 h-6 text-primary" />
              <div>
                <Image
                  src="/logo.png"
                  alt="Clima Scope"
                  width={180}
                  height={52}
                  className="h-8 w-auto brightness-0 invert"
                  priority
                />
                <p className="text-xs text-muted-foreground">
                  {sessionUser?.county || "—"} County
                </p>
              </div>
            </div>

            <nav className="p-4 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentScreen === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      navigateTo(item.id as Screen);
                      setSidebarOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium ${
                      isActive
                        ? "bg-primary/20 text-primary border border-primary/50"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                );
              })}

              <Link
                href="/pricing"
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50"
                onClick={() => setSidebarOpen(false)}
              >
                <CreditCard className="w-5 h-5" />
                <span>Pricing</span>
              </Link>

              <Link
                href="/limits"
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50"
                onClick={() => setSidebarOpen(false)}
              >
                <BarChart3 className="w-5 h-5" />
                <span>Usage Limits</span>
              </Link>
            </nav>
          </aside>

          {/* Main */}
          <main className="flex-1 flex flex-col overflow-hidden">
            {/* Header */}
            <header className="bg-card border-b border-border sticky top-0 z-20">
              <div className="flex items-center justify-between px-4 md:px-8 py-4">
                {/* Left */}
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="md:hidden p-2 hover:bg-muted rounded-lg"
                  >
                    {sidebarOpen ? (
                      <X className="w-5 h-5" />
                    ) : (
                      <Menu className="w-5 h-5" />
                    )}
                  </button>
                  <h2 className="text-2xl font-bold">
                    {getTitle(currentScreen as string)}
                  </h2>
                </div>
                {/* Right: Avatar vertical */}
                <div className="relative flex flex-col items-center">
                  <button
                    onClick={() => setUserMenuOpen((s) => !s)}
                    className="w-9 h-9 rounded-full border border-gray-400 flex items-center justify-center text-gray-400 font-semibold hover:bg-muted transition-colors"
                  >
                    {getAvatarLabel(sessionUser)}
                  </button>

                  <span className="text-xs text-muted-foreground mt-1">
                    Welcome, {getDisplayName(sessionUser)}
                  </span>

                  {/* Dropdown */}
                  {userMenuOpen && (
                    <div className="absolute right-0 top-12 w-36 bg-card border border-border rounded-lg shadow-lg z-50">
                      <Link
                        href="/profile"
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted/70 rounded-lg"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        <Settings className="w-4 h-4" />
                        Profile
                      </Link>
                      <button
                        onClick={handleLogout}
                        disabled={isLoggingOut}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <LogOut className="w-4 h-4" />
                        {isLoggingOut ? "Logging out…" : "Logout"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-auto">
              <div className="min-h-full">
                {renderPanel(
                  "dashboard",
                  <DashboardOverview
                    onNavigate={(screen: string) =>
                      navigateTo(screen as Screen)
                    }
                  />,
                )}
                {renderPanel(
                  "generate",
                  <ManualGeneration onBack={() => navigateTo("dashboard")} />,
                )}
                {renderPanel(
                  "archive",
                  selectedCounty ? (
                    <CountyDetail
                      county={selectedCounty}
                      reportId={selectedReportId || undefined}
                      onBack={() => {
                        setSelectedCounty(null);
                        setSelectedReportId(null);
                      }}
                    />
                  ) : (
                    <ReportArchive
                      onSelectCounty={(county, reportId) => {
                        setSelectedCounty(county);
                        setSelectedReportId(reportId || null);
                      }}
                    />
                  ),
                )}
                {renderPanel(
                  "config",
                  <SystemConfiguration
                    onBack={() => navigateTo("dashboard")}
                  />,
                )}
                {renderPanel(
                  "upload",
                  <DataUpload onBack={() => navigateTo("dashboard")} />,
                )}
              </div>
            </div>
          </main>
        </div>
      )}
    </div>
  );
}
