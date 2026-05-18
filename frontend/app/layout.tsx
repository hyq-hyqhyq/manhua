import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mock Comic Generator",
  description: "Entity Pool based mock multi-panel comic generator"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
