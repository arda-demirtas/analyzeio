"use client";

import { useEffect, useState } from "react";
import { initializePaddle } from "@paddle/paddle-js";
import { ArrowLeft, Check, Sparkles, AlertTriangle, RefreshCw, ShieldCheck, Zap, Calendar, MessageSquare, LineChart } from "lucide-react";
import Link from "next/link";

// Single-Tier Premium Pricing Definition
export const PricingTiers = [
  {
    name: "analyzeio Premium",
    id: "premium",
    description: "Get full institutional-grade access to our complete ensemble of AI forecasting models, automated support/resistance zones, and intra-day screener cycles.",
    features: [
      { title: "5 AI Ensemble Models", desc: "XGBoost, LSTM, Linear Regression, PatchTST, and Support/Resistance models working together for direction consensus." },
      { title: "Intra-day Forecasts", desc: "Predictions computed across 15-minute, 1-hour, 4-hour, and 1-day intervals to match high and low frequency strategies." },
      { title: "Support/Resistance Auto-Zones", desc: "Automatically updates 5 major support and resistance zones on the chart with vector acceleration." },
      { title: "100% Bullish Consensus Screener", desc: "Instantly scan and find assets where all 5 AI models predict a bullish trend with high confidence." },
      { title: "Unlimited Watchlists", desc: "Monitor as many assets and tickers as you want with personalized logs and instant prediction caching." },
      { title: "Priority GPU Queue", desc: "Fast-track your predictions and retrains through our dedicated GPU cloud queue." }
    ],
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

  // Helper values for annual savings display
  const priceValueMonthlyStr = prices[premiumTier.priceId.month] || "$2.00";
  const priceValueAnnualStr = prices[premiumTier.priceId.year] || "$20.00";

  return (
    <div className="min-h-screen bg-[#070a13] text-gray-100 flex flex-col font-sans relative overflow-hidden">
      
      {/* Custom Styles */}
      <style jsx global>{`
        .grid-bg {
          background-size: 50px 50px;
          background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        }
        .text-glow {
          text-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
        }
        .pricing-card-glow {
          box-shadow: 0 0 50px -10px rgba(139, 92, 246, 0.15), 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
      `}</style>

      {/* Grid Pattern Background */}
      <div className="absolute inset-0 grid-bg opacity-70 pointer-events-none" />

      {/* Ambient glowing radial shapes */}
      <div className="absolute top-[-10%] left-[50%] -translate-x-[50%] w-[800px] h-[600px] bg-gradient-to-b from-[#8b5cf6]/10 to-[#3b82f6]/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[20%] left-[-10%] w-[400px] h-[400px] bg-[#8b5cf6]/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] right-[-10%] w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Configuration Error Banner */}
      {hasConfigError && (
        <div className="relative z-50 bg-red-500/10 border-b border-red-500/25 py-4 px-6 flex items-center gap-3 text-red-400 text-xs">
          <AlertTriangle className="flex-shrink-0" style={{ width: "18px", height: "18px" }} />
          <div>
            <strong>Loud Configuration Error:</strong> Environment variables are missing. Please configure <code>NEXT_PUBLIC_PADDLE_CLIENT_TOKEN</code>, <code>NEXT_PUBLIC_PADDLE_ENV</code>, and Price IDs inside your <code>.env</code> file.
          </div>
        </div>
      )}

      {/* Top Navigation */}
      <header className="relative z-20 max-w-6xl w-full mx-auto px-6 pt-8 flex items-center justify-between">
        <Link href="/" className="btn-secondary" style={{ width: "fit-content" }}>
          <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
        </Link>
        
        <div className="text-[10px] uppercase tracking-wider text-gray-500 bg-white/[0.02] px-4 py-2 rounded-full border border-white/[0.06] backdrop-blur-md flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-[#8b5cf6] rounded-full animate-pulse" />
          Location: <span className="text-white font-bold">{initialCountry || "Auto-Detected (IP)"}</span>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-20 max-w-5xl w-full mx-auto px-6 py-12 flex-grow flex flex-col items-center justify-center">
        
        <div className="text-center mb-12">
          {/* Badge */}
          <div className="inline-flex items-center gap-1.5 bg-[#8b5cf6]/10 text-[#a78bfa] text-[10px] font-black tracking-widest uppercase px-4 py-1.5 rounded-full border border-[#8b5cf6]/35 mb-6 text-glow">
            <Sparkles style={{ width: "11px", height: "11px" }} /> Unrestricted Access
          </div>
          
          {/* Main Title */}
          <h1 className="text-4xl md:text-6xl font-black mb-4 tracking-tight text-white leading-tight">
            One Plan. <span style={{ background: "linear-gradient(to right, #a78bfa, #8b5cf6, #3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Full Ensemble.</span>
          </h1>
          
          {/* Description */}
          <p className="text-gray-400 max-w-xl mx-auto text-xs md:text-sm leading-relaxed">
            No limits, no complicated tiers. Subscribe once and unlock our entire machine learning architecture, consensus indicators, and multi-interval forecasts.
          </p>

          {/* Sliding Billing Toggle Switch */}
          <div className="mt-8 inline-flex bg-black/50 p-1.5 rounded-2xl border border-white/[0.05] backdrop-blur-xl">
            <button
              onClick={() => setFrequency("month")}
              className={`px-8 py-3 rounded-xl text-xs font-bold transition-all duration-300 ${
                frequency === "month"
                  ? "bg-[#8b5cf6] text-white shadow-lg shadow-purple-500/20"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Monthly billing
            </button>
            <button
              onClick={() => setFrequency("year")}
              className={`px-8 py-3 rounded-xl text-xs font-bold transition-all duration-300 flex items-center gap-2 ${
                frequency === "year"
                  ? "bg-[#8b5cf6] text-white shadow-lg shadow-purple-500/20"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Yearly billing
              <span className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-lg text-[9px] font-black border border-emerald-500/20">
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Premium Horizontal Split Layout Card */}
        <div className="w-full max-w-4xl glass-panel p-1 border border-white/[0.07] rounded-3xl overflow-hidden pricing-card-glow hover:border-[#8b5cf6]/30 transition-all duration-500 group relative">
          
          {/* Accent light shine effect */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#8b5cf6]/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
          
          <div className="grid grid-cols-1 md:grid-cols-12" style={{ background: "rgba(11, 15, 25, 0.4)" }}>
            
            {/* Left Column: CTA & Pricing Details */}
            <div className="md:col-span-5 p-8 md:p-10 flex flex-col justify-between border-b md:border-b-0 md:border-r border-white/[0.06] relative z-10">
              
              <div>
                <span className="text-[10px] font-black tracking-widest text-[#8b5cf6] uppercase block mb-1">PRO MEMBERSHIP</span>
                <h3 className="text-2xl font-black text-white mb-2">Premium Plan</h3>
                <p className="text-xs text-gray-500 leading-relaxed mb-8">Full access, including all future model releases and technical tools.</p>
              </div>

              {/* Large Price Presentation */}
              <div className="my-6">
                {loadingPrices ? (
                  <div className="flex items-center gap-3 text-2xl font-extrabold text-gray-600 animate-pulse py-2">
                    <RefreshCw className="animate-spin text-[#8b5cf6]" style={{ width: "20px", height: "20px" }} /> Fetching localized price...
                  </div>
                ) : displayPrice ? (
                  <div>
                    <div className="flex items-baseline">
                      <span className="text-5xl font-black text-white tracking-tight">{displayPrice}</span>
                      <span className="text-gray-500 text-xs font-semibold ml-2">
                        /{frequency === "month" ? "mo" : "yr"}
                      </span>
                    </div>
                    {frequency === "year" && (
                      <p className="text-[10px] text-emerald-400 font-semibold mt-2.5 flex items-center gap-1">
                        <Zap style={{ width: "12px", height: "12px" }} /> Localized discount applied (equivalent to {(parseFloat(priceValueAnnualStr.replace(/[^0-9.]/g, '')) / 12).toLocaleString(undefined, {style: 'currency', currency: 'USD'})} / mo)
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-red-400 italic">Price configuration error</div>
                )}
              </div>

              {/* Action Button & Trust Markers */}
              <div>
                <button
                  onClick={() => handleSubscribe(premiumTier)}
                  disabled={loadingPrices || hasConfigError || !displayPrice}
                  className="btn-primary w-full py-4 text-xs font-black shadow-lg shadow-purple-500/20 mb-6"
                >
                  {loadingPrices ? "Initializing Checkout..." : "Start 7-Day Free Trial"}
                </button>

                <div className="space-y-2.5">
                  <div className="flex items-center gap-2 text-[10px] text-gray-500">
                    <ShieldCheck style={{ width: "14px", height: "14px", color: "#8b5cf6" }} /> 
                    <span>Secure Checkout powered by <strong>Paddle</strong></span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-gray-500">
                    <Calendar style={{ width: "14px", height: "14px", color: "#8b5cf6" }} /> 
                    <span>Free trial runs for exactly 7 days</span>
                  </div>
                </div>
              </div>

            </div>

            {/* Right Column: Grid of Included Features */}
            <div className="md:col-span-7 p-8 md:p-10 flex flex-col justify-center relative z-10" style={{ background: "rgba(0, 0, 0, 0.15)" }}>
              <span className="text-[10px] font-black tracking-widest text-gray-500 uppercase block mb-6">WHAT'S INCLUDED</span>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {premiumTier.features.map((feat, idx) => (
                  <div key={idx} className="flex gap-3">
                    <div className="w-5 h-5 bg-[#8b5cf6]/10 rounded-lg flex items-center justify-center border border-[#8b5cf6]/20 flex-shrink-0 mt-0.5">
                      <Check style={{ width: "11px", height: "11px", color: "#a78bfa" }} />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white mb-1">{feat.title}</h4>
                      <p className="text-[10px] text-gray-500 leading-relaxed">{feat.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>

        {/* FAQ Section */}
        <section className="w-full max-w-4xl mt-24">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-black text-white tracking-tight">Frequently Asked Questions</h2>
            <p className="text-xs text-gray-500 mt-2">Everything you need to know about our billing and trials.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="glass-panel p-6 border border-white/[0.04] bg-white/[0.01]">
              <h4 className="text-xs font-bold text-white mb-2">How does the 7-day free trial work?</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                When you click subscribe, you authenticate with Paddle and sign up for a trial. You won't be charged anything today. If you cancel at any time within the first 7 days, your card will never be billed.
              </p>
            </div>
            
            <div className="glass-panel p-6 border border-white/[0.04] bg-white/[0.01]">
              <h4 className="text-xs font-bold text-white mb-2">How do I cancel my subscription?</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                You can cancel in seconds. Just click your Profile icon in the upper-right corner of the dashboard, choose "Aboneliği Yönet" (Manage Subscription) to open the secure Paddle billing portal, and click Cancel.
              </p>
            </div>

            <div className="glass-panel p-6 border border-white/[0.04] bg-white/[0.01]">
              <h4 className="text-xs font-bold text-white mb-2">Are the AI predictions guaranteed?</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                No, all financial forecasts are statistical predictions calculated by neural networks and ensembles. They represent probabilities, not financial advice or guarantees. Never trade more than you can afford to lose.
              </p>
            </div>

            <div className="glass-panel p-6 border border-white/[0.04] bg-white/[0.01]">
              <h4 className="text-xs font-bold text-white mb-2">Can I update my billing method?</h4>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Yes, our self-service billing portal is hosted securely by Paddle. You can change payment cards, update billing details, download invoices, or toggle billing cycles in one place.
              </p>
            </div>
          </div>
        </section>

      </main>

      {/* Footer policy links */}
      <footer className="relative z-20 border-t border-white/[0.04] py-8 text-center text-[10px] text-gray-600 max-w-6xl w-full mx-auto px-6 mt-16 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          © {new Date().getFullYear()} analyzeio. All rights reserved.
        </div>
        <div className="flex items-center gap-4 font-semibold text-gray-500">
          <Link href="/terms" className="hover:text-[#a78bfa] transition-colors">Terms of Service</Link>
          <span>•</span>
          <Link href="/privacy" className="hover:text-[#a78bfa] transition-colors">Privacy Policy</Link>
          <span>•</span>
          <Link href="/refunds" className="hover:text-[#a78bfa] transition-colors">Refund Policy</Link>
        </div>
      </footer>

    </div>
  );
}
