"use client";

import { useEffect, useState } from "react";
import { initializePaddle } from "@paddle/paddle-js";
import { ArrowLeft, Check, Sparkles, AlertTriangle, RefreshCw, Shield, HelpCircle } from "lucide-react";
import Link from "next/link";

const API_BASE_URL = typeof window !== "undefined" 
  ? (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
      ? "http://127.0.0.1:8000" 
      : window.location.origin) 
  : "http://127.0.0.1:8000";

// Single-Tier Premium Pricing Definition
export const PricingTiers = [
  {
    name: "analyzeio Premium",
    id: "premium",
    description: "Unlock the full potential of machine learning forecasts and indicator ensembles.",
    features: [
      "Access to all 5 AI Models (XGBoost, LSTM, LR, PatchTST, S/R)",
      "High-frequency intra-day prediction cycles (15m, 1h, 4h)",
      "100% Upward Trend Consensus Analysis",
      "Automatic Support & Resistance level overlays",
      "Unlimited watchlists and caching prioritisation",
      "Priority server processing and GPU training queues",
      "7-Day Free Trial included on all signups"
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
        const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
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
      alert("Error: Price ID is not configured.");
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
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#070a13",
      color: "var(--text-main)",
      fontFamily: "var(--font-family)",
      position: "relative",
      overflowX: "hidden",
      padding: "60px 20px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center"
    }}>
      
      {/* CSS Stylesheet Inject */}
      <style jsx>{`
        .bg-grid {
          position: absolute;
          inset: 0;
          background-size: 40px 40px;
          background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
          pointer-events: none;
          opacity: 0.8;
          z-index: 1;
        }
        .glow-orb-1 {
          position: absolute;
          top: -150px;
          left: 50%;
          transform: translateX(-50%);
          width: 700px;
          height: 500px;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%);
          border-radius: 50%;
          pointer-events: none;
          z-index: 2;
        }
        .glow-orb-2 {
          position: absolute;
          bottom: 10%;
          right: 5%;
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
          border-radius: 50%;
          pointer-events: none;
          z-index: 2;
        }
        .pricing-card {
          background: rgba(17, 24, 39, 0.45);
          border: 1px solid rgba(139, 92, 246, 0.2);
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(139, 92, 246, 0.06);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: 24px;
          padding: 40px;
          width: 100%;
          max-width: 480px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
        }
        .pricing-card:hover {
          border-color: rgba(139, 92, 246, 0.4);
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(139, 92, 246, 0.12);
          transform: translateY(-4px);
        }
        .pricing-badge {
          background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
          color: white;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 1.5px;
          text-transform: uppercase;
          padding: 6px 16px;
          border-radius: 20px;
          box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 24px;
        }
        .pricing-title {
          font-size: 28px;
          font-weight: 800;
          color: white;
          margin: 0 0 10px 0;
          letter-spacing: -0.5px;
        }
        .pricing-desc {
          font-size: 13px;
          color: var(--text-muted);
          line-height: 1.5;
          margin: 0;
        }
        .price-wrapper {
          display: flex;
          align-items: baseline;
          margin: 30px 0;
        }
        .price-amount {
          font-size: 54px;
          font-weight: 900;
          color: white;
          letter-spacing: -1.5px;
          line-height: 1;
        }
        .price-cycle {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-muted);
          margin-left: 8px;
        }
        .btn-checkout {
          width: 100%;
          padding: 16px 24px;
          background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        .btn-checkout:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 24px rgba(139, 92, 246, 0.45);
          background: linear-gradient(135deg, #9b72ff 0%, #8b5cf6 100%);
        }
        .btn-checkout:active {
          transform: translateY(1px);
        }
        .btn-checkout:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          transform: none !important;
          box-shadow: none !important;
        }
        .features-list {
          list-style: none;
          padding: 0;
          margin: 35px 0 0 0;
          border-top: 1px solid rgba(255, 255, 255, 0.06);
          padding-top: 30px;
        }
        .feature-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          font-size: 13px;
          color: #d1d5db;
          margin-bottom: 16px;
          line-height: 1.4;
        }
        .feature-icon-box {
          width: 18px;
          height: 18px;
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.25);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-top: 1px;
        }
        .toggle-switch-container {
          background: rgba(0, 0, 0, 0.45);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 30px;
          padding: 4px;
          display: inline-flex;
          margin-bottom: 40px;
        }
        .toggle-btn {
          border: none;
          background: none;
          color: var(--text-muted);
          padding: 10px 24px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.3s;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .toggle-btn.active {
          background: #8b5cf6;
          color: white;
          box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
        }
        .faq-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          width: 100%;
          max-width: 800px;
          margin-top: 60px;
        }
        @media (max-width: 768px) {
          .faq-grid {
            grid-template-columns: 1fr;
          }
        }
        .faq-card {
          background: rgba(255, 255, 255, 0.01);
          border: 1px solid rgba(255, 255, 255, 0.03);
          border-radius: 16px;
          padding: 24px;
        }
      `}</style>

      {/* Grid Pattern & Orbs */}
      <div className="bg-grid" />
      <div className="glow-orb-1" />
      <div className="glow-orb-2" />

      {/* Main Wrapper */}
      <div style={{
        maxWidth: "800px",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
        zIndex: 10
      }}>
        
        {/* Navigation & Logo Header */}
        <div style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "60px"
        }}>
          <Link href="/" className="btn-secondary">
            <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back
          </Link>
          <span style={{
            fontSize: "12px",
            fontWeight: "700",
            color: "var(--text-muted)",
            background: "rgba(255, 255, 255, 0.02)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
            padding: "6px 16px",
            borderRadius: "20px"
          }}>
            Pricing Localisation: <span style={{ color: "#a78bfa" }}>{initialCountry || "Auto (IP)"}</span>
          </span>
        </div>

        {/* Hero Title */}
        <div style={{ textAlign: "center", marginBottom: "10px" }}>
          <h1 style={{
            fontSize: "42px",
            fontWeight: "900",
            letterSpacing: "-1px",
            color: "white",
            marginBottom: "16px"
          }}>
            Get analyzeio Premium
          </h1>
          <p style={{
            fontSize: "14px",
            color: "var(--text-muted)",
            maxWidth: "460px",
            margin: "0 auto",
            lineHeight: "1.5"
          }}>
            Institutional-grade ensemble forecasts, automatic support/resistance levels, and bullish trend screeners in one place.
          </p>
        </div>

        {/* Toggle Billing Switch */}
        <div className="toggle-switch-container">
          <button
            onClick={() => setFrequency("month")}
            className={`toggle-btn ${frequency === "month" ? "active" : ""}`}
          >
            Monthly
          </button>
          <button
            onClick={() => setFrequency("year")}
            className={`toggle-btn ${frequency === "year" ? "active" : ""}`}
          >
            Yearly
            <span style={{
              fontSize: "9px",
              background: "rgba(16, 185, 129, 0.15)",
              color: "#10b981",
              padding: "1px 6px",
              borderRadius: "6px",
              marginLeft: "4px"
            }}>
              Save 17%
            </span>
          </button>
        </div>

        {/* Main Pricing Card (ChatGPT / Claude Pro Style) */}
        <div className="pricing-card">
          
          <div style={{ textAlign: "center" }}>
            <div className="pricing-badge">
              <Sparkles style={{ width: "12px", height: "12px" }} /> All Models Included
            </div>
            <h3 className="pricing-title">Premium</h3>
            <p className="pricing-desc">{premiumTier.description}</p>
          </div>

          {/* Pricing Amount */}
          <div className="price-wrapper" style={{ justifyContent: "center" }}>
            {loadingPrices ? (
              <div style={{
                fontSize: "20px",
                color: "var(--text-muted)",
                fontWeight: "700",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "15px 0"
              }}>
                <RefreshCw className="animate-spin text-[#8b5cf6]" style={{ width: "16px", height: "16px" }} /> Loading price...
              </div>
            ) : displayPrice ? (
              <>
                <span className="price-amount">{displayPrice}</span>
                <span className="price-cycle">/{frequency === "month" ? "month" : "year"}</span>
              </>
            ) : (
              <span style={{ fontSize: "14px", color: "var(--accent-danger)" }}>Configuration unavailable</span>
            )}
          </div>

          {/* Checkout Button */}
          <button
            onClick={() => handleSubscribe(premiumTier)}
            disabled={loadingPrices || hasConfigError || !displayPrice}
            className="btn-checkout"
          >
            {loadingPrices ? "Loading Plan..." : "Start 7-Day Free Trial"}
          </button>

          {/* Secure Trust Marker */}
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            fontSize: "11px",
            color: "var(--text-muted)",
            marginTop: "16px"
          }}>
            <Shield style={{ width: "14px", height: "14px", color: "#10b981" }} />
            <span>Secure checkout handled by <strong>Paddle</strong></span>
          </div>

          {/* Features Checkbox List */}
          <ul className="features-list">
            {premiumTier.features.map((feature, idx) => (
              <li key={idx} className="feature-item">
                <div className="feature-icon-box">
                  <Check style={{ width: "10px", height: "10px", color: "#10b981" }} />
                </div>
                <span>{feature}</span>
              </li>
            ))}
          </ul>

        </div>

        {/* Trust Badges / Frequently Asked Questions */}
        <div className="faq-grid">
          
          <div className="faq-card">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
              <HelpCircle style={{ width: "16px", height: "16px", color: "#8b5cf6" }} />
              <h4 style={{ fontSize: "13px", fontWeight: "700", color: "white" }}>How does the 7-day trial work?</h4>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.5" }}>
              You will not be billed anything during the first 7 days of signing up. If you cancel before the trial concludes, no payment is taken.
            </p>
          </div>

          <div className="faq-card">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
              <HelpCircle style={{ width: "16px", height: "16px", color: "#8b5cf6" }} />
              <h4 style={{ fontSize: "13px", fontWeight: "700", color: "white" }}>Can I cancel anytime?</h4>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.5" }}>
              Yes, easily. Open your profile dropdown settings and select "Aboneliği Yönet" to cancel, update billing info, or view invoice history.
            </p>
          </div>

        </div>

        {/* Footer Policy Links */}
        <footer style={{
          width: "100%",
          borderTop: "1px solid rgba(255, 255, 255, 0.05)",
          paddingTop: "24px",
          marginTop: "80px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "11px",
          color: "var(--text-muted)"
        }}>
          <div>
            © {new Date().getFullYear()} analyzeio. All rights reserved.
          </div>
          <div style={{ display: "flex", gap: "16px", fontWeight: "600" }}>
            <Link href="/terms" style={{ color: "var(--text-muted)", textDecoration: "none" }} className="hover-glow">Terms</Link>
            <Link href="/privacy" style={{ color: "var(--text-muted)", textDecoration: "none" }} className="hover-glow">Privacy</Link>
            <Link href="/refunds" style={{ color: "var(--text-muted)", textDecoration: "none" }} className="hover-glow">Refunds</Link>
          </div>
        </footer>

      </div>

    </div>
  );
}
