import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scale Without Borders · Verified Remote Jobs",
  description: "AI-verified remote opportunities for newcomers to Canada",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
