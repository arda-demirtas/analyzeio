"use client";

import { useEffect, useState } from "react";
import { initializePaddle } from "@paddle/paddle-js";
import { ArrowLeft, Check, Sparkles, AlertTriangle, RefreshCw } from "lucide-react";
import Link from "next/link";

// Single-Tier Premium Pricing Definition
export const PricingTiers = [
  {
    name: "Premium Access",
    id: "premium",
    description: "Designed for active traders seeking maximum model ensemble power.",
    features: [
      "All 5 AI Models (XGBoost, LSTM, Linear Regression, PatchTST, S/R Model)",
      "Intra-day prediction cycles (15m, 1h, 4h) + Daily (1d)",
      "100% Bullish Consensus Dashboard access",
      "Automatic Support & Resistance price levels overlay",
      "Unlimited Watchlists & Symbol tracking",
      "Priority predictions & live comments feed",
      "7-Day Free Trial included",
    ],
    featured: true,
    priceId: {
      month: process.env.NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_MONTH || process.env.NEXT_PUBLIC_PADDLE_PRICE_PRO_MONTH || "",
      year: process.env.NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_YEAR || process.env.NEXT_PUBLIC_PADDLE_PRICE_PRO_YEAR || "",
    },
  }
];

export function PricingClient({ initialCountry }) {
  const [frequency, setFrequency] = useState("month");
  const [paddle, setPaddle] = useState(undefined);
  const [prices, setPrices] = useState({});
  const [loadingPrices, setLoadingPrices] = useState(true);
  const [userEmail, setUserEmail] = useState("");

  const clientToken = process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN;
  const paddleEnv = process.env.NEXT_PUBLIC_PADDLE_ENV;
  
  const isConfigMissing = !clientToken || !paddleEnv;
  const isConfigPlaceholder = 
    clientToken?.includes("token_here") || 
    clientToken?.includes("dummy") || 
    paddleEnv === "sandbox_or_production";
  
  const hasConfigError = isConfigMissing || isConfigPlaceholder;

  // 1. Fetch authenticated user email
  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;
      try {
        const res = await fetch("http://46.225.59.232/api/auth/me", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data && data.email) {
            setUserEmail(data.email);
          }
        }
      } catch (err) {
        console.error("Failed to fetch user:", err);
      }
    };
    fetchUser();
  }, []);

  // 2. Initialize Paddle
  useEffect(() => {
    if (hasConfigError) {
      setLoadingPrices(false);
      return;
    }

    initializePaddle({
      token: clientToken,
      environment: paddleEnv,
    }).then((instance) => {
      if (instance) {
        setPaddle(instance);
      }
    }).catch(err => {
      console.error("Paddle initialization error:", err);
      setLoadingPrices(false);
    });
  }, [clientToken, paddleEnv, hasConfigError]);

  // 3. Fetch Prices
  useEffect(() => {
    if (!paddle) return;

    const items = PricingTiers.flatMap((tier) => {
      const itemsList = [];
      if (tier.priceId.month) itemsList.push({ priceId: tier.priceId.month, quantity: 1 });
      if (tier.priceId.year) itemsList.push({ priceId: tier.priceId.year, quantity: 1 });
      return itemsList;
    });

    if (items.length === 0) {
      setLoadingPrices(false);
      return;
    }

    const previewParams = {
      items,
      ...(initialCountry && { address: { countryCode: initialCountry } }),
    };

    setLoadingPrices(true);
    paddle.PricePreview(previewParams)
      .then((response) => {
        const priceMap = {};
        if (response?.data?.details?.lineItems) {
          response.data.details.lineItems.forEach((item) => {
            priceMap[item.price.id] = item.formattedTotals.total;
          });
        }
        setPrices(priceMap);
        setLoadingPrices(false);
      })
      .catch((err) => {
        console.error("Paddle PricePreview failed:", err);
        setLoadingPrices(false);
      });
  }, [paddle, initialCountry]);

  // 4. Handle Subscription Checkout
  const handleSubscribe = (tier) => {
    if (!paddle) return;
    
    const priceId = tier.priceId[frequency];
    if (!priceId) {
      alert("Error: Price ID is not configured for this plan.");
      return;
    }

    paddle.Checkout.open({
      items: [{ priceId, quantity: 1 }],
      customer: userEmail ? { email: userEmail } : undefined,
      settings: {
        displayMode: "overlay",
        variant: "one-page",
        theme: "dark",
        successUrl: `${window.location.origin}/welcome`,
      },
    });
  };

  const premiumTier = PricingTiers[0];
  const currentPriceId = premiumTier.priceId[frequency];
  const displayPrice = prices[currentPriceId];

  return (
    <div className="min-h-screen bg-[#070a13] text-gray-100 flex flex-col font-sans relative overflow-hidden">
      
      {/* Background radial glowing ambient lights */}
      <div className="absolute top-[-100px] left-[50%] -translate-x-[50%] w-[600px] h-[600px] bg-[#8b5cf6]/10 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[10%] right-[10%] w-[350px] h-[350px] bg-blue-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Configuration Error Banner */}
      {hasConfigError && (
        <div style={{
          background: "rgba(239, 68, 68, 0.15)",
          borderBottom: "1px solid rgba(239, 68, 68, 0.3)",
          padding: "16px 24px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          color: "#f87171",
          fontSize: "14px",
          zIndex: 100
        }}>
          <AlertTriangle style={{ flexShrink: 0, width: "20px", height: "20px" }} />
          <div>
            <strong>Loud Configuration Error:</strong> Paddle environment variables are missing or contain placeholder values. 
            Please configure <code>NEXT_PUBLIC_PADDLE_CLIENT_TOKEN</code>, <code>NEXT_PUBLIC_PADDLE_ENV</code>, and <code>NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_MONTH</code> / <code>NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_YEAR</code> inside your <code>.env</code> file.
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-4xl w-full mx-auto px-6 py-16 flex-grow flex flex-col justify-center relative z-10">
        
        {/* Header Navigation */}
        <div className="mb-16 flex items-center justify-between">
          <Link href="/" className="btn-secondary" style={{ width: "fit-content" }}>
            <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
          </Link>
          <div className="text-[11px] text-gray-400 bg-white/[0.03] px-3.5 py-2 rounded-full border border-white/[0.08] backdrop-blur-md">
            Country: <span className="text-[#a78bfa] font-bold">{initialCountry || "Auto (IP)"}</span>
          </div>
        </div>

        {/* Hero Title Area */}
        <div className="text-center mb-16">
          <h1 
            className="text-4xl md:text-5xl font-black mb-4 tracking-tight" 
            style={{ 
              background: "linear-gradient(to right, #a78bfa, #8b5cf6, #3b82f6)", 
              WebkitBackgroundClip: "text", 
              WebkitTextFillColor: "transparent" 
            }}
          >
            Upgrade to Premium
          </h1>
          <p className="text-[#9ca3af] max-w-lg mx-auto text-sm md:text-base mb-10 leading-relaxed">
            Unlock advanced machine learning predictions, deep technical consensus analysis, and premium indicators.
          </p>

          {/* Billing Frequency Toggle */}
          <div className="inline-flex bg-black/40 p-1 rounded-2xl border border-white/5 backdrop-blur-md">
            <button
              onClick={() => setFrequency("month")}
              className={`px-7 py-2.5 rounded-xl text-xs font-bold transition-all ${
                frequency === "month"
                  ? "bg-[#8b5cf6] text-white shadow-lg shadow-purple-500/25"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setFrequency("year")}
              className={`px-7 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                frequency === "year"
                  ? "bg-[#8b5cf6] text-white shadow-lg shadow-purple-500/25"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Yearly
              <span className="bg-[#10b981]/15 text-[#10b981] px-2.5 py-0.5 rounded-full text-[10px] font-black border border-[#10b981]/25">
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Premium Plan Card (Aligned to Glassmorphic Design System) */}
        <div className="max-w-lg w-full mx-auto">
          <div 
            className="glass-panel relative rounded-3xl p-10 flex flex-col border border-white/[0.08] shadow-2xl hover:border-[#8b5cf6]/35 group transition-all duration-300"
            style={{ background: "rgba(17, 24, 39, 0.55)" }}
          >
            
            {/* Ambient inner glow on hover */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#8b5cf6]/5 to-transparent rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* Premium Star Badge */}
            <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#8b5cf6] to-[#7c3aed] text-white px-5 py-1.5 rounded-full text-[9px] font-black tracking-widest uppercase shadow-lg shadow-purple-500/20 flex items-center gap-1.5">
              <Sparkles style={{ width: "10px", height: "10px" }} /> PREMIUM ENSEMBLE
            </span>

            {/* Plan Info */}
            <div className="mb-8 text-center relative z-10">
              <h3 className="text-2xl font-black mb-2 text-white">analyzeio Premium</h3>
              <p className="text-gray-400 text-xs leading-relaxed max-w-xs mx-auto">{premiumTier.description}</p>
            </div>

            {/* Price Display */}
            <div className="mb-8 flex items-baseline justify-center relative z-10">
              {loadingPrices ? (
                <div className="flex items-center gap-2 text-2xl font-black text-gray-500 animate-pulse">
                  <RefreshCw className="animate-spin text-[#8b5cf6]" style={{ width: "18px", height: "18px" }} /> Loading...
                </div>
              ) : displayPrice ? (
                <>
                  <span className="text-5xl font-black text-white tracking-tight">{displayPrice}</span>
                  <span className="text-gray-500 text-xs font-semibold ml-1.5">
                    /{frequency === "month" ? "mo" : "yr"}
                  </span>
                </>
              ) : (
                <div className="text-xs text-gray-500 italic">Price ID configuration missing</div>
              )}
            </div>

            {/* Subscribe Action */}
            <button
              onClick={() => handleSubscribe(premiumTier)}
              disabled={loadingPrices || hasConfigError || !displayPrice}
              className="btn-primary w-full py-4 text-xs font-black shadow-lg shadow-purple-500/20 mb-8 relative z-10"
            >
              {loadingPrices ? "Loading Plan..." : "Start 7-Day Free Trial"}
            </button>

            {/* Features list */}
            <div className="relative z-10">
              <h4 className="text-gray-400 text-[10px] font-black uppercase tracking-widest mb-5 text-center">Included Privileges</h4>
              <ul className="space-y-4 text-xs text-gray-300">
                {premiumTier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <div className="w-4 h-4 bg-[#10b981]/10 rounded-full flex items-center justify-center border border-[#10b981]/25 flex-shrink-0 mt-0.5">
                      <Check style={{ width: "10px", height: "10px", color: "#10b981" }} />
                    </div>
                    <span className="leading-normal">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

          </div>
        </div>

        {/* Legal & Notice footer */}
        <div className="text-center text-[10px] text-gray-500 max-w-md mx-auto leading-relaxed mt-16 relative z-10">
          <p className="mb-4">
            Your <strong>7-day free trial</strong> will automatically convert to a paid subscription. 
            Cancel anytime via your account dropdown settings.
          </p>
          <div className="flex items-center justify-center gap-4 text-gray-500 font-medium">
            <Link href="/terms" className="hover:text-[#a78bfa] transition-colors">Terms of Service</Link>
            <span>•</span>
            <Link href="/privacy" className="hover:text-[#a78bfa] transition-colors">Privacy Policy</Link>
            <span>•</span>
            <Link href="/refunds" className="hover:text-[#a78bfa] transition-colors">Refund Policy</Link>
          </div>
        </div>

      </div>
    </div>
  );
}
