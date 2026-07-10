import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "Refund Policy | analyzeio",
  description: "Refund policy detailing trial cancellations and subscription refunds for analyzeio.",
};

export default function RefundsPage() {
  return (
    <div className="min-h-screen bg-[#0d0f14] text-gray-300 font-sans py-16 px-6">
      <div className="max-w-3xl mx-auto">
        
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-12">
          <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
        </Link>

        {/* Title */}
        <h1 className="text-3xl md:text-4xl font-black text-white mb-4 tracking-tight">Refund Policy</h1>
        <p className="text-xs text-gray-500 mb-8">Last updated: July 10, 2026</p>

        {/* Contents */}
        <div className="space-y-8 text-sm leading-relaxed text-gray-400">
          
          <section>
            <h2 className="text-lg font-bold text-white mb-3">1. 7-Day Free Trial</h2>
            <p>
              We offer a 7-day free trial on all subscription plans. This allows you to explore all premium AI forecasting features, technical consensus screeners, and indicator analysis tools risk-free.
            </p>
            <p className="mt-2">
              If you cancel your subscription within the 7-day trial period, your payment method will not be charged, and no fees will be billed.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">2. Refund Terms</h2>
            <p>
              Once your 7-day free trial ends and your payment method is billed, all charges are generally non-refundable. Because our service delivers instant, digital access to machine learning outputs and streaming predictions data, we cannot offer retro-active refunds on processed billing cycles.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">3. Billing Discrepancies & Technical Failures</h2>
            <p>
              Exceptions to the non-refundable terms may be made in the following rare circumstances:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1.5 text-xs text-gray-500">
              <li>You were double-billed due to a payment processing bug.</li>
              <li>A critical system outage prevented you from accessing the platform for more than 48 consecutive hours.</li>
            </ul>
            <p className="mt-2">
              If you believe you have a billing discrepancy, please contact our support team with your transaction details.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">4. How to Cancel</h2>
            <p>
              You can cancel your subscription at any time to prevent future charges. To cancel:
            </p>
            <ol className="list-decimal pl-5 mt-2 space-y-1.5 text-xs text-gray-500">
              <li>Click your Profile icon in the upper-right corner of the dashboard.</li>
              <li>Select <strong>Manage Subscription</strong> (Aboneliği Yönet).</li>
              <li>This securely directs you to your Paddle Billing Portal where you can click "Cancel Subscription".</li>
            </ol>
            <p className="mt-2">
              Upon cancellation, your access remains active until the end of your current billing period.
            </p>
          </section>

        </div>

      </div>
    </div>
  );
}
