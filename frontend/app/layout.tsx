import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Opportunity Radar",
  description: "Discover news and hackathons. Save articles and track your hackathon applications.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider><Navbar />
        <main className="mx-auto max-w-7xl px-4 py-8">{children}</main></AuthProvider>
      </body>
    </html>
  );
}
