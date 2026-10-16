import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CausalMesh — Autonomous SRE & Incident Memory Mesh",
  description: "Autonomous multi-agent SRE platform powered by FalkorDB graph reasoning",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f6f7f9] text-[#182230] antialiased">
        {children}
      </body>
    </html>
  );
}
