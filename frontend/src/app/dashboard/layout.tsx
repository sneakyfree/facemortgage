import ProtectedLayout from "@/components/auth/ProtectedLayout";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
