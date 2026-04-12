import { Metadata } from "next";
import "./globals.css";
import type { ReactNode } from "react";
export const metadata: Metadata = { title: 'Horizon' }
export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
