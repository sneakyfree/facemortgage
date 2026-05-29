import ProtectedLayout from "@/components/auth/ProtectedLayout";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout requireAdmin>{children}</ProtectedLayout>;
}
