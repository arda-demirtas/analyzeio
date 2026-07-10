"use client";

import { useEffect, useState, useCallback } from "react";
import { initializePaddle } from "@paddle/paddle-js";
import { ArrowLeft, Check, Sparkles, AlertTriangle, RefreshCw } from "lucide-react";
import Link from "next/link";

// 3-Tier Pricing Model Definition (Tiers easily editable)
export const PricingTiers = [
  {
    name: "Starter",
    id: "starter",
    description: "Perfect for beginners exploring AI-driven market prediction.",
    features: [
      "1 Active Watchlist",
      "3 AI Models (XGBoost, LSTM, Linear Regression)",
      "Daily (1d) predictions",
      "Standard email support",
    ],
    featured: false,
    priceId: {
      month: process.env.NEXT_PUBLIC_PADDLE_PRICE_STARTER_MONTH || "",
      year: process.env.NEXT_PUBLIC_PADDLE_PRICE_STARTER_YEAR || "",
    },
  },
  {
    name: "Pro",
    id: "pro",
    description: "Designed for active traders seeking maximum model ensemble power.",
    features: [
      "Unlimited Watchlists",
      "All 5 AI Models (incl. PatchTST & S/R Model)",
      "Intra-day predictions (15m, 1h, 4h)",
      "100% Bullish Consensus Page access",
      "Fast cloud predictions",
    ],
    featured: true,
    priceId: {
      month: process.env.NEXT_PUBLIC_PADDLE_PRICE_PRO_MONTH || "",
      year: process.env.NEXT_PUBLIC_PADDLE_PRICE_PRO_YEAR || "",
    },
  },
  {
    name: "Advanced",
    id: "advanced",
    description: "For institutional clients and algorithmic trading systems.",
    features: [
      "Everything in Pro",
      "API access for custom trading bots",
      "Dedicated GPU training priority",
      "Dedicated account manager",
      "24/7 Priority developer support",
    ],
    featured: false,
    priceId: {
      month: process.env.NEXT_PUBLIC_PADDLE_PRICE_ADVANCED_MONTH || "",
      year: process.env.NEXT_PUBLIC_PADDLE_PRICE_ADVANCED_YEAR || "",
    },
  },
];

export function PricingClient({ initialCountry }) {
  const [frequency, setFrequency] = useState("month");
  const [paddle, setPaddle] = useState(undefined);
  const [prices, setPrices] = useState({});
  const [loadingPrices, setLoadingPrices] = useState(true);
  const [userEmail, setUserEmail] = useState("");
  const [authError, setAuthError] = useState(null);

  // Configuration check - fail loudly if unset or using default placeholders
  const clientToken = process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN;
  const paddleEnv = process.env.NEXT_PUBLIC_PADDLE_ENV;
  
  const isConfigMissing = !clientToken || !paddleEnv;
  const isConfigPlaceholder = 
    clientToken?.includes("token_here") || 
    clientToken?.includes("dummy") || 
    paddleEnv === "sandbox_or_production";
  
  const hasConfigError = isConfigMissing || isConfigPlaceholder;

  // 1. Fetch current signed-in user email if token exists in localStorage
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
        console.error("Failed to fetch authenticated user for prefill:", err);
      }
    };
    fetchUser();
  }, []);

  // 2. Initialize Paddle.js
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

  // 3. Load prices via PricePreview
  useEffect(() => {
    if (!paddle) return;

    // Collect all price IDs to fetch in a single batch
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
      // If initialCountry is null/absent, do not pass countryCode so Paddle auto-detects via visitor IP
      ...(initialCountry && { address: { countryCode: initialCountry } }),
    };

    setLoadingPrices(true);
    paddle.PricePreview(previewParams)
      .then((response) => {
        const priceMap = {};
        if (response && response.data && response.data.details && response.data.details.lineItems) {
          response.data.details.lineItems.forEach((item) => {
            // Store the formatted totals string directly (e.g. "$9.99" or "£8.50")
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
      alert("Error: Price ID is not configured for this tier and billing frequency.");
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

  return (
    <div className="min-h-screen bg-[#0d0f14] text-gray-100 flex flex-col font-sans">
      
      {/* Configuration Error Banner (Fail Loudly Requirement) */}
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
            Please configure <code>NEXT_PUBLIC_PADDLE_CLIENT_TOKEN</code>, <code>NEXT_PUBLIC_PADDLE_ENV</code>, and tier price IDs inside your <code>.env</code> file.
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-6xl w-full mx-auto px-6 py-12 flex-grow flex flex-col">
        
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
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-black mb-4 tracking-tight" style={{ background: "linear-gradient(to right, #ffffff, #9ca3af)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Choose Your AI Engine Plan
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto text-base md:text-lg mb-8">
            Access institutional-grade ensemble algorithms, intra-day forecasts, and live bullish consensus lists.
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

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-stretch mb-16">
          {PricingTiers.map((tier) => {
            const currentPriceId = tier.priceId[frequency];
            const displayPrice = prices[currentPriceId];
            
            return (
              <div
                key={tier.id}
                className={`relative rounded-3xl p-8 flex flex-col border transition-all duration-300 ${
                  tier.featured
                    ? "bg-gradient-to-b from-[#141822] to-[#0f111a] border-[#3b82f6]/40 shadow-2xl shadow-blue-500/5 md:-translate-y-2 scale-[1.02]"
                    : "bg-[#0f111a]/60 border-gray-800/80 hover:border-gray-700/80"
                }`}
              >
                {/* Popular Badge */}
                {tier.featured && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-1 rounded-full text-[10px] font-black tracking-widest uppercase shadow-md flex items-center gap-1">
                    <Sparkles style={{ width: "10px", height: "10px" }} /> Most Popular
                  </span>
                )}

                {/* Card Title & Desc */}
                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2 text-white">{tier.name}</h3>
                  <p className="text-gray-400 text-xs min-h-[36px]">{tier.description}</p>
                </div>

                {/* Price Display */}
                <div className="mb-8 flex items-baseline">
                  {loadingPrices ? (
                    <div className="flex items-center gap-2 text-2xl font-black text-gray-500 animate-pulse">
                      <RefreshCw className="animate-spin" style={{ width: "16px", height: "16px" }} /> Loading...
                    </div>
                  ) : displayPrice ? (
                    <>
                      <span className="text-4xl font-extrabold text-white tracking-tight">{displayPrice}</span>
                      <span className="text-gray-500 text-xs font-semibold ml-1">
                        /{frequency === "month" ? "mo" : "yr"}
                      </span>
                    </>
                  ) : (
                    <div className="text-xs text-gray-500 italic">Price unavailable</div>
                  )}
                </div>

                {/* Subscribe Button */}
                <button
                  onClick={() => handleSubscribe(tier)}
                  disabled={loadingPrices || hasConfigError || !displayPrice}
                  className={`w-full py-3.5 px-6 rounded-2xl text-xs font-bold transition-all mb-8 ${
                    tier.featured
                      ? "bg-[#3b82f6] text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20 disabled:opacity-40"
                      : "bg-gray-800 text-gray-200 hover:bg-gray-700 disabled:opacity-40"
                  }`}
                >
                  {loadingPrices ? "Loading Plan..." : "Subscribe Now"}
                </button>

                {/* Features List */}
                <div className="flex-grow">
                  <h4 className="text-gray-400 text-[11px] font-bold uppercase tracking-wider mb-4">Included Features</h4>
                  <ul className="space-y-3.5 text-xs text-gray-300">
                    {tier.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <Check style={{ width: "14px", height: "14px", color: "var(--accent-success)", flexShrink: 0, marginTop: "2px" }} />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>

        {/* Legal & Notice footer */}
        <div className="text-center text-[11px] text-gray-600 max-w-lg mx-auto leading-relaxed border-t border-gray-900/60 pt-8">
          All subscriptions include a <strong>7-day free trial</strong>. You can cancel at any time directly from your billing portal dashboard. 
          Default payment link must be configured in your Paddle Dashboard settings.
        </div>

      </div>
    </div>
  );
}
