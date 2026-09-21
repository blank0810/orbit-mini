import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orbit - ScaleSage",
  description: "Your ScaleSage client dashboard for managing your subscription.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="flex min-h-dvh flex-col bg-bg font-sans text-text antialiased">
        {/* Keyboard users must be able to bypass the header. */}
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-3 focus:font-medium focus:text-on-accent"
        >
          Skip to content
        </a>
        <header className="mx-auto flex w-full max-w-6xl items-center gap-2 px-6 py-6 sm:px-8">
          <span className="text-xl font-semibold tracking-tight">Orbit</span>
          <span aria-hidden="true" className="size-2 rounded-full bg-accent" />
        </header>
        <main id="main" tabIndex={-1} className="flex flex-1 flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
