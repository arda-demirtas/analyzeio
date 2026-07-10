import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "Terms of Service | analyzeio",
  description: "Terms and conditions governing the use of the analyzeio AI market forecasting platform.",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#0d0f14] text-gray-300 font-sans py-16 px-6">
      <div className="max-w-3xl mx-auto">
        
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-12">
          <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
        </Link>

        {/* Title */}
        <h1 className="text-3xl md:text-4xl font-black text-white mb-4 tracking-tight">Terms of Service</h1>
        <p className="text-xs text-gray-500 mb-8">Last updated: July 10, 2026</p>

        {/* Contents */}
        <div className="space-y-8 text-sm leading-relaxed text-gray-400">
          
          <section>
            <h2 className="text-lg font-bold text-white mb-3">1. Agreement to Terms</h2>
            <p>
              By accessing or using analyzeio (the "Service"), you agree to be bound by these Terms of Service. If you do not agree with any part of these terms, you are prohibited from using the Service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">2. Description of Service</h2>
            <p>
              analyzeio provides AI-driven market prediction models, technical indicator analysis, support & resistance level overlays, and market sentiment tracking. All insights are generated via machine learning algorithms and are for informational purposes only.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">3. Subscriptions & Billing</h2>
            <p>
              Subscriptions to our Premium plans are processed securely via our payment provider, Paddle. By subscribing, you agree to Paddle's Terms of Use and authorize recurring billing under the selected plan frequency (monthly or yearly). 
            </p>
            <p className="mt-2">
              All plans include a 7-day free trial. If you do not cancel before the end of the trial period, your payment method will be charged.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">4. Disclaimer of Financial Advice</h2>
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4 text-amber-400 text-xs">
              <strong>IMPORTANT:</strong> analyzeio is NOT a registered financial advisor. The AI predictions, technical metrics, and analysis presented on this platform do not constitute financial, investment, or trading advice. You should conduct your own research or consult with a licensed professional before making any financial decisions. Trading digital assets involves significant risk.
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">5. Intellectual Property</h2>
            <p>
              The AI models, vectorized data output, codebases, design assets, and logos are the sole property of analyzeio. You are granted a limited, non-exclusive, non-transferable license to view outputs for personal, non-commercial use.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">6. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, analyzeio shall not be liable for any direct, indirect, incidental, special, or consequential damages resulting from the use or inability to use our predictions or platform, even if advised of the possibility of such damages.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">7. Modifications</h2>
            <p>
              We reserve the right to modify these terms at any time. Your continued use of the platform following updates constitutes acceptance of the modified Terms of Service.
            </p>
          </section>

        </div>

      </div>
    </div>
  );
}
