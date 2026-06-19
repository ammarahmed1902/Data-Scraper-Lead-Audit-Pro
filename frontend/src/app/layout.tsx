import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { BrowserExtensionHydrationScript } from "@/components/browser-extension-hydration-script";
import { Providers } from "@/components/providers";
import "@/styles/globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Lead Audit Pro",
    template: "%s | Lead Audit Pro",
  },
  description:
    "Cold-calling and lead-generation platform with automated website audits.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen font-sans antialiased`}
        suppressHydrationWarning
      >
        <BrowserExtensionHydrationScript />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
