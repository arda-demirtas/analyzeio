import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Analyzeio - Market Predictions & Price Trends Dashboard",
  description: "Track and forecast daily price trends for your favorite stocks and cryptocurrencies. Analyzeio helps you make smarter market decisions with clear, easy-to-understand insights.",
  openGraph: {
    title: "Analyzeio - Market Predictions & Price Trends Dashboard",
    description: "Track and forecast daily price trends for your favorite stocks and cryptocurrencies. Analyzeio helps you make smarter market decisions with clear, easy-to-understand insights.",
    url: "http://analyze-io.com",
    siteName: "Analyzeio",
    images: [
      {
        url: "http://analyze-io.com/icon.svg",
        width: 100,
        height: 100,
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Analyzeio - Price Predictions & Trends",
    description: "Track and forecast daily price trends for your favorite stocks and cryptocurrencies with clear, easy-to-understand insights.",
    images: ["http://analyze-io.com/icon.svg"],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Analyzeio",
  "operatingSystem": "All",
  "applicationCategory": "FinanceApplication",
  "description": "Track and forecast daily price trends for your favorite stocks and cryptocurrencies with clear, easy-to-understand insights.",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
