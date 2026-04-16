import { Metadata } from "next";
import "./globals.css";
import type { ReactNode } from "react";
import { AuthProvider } from "../context/AuthContext";

export const metadata: Metadata = { title: 'Horizon' }

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
