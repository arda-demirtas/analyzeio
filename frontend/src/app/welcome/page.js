"use client";

import Link from "next/link";
import { Sparkles, Home, Zap, Cpu, Layers } from "lucide-react";

export default function WelcomePage() {
  return (
    <div className="welcome-container">
      {/* Background grid and glowing orbs to match /pricing */}
      <div className="bg-grid" />
      <div className="glow-orb-1" />
      <div className="glow-orb-2" />
      
      {/* Welcome Card */}
      <div className="welcome-card">
        {/* Success Badge */}
        <div className="success-badge">
          <Sparkles style={{ width: "12px", height: "12px", fill: "white" }} />
          <span>Subscription Active</span>
        </div>
        
        <h1 className="welcome-title">Welcome to Premium!</h1>
        <p className="welcome-desc">
          Your payment was successful and your membership is now active. You have unlocked all professional analysis features.
        </p>

        {/* Unlocked Features List */}
        <div className="features-container">
          <h4 className="features-title">What you've unlocked:</h4>
          
          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <Cpu style={{ width: "14px", height: "14px", color: "#a7f3d0" }} />
            </div>
            <div className="feature-text-wrapper">
              <span className="feature-label">All 5 AI Prediction Models</span>
              <span className="feature-sublabel">XGBoost, LSTM, Linear Regression, PatchTST, and Support/Resistance.</span>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <Zap style={{ width: "14px", height: "14px", color: "#fef3c7" }} />
            </div>
            <div className="feature-text-wrapper">
              <span className="feature-label">Intra-day Forecasts</span>
              <span className="feature-sublabel">Access predictions on 15m, 1h, and 4h intervals for high-frequency trends.</span>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon-wrapper">
              <Layers style={{ width: "14px", height: "14px", color: "#e0f2fe" }} />
            </div>
            <div className="feature-text-wrapper">
              <span className="feature-label">100% Upward Trend Consensus Analysis</span>
              <span className="feature-sublabel">Filter and discover assets where all 5 models have strong upward trend alignment.</span>
            </div>
          </div>
        </div>

        {/* Go to Dashboard CTA */}
        <Link href="/" className="btn-dashboard">
          <Home style={{ width: "16px", height: "16px" }} />
          <span>Go to Dashboard</span>
        </Link>
      </div>

      {/* CSS Stylesheet Inject */}
      <style jsx>{`
        .welcome-container {
          min-height: 100vh;
          background-color: #070a13;
          color: var(--text-main);
          font-family: var(--font-family, sans-serif);
          position: relative;
          overflow-x: hidden;
          padding: 60px 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
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
        .welcome-card {
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
          z-index: 10;
          text-align: center;
        }
        .welcome-card:hover {
          border-color: rgba(139, 92, 246, 0.4);
          box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(139, 92, 246, 0.12);
        }
        .success-badge {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 1.5px;
          text-transform: uppercase;
          padding: 6px 16px;
          border-radius: 20px;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 24px;
        }
        .welcome-title {
          font-size: 28px;
          font-weight: 800;
          color: white;
          margin: 0 0 10px 0;
          letter-spacing: -0.5px;
        }
        .welcome-desc {
          font-size: 13px;
          color: #9ca3af;
          line-height: 1.5;
          margin: 0 0 30px 0;
        }
        .features-container {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.03);
          border-radius: 16px;
          padding: 20px;
          margin-bottom: 30px;
          text-align: left;
        }
        .features-title {
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #9ca3af;
          margin: 0 0 15px 0;
        }
        .feature-item {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
          align-items: flex-start;
        }
        .feature-item:last-child {
          margin-bottom: 0;
        }
        .feature-icon-wrapper {
          background: rgba(139, 92, 246, 0.1);
          border: 1px solid rgba(139, 92, 246, 0.15);
          border-radius: 8px;
          padding: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .feature-text-wrapper {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .feature-label {
          font-size: 13px;
          font-weight: 650;
          color: white;
        }
        .feature-sublabel {
          font-size: 11px;
          color: #6b7280;
          line-height: 1.4;
        }
        .btn-dashboard {
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
          text-decoration: none;
        }
        .btn-dashboard:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 24px rgba(139, 92, 246, 0.45);
          background: linear-gradient(135deg, #9b72ff 0%, #8b5cf6 100%);
        }
        .btn-dashboard:active {
          transform: translateY(1px);
        }
      `}</style>
    </div>
  );
}
