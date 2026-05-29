import ProtectedLayout from "@/components/auth/ProtectedLayout";

export default function PartnerLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedLayout>{children}</ProtectedLayout>;
}
