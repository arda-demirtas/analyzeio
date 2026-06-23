"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Plus, 
  Trash, 
  LogOut, 
  Key, 
  UserMinus, 
  RefreshCw, 
  LineChart, 
  User,
  Lock,
  Mail,
  PieChart,
  Shield,
  Briefcase,
  Menu,
  X
} from "lucide-react";
import { Chart, registerables } from "chart.js";

// Register all Chart.js components
Chart.register(...registerables);

const API_BASE_URL = typeof window !== "undefined" 
  ? (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
      ? "http://127.0.0.1:8000" 
      : window.location.origin) 
  : "http://127.0.0.1:8000";

export default function Home() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login"); // login, register
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // App State
  const [activeSymbol, setActiveSymbol] = useState("BTC-USD");
  const [searchQuery, setSearchQuery] = useState("");
  const [watchlist, setWatchlist] = useState([]);
  const [predictionData, setPredictionData] = useState(null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictError, setPredictError] = useState("");

  // Helper to switch active symbol and reset states synchronously
  const selectSymbol = (symbol) => {
    if (symbol === activeSymbol) return;
    setActiveSymbol(symbol);
    setPredictionData(null);
    setPredictError("");
    setPredictLoading(true);
  };
  
  // Settings / Profile Modals
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");

  // Refs for Charts
  const priceChartRef = useRef(null);
  const rsiChartRef = useRef(null);
  const macdChartRef = useRef(null);
  const priceChartInst = useRef(null);
  const rsiChartInst = useRef(null);
  const macdChartInst = useRef(null);

  // 1. Check for token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      fetchWatchlist(savedToken);
    }
  }, []);

  // 2. Fetch Prediction data when activeSymbol changes
  useEffect(() => {
    if (token) {
      loadPrediction(activeSymbol);
    }
  }, [activeSymbol, token]);

  // 3. Render charts when predictionData updates
  useEffect(() => {
    if (!predictionData) return;
    renderCharts();
    
    // Cleanup on unmount or update
    return () => {
      destroyCharts();
    };
  }, [predictionData]);

  // Helper: Destroy existing charts
  const destroyCharts = () => {
    if (priceChartInst.current) {
      priceChartInst.current.destroy();
      priceChartInst.current = null;
    }
    if (rsiChartInst.current) {
      rsiChartInst.current.destroy();
      rsiChartInst.current = null;
    }
    if (macdChartInst.current) {
      macdChartInst.current.destroy();
      macdChartInst.current = null;
    }
  };

  // Helper: Render price, RSI, and MACD charts
  const renderCharts = () => {
    destroyCharts();
    if (!predictionData) return;

    const ctxPrice = priceChartRef.current?.getContext("2d");
    const ctxRsi = rsiChartRef.current?.getContext("2d");
    const ctxMacd = macdChartRef.current?.getContext("2d");

    const history = predictionData.history;
    const labels = history.map(item => item.date);
    const closePrices = history.map(item => item.close);
    
    // Add prediction point
    const extendedLabels = [...labels, predictionData.prediction_date];
    const predictedPrices = Array(labels.length).fill(null);
    // Link last actual price to prediction price for continuous chart line
    predictedPrices[labels.length - 1] = closePrices[closePrices.length - 1];
    predictedPrices.push(predictionData.predicted_close);

    // Price Chart
    if (ctxPrice) {
      priceChartInst.current = new Chart(ctxPrice, {
        type: "line",
        data: {
          labels: extendedLabels,
          datasets: [
            {
              label: "Historical Close",
              data: closePrices,
              borderColor: "#8b5cf6",
              backgroundColor: "rgba(139, 92, 246, 0.05)",
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.15,
              fill: true,
            },
            {
              label: "LSTM Prediction",
              data: predictedPrices,
              borderColor: "#10b981",
              backgroundColor: "rgba(16, 185, 129, 0.05)",
              borderWidth: 2,
              borderDash: [5, 5],
              pointRadius: 6,
              pointBackgroundColor: "#10b981",
              pointBorderColor: "#fff",
              tension: 0.15,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: "#9ca3af", font: { family: "Inter" } }
            },
            tooltip: {
              mode: "index",
              intersect: false,
            }
          },
          scales: {
            x: {
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#9ca3af", maxTicksLimit: 8 }
            },
            y: {
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#9ca3af" }
            }
          }
        }
      });
    }

    // RSI Chart
    if (ctxRsi) {
      const rsiValues = history.map(item => item.rsi);
      rsiChartInst.current = new Chart(ctxRsi, {
        type: "line",
        data: {
          labels: labels,
          datasets: [{
            label: "RSI (14)",
            data: rsiValues,
            borderColor: "#f59e0b",
            borderWidth: 1.5,
            pointRadius: 0,
            tension: 0.1,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { display: false }
            },
            y: {
              min: 0,
              max: 100,
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#9ca3af", stepSize: 20 },
              // Draw horizontal helper lines at 30 and 70
              border: { dash: [5, 5] }
            }
          }
        }
      });
    }

    // MACD Chart
    if (ctxMacd) {
      const macdValues = history.map(item => item.macd);
      const signalValues = history.map(item => item.macd_signal);
      const histValues = history.map(item => item.macd_hist);
      
      rsiChartInst.current = new Chart(ctxMacd, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              type: "line",
              label: "MACD",
              data: macdValues,
              borderColor: "#3b82f6",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            },
            {
              type: "line",
              label: "Signal",
              data: signalValues,
              borderColor: "#ec4899",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            },
            {
              label: "Histogram",
              data: histValues,
              backgroundColor: histValues.map(h => h >= 0 ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"),
              borderWidth: 0,
              barPercentage: 0.8
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { display: false }
            },
            y: {
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#9ca3af", maxTicksLimit: 5 }
            }
          }
        }
      });
    }
  };

  // API Call: Fetch Watchlist
  const fetchWatchlist = async (authToken) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/watchlist`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const data = await res.json();
      setWatchlist(data);
      
      // Populate standard items if user's watchlist is empty
      if (data.length === 0) {
        initializeDefaultWatchlist(authToken);
      }
    } catch (err) {
      console.error("Watchlist fetch failed:", err);
    }
  };

  // Populate basic starting symbols to watchlist for a new user
  const initializeDefaultWatchlist = async (authToken) => {
    const defaults = ["BTC-USD", "AAPL", "GC=F", "TSLA"];
    const addedItems = [];
    for (const sym of defaults) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/watchlist`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${authToken}`
          },
          body: JSON.stringify({ symbol: sym })
        });
        if (res.ok) {
          const item = await res.json();
          addedItems.push(item);
        }
      } catch (err) {
        console.error(err);
      }
    }
    setWatchlist(addedItems);
  };

  // API Call: Load LSTM Prediction
  const loadPrediction = async (symbol) => {
    setPredictLoading(true);
    setPredictError("");
    setPredictionData(null); // Clear old prediction data to trigger loading UI immediately
    try {
      const res = await fetch(`${API_BASE_URL}/api/predict?symbol=${symbol}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const data = await res.json();
      if (res.ok) {
        setPredictionData(data);
      } else {
        setPredictError(data.detail || "Failed to load prediction model.");
      }
    } catch (err) {
      setPredictError("Connection failed to Python FastAPI server.");
    } finally {
      setPredictLoading(false);
    }
  };

  // API Call: Register
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      });
      const data = await res.json();
      if (res.ok) {
        // Auto-login after registration
        handleLogin(e);
      } else {
        setAuthError(data.detail || "Registration failed. Try again.");
      }
    } catch (err) {
      setAuthError("Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  // API Call: Login
  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
        fetchWatchlist(data.access_token);
        // Clear forms
        setUsername("");
        setPassword("");
        setEmail("");
      } else {
        setAuthError(data.detail || "Invalid credentials.");
      }
    } catch (err) {
      setAuthError("Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  // API Call: Add Watchlist Item
  const handleAddWatchlist = async (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    const sym = searchQuery.toUpperCase().trim();
    setSearchQuery("");
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/watchlist`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ symbol: sym })
      });
      const data = await res.json();
      if (res.ok) {
        setWatchlist([...watchlist, data]);
        selectSymbol(data.symbol);
      } else {
        alert(data.detail || "Could not add symbol to watchlist.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Remove Watchlist Item
  const handleRemoveWatchlist = async (e, symbolToRemove) => {
    e.stopPropagation(); // Prevent clicking item from changing active symbol
    try {
      const res = await fetch(`${API_BASE_URL}/api/watchlist/${symbolToRemove}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const filtered = watchlist.filter(item => item.symbol !== symbolToRemove);
        setWatchlist(filtered);
        if (activeSymbol === symbolToRemove && filtered.length > 0) {
          selectSymbol(filtered[0].symbol);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Change Password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });
      const data = await res.json();
      if (res.ok) {
        setPasswordSuccess("Password updated successfully.");
        setOldPassword("");
        setNewPassword("");
        setTimeout(() => setShowPasswordModal(false), 2000);
      } else {
        setPasswordError(data.detail || "Failed to change password.");
      }
    } catch (err) {
      setPasswordError("Connection failed.");
    }
  };

  // API Call: Close/Delete Account
  const handleDeleteAccount = async () => {
    if (!window.confirm("WARNING: Are you absolutely sure you want to permanently close your account? This action deletes all your saved symbols and settings and cannot be undone.")) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/delete-account`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        alert("Account successfully deleted.");
        handleLogout();
      }
    } catch (err) {
      alert("Failed to delete account.");
    }
  };

  // Logout Local Handling
  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setWatchlist([]);
    setPredictionData(null);
    setActiveSymbol("BTC-USD");
  };

  // Helpers to calculate badges for RSI and MACD
  const getRsiBadge = (rsi) => {
    if (rsi === null || rsi === undefined) return <span className="badge badge-warning">N/A</span>;
    if (rsi >= 70) return <span className="badge badge-danger">RSI: {rsi.toFixed(1)} (Overbought)</span>;
    if (rsi <= 30) return <span className="badge badge-success">RSI: {rsi.toFixed(1)} (Oversold)</span>;
    return <span className="badge badge-warning">RSI: {rsi.toFixed(1)} (Neutral)</span>;
  };

  const getMacdBadge = (macd, hist) => {
    if (macd === null || macd === undefined) return <span className="badge badge-warning">N/A</span>;
    if (hist > 0) return <span className="badge badge-success">MACD: Bullish</span>;
    return <span className="badge badge-danger">MACD: Bearish</span>;
  };

  // Render Auth UI if not logged in
  if (!token) {
    return (
      <div className="auth-wrapper">
        <div className="glass-panel auth-card">
          <div className="auth-header">
            <h1 className="logo-text" style={{ fontSize: "36px", marginBottom: "10px" }}>analyzeio</h1>
            <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
              Secure & Professional LSTM Stock & Crypto Predictor
            </p>
          </div>
          
          <form onSubmit={authMode === "login" ? handleLogin : handleRegister} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div style={{ position: "relative" }}>
              <User style={{ position: "absolute", left: "14px", top: "13px", color: "var(--text-muted)", width: "18px" }} />
              <input
                type="text"
                placeholder="Username"
                className="input-field"
                value={username}
                onChange={e => setUsername(e.target.value)}
                style={{ paddingLeft: "42px" }}
                required
              />
            </div>

            {authMode === "register" && (
              <div style={{ position: "relative" }}>
                <Mail style={{ position: "absolute", left: "14px", top: "13px", color: "var(--text-muted)", width: "18px" }} />
                <input
                  type="email"
                  placeholder="Email Address"
                  className="input-field"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  style={{ paddingLeft: "42px" }}
                  required
                />
              </div>
            )}

            <div style={{ position: "relative" }}>
              <Lock style={{ position: "absolute", left: "14px", top: "13px", color: "var(--text-muted)", width: "18px" }} />
              <input
                type="password"
                placeholder="Password"
                className="input-field"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ paddingLeft: "42px" }}
                required
              />
            </div>

            {authError && (
              <div style={{ color: "var(--accent-danger)", fontSize: "13px", textAlign: "center", fontWeight: "500" }}>
                {authError}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={authLoading}>
              {authLoading ? <RefreshCw className="animate-spin" style={{ width: "18px" }} /> : null}
              {authMode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>

          <div className="auth-toggle">
            {authMode === "login" ? (
              <>
                New to analyzeio? <span onClick={() => { setAuthMode("register"); setAuthError(""); }}>Create an account</span>
              </>
            ) : (
              <>
                Already have an account? <span onClick={() => { setAuthMode("login"); setAuthError(""); }}>Sign In</span>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Render Dashboard if logged in
  return (
    <div className="app-container">
      {sidebarOpen && (
        <div 
          className="sidebar-backdrop" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Mobile Top Navbar */}
      <header className="mobile-navbar">
        <button 
          type="button"
          className="mobile-navbar-toggle" 
          onClick={() => setSidebarOpen(true)}
          aria-label="Open Menu"
        >
          <Menu style={{ width: "22px", height: "22px" }} />
        </button>
        <div className="mobile-navbar-logo">
          <Briefcase style={{ color: "var(--accent-primary)", width: "20px", height: "20px" }} />
          <span className="logo-text" style={{ fontSize: "18px" }}>analyzeio</span>
        </div>
        <div style={{ width: "40px" }} /> {/* Spacer to center the logo */}
      </header>
      
      {/* Sidebar Panel */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="logo-container" style={{ justifyContent: "space-between", width: "100%" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Briefcase style={{ color: "var(--accent-primary)", width: "28px", height: "28px" }} />
            <span className="logo-text">analyzeio</span>
          </div>
          <button 
            type="button"
            className="mobile-close-btn"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close Menu"
          >
            <X style={{ width: "20px", height: "20px" }} />
          </button>
        </div>

        {/* Search Input */}
        <form onSubmit={handleAddWatchlist} style={{ display: "flex", gap: "8px" }}>
          <div style={{ position: "relative", flexGrow: 1 }}>
            <Search style={{ position: "absolute", left: "12px", top: "12px", color: "var(--text-muted)", width: "16px" }} />
            <input
              type="text"
              placeholder="Search symbol (AAPL...)"
              className="input-field"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ paddingLeft: "36px", paddingRight: "10px", height: "40px" }}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ width: "40px", height: "40px", padding: 0 }}>
            <Plus style={{ width: "18px" }} />
          </button>
        </form>

        {/* Watchlist */}
        <div className="watchlist-container">
          <h3 className="watchlist-title">Your Watchlist</h3>
          {watchlist.map(item => (
            <div 
              key={item.id}
              onClick={() => {
                selectSymbol(item.symbol);
                setSidebarOpen(false);
              }}
              className={`watchlist-item ${activeSymbol === item.symbol ? "active" : ""}`}
            >
              <span className="watchlist-item-symbol">{item.symbol}</span>
              <button 
                onClick={(e) => handleRemoveWatchlist(e, item.symbol)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <Trash style={{ width: "14px" }} />
              </button>
            </div>
          ))}
        </div>

        {/* User profile controls */}
        <div className="user-panel">
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ background: "rgba(139, 92, 246, 0.2)", borderRadius: "50%", width: "32px", height: "32px", display: "flex", alignItems: "center", justifyItems: "center" }}>
                <User style={{ width: "16px", color: "var(--accent-primary)", margin: "auto" }} />
              </div>
              <span style={{ fontSize: "14px", fontWeight: "600" }}>Dashboard Session</span>
            </div>

            <button onClick={() => setShowPasswordModal(true)} className="btn-secondary" style={{ width: "100%", justifyContent: "flex-start" }}>
              <Key style={{ width: "14px" }} /> Change Password
            </button>
            <button onClick={handleDeleteAccount} className="btn-danger" style={{ width: "100%", textAlign: "left", display: "flex", alignItems: "center", gap: "6px" }}>
              <UserMinus style={{ width: "14px" }} /> Close Account
            </button>
            <button onClick={handleLogout} className="btn-secondary" style={{ width: "100%", justifyContent: "flex-start", marginTop: "10px" }}>
              <LogOut style={{ width: "14px" }} /> Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Panel Content */}
      <main className="main-content">
        {predictLoading || (!predictionData && !predictError) || (predictionData && predictionData.symbol !== activeSymbol) ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", gap: "20px" }}>
            <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)", width: "48px", height: "48px" }} />
            <h3 style={{ fontSize: "18px", color: "var(--text-main)", fontWeight: "600" }}>Fetching Market Data & Training LSTM...</h3>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", textAlign: "center", maxWidth: "400px" }}>
              Downloading historical daily prices, computing 11 indicators, and optimizing the neural network cache for {activeSymbol}.
            </p>
          </div>
        ) : predictError ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", color: "var(--accent-danger)", gap: "10px" }}>
            <span style={{ fontSize: "18px", fontWeight: "600" }}>Error Loading Data</span>
            <span style={{ textAlign: "center", maxWidth: "400px" }}>{predictError}</span>
            <button onClick={() => loadPrediction(activeSymbol)} className="btn-secondary" style={{ marginTop: "10px" }}>
              <RefreshCw style={{ width: "14px" }} /> Try Again
            </button>
          </div>
        ) : (
          <>
            {/* Main Content Header */}
            <div className="glass-panel header-panel">
              <div>
                <h2 className="asset-title">{predictionData ? predictionData.name : activeSymbol}</h2>
                <div className="header-badges-container">
                  <span style={{ fontSize: "14px", color: "var(--text-muted)", marginRight: "5px" }}>Ticker: {activeSymbol}</span>
                  {predictionData && (
                    <>
                      {getRsiBadge(predictionData.history[predictionData.history.length - 1]?.rsi)}
                      {getMacdBadge(
                        predictionData.history[predictionData.history.length - 1]?.macd,
                        predictionData.history[predictionData.history.length - 1]?.macd_hist
                      )}
                      <span className="badge badge-info">Open: ${predictionData.history[predictionData.history.length - 1]?.open?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Close: ${predictionData.history[predictionData.history.length - 1]?.close?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">High: ${predictionData.history[predictionData.history.length - 1]?.high?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Low: ${predictionData.history[predictionData.history.length - 1]?.low?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Vol: {predictionData.history[predictionData.history.length - 1]?.volume?.toLocaleString("en-US")}</span>
                      <span className="badge badge-info">EMA 20: ${predictionData.history[predictionData.history.length - 1]?.ema_20?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">EMA 50: ${predictionData.history[predictionData.history.length - 1]?.ema_50?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">BB Upper: ${predictionData.history[predictionData.history.length - 1]?.bb_upper?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">BB Lower: ${predictionData.history[predictionData.history.length - 1]?.bb_lower?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </>
                  )}
                </div>
              </div>
              <div className="header-price-panel">
                <div className="asset-price">
                  ${predictionData && predictionData.current_price !== undefined && predictionData.current_price !== null 
                    ? predictionData.current_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) 
                    : (predictionData ? predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "---")}
                </div>
                <span style={{ fontSize: "12px", color: "var(--accent-primary)", fontWeight: "600", display: "block" }}>
                  ● Live Market Price
                </span>
                {predictionData && (
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                    Last Close: ${predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({predictionData.last_date})
                  </span>
                )}
              </div>
            </div>

            {/* Dashboard Grid (Charts and Predictions) */}
            <div className="dashboard-grid">
              {/* Column 1: Charts */}
              <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
                {/* Price Chart Card */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "20px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <LineChart style={{ color: "var(--accent-primary)" }} /> Historical Price & Next Day Prediction
                  </h3>
                  <div className="chart-wrapper">
                    <canvas ref={priceChartRef} />
                  </div>
                </div>

                {/* Technical Indicators Chart Card */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px" }}>Technical Oscillators</h3>
                  <div className="indicator-grid">
                    <div>
                      <h4 style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>Relative Strength Index (RSI)</h4>
                      <div className="indicator-wrapper">
                        <canvas ref={rsiChartRef} />
                      </div>
                    </div>
                    <div>
                      <h4 style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>MACD Divergence</h4>
                      <div className="indicator-wrapper">
                        <canvas ref={macdChartRef} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Column 2: LSTM Prediction Summary */}
              <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
                {/* Prediction Highlight Card */}
                <div className="glass-panel prediction-card" style={{ minHeight: "220px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                  <span className="prediction-label">Next Trading Day Predicted Close</span>
                  <div className="prediction-value">
                    ${predictionData ? predictionData.predicted_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "---"}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "-5px" }}>
                    Expected Close: {predictionData ? predictionData.expected_close_time : "---"}
                  </div>
                  
                  {predictionData && (
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", fontWeight: "700", marginTop: "15px" }}>
                      {predictionData.price_change_percent >= 0 ? (
                        <>
                          <TrendingUp style={{ color: "var(--accent-success)" }} />
                          <span style={{ color: "var(--accent-success)" }}>
                            +{predictionData.price_change_percent.toFixed(2)}% (Bullish)
                          </span>
                        </>
                      ) : (
                        <>
                          <TrendingDown style={{ color: "var(--accent-danger)" }} />
                          <span style={{ color: "var(--accent-danger)" }}>
                            {predictionData.price_change_percent.toFixed(2)}% (Bearish)
                          </span>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Model Information & Metrics */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px" }}>LSTM Model Analytics</h3>
                  
                  <div className="stats-list">
                    <div className="stats-row">
                      <span>Cache Status</span>
                      <span>{predictionData ? predictionData.metrics.training_status : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>Backtest Root MSE (RMSE)</span>
                      <span>{predictionData ? `$${predictionData.metrics.rmse.toFixed(2)}` : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>Mean Absolute Error (MAPE)</span>
                      <span>{predictionData ? `${predictionData.metrics.mape.toFixed(2)}%` : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>Directional Accuracy</span>
                      <span style={{ color: predictionData && predictionData.metrics.directional_accuracy >= 55 ? "var(--accent-success)" : "inherit" }}>
                        {predictionData ? `${predictionData.metrics.directional_accuracy.toFixed(1)}%` : "---"}
                      </span>
                    </div>
                    <div className="stats-row">
                      <span>Features Used</span>
                      <span>RSI, MACD, Open, Close, Volume, High, Low, Bollinger Bands, EMA 20/50</span>
                    </div>
                    <div className="stats-row">
                      <span>Time Step (Sequence)</span>
                      <span>60 Days</span>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: "20px", fontSize: "12px", color: "var(--text-muted)", borderTop: "1px solid rgba(255, 255, 255, 0.05)", paddingTop: "15px" }}>
                    * The model calculates RSI (14) and MACD (12, 26, 9) and feeds normalized sequences into a deep LSTM network. Dynamic re-training optimizes parameters to fit the asset's current volatility.
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.7)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "400px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "20px" }}>Update Password</h3>
            <form onSubmit={handleChangePassword} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
              <input
                type="password"
                placeholder="Current Password"
                className="input-field"
                value={oldPassword}
                onChange={e => setOldPassword(e.target.value)}
                required
              />
              <input
                type="password"
                placeholder="New Password"
                className="input-field"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
              />
              {passwordError && <div style={{ color: "var(--accent-danger)", fontSize: "13px" }}>{passwordError}</div>}
              {passwordSuccess && <div style={{ color: "var(--accent-success)", fontSize: "13px" }}>{passwordSuccess}</div>}
              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button type="submit" className="btn-primary">Update</button>
                <button type="button" onClick={() => { setShowPasswordModal(false); setPasswordError(""); setPasswordSuccess(""); }} className="btn-secondary">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
