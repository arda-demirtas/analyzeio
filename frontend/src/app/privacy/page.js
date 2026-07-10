import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata = {
  title: "Privacy Policy | analyzeio",
  description: "Privacy Policy detailing how analyzeio collects, stores, and protects customer information.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#0d0f14] text-gray-300 font-sans py-16 px-6">
      <div className="max-w-3xl mx-auto">
        
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-12">
          <ArrowLeft style={{ width: "16px", height: "16px" }} /> Back to Dashboard
        </Link>

        {/* Title */}
        <h1 className="text-3xl md:text-4xl font-black text-white mb-4 tracking-tight">Privacy Policy</h1>
        <p className="text-xs text-gray-500 mb-8">Last updated: July 10, 2026</p>

        {/* Contents */}
        <div className="space-y-8 text-sm leading-relaxed text-gray-400">
          
          <section>
            <h2 className="text-lg font-bold text-white mb-3">1. Information We Collect</h2>
            <p>
              We collect information that you directly provide to us, such as your email address and username when registering an account, or uploading a profile picture.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">2. Payment Processing & Billing Data</h2>
            <p>
              We process subscription payments using Paddle. Paddle collects credit card details, billing address, and other payment metadata. We do not store or process your complete credit card information on our servers; it is handled strictly and securely by Paddle.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">3. How We Use Your Information</h2>
            <p>
              We use the collected data to:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1.5 text-xs text-gray-500">
              <li>Manage and sync your subscription premium access.</li>
              <li>Provide personalized watchlists and comment sections.</li>
              <li>Deliver security notifications or system stat emails.</li>
              <li>Improve our machine learning models and server response times.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">4. Cookies & Trackers</h2>
            <p>
              We use essential cookies and local storage tokens to keep you logged in to your account and preserve your language preferences. We do not use third-party tracking or advertising cookies.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">5. Data Sharing & Third Parties</h2>
            <p>
              We do not sell, trade, or rent your personal information to third parties. We share data only with service providers critical to our core functions:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1.5 text-xs text-gray-500">
              <li><strong>Paddle:</strong> Payment processing, billing, and subscription management.</li>
              <li><strong>SMTP Providers:</strong> Outgoing email notifications.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">6. Security</h2>
            <p>
              We implement industry-standard encryption, password hashing, and token authorization protocols to protect your personal data. However, no electronic transmission or storage method is 100% secure.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-white mb-3">7. Your Rights</h2>
            <p>
              You have the right to request access, correction, or deletion of your personal account data. You can delete your account permanently directly from your profile settings dropdown at any time.
            </p>
          </section>

        </div>

      </div>
    </div>
  );
}
