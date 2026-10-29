import { DataTabs } from "@/components/DataTabs";

export default function DataLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <DataTabs />
      {children}
    </>
  );
}
