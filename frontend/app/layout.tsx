import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Nivara",
  description: "Contextual safety-aware navigation and journey protection.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
