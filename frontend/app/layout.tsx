import type { Metadata } from "next";
import { Syne, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const syne = Syne({ subsets: ["latin"], variable: "--font-display" });
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-body" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "FormatGuard | Institution-Grade Formatting Compliance",
  description: "Automated document formatting compliance and auto-correction for universities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSans.variable} ${jetbrainsMono.variable} dark`}>
      <body className="min-h-screen bg-black text-white font-sans antialiased selection:bg-cyan-500/30">
        <main className="relative flex min-h-screen flex-col">
          {children}
        </main>
        <Toaster theme="dark" position="top-right" richColors />
      </body>
    </html>
  );
}
