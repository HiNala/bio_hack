import type { Metadata } from "next";
import "./globals.css";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import ServiceWorkerRegistration from "@/components/ServiceWorkerRegistration";
import { FeedbackWidget } from "@/components/FeedbackWidget";
import { OfflineIndicator } from "@/components/OfflineIndicator";

export const metadata: Metadata = {
  title: "ScienceRAG",
  description: "AI-powered scientific literature intelligence platform",
  icons: {
    icon: [
      { url: "/logo.png", type: "image/png" },
    ],
    apple: [
      { url: "/logo.png", type: "image/png" },
    ],
    shortcut: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link 
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" 
          rel="stylesheet" 
        />
        <link rel="icon" href="/logo.png" type="image/png" />
        <link rel="apple-touch-icon" href="/logo.png" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="ScienceRAG" />

        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://sciencerag.app/" />
        <meta property="og:title" content="ScienceRAG - AI-Powered Scientific Literature Intelligence" />
        <meta property="og:description" content="Transform how you discover, synthesize, and understand academic research with AI-powered analysis" />
        <meta property="og:image" content="/og-image.png" />

        {/* Twitter */}
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content="https://sciencerag.app/" />
        <meta property="twitter:title" content="ScienceRAG - AI-Powered Scientific Literature Intelligence" />
        <meta property="twitter:description" content="Transform how you discover, synthesize, and understand academic research with AI-powered analysis" />
        <meta property="twitter:image" content="/og-image.png" />

        {/* Additional SEO */}
        <meta name="robots" content="index, follow" />
        <meta name="author" content="ScienceRAG Team" />
        <meta name="keywords" content="scientific research, literature review, AI, machine learning, academic papers, research synthesis" />
      </head>
      <body className="antialiased">
        {/* Skip navigation for accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Skip to main content
        </a>

        <ErrorBoundary>
          {children}
        </ErrorBoundary>
        <ServiceWorkerRegistration />
        <FeedbackWidget />
        <OfflineIndicator />
      </body>
    </html>
  );
}
