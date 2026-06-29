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
  X,
  MessageSquare,
  CornerDownRight,
  Camera
} from "lucide-react";
import { Chart, registerables } from "chart.js";
import { TRANSLATIONS } from "./translations";

// Register all Chart.js components
Chart.register(...registerables);

const API_BASE_URL = typeof window !== "undefined" 
  ? (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
      ? "http://127.0.0.1:8000" 
      : window.location.origin) 
  : "http://127.0.0.1:8000";

const AUTO_TRAINED_SYMBOLS = [
  "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", 
  "SHIB-USD", "DOT-USD", "LINK-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "UNI-USD", "MATIC-USD", 
  "ICP-USD", "ETC-USD", "FIL-USD", "XLM-USD", "HBAR-USD", "ATOM-USD", "APT-USD", "VET-USD", 
  "RNDR-USD", "PEPE-USD", "OP-USD", "STX-USD", "GRT-USD", "LDO-USD", "INJ-USD", "THETA-USD", 
  "IMX-USD", "EGLD-USD", "FTM-USD", "ALGO-USD", "MKR-USD", "FLOW-USD", "MNT-USD", "AAVE-USD", 
  "SEI-USD", "AR-USD", "WIF-USD", "BONK-USD", "FLOKI-USD", "QNT-USD", "GALA-USD", "MANA-USD", 
  "AXS-USD", "SAND-USD", "JUP-USD", "PYTH-USD", "CHZ-USD", "DYDX-USD", "ENS-USD", "LRC-USD", 
  "ONE-USD", "CRO-USD", "TIA-USD", "MINA-USD",
  "GC=F", "SI=F",
  "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY", "AVGO",
  "JPM", "V", "UNH", "TSM", "WMT", "XOM", "MA", "PG", "JNJ", "HD",
  "ASML", "ORCL", "COST", "MRK", "CVX", "BAC", "ABBV", "AMD", "NFLX", "PEP",
  "KO", "TMO", "WFC", "DIS", "ADBE", "AZN", "CSCO", "QCOM", "NVO", "ACN",
  "SAP", "GE", "CAT", "AMGN", "TXN", "INTC", "IBM", "AXP", "MS", "PFE",
  "GS", "HON", "NKE", "SBUX", "UBER", "INTU", "ISRG", "LRCX", "SYK", "BA"
];

export default function Home() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [lang, setLang] = useState("en");

  // Read initial language on client mount
  useEffect(() => {
    const savedLang = localStorage.getItem("lang");
    if (savedLang) {
      setLang(savedLang);
    }
  }, []);

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem("lang", newLang);
  };

  const t = (key) => {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS["en"][key] || key;
  };

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

  const [chartInterval, setChartInterval] = useState("1d");
  const [chartHistory, setChartHistory] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  // Comments state variables
  const [comments, setComments] = useState([]);
  const [newCommentContent, setNewCommentContent] = useState("");
  const [replyingToId, setReplyingToId] = useState(null);
  const [replyContent, setReplyContent] = useState("");

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
  const [accuracyLogs, setAccuracyLogs] = useState([]);
  const [accuracyLoading, setAccuracyLoading] = useState(false);

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
      fetchCurrentUser(savedToken);
    }
  }, []);

  // Fetch comments when activeSymbol changes
  useEffect(() => {
    if (activeSymbol) {
      fetchComments(activeSymbol);
    }
  }, [activeSymbol]);

  // 2. Fetch Prediction data when activeSymbol, chartInterval, or lang changes
  useEffect(() => {
    if (token && activeSymbol) {
      loadPrediction(activeSymbol, chartInterval);
    }
  }, [activeSymbol, chartInterval, token, lang]);

  // 3. Render charts when predictionData or chartHistory updates
  useEffect(() => {
    if (!predictionData || !chartHistory || chartHistory.length === 0) return;
    renderCharts();
    
    // Cleanup on unmount or update
    return () => {
      destroyCharts();
    };
  }, [predictionData, chartHistory]);

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
    if (!predictionData || !chartHistory || chartHistory.length === 0) return;

    const ctxPrice = priceChartRef.current?.getContext("2d");
    const ctxRsi = rsiChartRef.current?.getContext("2d");
    const ctxMacd = macdChartRef.current?.getContext("2d");

    const history = chartHistory;
    const labels = history.map(item => item.date);
    const closePrices = history.map(item => item.close);
    const ema20Prices = history.map(item => item.ema_20);
    const ema50Prices = history.map(item => item.ema_50);
    const bbUpperPrices = history.map(item => item.bb_upper);
    const bbLowerPrices = history.map(item => item.bb_lower);
    
    // Include prediction point only for daily (1d) interval
    let extendedLabels = [...labels];
    let datasets = [
      {
        label: "Historical Close",
        data: closePrices,
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139, 92, 246, 0.05)",
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.15,
        fill: true,
      }
    ];

    if (predictionData) {
      extendedLabels = [...labels, predictionData.prediction_date];
      const predictedPrices = Array(labels.length).fill(null);
      predictedPrices[labels.length - 1] = closePrices[closePrices.length - 1];
      predictedPrices.push(predictionData.predicted_close);
      
      datasets.push({
        label: "LSTM Prediction",
        data: predictedPrices,
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.05)",
        borderWidth: 2.5,
        borderDash: [5, 5],
        pointRadius: 6,
        pointBackgroundColor: "#10b981",
        pointBorderColor: "#fff",
        tension: 0.15,
      });
    }

    datasets.push(
      {
        label: "EMA 20",
        data: ema20Prices,
        borderColor: "rgba(59, 130, 246, 0.65)",
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.15,
      },
      {
        label: "EMA 50",
        data: ema50Prices,
        borderColor: "rgba(236, 72, 153, 0.65)",
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.15,
      },
      {
        label: "BB Upper",
        data: bbUpperPrices,
        borderColor: "rgba(245, 158, 11, 0.35)",
        borderWidth: 1,
        borderDash: [3, 3],
        pointRadius: 0,
        fill: false,
      },
      {
        label: "BB Lower",
        data: bbLowerPrices,
        borderColor: "rgba(245, 158, 11, 0.35)",
        borderWidth: 1,
        borderDash: [3, 3],
        pointRadius: 0,
        fill: false,
      }
    );

    // Price Chart
    if (ctxPrice) {
      priceChartInst.current = new Chart(ctxPrice, {
        type: "line",
        data: {
          labels: extendedLabels,
          datasets: datasets
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
      
      macdChartInst.current = new Chart(ctxMacd, {
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

  // API Call: Fetch Prediction Accuracy Logs
  const fetchAccuracyLogs = async (symbol, interval = chartInterval) => {
    if (!token) return;
    setAccuracyLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/predictions/accuracy/${symbol}?interval=${interval}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAccuracyLogs(data);
      }
    } catch (err) {
      console.error("Error fetching accuracy logs:", err);
    } finally {
      setAccuracyLoading(false);
    }
  };

  // API Call: Load LSTM Prediction (timeframe-aware)
  const loadPrediction = async (symbol, interval = chartInterval) => {
    setPredictLoading(true);
    setPredictError("");
    setPredictionData(null); // Clear old prediction data to trigger loading UI immediately
    try {
      const res = await fetch(`${API_BASE_URL}/api/predict?symbol=${symbol}&interval=${interval}&lang=${lang}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      const data = await res.json();
      if (res.ok) {
        setPredictionData(data);
        setChartHistory(data.history);
        fetchAccuracyLogs(symbol, interval);
      } else {
        setPredictError(data.detail || "Failed to load prediction model.");
      }
    } catch (err) {
      setPredictError("Connection failed to Python FastAPI server.");
    } finally {
      setPredictLoading(false);
    }
  };

  // API Call: Fetch User Profile
  const fetchCurrentUser = async (authToken) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    } catch (err) {
      console.error("Error fetching user details:", err);
    }
  };

  // API Call: Profile Picture Upload
  const handleProfilePictureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 1024 * 1024) {
      alert("Image is too large. Please select an image under 1MB.");
      return;
    }

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async () => {
      const base64String = reader.result;
      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/profile-picture`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({ profile_picture: base64String })
        });
        const data = await res.json();
        if (res.ok) {
          setUser(data);
        } else {
          alert(data.detail || "Could not upload profile picture.");
        }
      } catch (err) {
        console.error("Profile picture upload failed:", err);
      }
    };
  };

  // API Call: Fetch Comments
  const fetchComments = async (symbol) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/comments/${symbol}`);
      if (res.ok) {
        const data = await res.json();
        setComments(data);
      }
    } catch (err) {
      console.error("Error fetching comments:", err);
    }
  };

  // API Call: Post Comment/Reply
  const handlePostComment = async (e, parentId = null) => {
    if (e) e.preventDefault();
    const content = parentId ? replyContent : newCommentContent;
    if (!content.trim()) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/comments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          symbol: activeSymbol,
          content: content,
          parent_id: parentId
        })
      });
      const data = await res.json();
      if (res.ok) {
        await fetchComments(activeSymbol);
        if (parentId) {
          setReplyContent("");
          setReplyingToId(null);
        } else {
          setNewCommentContent("");
        }
      } else {
        alert(data.detail || "Could not post comment.");
      }
    } catch (err) {
      console.error("Error posting comment:", err);
    }
  };

  // API Call: Delete Comment
  const handleDeleteComment = async (commentId) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/comments/${commentId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        await fetchComments(activeSymbol);
      } else {
        const data = await res.json();
        alert(data.detail || "Could not delete comment.");
      }
    } catch (err) {
      console.error("Error deleting comment:", err);
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
        fetchCurrentUser(data.access_token);
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
    if (rsi >= 70) return <span className="badge badge-danger">RSI: {rsi.toFixed(1)} ({t("rsi_status_overbought")})</span>;
    if (rsi <= 30) return <span className="badge badge-success">RSI: {rsi.toFixed(1)} ({t("rsi_status_oversold")})</span>;
    return <span className="badge badge-warning">RSI: {rsi.toFixed(1)} ({t("rsi_status_neutral")})</span>;
  };

  const getMacdBadge = (macd, hist) => {
    if (macd === null || macd === undefined) return <span className="badge badge-warning">N/A</span>;
    if (hist > 0) return <span className="badge badge-success">MACD: {t("bullish")}</span>;
    return <span className="badge badge-danger">MACD: {t("bearish")}</span>;
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
                placeholder={t("username")}
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
                  placeholder={t("email")}
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
                placeholder={t("password")}
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
              {authMode === "login" ? t("sign_in") : t("create_account")}
            </button>
          </form>

          <div className="auth-toggle">
            {authMode === "login" ? (
              <>
                {t("auth_no_account")} <span onClick={() => { setAuthMode("register"); setAuthError(""); }}>{t("create_account")}</span>
              </>
            ) : (
              <>
                {t("auth_have_account")} <span onClick={() => { setAuthMode("login"); setAuthError(""); }}>{t("sign_in")}</span>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Helper to render nested comments
  const renderCommentNode = (comment, depth = 0) => {
    const replies = comments.filter(c => c.parent_id === comment.id);
    const isOwner = user && user.id === comment.user.id;
    
    return (
      <div key={comment.id} style={{ marginLeft: depth > 0 ? `${Math.min(depth * 15, 45)}px` : "0px", borderLeft: depth > 0 ? "2px solid rgba(139, 92, 246, 0.15)" : "none", paddingLeft: depth > 0 ? "10px" : "0px", marginTop: "10px" }}>
        <div className="glass-panel" style={{ padding: "10px 12px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "var(--border-radius-md)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              {comment.user.profile_picture ? (
                <img 
                  src={comment.user.profile_picture} 
                  alt={comment.user.username}
                  style={{ width: "20px", height: "20px", borderRadius: "50%", objectFit: "cover" }}
                />
              ) : (
                <div style={{ background: "rgba(139, 92, 246, 0.2)", borderRadius: "50%", width: "20px", height: "20px", display: "flex", alignItems: "center", justifyItems: "center" }}>
                  <User style={{ width: "10px", color: "var(--accent-primary)", margin: "auto" }} />
                </div>
              )}
              <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-main)" }}>{comment.user.username}</span>
              <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                {new Date(comment.created_at + "Z").toLocaleString()}
              </span>
            </div>
            {isOwner && (
              <button 
                onClick={() => handleDeleteComment(comment.id)}
                style={{ background: "none", border: "none", color: "var(--accent-danger)", cursor: "pointer", opacity: 0.8, padding: "2px" }}
              >
                <Trash style={{ width: "11px" }} />
              </button>
            )}
          </div>
          
          <p style={{ fontSize: "12px", color: "var(--text-main)", margin: "4px 0", whiteSpace: "pre-wrap" }}>{comment.content}</p>
          
          <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
            <button 
              onClick={() => {
                if (replyingToId === comment.id) {
                  setReplyingToId(null);
                } else {
                  setReplyingToId(comment.id);
                  setReplyContent("");
                }
              }}
              style={{ background: "none", border: "none", color: "var(--accent-primary)", fontSize: "11px", fontWeight: "600", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", gap: "4px" }}
            >
              <CornerDownRight style={{ width: "10px" }} /> {t("reply_btn")}
            </button>
          </div>
          
          {/* Reply Input Box */}
          {replyingToId === comment.id && (
            <form onSubmit={(e) => handlePostComment(e, comment.id)} style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px", borderTop: "1px solid rgba(255, 255, 255, 0.05)", paddingTop: "8px" }}>
              <input
                type="text"
                placeholder={lang === "tr" ? `${comment.user.username} kullanıcısına yanıt ver...` : (lang === "de" ? `Antworten an ${comment.user.username}...` : (lang === "ru" ? `Ответить ${comment.user.username}...` : (lang === "zh" ? `回复 ${comment.user.username}...` : (lang === "es" ? `Responder a ${comment.user.username}...` : `Reply to ${comment.user.username}...`))))}
                className="input-field"
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                style={{ fontSize: "11px", height: "30px", padding: "0 8px" }}
                autoFocus
              />
              <div style={{ display: "flex", gap: "6px", alignSelf: "flex-end" }}>
                <button 
                  type="button" 
                  onClick={() => setReplyingToId(null)}
                  className="btn-secondary" 
                  style={{ height: "24px", padding: "0 8px", fontSize: "11px" }}
                >
                  {t("cancel_btn")}
                </button>
                <button 
                  type="submit" 
                  className="btn-primary" 
                  style={{ height: "24px", padding: "0 8px", fontSize: "11px" }}
                >
                  {t("post_btn")}
                </button>
              </div>
            </form>
          )}
        </div>
        
        {/* Replies rendering recursive */}
        {replies.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {replies.map(reply => renderCommentNode(reply, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Render Dashboard if logged in
  const activeHistory = (predictionData && chartHistory && chartHistory.length > 0) ? chartHistory : (predictionData ? predictionData.history : []);
  
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
              placeholder={t("search_placeholder")}
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
          <h3 className="watchlist-title">{t("watchlist_title")}</h3>
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
            <div style={{ display: "flex", alignItems: "center", gap: "10px", position: "relative" }}>
              <div style={{ position: "relative", width: "40px", height: "40px", flexShrink: 0 }}>
                {user && user.profile_picture ? (
                  <img 
                    src={user.profile_picture} 
                    alt="Profile"
                    style={{ width: "40px", height: "40px", borderRadius: "50%", objectFit: "cover", border: "2px solid var(--accent-primary)" }}
                  />
                ) : (
                  <div style={{ background: "rgba(139, 92, 246, 0.2)", borderRadius: "50%", width: "40px", height: "40px", display: "flex", alignItems: "center", justifyItems: "center", border: "1px solid rgba(255,255,255,0.1)" }}>
                    <User style={{ width: "20px", color: "var(--accent-primary)", margin: "auto" }} />
                  </div>
                )}
                <label 
                  htmlFor="profile-upload" 
                  style={{ position: "absolute", bottom: "-2px", right: "-2px", background: "var(--accent-primary)", borderRadius: "50%", width: "18px", height: "18px", display: "flex", alignItems: "center", justifyItems: "center", cursor: "pointer", border: "1px solid #fff", boxShadow: "0 2px 4px rgba(0,0,0,0.2)" }}
                >
                  <Camera style={{ width: "10px", color: "#fff", margin: "auto" }} />
                </label>
                <input 
                  id="profile-upload" 
                  type="file" 
                  accept="image/*" 
                  onChange={handleProfilePictureUpload} 
                  style={{ display: "none" }} 
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500", textTransform: "uppercase" }}>{t("active_user")}</span>
                <span style={{ fontSize: "14px", fontWeight: "700", color: "var(--text-main)" }}>
                  {user ? user.username : t("session")}
                </span>
              </div>
            </div>

            <button onClick={() => setShowPasswordModal(true)} className="btn-secondary" style={{ width: "100%", justifyContent: "flex-start" }}>
              <Key style={{ width: "14px" }} /> {t("change_password")}
            </button>
            <button onClick={handleDeleteAccount} className="btn-danger" style={{ width: "100%", textAlign: "left", display: "flex", alignItems: "center", gap: "6px" }}>
              <UserMinus style={{ width: "14px" }} /> {t("close_account")}
            </button>
            <button onClick={handleLogout} className="btn-secondary" style={{ width: "100%", justifyContent: "flex-start", marginTop: "10px" }}>
              <LogOut style={{ width: "14px" }} /> {t("sign_out")}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Panel Content */}
      <main className="main-content">
        {predictLoading || (!predictionData && !predictError) || (predictionData && predictionData.symbol !== activeSymbol) ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", gap: "20px" }}>
            <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)", width: "48px", height: "48px" }} />
            <h3 style={{ fontSize: "18px", color: "var(--text-main)", fontWeight: "600" }}>{t("loading")}</h3>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", textAlign: "center", maxWidth: "400px" }}>
              {t("loading_desc")
                .replace("{interval}", chartInterval === "1d" ? (lang === "tr" ? "günlük" : (lang === "de" ? "tägliche" : (lang === "ru" ? "дневные" : (lang === "zh" ? "日线" : (lang === "es" ? "diarios" : "daily"))))) : chartInterval)
                .replace("{symbol}", activeSymbol)}
            </p>
          </div>
        ) : predictError ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", color: "var(--accent-danger)", gap: "10px" }}>
            <span style={{ fontSize: "18px", fontWeight: "600" }}>{t("error_title")}</span>
            <span style={{ textAlign: "center", maxWidth: "400px" }}>{predictError}</span>
            <button onClick={() => loadPrediction(activeSymbol, chartInterval)} className="btn-secondary" style={{ marginTop: "10px" }}>
              <RefreshCw style={{ width: "14px" }} /> {t("try_again")}
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
                      {getRsiBadge(activeHistory[activeHistory.length - 1]?.rsi)}
                      {getMacdBadge(
                        activeHistory[activeHistory.length - 1]?.macd,
                        activeHistory[activeHistory.length - 1]?.macd_hist
                      )}
                      <span className="badge badge-info">Open: ${activeHistory[activeHistory.length - 1]?.open?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Close: ${activeHistory[activeHistory.length - 1]?.close?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">High: ${activeHistory[activeHistory.length - 1]?.high?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Low: ${activeHistory[activeHistory.length - 1]?.low?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">Vol: {activeHistory[activeHistory.length - 1]?.volume?.toLocaleString("en-US")}</span>
                      <span className="badge badge-info">EMA 20: ${activeHistory[activeHistory.length - 1]?.ema_20?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">EMA 50: ${activeHistory[activeHistory.length - 1]?.ema_50?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">BB Upper: ${activeHistory[activeHistory.length - 1]?.bb_upper?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      <span className="badge badge-info">BB Lower: ${activeHistory[activeHistory.length - 1]?.bb_lower?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </>
                  )}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                {/* Language Dropdown Selector */}
                <select
                  value={lang}
                  onChange={(e) => changeLanguage(e.target.value)}
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    color: "var(--text-main)",
                    borderRadius: "6px",
                    padding: "6px 10px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    outline: "none",
                    backdropFilter: "blur(4px)"
                  }}
                >
                  <option value="en" style={{ background: "#110b29", color: "#fff" }}>English</option>
                  <option value="tr" style={{ background: "#110b29", color: "#fff" }}>Türkçe</option>
                  <option value="de" style={{ background: "#110b29", color: "#fff" }}>Deutsch</option>
                  <option value="ru" style={{ background: "#110b29", color: "#fff" }}>Русский</option>
                  <option value="zh" style={{ background: "#110b29", color: "#fff" }}>中文</option>
                  <option value="es" style={{ background: "#110b29", color: "#fff" }}>Español</option>
                </select>

                <div className="header-price-panel">
                  <div className="asset-price">
                    ${predictionData && predictionData.current_price !== undefined && predictionData.current_price !== null 
                      ? predictionData.current_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) 
                      : (predictionData ? predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "---")}
                  </div>
                  <span style={{ fontSize: "12px", color: "var(--accent-primary)", fontWeight: "600", display: "block" }}>
                    ● {t("live_price")}
                  </span>
                  {predictionData && (
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                      {t("last_close")}: ${predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({predictionData.last_date})
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Dashboard Grid (Charts and Predictions) */}
            <div className="dashboard-grid">
              {/* Column 1: Charts */}
              <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
                {/* Price Chart Card */}
                <div className="glass-panel">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                    <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                      <LineChart style={{ color: "var(--accent-primary)" }} /> {t("chart_title")}
                    </h3>
                    
                    {/* Interval Toggles */}
                    <div style={{ display: "flex", gap: "6px", background: "rgba(255, 255, 255, 0.03)", padding: "4px", borderRadius: "var(--border-radius-md)", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                      {["15m", "1h", "4h", "1d"].map((interval) => (
                        <button
                          key={interval}
                          onClick={() => setChartInterval(interval)}
                          className={chartInterval === interval ? "btn-primary" : "btn-secondary"}
                          style={{
                            padding: "6px 12px",
                            fontSize: "12px",
                            height: "auto",
                            borderRadius: "calc(var(--border-radius-md) - 2px)",
                            border: "none",
                            fontWeight: "600",
                            textTransform: "uppercase"
                          }}
                          disabled={predictLoading}
                        >
                          {interval}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="chart-wrapper" style={{ position: "relative" }}>
                    {chartLoading && (
                      <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(11, 15, 25, 0.6)", backdropFilter: "blur(2px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10, borderRadius: "8px" }}>
                        <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)", width: "28px", height: "28px" }} />
                      </div>
                    )}
                    <canvas ref={priceChartRef} />
                  </div>
                </div>

                {/* Technical Indicators Chart Card */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px" }}>{t("chart_indicators")}</h3>
                  <div className="indicator-grid">
                    <div>
                      <h4 style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>{t("rsi_title")}</h4>
                      <div className="indicator-wrapper">
                        <canvas ref={rsiChartRef} />
                      </div>
                    </div>
                    <div>
                      <h4 style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>{t("macd_title")}</h4>
                      <div className="indicator-wrapper">
                        <canvas ref={macdChartRef} />
                      </div>
                    </div>
                  </div>

                  {/* Summary of Technical Signals */}
                  <div style={{ marginTop: "25px", paddingTop: "20px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
                    <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                      {t("signals_title")}
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "15px" }}>
                      <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>RSI (14)</span>
                        <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                          {activeHistory[activeHistory.length - 1]?.rsi?.toFixed(2) || "---"}
                        </span>
                        {(() => {
                          const rsi = activeHistory[activeHistory.length - 1]?.rsi;
                          if (rsi === null || rsi === undefined) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (rsi >= 70) return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_overbought")}</span>;
                          if (rsi <= 30) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_oversold")}</span>;
                          return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_neutral")}</span>;
                        })()}
                      </div>
                      
                      <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>MACD</span>
                        <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                          {activeHistory[activeHistory.length - 1]?.macd?.toFixed(2) || "---"}
                        </span>
                        {(() => {
                          const hist = activeHistory[activeHistory.length - 1]?.macd_hist;
                          if (hist === null || hist === undefined) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (hist > 0) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("macd_status_bullish")}</span>;
                          return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("macd_status_bearish")}</span>;
                        })()}
                      </div>
 
                      <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>EMA (20 vs 50)</span>
                        <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                          {(() => {
                            const ema20 = activeHistory[activeHistory.length - 1]?.ema_20;
                            const ema50 = activeHistory[activeHistory.length - 1]?.ema_50;
                            if (ema20 && ema50) {
                              return `${ema20.toFixed(1)} / ${ema50.toFixed(1)}`;
                            }
                            return "---";
                          })()}
                        </span>
                        {(() => {
                          const ema20 = activeHistory[activeHistory.length - 1]?.ema_20;
                          const ema50 = activeHistory[activeHistory.length - 1]?.ema_50;
                          const close = activeHistory[activeHistory.length - 1]?.close;
                          if (ema20 === null || ema50 === null || close === null) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (close > ema20 && ema20 > ema50) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("ema_status_uptrend")}</span>;
                          if (close < ema20 && ema20 < ema50) return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("ema_status_downtrend")}</span>;
                          if (ema20 > ema50) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("ema_status_golden")}</span>;
                          return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("ema_status_death")}</span>;
                        })()}
                      </div>
 
                      <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Bollinger Bands</span>
                        <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                          {(() => {
                            const upper = activeHistory[activeHistory.length - 1]?.bb_upper;
                            const lower = activeHistory[activeHistory.length - 1]?.bb_lower;
                            if (upper && lower) {
                              return `${upper.toFixed(1)} / ${lower.toFixed(1)}`;
                            }
                            return "---";
                          })()}
                        </span>
                        {(() => {
                          const upper = activeHistory[activeHistory.length - 1]?.bb_upper;
                          const lower = activeHistory[activeHistory.length - 1]?.bb_lower;
                          const close = activeHistory[activeHistory.length - 1]?.close;
                          if (upper === null || lower === null || close === null) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (close >= upper) return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("bb_status_overbought")}</span>;
                          if (close <= lower) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("bb_status_oversold")}</span>;
                          return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{t("bb_status_inside")}</span>;
                        })()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Comments & Discussion Panel */}
                <div className="glass-panel" style={{ marginTop: "10px" }}>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <MessageSquare style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} /> {t("discussion_title")} ({activeSymbol})
                  </h3>
                  
                  {/* Post New Comment Form */}
                  <form onSubmit={(e) => handlePostComment(e)} style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
                    <textarea
                      placeholder={t("discussion_placeholder")}
                      className="input-field"
                      rows="3"
                      value={newCommentContent}
                      onChange={(e) => setNewCommentContent(e.target.value)}
                      style={{ resize: "none", fontSize: "13px", padding: "10px" }}
                      required
                    />
                    <button type="submit" className="btn-primary" style={{ alignSelf: "flex-end", height: "36px", padding: "0 16px", fontSize: "13px" }}>
                      {t("comment_btn")}
                    </button>
                  </form>
                  
                  {/* Comments Tree */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px", maxHeight: "450px", overflowY: "auto", paddingRight: "5px" }}>
                    {comments.filter(c => c.parent_id === null).length === 0 ? (
                      <div style={{ color: "var(--text-muted)", fontSize: "13px", textAlign: "center", padding: "20px 0", fontStyle: "italic" }}>
                        {t("no_comments")}
                      </div>
                    ) : (
                      comments.filter(c => c.parent_id === null).map(comment => renderCommentNode(comment))
                    )}
                  </div>
                </div>
              </div>

              {/* Column 2: LSTM Prediction Summary */}
              <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
                {/* Prediction Highlight Card */}
                <div className="glass-panel prediction-card" style={{ minHeight: "220px", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                  <span className="prediction-label">{t("prediction_header")}</span>
                  <div className="prediction-value">
                    ${predictionData ? predictionData.predicted_close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "---"}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "-5px" }}>
                    {t("expected_close")}: {predictionData ? predictionData.expected_close_time : "---"}
                  </div>
                  
                  {predictionData && (
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "16px", fontWeight: "700", marginTop: "15px" }}>
                      {predictionData.price_change_percent >= 0 ? (
                        <>
                          <TrendingUp style={{ color: "var(--accent-success)" }} />
                          <span style={{ color: "var(--accent-success)" }}>
                            +{predictionData.price_change_percent.toFixed(2)}% ({t("bullish")})
                          </span>
                        </>
                      ) : (
                        <>
                          <TrendingDown style={{ color: "var(--accent-danger)" }} />
                          <span style={{ color: "var(--accent-danger)" }}>
                            {predictionData.price_change_percent.toFixed(2)}% ({t("bearish")})
                          </span>
                        </>
                      )}
                    </div>
                  )}
                  
                  {predictionData && predictionData.technical_recommendation && (
                    <div style={{ marginTop: "18px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "14px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500", textTransform: "uppercase" }}>{t("trading_action")}:</span>
                        {predictionData.technical_recommendation.signal === "STRONG_BUY" ? (
                          <span className="badge badge-success" style={{ fontWeight: "700" }}>{t("buy_long")}</span>
                        ) : predictionData.technical_recommendation.signal === "STRONG_SELL" ? (
                          <span className="badge badge-danger" style={{ fontWeight: "700" }}>{t("sell_short")}</span>
                        ) : (
                          <span className="badge badge-warning" style={{ fontWeight: "700" }}>{t("cash_hold")}</span>
                        )}
                      </div>
                      <p style={{ fontSize: "11.5px", color: "var(--text-muted)", lineHeight: "1.4", margin: 0 }}>
                        {predictionData.technical_recommendation.text}
                      </p>
                    </div>
                  )}
                </div>

                {/* Fundamental Analysis Card */}
                {predictionData && predictionData.fundamental_analysis && (
                  <div className="glass-panel">
                    <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <PieChart style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} /> {t("fundamental_title")}
                    </h3>
                    
                    <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
                      {/* Overall Sentiment Badge */}
                      <div style={{ display: "flex", alignItems: "center", justifyItems: "center", justifyContent: "space-between", background: "rgba(255, 255, 255, 0.03)", padding: "10px 14px", borderRadius: "var(--border-radius-md)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                        <span style={{ fontSize: "13px", color: "var(--text-muted)", fontWeight: "500" }}>{t("outlook")}:</span>
                        {predictionData.fundamental_analysis.sentiment_class === "Bullish" ? (
                          <span className="badge badge-success">{t("bullish")}</span>
                        ) : predictionData.fundamental_analysis.sentiment_class === "Bearish" ? (
                          <span className="badge badge-danger">{t("bearish")}</span>
                        ) : (
                          <span className="badge badge-warning">{t("neutral")}</span>
                        )}
                      </div>
                      
                      {/* Recommendation Text */}
                      <p style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: "1.6", background: "rgba(139, 92, 246, 0.05)", padding: "14px", borderRadius: "var(--border-radius-md)", borderLeft: "4px solid var(--accent-primary)", margin: 0 }}>
                        {predictionData.fundamental_analysis.recommendation}
                      </p>
                      
                      {/* News list */}
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "5px" }}>
                        <span style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "var(--text-muted)", letterSpacing: "0.5px" }}>{t("news_title")}</span>
                        {predictionData.fundamental_analysis.articles.length === 0 ? (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center" }}>{t("no_news")}</div>
                        ) : (
                          predictionData.fundamental_analysis.articles.map((art, idx) => (
                            <a 
                              key={idx}
                              href={art.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="watchlist-item"
                              style={{ textDecoration: "none", color: "inherit", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "6px", padding: "10px 14px", margin: 0 }}
                            >
                              <div style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff", lineHeight: "1.4", textAlign: "left" }}>{art.title}</span>
                              </div>
                              <div style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{art.publisher}</span>
                                {art.sentiment === "Bullish" ? (
                                  <span className="badge badge-success" style={{ fontSize: "9px", padding: "1px 6px" }}>{t("bullish")}</span>
                                ) : art.sentiment === "Bearish" ? (
                                  <span className="badge badge-danger" style={{ fontSize: "9px", padding: "1px 6px" }}>{t("bearish")}</span>
                                ) : (
                                  <span className="badge badge-warning" style={{ fontSize: "9px", padding: "1px 6px" }}>{t("neutral")}</span>
                                )}
                              </div>
                            </a>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Model Information & Metrics */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px" }}>{t("analytics_title")}</h3>
                  
                  <div className="stats-list">
                    <div className="stats-row">
                      <span>{t("cache_status")}</span>
                      <span>{predictionData ? predictionData.metrics.training_status : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>{t("rmse")}</span>
                      <span>{predictionData ? `$${predictionData.metrics.rmse.toFixed(2)}` : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>{t("mape")}</span>
                      <span>{predictionData ? `${predictionData.metrics.mape.toFixed(2)}%` : "---"}</span>
                    </div>
                    <div className="stats-row">
                      <span>{t("directional_accuracy")}</span>
                      <span style={{ color: predictionData && predictionData.metrics.directional_accuracy >= 55 ? "var(--accent-success)" : "inherit" }}>
                        {predictionData ? `${predictionData.metrics.directional_accuracy.toFixed(1)}%` : "---"}
                      </span>
                    </div>
                    <div className="stats-row">
                      <span>{t("features_used")}</span>
                      <span>RSI, MACD, Bollinger Bands (Upper/Lower/Width), EMA 20/50, Open, Close, Vol, High, Low, ATR, Lags (1,3,7), Vol Change (19 total)</span>
                    </div>
                    <div className="stats-row">
                      <span>{t("time_step")}</span>
                      <span>60 {t("days")}</span>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: "20px", fontSize: "12px", color: "var(--text-muted)", borderTop: "1px solid rgba(255, 255, 255, 0.05)", paddingTop: "15px" }}>
                    * The model calculates 19 normalized indicators (including RSI, MACD Signal/Hist, Bollinger Band Width, ATR, and short/weekly return lags) to feed into a deep LSTM network.
                  </div>
                </div>

                {/* Prediction Accuracy Logs */}
                {AUTO_TRAINED_SYMBOLS.includes(activeSymbol) && (
                  <div className="glass-panel" style={{ marginTop: "20px" }}>
                    <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <LineChart style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} /> {t("accuracy_title")}
                    </h3>
                    
                    {accuracyLoading ? (
                      <div style={{ display: "flex", justifyContent: "center", padding: "20px" }}>
                        <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)" }} />
                      </div>
                    ) : accuracyLogs.length === 0 ? (
                      <div style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", padding: "15px" }}>
                        {t("table_no_logs")}
                      </div>
                    ) : (
                      <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                          <thead>
                            <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", color: "var(--text-muted)", textAlign: "left" }}>
                              <th style={{ padding: "8px 4px" }}>{t("table_target_date")}</th>
                              <th style={{ padding: "8px 4px", textAlign: "right" }}>{t("table_predicted")}</th>
                              <th style={{ padding: "8px 4px", textAlign: "right" }}>{t("table_actual")}</th>
                              <th style={{ padding: "8px 4px", textAlign: "right" }}>{t("table_error")}</th>
                              <th style={{ padding: "8px 4px", textAlign: "center" }}>{t("table_direction")}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {accuracyLogs.map(log => {
                              const actualVal = log.actual_close;
                              const predVal = log.predicted_close;
                              const lastVal = log.last_close;
                              
                              let errorPct = "---";
                              let dirCorr = "---";
                              let dirBadgeClass = "badge-secondary";
                              
                              if (actualVal !== null && actualVal !== undefined) {
                                const err = Math.abs(predVal - actualVal) / actualVal;
                                errorPct = `${(err * 100).toFixed(2)}%`;
                                
                                const predUp = predVal > lastVal;
                                const actualUp = actualVal > lastVal;
                                const matched = predUp === actualUp;
                                
                                dirCorr = matched ? "✓" : "✗";
                                dirBadgeClass = matched ? "badge-success" : "badge-danger";
                              }
                              
                              return (
                                <tr key={log.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                                  <td style={{ padding: "8px 4px", whiteSpace: "nowrap" }}>
                                    {log.prediction_date}
                                  </td>
                                  <td style={{ padding: "8px 4px", textAlign: "right", fontWeight: "600" }}>
                                    ${predVal.toFixed(2)}
                                  </td>
                                  <td style={{ padding: "8px 4px", textAlign: "right" }}>
                                    {actualVal !== null ? `$${actualVal.toFixed(2)}` : (
                                      <span style={{ fontSize: "11px", color: "var(--text-muted)", fontStyle: "italic" }}>
                                        {t("table_pending")}
                                      </span>
                                    )}
                                  </td>
                                  <td style={{ padding: "8px 4px", textAlign: "right" }}>
                                    {errorPct}
                                  </td>
                                  <td style={{ padding: "8px 4px", textAlign: "center" }}>
                                    {actualVal !== null ? (
                                      <span className={`badge ${dirBadgeClass}`} style={{ fontSize: "10px", padding: "1px 6px" }}>
                                        {dirCorr}
                                      </span>
                                    ) : "---"}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.7)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "400px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "20px" }}>{t("update_password_title")}</h3>
            <form onSubmit={handleChangePassword} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
              <input
                type="password"
                placeholder={t("old_password")}
                className="input-field"
                value={oldPassword}
                onChange={e => setOldPassword(e.target.value)}
                required
              />
              <input
                type="password"
                placeholder={t("new_password")}
                className="input-field"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
              />
              {passwordError && <div style={{ color: "var(--accent-danger)", fontSize: "13px" }}>{passwordError}</div>}
              {passwordSuccess && <div style={{ color: "var(--accent-success)", fontSize: "13px" }}>{passwordSuccess}</div>}
              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button type="submit" className="btn-primary">{t("confirm")}</button>
                <button type="button" onClick={() => { setShowPasswordModal(false); setPasswordError(""); setPasswordSuccess(""); }} className="btn-secondary">{t("cancel_btn")}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
