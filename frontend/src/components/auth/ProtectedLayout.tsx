"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { apiClient } from "@/lib/api/client";

export default function ProtectedLayout({
  children,
  requireAdmin = false,
}: {
  children: React.ReactNode;
  requireAdmin?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, setUser } = useAuthStore();
  const [verified, setVerified] = useState(false);
  const [authed, setAuthed] = useState(isAuthenticated);

  useEffect(() => {
    let cancelled = false;
    async function verify() {
      try {
        const resp = await apiClient.get("/auth/me");
        if (cancelled) return;
        setUser(resp.data);
        setAuthed(true);
      } catch (e: any) {
        if (cancelled) return;
        const status = e?.response?.status;
        // Only treat 401/403 as a real auth failure. Transient network errors should retry.
        if (status === 401 || status === 403) {
          setUser(null);
          setAuthed(false);
          router.replace(`/auth/login?redirect=${encodeURIComponent(pathname || "/")}`);
        } else {
          // Network glitch (SW activation, brief connection drop). Retry once after 500ms.
          await new Promise(r => setTimeout(r, 500));
          if (cancelled) return;
          try {
            const resp2 = await apiClient.get("/auth/me");
            setUser(resp2.data);
            setAuthed(true);
          } catch (e2: any) {
            const s2 = e2?.response?.status;
            if (s2 === 401 || s2 === 403) {
              setUser(null);
              setAuthed(false);
              router.replace(`/auth/login?redirect=${encodeURIComponent(pathname || "/")}`);
            } else {
              // Persistent network failure: leave authed=null so page shows fallback.
              setAuthed(false);
            }
          }
        }
      } finally {
        if (!cancelled) setVerified(true);
      }
    }
    verify();
    return () => {
      cancelled = true;
    };
  }, [pathname, router, setUser]);

  useEffect(() => {
    if (verified && authed && requireAdmin && user && !(user as { is_admin?: boolean }).is_admin) {
      router.replace("/dashboard");
    }
  }, [verified, authed, requireAdmin, user, router]);

  if (!verified) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-600">
        <div className="animate-pulse">Verifying session…</div>
      </div>
    );
  }
  if (!authed) return null;
  if (requireAdmin && user && !(user as { is_admin?: boolean }).is_admin) return null;
  return <>{children}</>;
}
