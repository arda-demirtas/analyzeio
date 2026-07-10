"use client";

import { useEffect, useState } from "react";
import { initializePaddle } from "@paddle/paddle-js";
import { ArrowLeft, Check, Sparkles, AlertTriangle, RefreshCw } from "lucide-react";
import Link from "next/link";

// Single-Tier Premium Pricing Definition
export const PricingTiers = [
  {
    name: "Premium",
    id: "premium",
    description: "Full access to institutional-grade AI models and technical screening tools.",
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
    <div className="min-h-screen bg-[#0d0f14] text-gray-100 flex flex-col font-sans">
      
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
      <div className="max-w-4xl w-full mx-auto px-6 py-12 flex-grow flex flex-col justify-center">
        
        {/* Header */}
        <div className="mb-12 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
            <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
          </Link>
          <div className="text-xs text-gray-500 bg-gray-900/60 px-3 py-1.5 rounded-full border border-gray-800">
            Detected Country: <span className="text-[#3b82f6] font-semibold">{initialCountry || "Auto (IP)"}</span>
          </div>
        </div>

        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-black mb-4 tracking-tight" style={{ background: "linear-gradient(to right, #ffffff, #9ca3af)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Get analyzeio Premium
          </h1>
          <p className="text-gray-400 max-w-lg mx-auto text-sm md:text-base mb-8">
            Ensemble AI engine forecasts, automated support/resistance zones, and bullish trend screeners.
          </p>

          {/* Billing Frequency Toggle */}
          <div className="inline-flex bg-gray-900/80 p-1.5 rounded-full border border-gray-800">
            <button
              onClick={() => setFrequency("month")}
              className={`px-6 py-2 rounded-full text-xs font-bold transition-all ${
                frequency === "month"
                  ? "bg-[#3b82f6] text-white shadow-lg shadow-blue-500/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setFrequency("year")}
              className={`px-6 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 ${
                frequency === "year"
                  ? "bg-[#3b82f6] text-white shadow-lg shadow-blue-500/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Yearly
              <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full text-[10px] font-black border border-emerald-500/20">
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Single Premium Plan Card (Centered) */}
        <div className="max-w-md w-full mx-auto">
          <div className="relative rounded-3xl p-8 bg-gradient-to-b from-[#141822] to-[#0f111a] border border-[#3b82f6]/40 shadow-2xl shadow-blue-500/5">
            
            {/* Featured Badge */}
            <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-1 rounded-full text-[10px] font-black tracking-widest uppercase shadow-md flex items-center gap-1">
              <Sparkles style={{ width: "10px", height: "10px" }} /> Full Access
            </span>

            {/* Plan Title & Desc */}
            <div className="mb-6 text-center">
              <h3 className="text-2xl font-black mb-2 text-white">{premiumTier.name}</h3>
              <p className="text-gray-400 text-xs">{premiumTier.description}</p>
            </div>

            {/* Price Display */}
            <div className="mb-8 flex items-baseline justify-center">
              {loadingPrices ? (
                <div className="flex items-center gap-2 text-2xl font-black text-gray-500 animate-pulse">
                  <RefreshCw className="animate-spin" style={{ width: "16px", height: "16px" }} /> Loading...
                </div>
              ) : displayPrice ? (
                <>
                  <span className="text-5xl font-extrabold text-white tracking-tight">{displayPrice}</span>
                  <span className="text-gray-500 text-xs font-semibold ml-1">
                    /{frequency === "month" ? "mo" : "yr"}
                  </span>
                </>
              ) : (
                <div className="text-xs text-gray-500 italic">Price ID configuration missing</div>
              )}
            </div>

            {/* Subscribe Button */}
            <button
              onClick={() => handleSubscribe(premiumTier)}
              disabled={loadingPrices || hasConfigError || !displayPrice}
              className="w-full py-4 px-6 rounded-2xl text-xs font-bold transition-all mb-8 bg-[#3b82f6] text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20 disabled:opacity-40"
            >
              {loadingPrices ? "Loading Plan..." : "Start 7-Day Free Trial"}
            </button>

            {/* Features List */}
            <div>
              <h4 className="text-gray-400 text-[11px] font-bold uppercase tracking-wider mb-4 text-center">Included Privileges</h4>
              <ul className="space-y-3.5 text-xs text-gray-300">
                {premiumTier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check style={{ width: "14px", height: "14px", color: "var(--accent-success)", flexShrink: 0, marginTop: "2px" }} />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

          </div>
        </div>

        {/* Legal & Notice footer */}
        <div className="text-center text-[10px] text-gray-600 max-w-sm mx-auto leading-relaxed mt-12">
          Your <strong>7-day free trial</strong> will automatically convert to a paid subscription. 
          Cancel anytime via your account dropdown settings.
        </div>

      </div>
    </div>
  );
}
