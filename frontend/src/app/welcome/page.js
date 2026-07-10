import Link from "next/link";
import { CheckCircle, Home, TrendingUp, Sparkles } from "lucide-react";

export const metadata = {
  title: "Welcome to Premium | analyzeio",
  description: "Subscription activated successfully! Welcome to analyzeio Premium.",
};

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-[#0d0f14] text-gray-100 flex flex-col items-center justify-center font-sans px-6 relative overflow-hidden">
      
      {/* Background glowing gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-[300px] h-[300px] bg-emerald-500/5 rounded-full blur-[80px] pointer-events-none" />

      {/* Main card */}
      <div className="glass-panel max-w-lg w-full text-center p-10 flex flex-col items-center relative z-10 border border-gray-800/80 rounded-3xl" style={{ background: "rgba(15, 17, 26, 0.7)", backdropFilter: "blur(12px)" }}>
        
        {/* Success Icon */}
        <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mb-8 border border-emerald-500/20 shadow-lg shadow-emerald-500/5">
          <CheckCircle style={{ width: "32px", height: "32px" }} />
        </div>

        {/* Header */}
        <h1 className="text-3xl font-black mb-4 tracking-tight text-white flex items-center justify-center gap-2">
          <Sparkles style={{ width: "24px", height: "24px", color: "#eab308" }} />
          Welcome to Premium!
        </h1>
        
        <p className="text-gray-400 text-sm leading-relaxed mb-8">
          Your payment was successful and your subscription is active! 
          You now have full unrestricted access to all 5 AI models (XGBoost, LSTM, Linear Regression, PatchTST, and Support/Resistance), intra-day (15m, 1h, 4h) prediction cycles, and the 100% Bullish Consensus Dashboard.
        </p>

        {/* Feature Highlights */}
        <div className="w-full bg-gray-900/60 rounded-2xl p-5 mb-8 border border-gray-800/50 text-left space-y-4">
          <div className="flex items-start gap-3">
            <TrendingUp style={{ width: "16px", height: "16px", color: "var(--accent-primary)", flexShrink: 0, marginTop: "2px" }} />
            <div>
              <h4 className="text-xs font-bold text-white">Intra-day AI Forecasting</h4>
              <p className="text-[11px] text-gray-500 mt-0.5">Explore predictions on 15m, 1h, and 4h intervals for high-frequency insights.</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Sparkles style={{ width: "16px", height: "16px", color: "var(--accent-primary)", flexShrink: 0, marginTop: "2px" }} />
            <div>
              <h4 className="text-xs font-bold text-white">5-Model Ensemble Consensus</h4>
              <p className="text-[11px] text-gray-500 mt-0.5">Verify consensus across all machine learning and deep learning models simultaneously.</p>
            </div>
          </div>
        </div>

        {/* CTAs */}
        <Link href="/" className="btn-primary w-full py-3.5 rounded-2xl text-xs font-bold shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2">
          <Home style={{ width: "14px", height: "14px" }} /> Go to Dashboard
        </Link>

      </div>
      
    </div>
  );
}
