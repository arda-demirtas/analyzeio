import { headers } from "next/headers";
import { PricingClient } from "./PricingClient";

export const metadata = {
  title: "Pricing | analyzeio",
  description: "Flexible, localization-optimized subscription tiers powered by all 5 ML models.",
};

export default async function PricingPage() {
  const h = await headers();
  
  // Detect country code from common proxy/hosting headers (Vercel, Cloudflare, etc.)
  // If none is found, we pass null so Paddle PricePreview falls back to visitor IP auto-detection.
  const country = h.get("x-vercel-ip-country") || h.get("cf-ipcountry") || null;
  
  return <PricingClient initialCountry={country} />;
}
