import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
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
  title: "Analyzeio - AI-Backed Graphic & Technical Analysis Platform",
  description: "Analyzeio is an AI-Backed Graphical and Technical Analysis SaaS Platform. Analyze market data and charts for stocks and cryptocurrencies with algorithmic insights.",
  openGraph: {
    title: "Analyzeio - AI-Backed Graphic & Technical Analysis Platform",
    description: "Analyzeio is an AI-Backed Graphical and Technical Analysis SaaS Platform. Analyze market data and charts for stocks and cryptocurrencies with algorithmic insights.",
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
    title: "Analyzeio - AI-Backed Graphic & Technical Analysis Platform",
    description: "Analyzeio is an AI-Backed Graphical and Technical Analysis SaaS Platform. Analyze market data and charts for stocks and cryptocurrencies with algorithmic insights.",
    images: ["http://analyze-io.com/icon.svg"],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Analyzeio",
  "operatingSystem": "All",
  "applicationCategory": "FinanceApplication",
  "description": "Analyzeio is an AI-Backed Graphical and Technical Analysis SaaS Platform. Analyze market data and charts for stocks and cryptocurrencies with algorithmic insights.",
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
      suppressHydrationWarning
    >
      <head>
        {/* Google Analytics */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-M6VDD86L75"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-M6VDD86L75');
          `}
        </Script>

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <Script 
          async 
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3992383565761354"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
