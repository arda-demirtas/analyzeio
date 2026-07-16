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
  Camera,
  Maximize2,
  Minimize2,
  LogIn,
  UserPlus
} from "lucide-react";
import { Chart, registerables } from "chart.js";
import { TRANSLATIONS } from "./translations";

// Custom plugin to draw Candlestick Wicks (High/Low shadows)
const candlestickPlugin = {
  id: "candlestickWicks",
  afterDatasetsDraw(chart, args, options) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    if (!meta || meta.type !== "bar" || !options || !options.enabled || !options.history) return;
    
    ctx.save();
    ctx.lineWidth = 1.5;
    
    meta.data.forEach((bar, index) => {
      const hPoint = options.history[index];
      if (!hPoint) return;
      
      const x = bar.x;
      const yScale = chart.scales.y;
      
      const highY = yScale.getPixelForValue(hPoint.high);
      const lowY = yScale.getPixelForValue(hPoint.low);
      
      const isGreen = hPoint.close >= hPoint.open;
      ctx.strokeStyle = isGreen ? "#10b981" : "#ef4848";
      
      // Draw wick from High to Low
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();
    });
    
    ctx.restore();
  }
};

// Register all Chart.js components
Chart.register(...registerables, candlestickPlugin);

const API_BASE_URL = typeof window !== "undefined" 
  ? (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
      ? "http://127.0.0.1:8001" 
      : window.location.origin) 
  : (process.env.NODE_ENV === "production" ? "http://127.0.0.1:8000" : "http://127.0.0.1:8001");

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
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // Read initial language, history limit and register chart zoom on client mount
  useEffect(() => {
    const savedLang = localStorage.getItem("lang");
    if (savedLang) {
      setLang(savedLang);
    }
    const savedLimit = localStorage.getItem("historyLimit");
    if (savedLimit) {
      const parsed = parseInt(savedLimit, 10);
      if (!isNaN(parsed) && parsed >= 180 && parsed <= 720) {
        setHistoryLimit(parsed);
      }
    }
    
    // Dynamically register zoom plugin on the client side
    const initZoomPlugin = async () => {
      try {
        const zoomPlugin = (await import("chartjs-plugin-zoom")).default;
        Chart.register(zoomPlugin);
      } catch (err) {
        console.error("Zoom plugin registration failed:", err);
      }
    };
    initZoomPlugin();
  }, []);

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem("lang", newLang);
  };

  const LOCAL_TRANSLATIONS = {
    en: {
      ai_screener: "AI Market Screener",
      news_sentiment: "News Sentiment Analysis",
      news_gauge: "Overall Sentiment",
      screener_title: "AI Market Screener",
      screener_all: "All Assets",
      screener_bullish: "AI: Bullish",
      screener_bearish: "AI: Bearish",
      screener_oversold: "Oversold (RSI < 35)",
      screener_overbought: "Overbought (RSI > 65)",
      screener_asset: "Asset",
      screener_price: "Price",
      screener_pred_change: "AI Pred Change",
      screener_rsi: "RSI (14)",
      screener_macd: "MACD Signal",
      news_title_sec: "Latest News & AI Sentiment",
      news_sentiment_score: "Sentiment Score",
      rating_bullish: "Bullish",
      rating_bearish: "Bearish",
      rating_neutral: "Neutral"
    },
    tr: {
      ai_screener: "AI Market Tarayıcı",
      news_sentiment: "Haber Duyarlılık Analizi",
      news_gauge: "Genel Duyarlılık",
      screener_title: "AI Market Tarayıcı",
      screener_all: "Tüm Varlıklar",
      screener_bullish: "AI: Boğa",
      screener_bearish: "AI: Ayı",
      screener_oversold: "Aşırı Satım (RSI < 35)",
      screener_overbought: "Aşırı Alım (RSI > 65)",
      screener_asset: "Varlık",
      screener_price: "Fiyat",
      screener_pred_change: "AI Tahmin Değişim",
      screener_rsi: "RSI (14)",
      screener_macd: "MACD Sinyali",
      news_title_sec: "Son Haberler & Yapay Zeka Analizi",
      news_sentiment_score: "Duyarlılık Skoru",
      rating_bullish: "Boğa",
      rating_bearish: "Ayı",
      rating_neutral: "Yatay"
    }
  };

  const t = (key) => {
    if (LOCAL_TRANSLATIONS[lang]?.[key]) {
      return LOCAL_TRANSLATIONS[lang][key];
    }
    if (LOCAL_TRANSLATIONS["en"]?.[key]) {
      return LOCAL_TRANSLATIONS["en"][key];
    }
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS["en"][key] || key;
  };

  const [authMode, setAuthMode] = useState("login"); // login, register
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [isVerifyingRegister, setIsVerifyingRegister] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [registeredEmail, setRegisteredEmail] = useState("");
  
  const [isVerifyingPasswordChange, setIsVerifyingPasswordChange] = useState(false);
  const [passwordVerificationCode, setPasswordVerificationCode] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // App State
  const [activeSymbol, setActiveSymbol] = useState("BTC-USD");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(-1);
  const [searchNoResults, setSearchNoResults] = useState(false);
  const [watchlist, setWatchlist] = useState([
    { id: "anon-btc", symbol: "BTC-USD" },
    { id: "anon-eth", symbol: "ETH-USD" },
    { id: "anon-sol", symbol: "SOL-USD" },
    { id: "anon-aapl", symbol: "AAPL" },
    { id: "anon-tsla", symbol: "TSLA" }
  ]);
  const [predictionData, setPredictionData] = useState(null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [predictError, setPredictError] = useState("");
  const [loadingStep, setLoadingStep] = useState(1);

  const [chartInterval, setChartInterval] = useState("1d");
  const [chartHistory, setChartHistory] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartType, setChartType] = useState("line");
  const [isChartFullscreen, setIsChartFullscreen] = useState(false);
  const [historyLimit, setHistoryLimit] = useState(300);

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

  // --- Symbol Autocomplete Catalog ---
  const SYMBOL_CATALOG = [
    // Crypto
    { symbol: "BTC-USD",  name: "Bitcoin",       category: "Crypto" },
    { symbol: "ETH-USD",  name: "Ethereum",      category: "Crypto" },
    { symbol: "SOL-USD",  name: "Solana",        category: "Crypto" },
    { symbol: "BNB-USD",  name: "BNB",           category: "Crypto" },
    { symbol: "XRP-USD",  name: "XRP",           category: "Crypto" },
    { symbol: "ADA-USD",  name: "Cardano",       category: "Crypto" },
    { symbol: "AVAX-USD", name: "Avalanche",     category: "Crypto" },
    { symbol: "DOGE-USD", name: "Dogecoin",      category: "Crypto" },
    { symbol: "SHIB-USD", name: "Shiba Inu",     category: "Crypto" },
    { symbol: "DOT-USD",  name: "Polkadot",      category: "Crypto" },
    { symbol: "LINK-USD", name: "Chainlink",     category: "Crypto" },
    { symbol: "LTC-USD",  name: "Litecoin",      category: "Crypto" },
    { symbol: "BCH-USD",  name: "Bitcoin Cash",  category: "Crypto" },
    { symbol: "NEAR-USD", name: "NEAR Protocol", category: "Crypto" },
    { symbol: "UNI7083-USD", name: "Uniswap",   category: "Crypto" },
    { symbol: "MATIC-USD",name: "Polygon",       category: "Crypto" },
    { symbol: "ICP-USD",  name: "Internet Computer", category: "Crypto" },
    { symbol: "ETC-USD",  name: "Ethereum Classic", category: "Crypto" },
    { symbol: "FIL-USD",  name: "Filecoin",      category: "Crypto" },
    { symbol: "XLM-USD",  name: "Stellar",       category: "Crypto" },
    { symbol: "HBAR-USD", name: "Hedera",        category: "Crypto" },
    { symbol: "ATOM-USD", name: "Cosmos",        category: "Crypto" },
    { symbol: "APT-USD",  name: "Aptos",         category: "Crypto" },
    { symbol: "VET-USD",  name: "VeChain",       category: "Crypto" },
    { symbol: "RNDR-USD", name: "Render",        category: "Crypto" },
    { symbol: "PEPE-USD", name: "Pepe",          category: "Crypto" },
    { symbol: "OP-USD",   name: "Optimism",      category: "Crypto" },
    { symbol: "STX-USD",  name: "Stacks",        category: "Crypto" },
    { symbol: "GRT-USD",  name: "The Graph",     category: "Crypto" },
    { symbol: "LDO-USD",  name: "Lido DAO",      category: "Crypto" },
    { symbol: "INJ-USD",  name: "Injective",     category: "Crypto" },
    { symbol: "THETA-USD",name: "Theta Network", category: "Crypto" },
    { symbol: "IMX-USD",  name: "Immutable",     category: "Crypto" },
    { symbol: "EGLD-USD", name: "MultiversX",    category: "Crypto" },
    { symbol: "FTM-USD",  name: "Fantom",        category: "Crypto" },
    { symbol: "ALGO-USD", name: "Algorand",      category: "Crypto" },
    { symbol: "MKR-USD",  name: "Maker",         category: "Crypto" },
    { symbol: "FLOW-USD", name: "Flow",          category: "Crypto" },
    { symbol: "MNT-USD",  name: "Mantle",        category: "Crypto" },
    { symbol: "AAVE-USD", name: "Aave",          category: "Crypto" },
    { symbol: "SEI-USD",  name: "Sei",           category: "Crypto" },
    { symbol: "AR-USD",   name: "Arweave",       category: "Crypto" },
    { symbol: "WIF-USD",  name: "dogwifhat",     category: "Crypto" },
    { symbol: "BONK-USD", name: "Bonk",          category: "Crypto" },
    { symbol: "FLOKI-USD",name: "Floki",         category: "Crypto" },
    { symbol: "QNT-USD",  name: "Quant",         category: "Crypto" },
    { symbol: "GALA-USD", name: "Gala",          category: "Crypto" },
    { symbol: "MANA-USD", name: "Decentraland",  category: "Crypto" },
    { symbol: "AXS-USD",  name: "Axie Infinity", category: "Crypto" },
    { symbol: "SAND-USD", name: "The Sandbox",   category: "Crypto" },
    { symbol: "JUP-USD",  name: "Jupiter",       category: "Crypto" },
    { symbol: "PYTH-USD", name: "Pyth Network",  category: "Crypto" },
    { symbol: "CHZ-USD",  name: "Chiliz",        category: "Crypto" },
    { symbol: "DYDX-USD", name: "dYdX",          category: "Crypto" },
    { symbol: "ENS-USD",  name: "Ethereum Name Service", category: "Crypto" },
    { symbol: "LRC-USD",  name: "Loopring",      category: "Crypto" },
    { symbol: "ONE-USD",  name: "Harmony",       category: "Crypto" },
    { symbol: "CRO-USD",  name: "Cronos",        category: "Crypto" },
    { symbol: "TIA-USD",  name: "Celestia",      category: "Crypto" },
    { symbol: "MINA-USD", name: "Mina Protocol", category: "Crypto" },
    // Commodities
    { symbol: "GC=F",     name: "Gold Futures",  category: "Commodity" },
    { symbol: "SI=F",     name: "Silver Futures",category: "Commodity" },
    // US Stocks
    { symbol: "AAPL",  name: "Apple",            category: "Stock" },
    { symbol: "MSFT",  name: "Microsoft",        category: "Stock" },
    { symbol: "GOOGL", name: "Alphabet / Google",category: "Stock" },
    { symbol: "AMZN",  name: "Amazon",           category: "Stock" },
    { symbol: "NVDA",  name: "NVIDIA",           category: "Stock" },
    { symbol: "META",  name: "Meta Platforms",   category: "Stock" },
    { symbol: "TSLA",  name: "Tesla",            category: "Stock" },
    { symbol: "BRK-B", name: "Berkshire Hathaway", category: "Stock" },
    { symbol: "LLY",   name: "Eli Lilly",        category: "Stock" },
    { symbol: "AVGO",  name: "Broadcom",         category: "Stock" },
    { symbol: "JPM",   name: "JPMorgan Chase",   category: "Stock" },
    { symbol: "V",     name: "Visa",             category: "Stock" },
    { symbol: "UNH",   name: "UnitedHealth",     category: "Stock" },
    { symbol: "TSM",   name: "Taiwan Semiconductor", category: "Stock" },
    { symbol: "WMT",   name: "Walmart",          category: "Stock" },
    { symbol: "XOM",   name: "ExxonMobil",       category: "Stock" },
    { symbol: "MA",    name: "Mastercard",       category: "Stock" },
    { symbol: "PG",    name: "Procter & Gamble", category: "Stock" },
    { symbol: "JNJ",   name: "Johnson & Johnson",category: "Stock" },
    { symbol: "HD",    name: "Home Depot",       category: "Stock" },
    { symbol: "ASML",  name: "ASML Holding",     category: "Stock" },
    { symbol: "ORCL",  name: "Oracle",           category: "Stock" },
    { symbol: "COST",  name: "Costco",           category: "Stock" },
    { symbol: "MRK",   name: "Merck",            category: "Stock" },
    { symbol: "CVX",   name: "Chevron",          category: "Stock" },
    { symbol: "BAC",   name: "Bank of America",  category: "Stock" },
    { symbol: "ABBV",  name: "AbbVie",           category: "Stock" },
    { symbol: "AMD",   name: "AMD",              category: "Stock" },
    { symbol: "NFLX",  name: "Netflix",          category: "Stock" },
    { symbol: "PEP",   name: "PepsiCo",          category: "Stock" },
    { symbol: "KO",    name: "Coca-Cola",        category: "Stock" },
    { symbol: "TMO",   name: "Thermo Fisher",    category: "Stock" },
    { symbol: "WFC",   name: "Wells Fargo",      category: "Stock" },
    { symbol: "DIS",   name: "Walt Disney",      category: "Stock" },
    { symbol: "ADBE",  name: "Adobe",            category: "Stock" },
    { symbol: "AZN",   name: "AstraZeneca",      category: "Stock" },
    { symbol: "CSCO",  name: "Cisco",            category: "Stock" },
    { symbol: "QCOM",  name: "Qualcomm",         category: "Stock" },
    { symbol: "NVO",   name: "Novo Nordisk",     category: "Stock" },
    { symbol: "ACN",   name: "Accenture",        category: "Stock" },
    { symbol: "SAP",   name: "SAP",              category: "Stock" },
    { symbol: "GE",    name: "GE Aerospace",     category: "Stock" },
    { symbol: "CAT",   name: "Caterpillar",      category: "Stock" },
    { symbol: "AMGN",  name: "Amgen",            category: "Stock" },
    { symbol: "TXN",   name: "Texas Instruments",category: "Stock" },
    { symbol: "INTC",  name: "Intel",            category: "Stock" },
    { symbol: "IBM",   name: "IBM",              category: "Stock" },
    { symbol: "AXP",   name: "American Express", category: "Stock" },
    { symbol: "MS",    name: "Morgan Stanley",   category: "Stock" },
    { symbol: "PFE",   name: "Pfizer",           category: "Stock" },
    { symbol: "GS",    name: "Goldman Sachs",    category: "Stock" },
    { symbol: "HON",   name: "Honeywell",        category: "Stock" },
    { symbol: "NKE",   name: "Nike",             category: "Stock" },
    { symbol: "SBUX",  name: "Starbucks",        category: "Stock" },
    { symbol: "UBER",  name: "Uber",             category: "Stock" },
    { symbol: "INTU",  name: "Intuit",           category: "Stock" },
    { symbol: "ISRG",  name: "Intuitive Surgical",category: "Stock" },
    { symbol: "LRCX",  name: "Lam Research",     category: "Stock" },
    { symbol: "SYK",   name: "Stryker",          category: "Stock" },
    { symbol: "BA",    name: "Boeing",           category: "Stock" },
    // BIST (Turkish Stocks)
    { symbol: "THYAO.IS", name: "Türk Hava Yolları", category: "BIST" },
    { symbol: "EREGL.IS", name: "Ereğli Demir Çelik", category: "BIST" },
    { symbol: "GARAN.IS", name: "Garanti BBVA",        category: "BIST" },
    { symbol: "KCHOL.IS", name: "Koç Holding",         category: "BIST" },
    { symbol: "AKBNK.IS", name: "Akbank",              category: "BIST" },
    { symbol: "ASELS.IS", name: "Aselsan",             category: "BIST" },
    { symbol: "TUPRS.IS", name: "Tüpraş",              category: "BIST" },
    { symbol: "SISE.IS",  name: "Şişecam",             category: "BIST" },
    { symbol: "TCELL.IS", name: "Turkcell",            category: "BIST" },
    { symbol: "BIMAS.IS", name: "BİM Mağazaları",      category: "BIST" },
    // World Indices (Borsa Endeksleri)
    { symbol: "^GSPC",    name: "S&P 500",             category: "Index" },
    { symbol: "^IXIC",    name: "NASDAQ Composite",    category: "Index" },
    { symbol: "^DJI",     name: "Dow Jones Industrial",category: "Index" },
    { symbol: "^NYA",     name: "NYSE Composite",      category: "Index" },
    { symbol: "^RUT",     name: "Russell 2000",        category: "Index" },
    { symbol: "^VIX",     name: "VIX Volatility Index",category: "Index" },
    { symbol: "^FTSE",    name: "FTSE 100 (London)",   category: "Index" },
    { symbol: "^GDAXI",   name: "DAX (Frankfurt)",     category: "Index" },
    { symbol: "^FCHI",    name: "CAC 40 (Paris)",      category: "Index" },
    { symbol: "^IBEX",    name: "IBEX 35 (Madrid)",    category: "Index" },
    { symbol: "^AEX",     name: "AEX (Amsterdam)",     category: "Index" },
    { symbol: "^STOXX50E",name: "Euro Stoxx 50",       category: "Index" },
    { symbol: "^N225",    name: "Nikkei 225 (Tokyo)",  category: "Index" },
    { symbol: "^HSI",     name: "Hang Seng (Hong Kong)",category: "Index" },
    { symbol: "^BSESN",   name: "BSE Sensex (Mumbai)", category: "Index" },
    { symbol: "^NSEI",    name: "NIFTY 50 (India)",    category: "Index" },
    { symbol: "^BVSP",    name: "Bovespa (Brazil)",    category: "Index" },
    { symbol: "^AXJO",    name: "ASX 200 (Australia)", category: "Index" },
    { symbol: "^KS11",    name: "KOSPI (Seoul)",       category: "Index" },
    { symbol: "^SSMI",    name: "SMI (Switzerland)",   category: "Index" },
    { symbol: "XU100.IS", name: "BIST 100 (Istanbul)", category: "Index" },
    { symbol: "^TWII",    name: "Taiwan Weighted",     category: "Index" },
    // Popular ETFs
    { symbol: "SPY",  name: "SPDR S&P 500 ETF",        category: "ETF" },
    { symbol: "QQQ",  name: "Invesco NASDAQ 100 ETF",  category: "ETF" },
    { symbol: "DIA",  name: "SPDR Dow Jones ETF",      category: "ETF" },
    { symbol: "IWM",  name: "iShares Russell 2000 ETF",category: "ETF" },
    { symbol: "GLD",  name: "SPDR Gold ETF",           category: "ETF" },
    { symbol: "SLV",  name: "iShares Silver ETF",      category: "ETF" },
    { symbol: "TLT",  name: "iShares 20+ Year Treasury",category: "ETF" },
    { symbol: "XLE",  name: "Energy Select SPDR ETF",  category: "ETF" },
    { symbol: "XLF",  name: "Financial Select SPDR ETF",category: "ETF" },
    { symbol: "XLK",  name: "Technology Select SPDR ETF",category: "ETF" },
  ];

  // Helper: Triggers autocomplete search (merges static catalog & dynamic API search results)
  const triggerSearch = async (queryVal) => {
    const q = queryVal.trim().toLowerCase();
    if (!q) {
      setSearchSuggestions([]);
      setShowSuggestions(false);
      setSearchNoResults(false);
      return;
    }

    // 1. Get static matches instantly
    const staticMatches = SYMBOL_CATALOG.filter(item =>
      item.symbol.toLowerCase().includes(q) ||
      item.name.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    );

    setSearchSuggestions(staticMatches.slice(0, 8));
    if (staticMatches.length > 0) {
      setShowSuggestions(true);
      setSearchNoResults(false);
    } else {
      setShowSuggestions(false);
    }
    setSuggestionIndex(-1);

    // 2. Fetch dynamic matches from API and merge them
    try {
      const res = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const dynamicMatches = await res.json();
        const merged = [...staticMatches];
        dynamicMatches.forEach(item => {
          if (!merged.some(m => m.symbol.toUpperCase() === item.symbol.toUpperCase())) {
            merged.push(item);
          }
        });
        const finalResults = merged.slice(0, 8);
        setSearchSuggestions(finalResults);
        
        if (finalResults.length > 0) {
          setShowSuggestions(true);
          setSearchNoResults(false);
        } else {
          setShowSuggestions(false);
          setSearchNoResults(true);
        }
      } else {
        if (staticMatches.length === 0) {
          setSearchNoResults(true);
        }
      }
    } catch (err) {
      console.error("Dynamic search error:", err);
      if (staticMatches.length === 0) {
        setSearchNoResults(true);
      }
    }
  };


  // Settings / Profile Modals
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  // Basic Pages Modals State
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [contactSubject, setContactSubject] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactStatus, setContactStatus] = useState("");

  // AI Market Screener State
  const [showScreener, setShowScreener] = useState(false);
  const [screenerData, setScreenerData] = useState([]);
  const [screenerFilter, setScreenerFilter] = useState("all");
  const [screenerSearch, setScreenerSearch] = useState("");
  const [screenerType, setScreenerType] = useState("all");
  const [screenerLoading, setScreenerLoading] = useState(false);

  // News Sentiment State
  const [newsData, setNewsData] = useState(null);
  const [newsLoading, setNewsLoading] = useState(false);

  // Market Info State (market cap, 52w range, etc.)
  const [marketInfo, setMarketInfo] = useState(null);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [accuracyLogs, setAccuracyLogs] = useState([]);
  const [accuracyLoading, setAccuracyLoading] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [adminActiveTab, setAdminActiveTab] = useState("users");
  const [adminLoading, setAdminLoading] = useState(false);
  const [autoTrainSymbols, setAutoTrainSymbols] = useState([]);
  const [newAutoTrainSymbol, setNewAutoTrainSymbol] = useState("");
  const [mockTradingState, setMockTradingState] = useState(null);
  const [modelType, setModelType] = useState("xgboost");
  const [daemonLogs, setDaemonLogs] = useState({ out: [], error: [], daemon_out: [], daemon_err: [] });
  const [adminPerformance, setAdminPerformance] = useState(null);
  const [adminPerfSearch, setAdminPerfSearch] = useState("");
  const [adminPerfFilter, setAdminPerfFilter] = useState("all");


  const lastCloseVal = predictionData ? predictionData.last_close : null;
  const xgbChangeVal = (predictionData && predictionData.xgb_predicted_close !== null)
    ? (predictionData.xgb_predicted_close - 0.5) * 100
    : null;
  const lstmChangeVal = (predictionData && predictionData.lstm_predicted_close !== null)
    ? (predictionData.lstm_predicted_close - 0.5) * 100
    : null;
  const lrChangeVal = (predictionData && predictionData.lr_predicted_close !== null)
    ? (predictionData.lr_predicted_close - 0.5) * 100
    : null;
  const srChangeVal = (predictionData && predictionData.sr_predicted_close !== null && predictionData.sr_predicted_close !== undefined)
    ? (predictionData.sr_predicted_close - 0.5) * 100
    : null;


  const getPredictionHeader = () => {
    if (chartInterval === "1d") {
      return t("prediction_header");
    }
    if (lang === "tr") {
      if (chartInterval === "15m") return "Sonraki 15 Dakikalık Tahmini Kapanış";
      if (chartInterval === "1h") return "Sonraki 1 Saatlik Tahmini Kapanış";
      if (chartInterval === "4h") return "Sonraki 4 Saatlik Tahmini Kapanış";
    }
    if (lang === "de") {
      if (chartInterval === "15m") return "Prognostizierter Schlusskurs für die nächsten 15 Min.";
      if (chartInterval === "1h") return "Prognostizierter Schlusskurs für die nächste Stunde";
      if (chartInterval === "4h") return "Prognostizierter Schlusskurs für die nächsten 4 Stunden";
    }
    if (lang === "ru") {
      if (chartInterval === "15m") return "Прогноз закрытия на следующие 15 минут";
      if (chartInterval === "1h") return "Прогноз закрытия на следующий 1 час";
      if (chartInterval === "4h") return "Прогноз закрытия на следующие 4 часа";
    }
    if (lang === "zh") {
      if (chartInterval === "15m") return "未来 15 分钟预测收盘价";
      if (chartInterval === "1h") return "未来 1 小时预测收盘价";
      if (chartInterval === "4h") return "未来 4 小时预测收盘价";
    }
    if (lang === "es") {
      if (chartInterval === "15m") return "Próximos 15 Minutos Cierre Previsto";
      if (chartInterval === "1h") return "Próxima 1 Hora Cierre Previsto";
      if (chartInterval === "4h") return "Próximas 4 Horas Cierre Previsto";
    }
    if (chartInterval === "15m") return "Next 15 Minutes Predicted Close";
    if (chartInterval === "1h") return "Next Hour Predicted Close";
    if (chartInterval === "4h") return "Next 4 Hours Predicted Close";
    return t("prediction_header");
  };

  // Refs for Charts
  const priceChartRef = useRef(null);
  const rsiChartRef = useRef(null);
  const macdChartRef = useRef(null);
  const stochChartRef = useRef(null);
  const atrChartRef = useRef(null);
  const obvChartRef = useRef(null);
  const cciChartRef = useRef(null);
  const williamsChartRef = useRef(null);

  const priceChartInst = useRef(null);
  const rsiChartInst = useRef(null);
  const macdChartInst = useRef(null);
  const stochChartInst = useRef(null);
  const atrChartInst = useRef(null);
  const obvChartInst = useRef(null);
  const cciChartInst = useRef(null);
  const williamsChartInst = useRef(null);

  const [activeIndicatorTab, setActiveIndicatorTab] = useState("rsi_macd");

  // 1. Check for token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      fetchWatchlist(savedToken);
      fetchCurrentUser(savedToken);
    }
  }, []);

  // Clear chart tooltips on outside clicks/touches
  useEffect(() => {
    const handleOutsideClick = (e) => {
      const isClickInsideChart = 
        priceChartRef.current?.contains(e.target) || 
        rsiChartRef.current?.contains(e.target) || 
        macdChartRef.current?.contains(e.target) ||
        stochChartRef.current?.contains(e.target) ||
        atrChartRef.current?.contains(e.target) ||
        obvChartRef.current?.contains(e.target) ||
        cciChartRef.current?.contains(e.target) ||
        williamsChartRef.current?.contains(e.target);

      if (!isClickInsideChart) {
        [
          priceChartInst.current, rsiChartInst.current, macdChartInst.current,
          stochChartInst.current, atrChartInst.current, obvChartInst.current,
          cciChartInst.current, williamsChartInst.current
        ].forEach(chart => {
          if (chart) {
            chart.setActiveElements([]);
            if (chart.tooltip) {
              chart.tooltip.setActiveElements([], { x: 0, y: 0 });
            }
            chart.update();
          }
        });
      }
    };

    window.addEventListener("click", handleOutsideClick);
    window.addEventListener("touchstart", handleOutsideClick);

    return () => {
      window.removeEventListener("click", handleOutsideClick);
      window.removeEventListener("touchstart", handleOutsideClick);
    };
  }, []);


  // Fetch comments and news sentiment when activeSymbol changes
  useEffect(() => {
    if (activeSymbol) {
      fetchComments(activeSymbol);
      fetchNewsSentiment(activeSymbol);
    }
  }, [activeSymbol]);

  // Fetch market screener data on mount, periodically, and when opened
  useEffect(() => {
    fetchScreenerData();
    const interval = setInterval(() => {
      fetchScreenerData();
    }, 60000); // refresh every 60 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (showScreener) {
      fetchScreenerData();
    }
  }, [showScreener]);

  // 2. Fetch Prediction data when activeSymbol, chartInterval, modelType, or lang changes
  useEffect(() => {
    if (activeSymbol) {
      let currentModelType = modelType;
      // Enforce Linear Regression only for BTC-USD
      if (modelType === "linear_regression" && activeSymbol !== "BTC-USD") {
        currentModelType = "xgboost";
        setModelType("xgboost");
        return;
      }
      loadPrediction(activeSymbol, chartInterval, currentModelType);
    }
  }, [activeSymbol, chartInterval, modelType, token, lang]);

  // 3. Render charts when predictionData, chartHistory, historyLimit, isChartFullscreen, or showScreener updates
  useEffect(() => {
    if (showScreener) return;
    if (!predictionData || !chartHistory || chartHistory.length === 0) return;
    
    const timer = setTimeout(() => {
      renderCharts();
    }, 50);
    
    // Cleanup on unmount or update
    return () => {
      clearTimeout(timer);
      destroyCharts();
    };
  }, [predictionData, chartHistory, historyLimit, isChartFullscreen, showScreener]);

  // Handle price chart resize and body overflow on fullscreen state toggle
  useEffect(() => {
    if (isChartFullscreen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    
    if (priceChartInst.current) {
      const timer = setTimeout(() => {
        priceChartInst.current.resize();
      }, 100);
      return () => {
        clearTimeout(timer);
        document.body.style.overflow = "";
      };
    }
  }, [isChartFullscreen]);

  // Re-render charts when chartType changes
  useEffect(() => {
    if (predictionData && chartHistory && chartHistory.length > 0) {
      renderCharts();
    }
  }, [chartType]);

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
    if (stochChartInst.current) {
      stochChartInst.current.destroy();
      stochChartInst.current = null;
    }
    if (atrChartInst.current) {
      atrChartInst.current.destroy();
      atrChartInst.current = null;
    }
    if (obvChartInst.current) {
      obvChartInst.current.destroy();
      obvChartInst.current = null;
    }
    if (cciChartInst.current) {
      cciChartInst.current.destroy();
      cciChartInst.current = null;
    }
    if (williamsChartInst.current) {
      williamsChartInst.current.destroy();
      williamsChartInst.current = null;
    }
  };

  // Helper: Calculate support and resistance levels (Swing High/Low Pivot method)
  const calculateSupportResistance = (history) => {
    if (!history || history.length < 10) return { supports: [], resistances: [] };
    
    const closes = history.map(h => h.close);
    const highs = history.map(h => h.high !== null && h.high !== undefined ? h.high : h.close);
    const lows = history.map(h => h.low !== null && h.low !== undefined ? h.low : h.close);
    
    const windowSize = history.length > 300 ? 20 : 5;
    const peaks = [];
    const valleys = [];
    
    for (let i = windowSize; i < history.length - windowSize; i++) {
      // Peak (Local Maximum)
      const leftHighs = highs.slice(i - windowSize, i);
      const rightHighs = highs.slice(i + 1, i + windowSize + 1);
      if (highs[i] === Math.max(highs[i], ...leftHighs, ...rightHighs)) {
        peaks.push(highs[i]);
      }
      
      // Valley (Local Minimum)
      const leftLows = lows.slice(i - windowSize, i);
      const rightLows = lows.slice(i + 1, i + windowSize + 1);
      if (lows[i] === Math.min(lows[i], ...leftLows, ...rightLows)) {
        valleys.push(lows[i]);
      }
    }
    
    const currentPrice = closes[closes.length - 1];
    
    // Select up to 5 distinct supports (valleys below current price) and 5 resistances (peaks above current price)
    let supports = [...new Set(valleys.filter(v => v < currentPrice))].sort((a, b) => b - a).slice(0, 5);
    let resistances = [...new Set(peaks.filter(p => p > currentPrice))].sort((a, b) => a - b).slice(0, 5);
    
    // Fallbacks based on Pivot point calculations if not found
    if (supports.length === 0 || resistances.length === 0) {
      const h = highs[highs.length - 1];
      const l = lows[lows.length - 1];
      const c = closes[closes.length - 1];
      const pivot = (h + l + c) / 3.0;
      
    if (supports.length === 0) {
        supports = [2 * pivot - h, pivot - (h - l)];
      }
      if (resistances.length === 0) {
        resistances = [2 * pivot - l, pivot + (h - l)];
      }
    }
    
    return {
      supports: supports.sort((a, b) => a - b),
      resistances: resistances.sort((a, b) => a - b)
    };
  };

  // Helper: Render price, RSI, and MACD charts
  const renderCharts = () => {
    try {
      destroyCharts();
      if (!predictionData || !chartHistory || chartHistory.length === 0) return;

      const ctxPrice = priceChartRef.current?.getContext("2d");
      const ctxRsi = rsiChartRef.current?.getContext("2d");
      const ctxMacd = macdChartRef.current?.getContext("2d");
      const ctxStoch = stochChartRef.current?.getContext("2d");
      const ctxAtr = atrChartRef.current?.getContext("2d");
      const ctxObv = obvChartRef.current?.getContext("2d");
      const ctxCci = cciChartRef.current?.getContext("2d");
      const ctxWilliams = williamsChartRef.current?.getContext("2d");

      const isTouchDevice = typeof window !== "undefined" && ("ontouchstart" in window || navigator.maxTouchPoints > 0);
      const chartEvents = isTouchDevice ? ["click"] : ["mousemove", "mouseout", "click", "touchstart", "touchmove", "touchend"];

      const history = chartHistory.slice(-historyLimit);
      const labels = history.map(item => item.date);
      const closePrices = history.map(item => item.close);
      const ema20Prices = history.map(item => item.ema_20);
      const ema50Prices = history.map(item => item.ema_50);
      const bbUpperPrices = history.map(item => item.bb_upper);
      const bbLowerPrices = history.map(item => item.bb_lower);
      
      // Include prediction point only for daily (1d) interval
      let extendedLabels = [...labels];
      const isPendingData = predictionData && predictionData.prediction_status === "pending_data";
      if (predictionData && predictionData.prediction_date && !isPendingData) {
        extendedLabels.push(predictionData.prediction_date);
      }
      let datasets = [];
      if (chartType === "candle") {
        const candleColors = history.map(h => h.close >= h.open ? "rgba(16, 185, 129, 0.75)" : "rgba(239, 68, 68, 0.75)");
        const candleBorderColors = history.map(h => h.close >= h.open ? "#10b981" : "#ef4848");
        
        datasets.push({
          label: activeSymbol,
          type: "bar",
          data: history.map(h => [h.open, h.close]),
          backgroundColor: candleColors,
          borderColor: candleBorderColors,
          borderWidth: 1,
          barPercentage: 0.75,
          categoryPercentage: 0.95
        });
      } else {
        datasets.push({
          label: "Historical Close",
          type: "line",
          data: closePrices,
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.05)",
          borderWidth: 2.5,
          pointRadius: 0,
          tension: 0.15,
          fill: true,
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
          hidden: true,
        },
        {
          label: "EMA 50",
          data: ema50Prices,
          borderColor: "rgba(236, 72, 153, 0.65)",
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.15,
          hidden: true,
        },
        {
          label: "BB Upper",
          data: bbUpperPrices,
          borderColor: "rgba(245, 158, 11, 0.35)",
          borderWidth: 1,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false,
          hidden: true,
        },
        {
          label: "BB Lower",
          data: bbLowerPrices,
          borderColor: "rgba(245, 158, 11, 0.35)",
          borderWidth: 1,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false,
          hidden: true,
        }
      );



      // Add Support and Resistance Levels (All-symbols for premium, BTC-USD for everyone)
      const canShowSR = (activeSymbol === "BTC-USD") || (user && user.is_premium);
      
      if (canShowSR) {
        const { supports, resistances } = calculateSupportResistance(history);
        
        supports.forEach((val, idx) => {
          datasets.push({
            label: `${t("support")} ${idx + 1} (${val.toLocaleString(undefined, { maximumFractionDigits: 1 })})`,
            data: Array(extendedLabels.length).fill(val),
            borderColor: "rgba(16, 185, 129, 0.7)",
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
            hidden: true,
          });
        });

        resistances.forEach((val, idx) => {
          datasets.push({
            label: `${t("resistance")} ${idx + 1} (${val.toLocaleString(undefined, { maximumFractionDigits: 1 })})`,
            data: Array(extendedLabels.length).fill(val),
            borderColor: "rgba(239, 68, 68, 0.7)",
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
            tension: 0,
            hidden: true,
          });
        });
      }

      // Price Chart
      if (ctxPrice) {
        priceChartInst.current = new Chart(ctxPrice, {
          type: "line",
          data: {
            labels: extendedLabels,
            datasets: datasets
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              candlestickWicks: {
                enabled: chartType === "candle",
                history: history
              },
              legend: {
                labels: { color: "#9ca3af", font: { family: "Inter" } }
              },
              tooltip: {
                mode: "index",
                intersect: false,
              },
              zoom: {
                zoom: {
                  wheel: {
                    enabled: isChartFullscreen,
                    speed: 0.05,
                  },
                  pinch: {
                    enabled: isChartFullscreen
                  },
                  mode: "x",
                  onZoom: ({ chart }) => {
                    const lastIndex = chart.data.labels.length - 1;
                    if (chart.options.scales.x) {
                      chart.options.scales.x.max = lastIndex;
                    }
                    chart.update("none");
                  }
                },
                pan: {
                  enabled: isChartFullscreen,
                  mode: "x",
                  modifierKey: null,
                }
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
            events: chartEvents,
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
            events: chartEvents,
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

      // Stochastic RSI Chart
      if (ctxStoch) {
        const stochKValues = history.map(item => item.stoch_k !== undefined ? item.stoch_k : 50.0);
        const stochDValues = history.map(item => item.stoch_d !== undefined ? item.stoch_d : 50.0);
        
        stochChartInst.current = new Chart(ctxStoch, {
          type: "line",
          data: {
            labels: labels,
            datasets: [
              {
                label: "%K",
                data: stochKValues,
                borderColor: "#f59e0b",
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.1,
              },
              {
                label: "%D",
                data: stochDValues,
                borderColor: "#06b6d4",
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.1,
              }
            ]
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { display: false } },
              y: {
                min: 0,
                max: 100,
                grid: { color: "rgba(255, 255, 255, 0.05)" },
                ticks: { color: "#9ca3af", stepSize: 20 },
                border: { dash: [5, 5] }
              }
            }
          }
        });
      }

      // ATR Chart
      if (ctxAtr) {
        const atrValues = history.map(item => item.atr !== undefined ? item.atr : 0.0);
        
        atrChartInst.current = new Chart(ctxAtr, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "ATR",
              data: atrValues,
              borderColor: "#a855f7",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            }]
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { display: false } },
              y: {
                grid: { color: "rgba(255, 255, 255, 0.05)" },
                ticks: { color: "#9ca3af" }
              }
            }
          }
        });
      }

      // OBV Chart
      if (ctxObv) {
        const obvValues = history.map(item => item.obv !== undefined ? item.obv : 0.0);
        
        obvChartInst.current = new Chart(ctxObv, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "OBV",
              data: obvValues,
              borderColor: "#10b981",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            }]
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { display: false } },
              y: {
                grid: { color: "rgba(255, 255, 255, 0.05)" },
                ticks: { 
                  color: "#9ca3af",
                  callback: (val) => {
                    if (Math.abs(val) >= 1e9) return (val / 1e9).toFixed(1) + "B";
                    if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + "M";
                    if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + "K";
                    return val;
                  }
                }
              }
            }
          }
        });
      }

      // CCI Chart
      if (ctxCci) {
        const cciValues = history.map(item => item.cci !== undefined ? item.cci : 0.0);
        
        cciChartInst.current = new Chart(ctxCci, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "CCI",
              data: cciValues,
              borderColor: "#3b82f6",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            }]
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { display: false } },
              y: {
                grid: { color: "rgba(255, 255, 255, 0.05)" },
                ticks: { color: "#9ca3af", stepSize: 100 },
                border: { dash: [5, 5] }
              }
            }
          }
        });
      }

      // Williams %R Chart
      if (ctxWilliams) {
        const williamsValues = history.map(item => item.williams_r !== undefined ? item.williams_r : -50.0);
        
        williamsChartInst.current = new Chart(ctxWilliams, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: "Williams %R",
              data: williamsValues,
              borderColor: "#ec4899",
              borderWidth: 1.5,
              pointRadius: 0,
              tension: 0.1,
            }]
          },
          options: {
            events: chartEvents,
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { display: false } },
              y: {
                min: -100,
                max: 0,
                grid: { color: "rgba(255, 255, 255, 0.05)" },
                ticks: { color: "#9ca3af", stepSize: 20 },
                border: { dash: [5, 5] }
              }
            }
          }
        });
      }
    } catch (err) {
      console.error("Error inside renderCharts:", err);
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
      setWatchlist(Array.isArray(data) ? data : []);
      
      // Populate standard items if user's watchlist is empty
      if (Array.isArray(data) && data.length === 0) {
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
    setAccuracyLoading(true);
    try {
      const headers = token ? { "Authorization": `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE_URL}/api/predictions/accuracy/${symbol}?interval=${interval}`, {
        headers
      });
      if (res.ok) {
        const data = await res.json();
        setAccuracyLogs(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error fetching accuracy logs:", err);
    } finally {
      setAccuracyLoading(false);
    }
  };

  // API Call: Load LSTM Prediction (timeframe-aware)
  const loadPrediction = async (symbol, interval = chartInterval, mType = modelType, forceRetrain = false) => {
    setPredictLoading(true);
    setPredictError("");
    setPredictionData(null); // Clear old prediction data to trigger loading UI immediately
    setLoadingStep(1);
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => (prev < 6 ? prev + 1 : prev));
    }, 600);
    try {
      const headers = token ? { "Authorization": `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE_URL}/api/predict?symbol=${symbol}&interval=${interval}&lang=${lang}&model_type=${mType}&force_retrain=${forceRetrain}`, {
        headers
      });
      if (res.status === 401 && token) {
        handleLogout();
        return;
      }
      const data = await res.json();
      if (res.ok) {
        setPredictionData(data);
        setChartHistory(data.history);
        fetchMarketInfo(symbol);
        fetchScreenerData(); // Refresh the screener list to display consensus changes immediately
        if (AUTO_TRAINED_SYMBOLS.includes(symbol) && interval === "1d") {
          fetchAccuracyLogs(symbol, interval);
        } else {
          setAccuracyLogs([]);
        }
      } else {
        setPredictError(data.detail || "Failed to load prediction model.");
      }
    } catch (err) {
      setPredictError("Connection failed to Python FastAPI server.");
    } finally {
      clearInterval(stepInterval);
      setPredictLoading(false);
    }
  };

  // API Call: Fetch Market Info (market cap, P/E, 52w range, sector)
  const fetchMarketInfo = async (symbol) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/market-info/${encodeURIComponent(symbol)}`);
      if (res.ok) {
        const data = await res.json();
        setMarketInfo(data);
      } else {
        setMarketInfo(null);
      }
    } catch {
      setMarketInfo(null);
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
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
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

  // API Call: Toggle Premium Status
  const handlePremiumToggle = async () => {
    if (!token) {
      setAuthError(lang === "tr" ? "Premium avantajlarından yararlanmak için lütfen giriş yapın veya kayıt olun." : "Please sign in or create an account to get premium benefits.");
      setShowAuthModal(true);
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/premium/toggle`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        setUser(data);
      } else {
        alert(data.detail || "Could not toggle premium status.");
      }
    } catch (err) {
      console.error("Premium toggle failed:", err);
    }
  };

  // API Call: Fetch Comments
  const fetchComments = async (symbol) => {
    try {
      const headers = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API_BASE_URL}/api/comments/${symbol}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setComments(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error fetching comments:", err);
    }
  };

  // API Call: Fetch Market Screener Data
  const fetchScreenerData = async () => {
    setScreenerLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/screener?t=${Date.now()}`);
      if (res.ok) {
        const data = await res.json();
        setScreenerData(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error fetching screener data:", err);
    } finally {
      setScreenerLoading(false);
    }
  };

  // API Call: Fetch News Sentiment
  const fetchNewsSentiment = async (symbol) => {
    setNewsLoading(true);
    setNewsData(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/news/${symbol}`);
      if (res.ok) {
        const data = await res.json();
        setNewsData(data);
      }
    } catch (err) {
      console.error("Error fetching news sentiment:", err);
    } finally {
      setNewsLoading(false);
    }
  };

  // API Call: Post Comment/Reply
  const handlePostComment = async (e, parentId = null) => {
    if (e) e.preventDefault();
    if (!token) {
      setAuthError(lang === "tr" ? "Yorum yapabilmek veya yanıt yazabilmek için lütfen giriş yapın." : "Please sign in to post comments or replies.");
      setShowAuthModal(true);
      return;
    }
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

  // API Call: React (like/dislike) on Comment
  const handleReactComment = async (commentId, reaction) => {
    if (!token) {
      setAuthError(lang === "tr" ? "Tepki verebilmek için lütfen giriş yapın." : "Please sign in to react to comments.");
      setShowAuthModal(true);
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/comments/${commentId}/react`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ reaction })
      });
      if (res.ok) {
        setComments(prev => prev.map(c => {
          if (c.id !== commentId) return c;
          const wasLiked = c.user_reaction === "like";
          const wasDisliked = c.user_reaction === "dislike";
          if (c.user_reaction === reaction) {
            return { ...c, user_reaction: null, likes: reaction === "like" ? c.likes - 1 : c.likes, dislikes: reaction === "dislike" ? c.dislikes - 1 : c.dislikes };
          } else {
            return {
              ...c,
              user_reaction: reaction,
              likes: reaction === "like" ? c.likes + 1 : (wasLiked ? c.likes - 1 : c.likes),
              dislikes: reaction === "dislike" ? c.dislikes + 1 : (wasDisliked ? c.dislikes - 1 : c.dislikes)
            };
          }
        }));
      }
    } catch (err) {
      console.error("Error reacting to comment:", err);
    }
  };

  // API Call: Register Request
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      });
      const data = await res.json();
      if (res.ok) {
        setRegisteredEmail(email);
        setIsVerifyingRegister(true);
      } else {
        setAuthError(data.detail || "Registration failed. Try again.");
      }
    } catch (err) {
      setAuthError("Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  // API Call: Register Confirmation
  const handleConfirmRegister = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: registeredEmail, code: verificationCode })
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
        setVerificationCode("");
        setRegisteredEmail("");
        setIsVerifyingRegister(false);
        setShowAuthModal(false);
      } else {
        setAuthError(data.detail || "Invalid or expired verification code.");
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
        setShowAuthModal(false);
      } else {
        setAuthError(data.detail || "Invalid credentials.");
      }
    } catch (err) {
      setAuthError("Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  // API Call: Add Watchlist Item Helper
  const addSymbolToWatchlist = async (symbolToAdd) => {
    if (!symbolToAdd) return;
    if (!token) {
      setAuthError(lang === "tr" ? "Arama yapmak veya takip listenizi özelleştirmek için giriş yapın." : "Sign in to search and customize your watchlist.");
      setShowAuthModal(true);
      return;
    }
    const sym = symbolToAdd.toUpperCase().trim();
    
    // If symbol is already in watchlist, directly select it and clear search query without showing an alert
    if (watchlist.some(w => w.symbol === sym)) {
      selectSymbol(sym);
      setSearchQuery("");
      setShowSuggestions(false);
      setSidebarOpen(false);
      return;
    }
    
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
        if (!watchlist.some(w => w.symbol === data.symbol)) {
          setWatchlist([...watchlist, data]);
        }
        selectSymbol(data.symbol);
        setSearchQuery("");
        setShowSuggestions(false);
        setSidebarOpen(false);
      } else {
        alert(data.detail || "Could not add symbol to watchlist.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Search Submit (Enter/Search click) for Dynamic Autocomplete
  const handleSearchSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;
    await triggerSearch(searchQuery);
  };


  // API Call: Remove Watchlist Item
  const handleRemoveWatchlist = async (e, symbolToRemove) => {
    e.stopPropagation(); // Prevent clicking item from changing active symbol
    if (!token) {
      setAuthError(lang === "tr" ? "Takip listesinden kaldırmak için giriş yapın." : "Sign in to modify your watchlist.");
      setShowAuthModal(true);
      return;
    }
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

  // API Call: Change Password Request
  const handleChangePasswordRequest = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/change-password/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });
      const data = await res.json();
      if (res.ok) {
        setPasswordSuccess("Verification code sent to your email.");
        setIsVerifyingPasswordChange(true);
      } else {
        setPasswordError(data.detail || "Failed to initiate password change.");
      }
    } catch (err) {
      setPasswordError("Connection failed.");
    }
  };

  // API Call: Confirm Password Change
  const handleConfirmPasswordChange = async (e) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/change-password/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ code: passwordVerificationCode })
      });
      const data = await res.json();
      if (res.ok) {
        setPasswordSuccess("Password updated successfully.");
        setOldPassword("");
        setNewPassword("");
        setPasswordVerificationCode("");
        setIsVerifyingPasswordChange(false);
        setTimeout(() => setShowPasswordModal(false), 2000);
      } else {
        setPasswordError(data.detail || "Invalid or expired verification code.");
      }
    } catch (err) {
      setPasswordError("Connection failed.");
    }
  };

  const getTimeStepText = (interval) => {
    if (interval === "1d") {
      return `60 ${t("days")}`;
    }
    if (interval === "4h") {
      if (lang === "tr") return "60 Mum (240 Saat / 10 Gün)";
      if (lang === "de") return "60 Kerzen (240 Stunden / 10 Tage)";
      if (lang === "ru") return "60 свечей (240 часов / 10 дней)";
      if (lang === "zh") return "60 根K线 (240 小时 / 10 天)";
      if (lang === "es") return "60 velas (240 horas / 10 días)";
      return "60 Candles (240 Hours / 10 Days)";
    }
    if (interval === "1h") {
      if (lang === "tr") return "60 Mum (60 Saat / 2.5 Gün)";
      if (lang === "de") return "60 Kerzen (60 Stunden / 2.5 Tage)";
      if (lang === "ru") return "60 свечей (60 часов / 2.5 дней)";
      if (lang === "zh") return "60 根K线 (60 小时 / 2.5 天)";
      if (lang === "es") return "60 velas (60 horas / 2.5 días)";
      return "60 Candles (60 Hours / 2.5 Days)";
    }
    if (interval === "15m") {
      if (lang === "tr") return "60 Mum (15 Saat)";
      if (lang === "de") return "60 Kerzen (15 Stunden)";
      if (lang === "ru") return "60 свечей (15 часов)";
      if (lang === "zh") return "60 根K线 (15 小时)";
      if (lang === "es") return "60 velas (15 horas)";
      return "60 Candles (15 Hours)";
    }
    return `60 ${t("days")}`;
  };

  const getSymbolDetails = (symbol) => {
    if (!symbol) return null;
    const s = symbol.toUpperCase().trim();
    const isTr = lang === "tr";
    
    if (s.endsWith(".IS")) {
      return {
        exchange: "Borsa İstanbul (BIST)",
        country: isTr ? "Türkiye" : "Turkey",
        market: isTr ? "Hisse Senedi" : "Stock"
      };
    }
    
    if (s.endsWith("-USD") || s.endsWith("-BTC") || s.endsWith("-EUR")) {
      return {
        exchange: isTr ? "Merkeziyetsiz / Global Kripto" : "Decentralized / Global Crypto",
        country: "Global",
        market: isTr ? "Kripto Para" : "Cryptocurrency"
      };
    }
    
    if (s === "GC=F" || s === "GOLD") {
      return {
        exchange: "COMEX (Chicago Mercantile Exchange)",
        country: isTr ? "Amerika (Global)" : "United States (Global)",
        market: isTr ? "Altın Emtiası" : "Gold Commodity"
      };
    }
    
    if (s === "CL=F" || s === "OIL" || s === "BZ=F") {
      return {
        exchange: "NYMEX (New York Mercantile Exchange)",
        country: "Global",
        market: isTr ? "Ham Petrol" : "Crude Oil"
      };
    }
    
    if (s === "SI=F" || s === "SILVER") {
      return {
        exchange: "COMEX",
        country: "Global",
        market: isTr ? "Gümüş Emtiası" : "Silver Commodity"
      };
    }
    
    if (s.includes("=F")) {
      return {
        exchange: isTr ? "Vadeli İşlem Borsaları" : "Futures Exchange",
        country: "Global",
        market: isTr ? "Vadeli İşlem / Emtia" : "Futures / Commodity"
      };
    }
    
    return {
      exchange: "NASDAQ / NYSE",
      country: isTr ? "Amerika Birleşik Devletleri (ABD)" : "United States (USA)",
      market: isTr ? "Hisse Senedi" : "Stock"
    };
  };

  const fetchMockTradingState = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/mock-trading`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMockTradingState(data);
      }
    } catch (err) {
      console.error("Error fetching mock trading state:", err);
    }
  };

  const handleResetMockTrading = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    if (!window.confirm(lang === "tr" ? "Simülasyonu sıfırlamak istediğinize emin misiniz? Bakiye $2,000.00 olacaktır." : "Are you sure you want to reset the simulation? Balance will return to $2,000.00.")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/mock-trading/reset`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMockTradingState(data);
      }
    } catch (err) {
      console.error("Error resetting mock trading:", err);
    }
  };

  const fetchAdminData = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    setAdminLoading(true);
    try {
      const usersRes = await fetch(`${API_BASE_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setAdminUsers(usersData);
      }
      
      const statsRes = await fetch(`${API_BASE_URL}/api/admin/system-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setAdminStats(statsData);
      }
      
      const symbolsRes = await fetch(`${API_BASE_URL}/api/admin/auto-train-symbols`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (symbolsRes.ok) {
        const symbolsData = await symbolsRes.json();
        setAutoTrainSymbols(Array.isArray(symbolsData) ? symbolsData : []);
      }
      
      const logsRes = await fetch(`${API_BASE_URL}/api/temp-logs`);
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setDaemonLogs(logsData);
      }
      
      const perfRes = await fetch(`${API_BASE_URL}/api/admin/predictions-performance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (perfRes.ok) {
        const perfData = await perfRes.json();
        setAdminPerformance(perfData);
      }
      
      await fetchMockTradingState();
    } catch (err) {
      console.error("Error fetching admin data:", err);
    } finally {
      setAdminLoading(false);
    }
  };

  const handleAddAutoTrainSymbol = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token || !newAutoTrainSymbol.trim()) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/auto-train-symbols`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ symbol: newAutoTrainSymbol })
      });
      if (res.ok) {
        const added = await res.json();
        setAutoTrainSymbols(prev => [...prev, added].sort((a, b) => a.symbol.localeCompare(b.symbol)));
        setNewAutoTrainSymbol("");
      } else {
        const errData = await res.json();
        alert(errData.detail || "Error adding symbol");
      }
    } catch (err) {
      console.error("Error adding symbol:", err);
    }
  };

  const handleDeleteAutoTrainSymbol = async (symbol) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    if (!confirm(`Are you sure you want to remove ${symbol} from the auto-train list?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/auto-train-symbols/${symbol}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setAutoTrainSymbols(prev => prev.filter(s => s.symbol !== symbol));
      } else {
        const errData = await res.json();
        alert(errData.detail || "Error deleting symbol");
      }
    } catch (err) {
      console.error("Error deleting symbol:", err);
    }
  };

  const handleAdminTogglePremium = async (userId) => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/toggle-premium`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAdminData();
      }
    } catch (err) {
      console.error("Error toggling user premium status:", err);
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
    setUser(null);
    setWatchlist([
      { id: "anon-btc", symbol: "BTC-USD" },
      { id: "anon-eth", symbol: "ETH-USD" },
      { id: "anon-sol", symbol: "SOL-USD" },
      { id: "anon-aapl", symbol: "AAPL" },
      { id: "anon-tsla", symbol: "TSLA" }
    ]);
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

  // Render Auth UI in overlay modal
  const renderAuthModal = () => {
    if (!showAuthModal) return null;
    return (
      <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.85)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10000 }}>
        <div className="glass-panel auth-card" style={{ position: "relative", width: "90%", maxWidth: "420px" }}>
          {/* Close button for the modal */}
          <button 
            onClick={() => {
              setShowAuthModal(false);
              setAuthError("");
              setIsVerifyingRegister(false);
            }}
            style={{ position: "absolute", top: "15px", right: "15px", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
            aria-label="Close"
          >
            <X style={{ width: "20px", height: "20px" }} />
          </button>
          
          <div className="auth-header">
            <h1 className="logo-text" style={{ fontSize: "36px", marginBottom: "10px" }}>analyzeio</h1>
            <p style={{ color: "var(--text-muted)", fontSize: "12px", lineHeight: "1.4" }}>
              {lang === "tr" 
                ? "Yapay Zeka Destekli Grafik ve Teknik Analiz Platformu (SaaS)" 
                : "AI-Backed Graphic & Technical Analysis Platform (SaaS)"}
            </p>
          </div>
          
          {isVerifyingRegister ? (
            <form onSubmit={handleConfirmRegister} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{ textAlign: "center", color: "var(--text-main)", fontSize: "14px", marginBottom: "10px", lineHeight: "1.5" }}>
                {lang === "tr" 
                  ? `Lütfen ${registeredEmail} adresine gönderilen 6 haneli doğrulama kodunu girin.` 
                  : `Please enter the 6-digit verification code sent to ${registeredEmail}.`}
              </div>
              <div style={{ position: "relative" }}>
                <Lock style={{ position: "absolute", left: "14px", top: "13px", color: "var(--text-muted)", width: "18px" }} />
                <input
                  type="text"
                  placeholder={lang === "tr" ? "Doğrulama Kodu" : "Verification Code"}
                  className="input-field"
                  value={verificationCode}
                  onChange={e => setVerificationCode(e.target.value)}
                  style={{ paddingLeft: "42px", letterSpacing: "4px", textAlign: "center", fontWeight: "bold" }}
                  maxLength={6}
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
                {lang === "tr" ? "Doğrula ve Kaydol" : "Verify & Sign Up"}
              </button>

              <button 
                type="button" 
                className="btn-secondary" 
                onClick={() => {
                  setIsVerifyingRegister(false);
                  setAuthError("");
                  setVerificationCode("");
                }}
              >
                {lang === "tr" ? "Geri Dön" : "Go Back"}
              </button>
            </form>
          ) : (
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
          )}

          {!isVerifyingRegister && (
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
          )}
        </div>
      </div>
    );
  };

  // Helper to render nested comments
  const renderCommentNode = (comment, depth = 0) => {
    const replies = comments.filter(c => c.parent_id === comment.id);
    const isOwner = user && user.id === comment.user.id;

    // Find parent username for @mention display
    let parentUsername = null;
    if (comment.parent_id) {
      const parent = comments.find(c => c.id === comment.parent_id);
      if (parent) parentUsername = parent.user.username;
    }
    
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
          
          <p style={{ fontSize: "12px", color: "var(--text-main)", margin: "4px 0", whiteSpace: "pre-wrap" }}>
            {parentUsername && (
              <span style={{ color: "var(--accent-primary)", fontWeight: "700", marginRight: "4px" }}>@{parentUsername}</span>
            )}
            {comment.content}
          </p>
          
          <div style={{ display: "flex", gap: "8px", marginTop: "6px", alignItems: "center" }}>
            {/* Like button */}
            <button 
              onClick={() => handleReactComment(comment.id, "like")}
              style={{ 
                background: "none", border: "none", cursor: "pointer", padding: "2px 6px",
                display: "flex", alignItems: "center", gap: "3px", fontSize: "11px", fontWeight: "600",
                color: comment.user_reaction === "like" ? "var(--accent-success)" : "var(--text-muted)",
                borderRadius: "4px",
                transition: "all 0.2s"
              }}
            >
              👍 {comment.likes > 0 && <span>{comment.likes}</span>}
            </button>
            
            {/* Dislike button */}
            <button 
              onClick={() => handleReactComment(comment.id, "dislike")}
              style={{ 
                background: "none", border: "none", cursor: "pointer", padding: "2px 6px",
                display: "flex", alignItems: "center", gap: "3px", fontSize: "11px", fontWeight: "600",
                color: comment.user_reaction === "dislike" ? "var(--accent-danger)" : "var(--text-muted)",
                borderRadius: "4px",
                transition: "all 0.2s"
              }}
            >
              👎 {comment.dislikes > 0 && <span>{comment.dislikes}</span>}
            </button>

            {/* Reply button */}
            <button 
              onClick={() => {
                if (replyingToId === comment.id) {
                  setReplyingToId(null);
                } else {
                  setReplyingToId(comment.id);
                  setReplyContent("");
                }
              }}
              style={{ background: "none", border: "none", color: "var(--accent-primary)", fontSize: "11px", fontWeight: "600", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", gap: "4px", marginLeft: "4px" }}
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
  
  const getBestModel = () => {
    if (!predictionData) return null;
    const models = [
      { key: "xgboost", name: "XGBoost", da: predictionData.xgb_metrics?.directional_accuracy, pred: predictionData.xgb_predicted_close },
      { key: "lstm", name: "LSTM", da: predictionData.lstm_metrics?.directional_accuracy, pred: predictionData.lstm_predicted_close },
      { key: "linear_regression", name: lang === "tr" ? "Lineer Regresyon" : "Linear Regression", da: predictionData.lr_metrics?.directional_accuracy, pred: predictionData.lr_predicted_close },
      { key: "patchtst", name: "PatchTST", da: predictionData.patchtst_metrics?.directional_accuracy, pred: predictionData.patchtst_predicted_close },
      { key: "support_resistance", name: lang === "tr" ? "Destek/Direnç" : "Support/Resistance", da: predictionData.sr_metrics?.directional_accuracy, pred: predictionData.sr_predicted_close }
    ];
    
    // Do not select a best model if any model is still training/pending (shows ---)
    const hasAnyNull = models.some(m => m.pred === null || m.pred === undefined);
    if (hasAnyNull) return null;

    const validModels = models.filter(m => m.da !== null && m.da !== undefined && !isNaN(m.da));
    if (validModels.length === 0) return null;
    validModels.sort((a, b) => b.da - a.da);
    return validModels[0];
  };

  const getBoxStyle = (modelKey, defaultBg, defaultBorder) => {
    const bestModel = getBestModel();
    const isBest = bestModel && bestModel.key === modelKey;
    if (isBest) {
      return {
        padding: "10px 14px",
        background: "linear-gradient(90deg, rgba(245, 158, 11, 0.12) 0%, rgba(251, 191, 36, 0.03) 100%)",
        border: "1.5px solid rgba(245, 158, 11, 0.75)",
        borderRadius: "var(--border-radius-md)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        boxShadow: "0 0 15px rgba(245, 158, 11, 0.2)"
      };
    }
    return {
      padding: "10px 14px",
      background: defaultBg,
      border: defaultBorder,
      borderRadius: "var(--border-radius-md)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center"
    };
  };

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
        <div onClick={() => { setShowScreener(false); setSidebarOpen(false); }} className="mobile-navbar-logo" style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
          <Briefcase style={{ color: "var(--accent-primary)", width: "20px", height: "20px" }} />
          <h1 className="logo-text" style={{ fontSize: "18px", margin: 0 }}>analyzeio</h1>
        </div>
        <div style={{ width: "40px" }} /> {/* Spacer to center the logo */}
      </header>
      
      {/* Sidebar Panel */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="logo-container" style={{ justifyContent: "space-between", width: "100%" }}>
          <div onClick={() => { setShowScreener(false); setSidebarOpen(false); }} style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}>
            <Briefcase style={{ color: "var(--accent-primary)", width: "28px", height: "28px" }} />
            <h1 className="logo-text" style={{ fontSize: "24px", margin: 0 }}>analyzeio</h1>
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

        {/* Search Input with Autocomplete */}
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "8px" }}>
            <div style={{ position: "relative", flexGrow: 1 }}>
              <Search style={{ position: "absolute", left: "12px", top: "12px", color: "var(--text-muted)", width: "16px", zIndex: 1 }} />
              <input
                type="text"
                placeholder={t("search_placeholder")}
                className="input-field"
                value={searchQuery}
                onChange={e => {
                  const val = e.target.value;
                  setSearchQuery(val);
                  triggerSearch(val);
                }}
                onFocus={() => triggerSearch(searchQuery)}
                onBlur={() => setTimeout(() => { setShowSuggestions(false); setSearchNoResults(false); }, 250)}
                onKeyDown={e => {
                  if (!showSuggestions) return;
                  if (e.key === "ArrowDown") {
                    e.preventDefault();
                    setSuggestionIndex(i => Math.min(i + 1, searchSuggestions.length - 1));
                  } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    setSuggestionIndex(i => Math.max(i - 1, -1));
                  } else if (e.key === "Enter" && suggestionIndex >= 0) {
                    e.preventDefault();
                    const chosen = searchSuggestions[suggestionIndex];
                    setShowSuggestions(false);
                    addSymbolToWatchlist(chosen.symbol);
                  } else if (e.key === "Escape") {
                    setShowSuggestions(false);
                  }
                }}
                style={{ paddingLeft: "36px", paddingRight: "10px", height: "40px" }}
              />
              {/* Autocomplete Dropdown */}
              {showSuggestions && (
                <div style={{
                  position: "absolute",
                  top: "calc(100% + 4px)",
                  left: 0,
                  right: 0,
                  background: "rgba(15, 10, 30, 0.98)",
                  border: "1px solid rgba(139, 92, 246, 0.3)",
                  borderRadius: "10px",
                  zIndex: 9999,
                  overflow: "hidden",
                  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
                  backdropFilter: "blur(12px)"
                }}>
                  {searchSuggestions.map((item, idx) => {
                    const catColors = { Crypto: "#f59e0b", Stock: "#3b82f6", BIST: "#10b981", Commodity: "#f97316", Index: "#a855f7", ETF: "#06b6d4" };
                    const isHighlighted = idx === suggestionIndex;
                    return (
                      <div
                        key={item.symbol}
                        onMouseDown={() => {
                          addSymbolToWatchlist(item.symbol);
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "9px 14px",
                          cursor: "pointer",
                          background: isHighlighted ? "rgba(139, 92, 246, 0.15)" : "transparent",
                          borderBottom: idx < searchSuggestions.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
                          transition: "background 0.15s"
                        }}
                        onMouseEnter={() => setSuggestionIndex(idx)}
                      >
                        <Search style={{ width: "12px", color: "var(--text-muted)", flexShrink: 0 }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-main)" }}>{item.symbol}</div>
                          <div style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.name}</div>
                        </div>
                        <span style={{
                          fontSize: "9px",
                          fontWeight: "700",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: `${catColors[item.category] || "#6b7280"}20`,
                          color: catColors[item.category] || "#6b7280",
                          border: `1px solid ${catColors[item.category] || "#6b7280"}40`,
                          flexShrink: 0
                        }}>
                          {item.category.toUpperCase()}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            <button type="submit" className="btn-primary" style={{ width: "40px", height: "40px", padding: 0 }} aria-label="Search">
              <Search style={{ width: "18px" }} />
            </button>
          </form>
          {searchNoResults && searchQuery.trim() !== "" && (
            <div style={{ 
              color: "var(--accent-danger)", 
              fontSize: "12px", 
              marginTop: "2px", 
              paddingLeft: "4px",
              fontWeight: "500" 
            }}>
              {lang === "tr" ? "Sembol bulunamadı. Tekrar girin" : "Symbol not found. Please enter again"}
            </div>
          )}
        </div>


        {/* Navigation Tabs */}
        <div style={{ display: "flex", gap: "8px", marginTop: "5px", marginBottom: "15px" }}>
          <button 
            onClick={() => { setShowScreener(false); setSidebarOpen(false); }}
            className={!showScreener ? "btn-primary" : "btn-secondary"}
            style={{ flex: 1, height: "36px", fontSize: "13px", padding: 0, justifyContent: "center", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <LineChart style={{ width: "14px" }} /> {lang === "tr" ? "Grafik" : "Dashboard"}
          </button>
          <button 
            onClick={() => { setShowScreener(true); setSidebarOpen(false); }}
            className={showScreener ? "btn-primary" : "btn-secondary"}
            style={{ flex: 1, height: "36px", fontSize: "13px", padding: 0, justifyContent: "center", display: "flex", alignItems: "center", gap: "6px" }}
          >
            <PieChart style={{ width: "14px" }} /> {t("ai_screener")}
          </button>
        </div>

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

        {/* Sidebar Footer - Basic Pages Links */}
        <div style={{ 
          borderTop: "1px solid rgba(255, 255, 255, 0.05)", 
          paddingTop: "12px", 
          marginTop: "auto", 
          display: "flex", 
          flexDirection: "column", 
          gap: "6px",
          alignItems: "center"
        }}>
          <div style={{ display: "flex", gap: "8px", fontSize: "11px", color: "var(--text-muted)", flexWrap: "wrap", justifyContent: "center" }}>
            <span onClick={() => setShowAboutModal(true)} style={{ cursor: "pointer", transition: "color 0.2s" }} className="footer-link-item">
              {lang === "tr" ? "Hakkımızda" : "About Us"}
            </span>
            <span>•</span>
            <span onClick={() => setShowPrivacyModal(true)} style={{ cursor: "pointer", transition: "color 0.2s" }} className="footer-link-item">
              {lang === "tr" ? "Gizlilik" : "Privacy"}
            </span>
            <span>•</span>
            <span onClick={() => setShowContactModal(true)} style={{ cursor: "pointer", transition: "color 0.2s" }} className="footer-link-item">
              {lang === "tr" ? "İletişim" : "Contact"}
            </span>
          </div>
          <span style={{ fontSize: "9px", color: "var(--text-dark)", textAlign: "center" }}>
            &copy; {new Date().getFullYear()} analyzeio
          </span>
          <p style={{ fontSize: "8px", color: "var(--text-dark)", textAlign: "center", margin: "6px 0 0 0", lineHeight: "1.3" }}>
            {lang === "tr" 
              ? "Yatırım Tavsiyesi Değildir. Bu site yapay zeka destekli grafik analiz platformudur." 
              : "Not Investment Advice. This site is an AI-backed graphical analysis platform."}
          </p>
        </div>

      </aside>

      {/* Main Panel Content */}
      <main className="main-content" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        
        {/* Global Top Navbar */}
        <div className="glass-panel navbar-container" style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center", 
          padding: "10px 20px", 
          borderRadius: "var(--border-radius-lg)",
          zIndex: 100
        }}>
          {/* Left side: Terminal Logo / Welcome */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Briefcase style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} />
            <span className="hide-mobile" style={{ fontSize: "16px", fontWeight: "700", display: "flex", alignItems: "center" }}>
              {lang === "tr" ? "Piyasa Terminali" : "Market Terminal"}
            </span>
          </div>
          
          {/* Right side: Language selection & Profile */}
          <div className="navbar-right" style={{ display: "flex", alignItems: "center", gap: "15px" }}>
            {/* Language Selector */}
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
              <option value="en" style={{ background: "#0b0f19" }}>EN</option>
              <option value="tr" style={{ background: "#0b0f19" }}>TR</option>
              <option value="de" style={{ background: "#0b0f19" }}>DE</option>
              <option value="ru" style={{ background: "#0b0f19" }}>RU</option>
              <option value="zh" style={{ background: "#0b0f19" }}>ZH</option>
              <option value="es" style={{ background: "#0b0f19" }}>ES</option>
            </select>
            
            {/* User Profile dropdown/pill */}
            {token && user ? (
              <div style={{ position: "relative" }}>
                <div 
                  onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                  style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    gap: "8px", 
                    background: "rgba(255, 255, 255, 0.03)", 
                    border: "1px solid rgba(255, 255, 255, 0.08)", 
                    borderRadius: "30px", 
                    padding: "4px 12px 4px 4px", 
                    cursor: "pointer",
                    transition: "var(--transition-smooth)"
                  }}
                  className="profile-pill"
                >
                  {user.profile_picture ? (
                    <img 
                      src={user.profile_picture} 
                      alt="Profile"
                      style={{ width: "32px", height: "32px", borderRadius: "50%", objectFit: "cover" }}
                    />
                  ) : (
                    <div style={{ background: "rgba(139, 92, 246, 0.2)", borderRadius: "50%", width: "32px", height: "32px", display: "flex", alignItems: "center", justifyItems: "center" }}>
                      <User style={{ width: "16px", color: "var(--accent-primary)", margin: "auto" }} />
                    </div>
                  )}
                  <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-main)" }}>
                    {user.username}
                  </span>
                  {user.is_premium && (
                    <span style={{ 
                      fontSize: "9px", 
                      background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", 
                      color: "#fff", 
                      padding: "1px 6px", 
                      borderRadius: "10px", 
                      fontWeight: "700"
                    }}>
                      ★ {t("premium_badge")}
                    </span>
                  )}
                </div>
                
                {/* Dropdown Menu */}
                {showProfileDropdown && (
                  <>
                    <div 
                      onClick={() => setShowProfileDropdown(false)} 
                      style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 998 }}
                    />
                    <div style={{ 
                      position: "absolute", 
                      right: 0, 
                      top: "42px", 
                      background: "rgba(17, 24, 39, 0.95)", 
                      border: "1px solid rgba(255, 255, 255, 0.08)", 
                      borderRadius: "var(--border-radius-md)", 
                      width: "220px", 
                      padding: "12px", 
                      boxShadow: "0 10px 25px rgba(0,0,0,0.5)", 
                      display: "flex", 
                      flexDirection: "column", 
                      gap: "8px", 
                      zIndex: 999,
                      backdropFilter: "blur(16px)"
                    }}>
                      {/* Avatar Upload Camera button */}
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px", marginBottom: "4px" }}>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500", textTransform: "uppercase" }}>{t("active_user")}</span>
                        <label 
                          htmlFor="navbar-profile-upload" 
                          style={{ marginLeft: "auto", background: "var(--accent-primary)", borderRadius: "50%", width: "20px", height: "20px", display: "flex", alignItems: "center", justifyItems: "center", cursor: "pointer" }}
                        >
                          <Camera style={{ width: "10px", color: "#fff", margin: "auto" }} />
                        </label>
                        <input 
                          id="navbar-profile-upload" 
                          type="file" 
                          accept="image/*" 
                          onChange={(e) => { handleProfilePictureUpload(e); setShowProfileDropdown(false); }} 
                          style={{ display: "none" }} 
                        />
                      </div>

                      <button 
                        onClick={() => { handlePremiumToggle(); setShowProfileDropdown(false); }} 
                        className="btn-secondary" 
                        style={{ 
                          width: "100%", 
                          justifyContent: "flex-start", 
                          fontSize: "12px",
                          padding: "6px 12px",
                          border: user.is_premium ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid rgba(255, 255, 255, 0.08)",
                          background: user.is_premium ? "rgba(245, 158, 11, 0.05)" : "rgba(255, 255, 255, 0.02)"
                        }}
                      >
                        <span style={{ color: user.is_premium ? "#f59e0b" : "var(--text-muted)", marginRight: "8px", fontWeight: "700" }}>★</span>
                        {user.is_premium ? t("premium_downgrade") : t("premium_upgrade")}
                      </button>

                      {user.email === "arda.demirtas2002@gmail.com" && (
                        <button 
                          onClick={() => {
                            setShowAdminModal(true);
                            fetchAdminData();
                            setShowProfileDropdown(false);
                          }} 
                          className="btn-secondary" 
                          style={{ 
                            width: "100%", 
                            justifyContent: "flex-start",
                            fontSize: "12px",
                            padding: "6px 12px",
                            border: "1px solid rgba(245, 158, 11, 0.4)",
                            background: "rgba(245, 158, 11, 0.08)",
                            color: "#f59e0b",
                            fontWeight: "600"
                          }}
                        >
                          <Shield style={{ width: "12px" }} /> Admin Panel
                        </button>
                      )}

                      <button 
                        onClick={() => { setShowPasswordModal(true); setShowProfileDropdown(false); }} 
                        className="btn-secondary" 
                        style={{ width: "100%", justifyContent: "flex-start", fontSize: "12px", padding: "6px 12px" }}
                      >
                        <Key style={{ width: "12px" }} /> {t("change_password")}
                      </button>

                      <button 
                        onClick={() => { handleDeleteAccount(); setShowProfileDropdown(false); }} 
                        className="btn-danger" 
                        style={{ width: "100%", display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", padding: "6px 12px" }}
                      >
                        <UserMinus style={{ width: "12px" }} /> {t("close_account")}
                      </button>

                      <button 
                        onClick={() => { handleLogout(); setShowProfileDropdown(false); }} 
                        className="btn-secondary" 
                        style={{ width: "100%", justifyContent: "flex-start", fontSize: "12px", padding: "6px 12px", borderTop: "1px solid rgba(255,255,255,0.05)", borderRadius: 0, marginTop: "4px" }}
                      >
                        <LogOut style={{ width: "12px" }} /> {t("sign_out")}
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <button 
                  onClick={() => { setAuthMode("login"); setShowAuthModal(true); }} 
                  className="btn-primary" 
                  style={{ height: "32px", fontSize: "12px", padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "center", gap: "4px" }}
                >
                  <LogIn style={{ width: "14px" }} /> <span className="hide-mobile">{t("sign_in")}</span>
                </button>
                <button 
                  onClick={() => { setAuthMode("register"); setShowAuthModal(true); }} 
                  className="btn-secondary" 
                  style={{ height: "32px", fontSize: "12px", padding: "0 10px", display: "flex", alignItems: "center", justifyContent: "center", gap: "4px" }}
                >
                  <UserPlus style={{ width: "14px" }} /> <span className="hide-mobile">{t("create_account")}</span>
                </button>
              </div>
            )}
          </div>
        </div>
        {showScreener ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px", height: "100%" }}>
            {/* Screener Header */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "15px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                <h2 style={{ fontSize: "20px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                  <PieChart style={{ color: "var(--accent-primary)", width: "22px" }} /> {t("screener_title")}
                </h2>
                <div style={{ position: "relative", width: "100%", maxWidth: "250px" }}>
                  <Search style={{ position: "absolute", left: "10px", top: "10px", color: "var(--text-muted)", width: "14px" }} />
                  <input 
                    type="text"
                    placeholder={lang === "tr" ? "Varlık ara..." : "Search assets..."}
                    className="input-field"
                    value={screenerSearch}
                    onChange={e => setScreenerSearch(e.target.value)}
                    style={{ paddingLeft: "32px", height: "34px", fontSize: "13px" }}
                  />
                </div>
              </div>

              {/* Filtering Controls */}
              <div style={{ 
                display: "flex", 
                background: "rgba(0, 0, 0, 0.25)", 
                padding: "4px", 
                borderRadius: "30px", 
                border: "1px solid rgba(255, 255, 255, 0.05)",
                width: "fit-content",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "4px"
              }}>
                <button 
                  onClick={() => setScreenerFilter("all")} 
                  style={{
                    background: screenerFilter === "all" ? "var(--accent-primary)" : "transparent",
                    color: screenerFilter === "all" ? "#fff" : "var(--text-muted)",
                    border: "none",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "var(--transition-smooth)"
                  }}
                >
                  {t("screener_all")}
                </button>
                <button 
                  onClick={() => setScreenerFilter("bullish")} 
                  style={{
                    background: screenerFilter === "bullish" ? "var(--accent-success)" : "transparent",
                    color: screenerFilter === "bullish" ? "#fff" : "var(--text-muted)",
                    border: "none",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "var(--transition-smooth)"
                  }}
                >
                  {t("screener_bullish")}
                </button>
                <button 
                  onClick={() => setScreenerFilter("bearish")} 
                  style={{
                    background: screenerFilter === "bearish" ? "var(--accent-danger)" : "transparent",
                    color: screenerFilter === "bearish" ? "#fff" : "var(--text-muted)",
                    border: "none",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "var(--transition-smooth)"
                  }}
                >
                  {t("screener_bearish")}
                </button>
                <button 
                  onClick={() => setScreenerFilter("oversold")} 
                  style={{
                    background: screenerFilter === "oversold" ? "rgba(16, 185, 129, 0.2)" : "transparent",
                    color: screenerFilter === "oversold" ? "var(--accent-success)" : "var(--text-muted)",
                    border: "none",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "var(--transition-smooth)",
                    boxShadow: screenerFilter === "oversold" ? "inset 0 0 0 1px rgba(16, 185, 129, 0.4)" : "none"
                  }}
                >
                  {t("screener_oversold")}
                </button>
                <button 
                  onClick={() => setScreenerFilter("overbought")} 
                  style={{
                    background: screenerFilter === "overbought" ? "rgba(239, 68, 68, 0.2)" : "transparent",
                    color: screenerFilter === "overbought" ? "var(--accent-danger)" : "var(--text-muted)",
                    border: "none",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "600",
                    cursor: "pointer",
                    transition: "var(--transition-smooth)",
                    boxShadow: screenerFilter === "overbought" ? "inset 0 0 0 1px rgba(239, 68, 68, 0.4)" : "none"
                  }}
                >
                  {t("screener_overbought")}
                </button>
              </div>

              {/* Asset Type Tabs */}
              <div style={{ display: "flex", gap: "15px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "10px", fontSize: "13px" }}>
                <span 
                  onClick={() => setScreenerType("all")}
                  style={{ cursor: "pointer", fontWeight: "600", color: screenerType === "all" ? "var(--accent-primary)" : "var(--text-muted)" }}
                >
                  {lang === "tr" ? "Hepsi" : "All Types"}
                </span>
                <span 
                  onClick={() => setScreenerType("crypto")}
                  style={{ cursor: "pointer", fontWeight: "600", color: screenerType === "crypto" ? "var(--accent-primary)" : "var(--text-muted)" }}
                >
                  {lang === "tr" ? "Kripto" : "Cryptos"}
                </span>
                <span 
                  onClick={() => setScreenerType("stock")}
                  style={{ cursor: "pointer", fontWeight: "600", color: screenerType === "stock" ? "var(--accent-primary)" : "var(--text-muted)" }}
                >
                  {lang === "tr" ? "Hisseler" : "Stocks"}
                </span>
                <span 
                  onClick={() => setScreenerType("commodity")}
                  style={{ cursor: "pointer", fontWeight: "600", color: screenerType === "commodity" ? "var(--accent-primary)" : "var(--text-muted)" }}
                >
                  {lang === "tr" ? "Emtialar" : "Commodities"}
                </span>
              </div>
            </div>

            {/* Screener Results Table */}
            <div className="glass-panel" style={{ flexGrow: 1, padding: "0", overflow: "hidden", display: "flex", flexDirection: "column" }}>
              {screenerLoading ? (
                <div style={{ display: "flex", flexDirection: "column", padding: "40px", alignItems: "center", justifyContent: "center", gap: "10px", flexGrow: 1 }}>
                  <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)", width: "30px" }} />
                  <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>{t("loading")}</span>
                </div>
              ) : (
                <div style={{ overflowX: "auto", flexGrow: 1 }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13.5px", textAlign: "left" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", color: "var(--text-muted)", fontWeight: "600" }}>
                        <th style={{ padding: "12px 16px" }}>{t("screener_asset")}</th>
                        <th style={{ padding: "12px 16px" }}>{t("screener_price")}</th>
                        <th style={{ padding: "12px 16px" }}>{t("screener_pred_change")}</th>
                        <th style={{ padding: "12px 16px" }}>{t("screener_rsi")}</th>
                        <th style={{ padding: "12px 16px" }}>{t("screener_macd")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        let filtered = screenerData;
                        
                        if (screenerSearch.trim()) {
                          const q = screenerSearch.toLowerCase().trim();
                          filtered = filtered.filter(item => 
                            item.symbol.toLowerCase().includes(q) || 
                            (item.name && item.name.toLowerCase().includes(q))
                          );
                        }

                        if (screenerType === "crypto") {
                          filtered = filtered.filter(item => item.symbol.endsWith("-USD"));
                        } else if (screenerType === "commodity") {
                          filtered = filtered.filter(item => item.symbol.includes("=F"));
                        } else if (screenerType === "stock") {
                          filtered = filtered.filter(item => !item.symbol.endsWith("-USD") && !item.symbol.includes("=F"));
                        }

                        if (screenerFilter === "bullish") {
                          filtered = filtered.filter(item => item.predicted_change >= 0.2);
                        } else if (screenerFilter === "bearish") {
                          filtered = filtered.filter(item => item.predicted_change <= -0.2);
                        } else if (screenerFilter === "oversold") {
                          filtered = filtered.filter(item => item.rsi < 35);
                        } else if (screenerFilter === "overbought") {
                          filtered = filtered.filter(item => item.rsi > 65);
                        }

                        if (filtered.length === 0) {
                          return (
                            <tr>
                              <td colSpan={5} style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontStyle: "italic" }}>
                                {lang === "tr" ? "Eşleşen varlık bulunamadı." : "No matching assets found."}
                              </td>
                            </tr>
                          );
                        }

                        return filtered.map(item => {
                          const isBullish = item.predicted_change >= 0.2;
                          const isBearish = item.predicted_change <= -0.2;
                          
                          let sentimentBadge;
                          if (isBullish) {
                            sentimentBadge = <span style={{ color: "var(--accent-success)", fontWeight: "700" }}>▲ +{item.predicted_change.toFixed(2)}%</span>;
                          } else if (isBearish) {
                            sentimentBadge = <span style={{ color: "var(--accent-danger)", fontWeight: "700" }}>▼ {item.predicted_change.toFixed(2)}%</span>;
                          } else {
                            sentimentBadge = <span style={{ color: "var(--text-muted)" }}>~ {item.predicted_change?.toFixed(2)}%</span>;
                          }

                          let rsiBadge;
                          if (item.rsi < 35) {
                            rsiBadge = <span className="badge badge-success" style={{ padding: "2px 6px" }}>{item.rsi.toFixed(1)} ({t("oversold")})</span>;
                          } else if (item.rsi > 65) {
                            rsiBadge = <span className="badge badge-danger" style={{ padding: "2px 6px" }}>{item.rsi.toFixed(1)} ({t("overbought")})</span>;
                          } else {
                            rsiBadge = <span className="badge badge-warning" style={{ padding: "2px 6px" }}>{item.rsi.toFixed(1)}</span>;
                          }

                          const isMacdBullish = item.macd_signal === "BULLISH";
                          const macdBadge = isMacdBullish 
                            ? <span style={{ color: "var(--accent-success)" }}>▲ {t("macd_status_bullish")}</span> 
                            : <span style={{ color: "var(--accent-danger)" }}>▼ {t("macd_status_bearish")}</span>;

                          return (
                            <tr 
                              key={item.id} 
                              onClick={() => {
                                selectSymbol(item.symbol);
                                setShowScreener(false);
                              }}
                              style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", cursor: "pointer", transition: "background 0.2s" }}
                              className="watchlist-item-row"
                            >
                              <td style={{ padding: "12px 16px" }}>
                                <div style={{ display: "flex", flexDirection: "column" }}>
                                  <strong style={{ color: "var(--text-main)", fontSize: "14px" }}>{item.symbol}</strong>
                                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{item.name}</span>
                                </div>
                              </td>
                              <td style={{ padding: "12px 16px", fontWeight: "600", color: "var(--text-main)" }}>
                                {item.price > 0 ? `$${item.price.toLocaleString()}` : "N/A"}
                              </td>
                              <td style={{ padding: "12px 16px" }}>
                                {sentimentBadge}
                              </td>
                              <td style={{ padding: "12px 16px" }}>
                                {rsiBadge}
                              </td>
                              <td style={{ padding: "12px 16px", fontSize: "12.5px" }}>
                                {macdBadge}
                              </td>
                            </tr>
                          );
                        });
                      })()}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : predictLoading || (!predictionData && !predictError) || (predictionData && predictionData.symbol !== activeSymbol) ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", gap: "24px", padding: "20px" }}>
            <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)", width: "48px", height: "48px" }} />
            
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%", maxWidth: "380px", background: "rgba(255, 255, 255, 0.02)", padding: "20px", borderRadius: "12px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
              {[1, 2, 3, 4, 5, 6].map((s) => {
                const isCompleted = loadingStep > s;
                const isActive = loadingStep === s;
                let statusIcon = "○";
                let textColor = "var(--text-muted)";
                let fontWeight = "normal";

                if (isCompleted) {
                  statusIcon = "✓";
                  textColor = "#10B981";
                } else if (isActive) {
                  statusIcon = "⏳";
                  textColor = "var(--accent-primary)";
                  fontWeight = "600";
                }

                const getStepDesc = (stepIndex) => {
                  const trDesc = [
                    "Geçmiş piyasa verileri çekiliyor...",
                    "Teknik indikatörler hesaplanıyor...",
                    "Yapay zeka modelleri çalıştırılıyor...",
                    "Ensemble konsensüsü hesaplanıyor...",
                    "Haber ve duyarlılık analizi yapılıyor...",
                    "Arayüz bileşenleri yükleniyor..."
                  ];
                  const enDesc = [
                    "Fetching historical market data...",
                    "Calculating technical indicators...",
                    "Running machine learning models...",
                    "Computing ensemble consensus...",
                    "Analyzing news and sentiment...",
                    "Loading interface components..."
                  ];
                  return lang === "tr" ? trDesc[stepIndex - 1] : enDesc[stepIndex - 1];
                };

                return (
                  <div key={s} style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "13.5px", color: textColor, fontWeight: fontWeight, transition: "all 0.2s ease" }}>
                    <span style={{ minWidth: "16px", display: "inline-block", textAlign: "center" }}>{statusIcon}</span>
                    <span>{getStepDesc(s)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : predictError ? (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: "60vh", alignItems: "center", justifyContent: "center", gap: "15px" }}>
            {predictError.toLowerCase().includes("beklemede") || predictError.toLowerCase().includes("pending") ? (
              <>
                <div className="badge badge-warning" style={{ fontSize: "14px", padding: "6px 16px", borderRadius: "20px" }}>
                  ⏳ {lang === "tr" ? "Tahmin Beklemede" : "Prediction Pending"}
                </div>
                <p style={{ textAlign: "center", maxWidth: "450px", color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.6" }}>
                  {predictError}
                </p>
                <button onClick={() => loadPrediction(activeSymbol, chartInterval)} className="btn-primary" style={{ marginTop: "10px" }}>
                  <RefreshCw style={{ width: "14px" }} /> {lang === "tr" ? "Yeniden Sorgula" : "Query Again"}
                </button>
              </>
            ) : (
              <>
                <span style={{ fontSize: "18px", fontWeight: "600", color: "var(--accent-danger)" }}>{t("error_title")}</span>
                <span style={{ textAlign: "center", maxWidth: "400px", color: "var(--accent-danger)" }}>{predictError}</span>
                <button onClick={() => loadPrediction(activeSymbol, chartInterval)} className="btn-secondary" style={{ marginTop: "10px" }}>
                  <RefreshCw style={{ width: "14px" }} /> {t("try_again")}
                </button>
              </>
            )}
          </div>
        ) : (
          <>
            {/* Main Content Header */}
            <div className="glass-panel header-panel">
              <div>
                <h2 className="asset-title">{predictionData ? predictionData.name : activeSymbol}</h2>
                {(() => {
                  const details = getSymbolDetails(activeSymbol);
                  if (!details) return null;
                  return (
                    <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px", marginBottom: "8px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                      <span>📍 <strong>{lang === "tr" ? "Ülke" : "Country"}:</strong> {details.country}</span>
                      <span style={{ width: "4px", height: "4px", borderRadius: "50%", background: "rgba(255,255,255,0.2)" }} />
                      <span>🏛️ <strong>{lang === "tr" ? "Borsa" : "Exchange"}:</strong> {details.exchange}</span>
                      <span style={{ width: "4px", height: "4px", borderRadius: "50%", background: "rgba(255,255,255,0.2)" }} />
                      <span>📈 <strong>{lang === "tr" ? "Piyasa" : "Market"}:</strong> {details.market}</span>
                    </div>
                  );
                })()}
                <div className="header-badges-container">
                  <span style={{ fontSize: "14px", color: "var(--text-muted)", marginRight: "5px" }}>Ticker: {activeSymbol}</span>
                  {predictionData && (
                    <>
                      {getRsiBadge(activeHistory[activeHistory.length - 1]?.rsi)}
                      {getMacdBadge(
                        activeHistory[activeHistory.length - 1]?.macd,
                        activeHistory[activeHistory.length - 1]?.macd_hist
                      )}
                      <span className="badge badge-info">Open: ${activeHistory[activeHistory.length - 1]?.open?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">Close: ${activeHistory[activeHistory.length - 1]?.close?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">High: ${activeHistory[activeHistory.length - 1]?.high?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">Low: ${activeHistory[activeHistory.length - 1]?.low?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">Vol: {activeHistory[activeHistory.length - 1]?.volume?.toLocaleString("en-US")}</span>
                      <span className="badge badge-info">EMA 20: ${activeHistory[activeHistory.length - 1]?.ema_20?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">EMA 50: ${activeHistory[activeHistory.length - 1]?.ema_50?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">BB Upper: ${activeHistory[activeHistory.length - 1]?.bb_upper?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                      <span className="badge badge-info">BB Lower: ${activeHistory[activeHistory.length - 1]?.bb_lower?.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                    </>
                  )}
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                <div className="header-price-panel">
                  <div className="asset-price">
                    ${predictionData && predictionData.current_price !== undefined && predictionData.current_price !== null 
                      ? predictionData.current_price.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 }) 
                      : (predictionData ? predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 }) : "---")}
                  </div>
                  <span style={{ fontSize: "12px", color: "var(--accent-primary)", fontWeight: "600", display: "block" }}>
                    ● {t("live_price")}
                  </span>
                  {predictionData && (
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                      {t("last_close")}: ${predictionData.last_close.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 })} ({predictionData.last_date})
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Dashboard Grid (Charts and Predictions) */}
            <div className="dashboard-grid">
              {/* Column 1: Charts */}
              <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
                {(!user || !user.is_premium) && activeSymbol !== "BTC-USD" && (
                  <div className="glass-panel" style={{
                    padding: "20px",
                    background: "linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(217, 119, 6, 0.03) 100%)",
                    border: "1px solid rgba(245, 158, 11, 0.25)",
                    borderRadius: "var(--border-radius-lg)",
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "20px",
                    flexWrap: "wrap"
                  }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1, minWidth: "280px" }}>
                      <h4 style={{ fontSize: "16px", fontWeight: "700", color: "#f59e0b", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
                        ★ {lang === "tr" ? "Premium Özellikler Kilitli" : "Premium Features Locked"}
                      </h4>
                      <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: 0, lineHeight: "1.5" }}>
                        {lang === "tr" 
                          ? "BTC dışındaki bu sembolde yapay zeka fiyat tahminlerini görmek ve grafikteki otomatik 5'er adet destek/direnç seviyelerini açmak için Premium üyeliğe yükseltin." 
                          : "Upgrade to Premium to view AI machine learning price predictions and access automatic Support & Resistance overlay levels on this asset."}
                      </p>
                    </div>
                    {user ? (
                      <button 
                        onClick={handlePremiumToggle} 
                        className="btn-primary" 
                        style={{ 
                          background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", 
                          borderColor: "#d97706",
                          color: "#fff",
                          fontWeight: "700",
                          padding: "10px 20px",
                          fontSize: "13px",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          whiteSpace: "nowrap"
                        }}
                      >
                        ★ {t("premium_upgrade")}
                      </button>
                    ) : (
                      <button 
                        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
                        className="btn-primary" 
                        style={{ 
                          background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", 
                          borderColor: "#d97706",
                          color: "#fff",
                          fontWeight: "700",
                          padding: "10px 20px",
                          fontSize: "13px",
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                          whiteSpace: "nowrap"
                        }}
                      >
                        🔑 {lang === "tr" ? "Giriş Yap ve Yükselt" : "Login to Upgrade"}
                      </button>
                    )}
                  </div>
                )}

                {/* Price Chart Card */}
                <div 
                  className={isChartFullscreen ? "" : "glass-panel"}
                  style={isChartFullscreen ? {
                    position: "fixed",
                    top: 0,
                    left: 0,
                    width: "100vw",
                    height: "100vh",
                    zIndex: 9999,
                    background: "#090514",
                    padding: "30px",
                    display: "flex",
                    flexDirection: "column",
                    boxSizing: "border-box"
                  } : {}}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                      <h3 style={{ fontSize: "18px", fontWeight: "700", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                        <LineChart style={{ color: "var(--accent-primary)" }} /> {t("chart_title")}
                      </h3>
                      {(() => {
                        const bestModel = getBestModel();
                        if (!bestModel) return null;
                        return (
                          <div style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "4px 10px",
                            background: "rgba(245, 158, 11, 0.08)",
                            border: "1px solid rgba(245, 158, 11, 0.3)",
                            borderRadius: "20px",
                            fontSize: "12px",
                            fontWeight: "700",
                            color: "#f59e0b",
                            boxShadow: "0 0 10px rgba(245, 158, 11, 0.15)"
                          }}>
                            <span>👑</span>
                            <span>
                              {lang === "tr" 
                                ? `En Başarılı Model: ${bestModel.name} (Doğruluk: ${bestModel.da.toFixed(1)}%)`
                                : `Best Model: ${bestModel.name} (Accuracy: ${bestModel.da.toFixed(1)}%)`
                              }
                            </span>
                          </div>
                        );
                      })()}
                    </div>
                    
                    {/* Price Chart Header Actions */}
                    <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                      {/* Candle Count Selector (Slider) */}
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(255, 255, 255, 0.03)", padding: "4px 10px", borderRadius: "var(--border-radius-md)", border: "1px solid rgba(255, 255, 255, 0.06)", height: "30px" }}>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600", whiteSpace: "nowrap" }}>
                          {lang === "tr" ? "Kapanış:" : "Candles:"} <span style={{ color: "var(--accent-primary)", fontFamily: "monospace" }}>{historyLimit}</span>
                        </span>
                        <input
                          type="range"
                          min="180"
                          max="720"
                          step="10"
                          value={historyLimit}
                          onChange={(e) => {
                            const val = parseInt(e.target.value, 10);
                            setHistoryLimit(val);
                            localStorage.setItem("historyLimit", val);
                          }}
                          style={{
                            width: "80px",
                            cursor: "pointer",
                            accentColor: "var(--accent-primary)",
                            verticalAlign: "middle"
                          }}
                        />
                      </div>

                      {/* Chart Type Toggle (Line vs Candle) */}
                      <div style={{ display: "flex", gap: "2px", background: "rgba(255, 255, 255, 0.03)", padding: "2px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                        <button
                          onClick={() => setChartType("line")}
                          className={chartType === "line" ? "btn-primary" : "btn-secondary"}
                          style={{ padding: "4px 8px", fontSize: "11px", height: "auto", border: "none", fontWeight: "600" }}
                        >
                          {lang === "tr" ? "Çizgi" : "Line"}
                        </button>
                        <button
                          onClick={() => setChartType("candle")}
                          className={chartType === "candle" ? "btn-primary" : "btn-secondary"}
                          style={{ padding: "4px 8px", fontSize: "11px", height: "auto", border: "none", fontWeight: "600" }}
                        >
                          {lang === "tr" ? "Mum" : "Candle"}
                        </button>
                      </div>

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

                      {/* Fullscreen Button */}
                      <button
                        onClick={() => setIsChartFullscreen(!isChartFullscreen)}
                        className="btn-secondary"
                        style={{ padding: "8px", height: "32px", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px" }}
                        title={isChartFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                      >
                        {isChartFullscreen ? <Minimize2 style={{ width: "16px", height: "16px" }} /> : <Maximize2 style={{ width: "16px", height: "16px" }} />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="chart-wrapper" style={{ 
                    position: "relative",
                    height: isChartFullscreen ? "calc(100vh - 120px)" : "350px",
                    width: "100%"
                  }}>
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
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "20px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "12px" }}>
                    {t("chart_indicators")}
                  </h3>

                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                    gap: "20px"
                  }}>
                    {/* RSI Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          {lang === "tr" ? "Göreceli Güç Endeksi (RSI)" : "Relative Strength Index (RSI)"}
                        </h4>
                        {(() => {
                          const rsi = activeHistory[activeHistory.length - 1]?.rsi;
                          if (rsi === null || rsi === undefined) return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (rsi >= 70) return <span className="badge badge-danger" style={{ padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_overbought")}</span>;
                          if (rsi <= 30) return <span className="badge badge-success" style={{ padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_oversold")}</span>;
                          return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>{t("rsi_status_neutral")}</span>;
                        })()}
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={rsiChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Fiyat hareketlerinin hızını ve değişimini ölçer. 70 üzeri aşırı alım (düşüş ihtimali), 30 altı aşırı satım (yükseliş ihtimali) anlamına gelir." 
                          : "Measures velocity of price changes. Over 70 signals overbought (potential drop), under 30 signals oversold (potential rise)."}
                      </span>
                    </div>

                    {/* MACD Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          MACD (Trend Göstergesi)
                        </h4>
                        {(() => {
                          const hist = activeHistory[activeHistory.length - 1]?.macd_hist;
                          if (hist === null || hist === undefined) return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (hist > 0) return <span className="badge badge-success" style={{ padding: "2px 6px", fontSize: "10px" }}>{t("macd_status_bullish")}</span>;
                          return <span className="badge badge-danger" style={{ padding: "2px 6px", fontSize: "10px" }}>{t("macd_status_bearish")}</span>;
                        })()}
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={macdChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Kısa ve uzun vadeli hareketli ortalamaların ilişkisini gösterir. Mavi çizgi pembeyi yukarı keserse al, aşağı keserse sat sinyalidir." 
                          : "Shows relationship between short and long term moving averages. Blue line crossing above pink indicates buy, below indicates sell."}
                      </span>
                    </div>

                    {/* Stochastic RSI Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          {lang === "tr" ? "Stokastik RSI" : "Stochastic RSI"}
                        </h4>
                        {(() => {
                          const k = activeHistory[activeHistory.length - 1]?.stoch_k;
                          if (k === null || k === undefined) return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (k >= 80) return <span className="badge badge-danger" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Aşırı Alım" : "Overbought"}</span>;
                          if (k <= 20) return <span className="badge badge-success" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Aşırı Satım" : "Oversold"}</span>;
                          return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Yatay" : "Neutral"}</span>;
                        })()}
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={stochChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Normal RSI'a kıyasla fiyattaki momentum dönüşlerini çok daha hassas gösterir. Sarı (%K) ve mavi (%D) çizgilerin kesişimleri takip edilir." 
                          : "Generates more sensitive momentum signals than standard RSI. Crossovers between yellow (%K) and cyan (%D) lines are key."}
                      </span>
                    </div>

                    {/* ATR Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          {lang === "tr" ? "Ortalama Gerçek Aralık (ATR)" : "Average True Range (ATR)"}
                        </h4>
                        <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>
                          {activeHistory[activeHistory.length - 1]?.atr?.toFixed(3) || "---"}
                        </span>
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={atrChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Belirli bir dönemdeki fiyat dalgalanmasının büyüklüğünü ölçer. ATR yükseldikçe piyasadaki oynaklık (volatilite/risk) artar." 
                          : "Measures market volatility over a specific period. Higher ATR values indicate higher volatility and potential risk."}
                      </span>
                    </div>

                    {/* OBV Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          {lang === "tr" ? "Denge İşlem Hacmi (OBV)" : "On-Balance Volume (OBV)"}
                        </h4>
                        <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>
                          {lang === "tr" ? "Hacim Akışı" : "Volume Flow"}
                        </span>
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={obvChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Fiyat hareketlerini hacim akışıyla teyit eder. Fiyat yatayken OBV'nin yukarı yönelmesi, kurumsal alım/toplama (akümülasyon) işaretidir." 
                          : "Relates price momentum to volume flow. An increasing OBV while price is flat suggests institutional accumulation."}
                      </span>
                    </div>

                    {/* CCI Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          {lang === "tr" ? "Emtia Kanal Endeksi (CCI)" : "Commodity Channel Index (CCI)"}
                        </h4>
                        {(() => {
                          const cci = activeHistory[activeHistory.length - 1]?.cci;
                          if (cci === null || cci === undefined) return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (cci >= 100) return <span className="badge badge-success" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Güçlü Boğa" : "Strong Bullish"}</span>;
                          if (cci <= -100) return <span className="badge badge-danger" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Güçlü Ayı" : "Strong Bearish"}</span>;
                          return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Yatay" : "Neutral"}</span>;
                        })()}
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={cciChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Fiyatın istatistiksel ortalamasından sapmasını ölçer. +100 üzeri yeni bir güçlü yükseliş trendi, -100 altı ise düşüş trendi başlatır." 
                          : "Measures price deviation from its average. Values above +100 signal a strong uptrend, below -100 signal a strong downtrend."}
                      </span>
                    </div>

                    {/* Williams %R Card */}
                    <div className="glass-panel" style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "10px", background: "rgba(0, 0, 0, 0.12)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ fontSize: "13px", fontWeight: "700", color: "#f3e8ff", margin: 0, textTransform: "uppercase" }}>
                          Williams %R
                        </h4>
                        {(() => {
                          const w = activeHistory[activeHistory.length - 1]?.williams_r;
                          if (w === null || w === undefined) return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          if (w >= -20) return <span className="badge badge-danger" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Aşırı Alım" : "Overbought"}</span>;
                          if (w <= -80) return <span className="badge badge-success" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Aşırı Satım" : "Oversold"}</span>;
                          return <span className="badge badge-warning" style={{ padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Yatay" : "Neutral"}</span>;
                        })()}
                      </div>
                      <div className="indicator-wrapper" style={{ height: "140px", position: "relative" }}>
                        <canvas ref={williamsChartRef} />
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
                        {lang === "tr" 
                          ? "Kapanış fiyatını son tepe ve dip seviyelerine göre karşılaştırır. 0 ile -20 arası aşırı alım, -80 ile -100 arası aşırı satımdır." 
                          : "Compares close price relative to the highest high and lowest low. Range 0 to -20 is overbought, -80 to -100 is oversold."}
                      </span>
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

                      {/* Volume Info Card */}
                      <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{lang === "tr" ? "Hacim" : "Volume"}</span>
                        <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                          {activeHistory[activeHistory.length - 1]?.volume?.toLocaleString("en-US") || "---"}
                        </span>
                        {(() => {
                          const history = activeHistory;
                          if (!history || history.length < 20) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          const lastVol = history[history.length - 1]?.volume;
                          const last20 = history.slice(-20);
                          const avgVol = last20.reduce((sum, item) => sum + (item.volume || 0), 0) / 20;
                          if (!lastVol || !avgVol) return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>N/A</span>;
                          
                          if (lastVol > avgVol * 1.5) {
                            return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Yüksek Hacim" : "High Volume"}</span>;
                          } else if (lastVol < avgVol * 0.5) {
                            return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Düşük Hacim" : "Low Volume"}</span>;
                          }
                          return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Normal Hacim" : "Normal Volume"}</span>;
                        })()}
                      </div>

                      {(() => {
                        const canShowSR = (activeSymbol === "BTC-USD") || (user && user.is_premium);
                        if (canShowSR) {
                          const { supports, resistances } = calculateSupportResistance(activeHistory);
                          return (
                            <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)", border: "1px solid rgba(139, 92, 246, 0.15)" }}>
                              <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{t("support")} / {t("resistance")}</span>
                              <div style={{ display: "flex", flexDirection: "column", gap: "2px", fontSize: "12px", fontFamily: "monospace" }}>
                                <span style={{ color: "#10b981", fontWeight: "700" }}>
                                  S: {supports.map(s => s.toLocaleString(undefined, { maximumFractionDigits: 1 })).join(" | ")}
                                </span>
                                <span style={{ color: "#ef4848", fontWeight: "700" }}>
                                  R: {resistances.map(r => r.toLocaleString(undefined, { maximumFractionDigits: 1 })).join(" | ")}
                                </span>
                              </div>
                              <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px", color: "#f59e0b", borderColor: "rgba(245, 158, 11, 0.3)", background: "rgba(245, 158, 11, 0.05)" }}>
                                Swing High/Low
                              </span>
                            </div>
                          );
                        } else {
                          return (
                            <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)", border: "1px solid rgba(255, 255, 255, 0.05)", opacity: 0.7 }}>
                              <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{t("support")} / {t("resistance")}</span>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--text-muted)", fontWeight: "600", marginTop: "4px" }}>
                                <span>🔒</span>
                                <span style={{ color: "#f59e0b", background: "rgba(245, 158, 11, 0.1)", padding: "1px 6px", borderRadius: "10px", fontSize: "9px" }}>
                                  ★ {t("premium_badge")}
                                </span>
                              </div>
                            </div>
                          );
                        }
                      })()}
                    </div>
                  </div>

                  {/* Market Info Panel */}
                  {marketInfo && (
                    <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                      <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                        📊 {lang === "tr" ? "Piyasa Bilgileri" : "Market Data"}
                        {marketInfo.exchange_name && (
                          <span style={{ fontSize: "11px", fontWeight: "500", color: "var(--text-muted)", marginLeft: "4px" }}>
                            — {marketInfo.exchange_name}
                          </span>
                        )}
                      </h4>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "12px" }}>

                        {/* Today's Volume */}
                        <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                          <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{lang === "tr" ? "Günlük Hacim" : "Today's Volume"}</span>
                          <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                            {(() => {
                              const v = marketInfo.regular_market_volume;
                              if (!v) return "---";
                              if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
                              if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
                              if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
                              return v.toLocaleString();
                            })()}
                          </span>
                          <span className="badge badge-info" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>
                            {marketInfo.currency || "USD"}
                          </span>
                        </div>

                        {/* 20-Day Avg Volume */}
                        <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                          <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{lang === "tr" ? "Ort. Hacim (20G)" : "Avg Volume (20D)"}</span>
                          <span style={{ fontSize: "14px", fontWeight: "700", fontFamily: "monospace" }}>
                            {(() => {
                              const v = marketInfo.average_volume;
                              if (!v) return "---";
                              if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
                              if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
                              if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
                              return v.toLocaleString();
                            })()}
                          </span>
                          {(() => {
                            const cur = marketInfo.regular_market_volume;
                            const avg = marketInfo.average_volume;
                            if (!cur || !avg) return null;
                            if (cur > avg * 1.5) return <span className="badge badge-success" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "▲ Yüksek" : "▲ High"}</span>;
                            if (cur < avg * 0.5) return <span className="badge badge-danger" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "▼ Düşük" : "▼ Low"}</span>;
                            return <span className="badge badge-warning" style={{ alignSelf: "flex-start", padding: "2px 6px", fontSize: "10px" }}>{lang === "tr" ? "Normal" : "Normal"}</span>;
                          })()}
                        </div>

                        {/* 52-Week Range */}
                        {(marketInfo.fifty_two_week_high || marketInfo.fifty_two_week_low) && (
                          <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                            <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{lang === "tr" ? "52 Hafta Aralığı" : "52-Week Range"}</span>
                            <span style={{ fontSize: "12px", fontWeight: "700", fontFamily: "monospace", color: "#10b981" }}>
                              ▲ {marketInfo.fifty_two_week_high?.toLocaleString("en-US", { maximumFractionDigits: 3 }) || "---"}
                            </span>
                            <span style={{ fontSize: "12px", fontWeight: "700", fontFamily: "monospace", color: "#ef4444" }}>
                              ▼ {marketInfo.fifty_two_week_low?.toLocaleString("en-US", { maximumFractionDigits: 3 }) || "---"}
                            </span>
                          </div>
                        )}

                        {/* Today's Range */}
                        {(marketInfo.day_high || marketInfo.day_low) && (
                          <div className="glass-panel" style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "4px", background: "rgba(0,0,0,0.15)" }}>
                            <span style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>{lang === "tr" ? "Günlük Aralık" : "Day Range"}</span>
                            <span style={{ fontSize: "12px", fontWeight: "700", fontFamily: "monospace", color: "#10b981" }}>
                              H: {marketInfo.day_high?.toLocaleString("en-US", { maximumFractionDigits: 3 }) || "---"}
                            </span>
                            <span style={{ fontSize: "12px", fontWeight: "700", fontFamily: "monospace", color: "#ef4444" }}>
                              L: {marketInfo.day_low?.toLocaleString("en-US", { maximumFractionDigits: 3 }) || "---"}
                            </span>
                          </div>
                        )}

                      </div>
                    </div>
                  )}
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
                <div className="glass-panel prediction-card" style={{ minHeight: "220px", display: "flex", flexDirection: "column", justifyContent: "flex-start", position: "relative", overflow: "hidden", padding: "20px" }}>


                  {predictLoading ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, minHeight: "120px" }}>
                      <div className="spinner" style={{ marginBottom: "10px" }}></div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        {lang === "tr" ? "Tahmin hesaplanıyor..." : "Calculating prediction..."}
                      </span>
                    </div>
                  ) : predictionData && predictionData.prediction_status === "pending_data" ? (
                    <div style={{ textAlign: "center", padding: "15px" }}>
                      <span style={{ fontSize: "28px", display: "block", marginBottom: "8px" }}>⏳</span>
                      <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#f59e0b", marginBottom: "6px" }}>
                        {lang === "tr" ? "Tahmin Beklemede" : "Prediction Pending"}
                      </h4>
                      <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "0 0 12px 0", lineHeight: "1.5" }}>
                        {predictionData.prediction_error || (lang === "tr" ? "En son günlük mum verisi bekleniyor." : "Waiting for the latest daily candle data.")}
                      </p>
                      <button onClick={() => loadPrediction(activeSymbol, chartInterval)} className="btn-secondary" style={{ fontSize: "11px", height: "30px", padding: "0 15px", marginTop: "5px" }}>
                        <RefreshCw style={{ width: "10px", marginRight: "5px" }} /> {lang === "tr" ? "Yeniden Sorgula" : "Query Again"}
                      </button>
                    </div>
                  ) : predictionData && predictionData.predicted_close === null ? (() => {
                    const hasAccess = (activeSymbol === "BTC-USD") || (user && user.is_premium);
                    if (hasAccess) {
                      return (
                        <div style={{ textAlign: "center", padding: "20px 10px" }}>
                          <span style={{ fontSize: "28px", display: "block", marginBottom: "10px", animation: "spin 3s linear infinite" }}>⚙️</span>
                          <h4 style={{ fontSize: "14px", fontWeight: "700", color: "var(--accent-primary)", marginBottom: "6px" }}>
                            {lang === "tr" ? "Modeller Eğitiliyor..." : "Models Training..."}
                          </h4>
                          <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "0 0 12px 0", lineHeight: "1.4" }}>
                            {lang === "tr" 
                              ? "Yapay zeka modelleri arka planda eğitilmektedir. Sıra bu hisseye ulaştığında tahminler aktif olacaktır." 
                              : "AI models are currently training in the background. Predictions will be live once the queue reaches this asset."}
                          </p>
                          <button onClick={() => loadPrediction(activeSymbol, chartInterval)} className="btn-secondary" style={{ fontSize: "11px", height: "30px", padding: "0 15px" }}>
                            <RefreshCw style={{ width: "10px", marginRight: "5px" }} /> {lang === "tr" ? "Yeniden Sorgula" : "Query Again"}
                          </button>
                        </div>
                      );
                    }
                    return (
                      <div style={{ textAlign: "center", padding: "10px" }}>
                        <span style={{ fontSize: "28px", display: "block", marginBottom: "8px" }}>🔒</span>
                        <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#f59e0b", marginBottom: "6px" }}>
                          ★ {t("premium_badge")} {t("expected_close")}
                        </h4>
                        <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "0 0 12px 0", lineHeight: "1.4" }}>
                          {t("premium_only_msg")}
                        </p>
                        <button onClick={handlePremiumToggle} className="btn-primary" style={{ fontSize: "11px", height: "30px", padding: "0 15px", background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", border: "none" }}>
                          ★ {t("premium_upgrade")}
                        </button>
                      </div>
                    );
                  })() : (
                    <>
                      <span className="prediction-label" style={{ marginBottom: "12px", display: "block" }}>
                        {lang === "tr" ? "Model Tahmin Fiyatları" : "Model Prediction Prices"}
                      </span>
                      
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%", marginBottom: "15px" }}>
                        {/* Analyzeio (Ensemble) Box */}
                        <div style={{ 
                          padding: "10px 14px", 
                          background: "rgba(16, 185, 129, 0.06)", 
                          border: "1px solid rgba(16, 185, 129, 0.25)", 
                          borderRadius: "var(--border-radius-md)",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center"
                        }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 8px #10b981" }}></span>
                            <span style={{ fontSize: "13px", fontWeight: "700", color: "#a7f3d0" }}>Analyzeio (Ensemble)</span>
                          </div>
                          {predictionData && predictionData.analyzeio_predicted_close !== null ? (() => {
                            const prob = predictionData.analyzeio_predicted_close;
                            const isBullish = prob >= 0.5;
                            const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                            const label = lang === "tr" ? "Olasılık" : "Probability";
                            return (
                              <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                              </span>
                            );
                          })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                        </div>

                        {/* XGBoost Box */}
                        <div style={getBoxStyle("xgboost", "rgba(168, 85, 247, 0.04)", "1px solid rgba(168, 85, 247, 0.15)")}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#a855f7", boxShadow: "0 0 8px #a855f7" }}></span>
                            <span style={{ fontSize: "13px", fontWeight: "600", color: "#f3e8ff" }}>
                              XGBoost
                              {getBestModel()?.key === "xgboost" && (
                                <span style={{
                                  marginLeft: "6px",
                                  padding: "2px 6px",
                                  background: "#f59e0b",
                                  color: "#000",
                                  borderRadius: "10px",
                                  fontSize: "9px",
                                  fontWeight: "900",
                                  textTransform: "uppercase"
                                }}>
                                  {lang === "tr" ? "👑 EN BAŞARILI" : "👑 BEST MODEL"}
                                </span>
                              )}
                            </span>
                          </div>
                          {predictionData && predictionData.xgb_predicted_close !== null ? (() => {
                            const prob = predictionData.xgb_predicted_close;
                            const isBullish = prob >= 0.5;
                            const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                            const label = lang === "tr" ? "Olasılık" : "Probability";
                            return (
                              <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                              </span>
                            );
                          })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                        </div>

                        {/* LSTM Box */}
                        <div style={getBoxStyle("lstm", "rgba(14, 165, 233, 0.04)", "1px solid rgba(14, 165, 233, 0.15)")}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#0ea5e9", boxShadow: "0 0 8px #0ea5e9" }}></span>
                            <span style={{ fontSize: "13px", fontWeight: "600", color: "#e0f2fe" }}>
                              LSTM
                              {getBestModel()?.key === "lstm" && (
                                <span style={{
                                  marginLeft: "6px",
                                  padding: "2px 6px",
                                  background: "#f59e0b",
                                  color: "#000",
                                  borderRadius: "10px",
                                  fontSize: "9px",
                                  fontWeight: "900",
                                  textTransform: "uppercase"
                                }}>
                                  {lang === "tr" ? "👑 EN BAŞARILI" : "👑 BEST MODEL"}
                                </span>
                              )}
                            </span>
                          </div>
                          {predictionData && predictionData.lstm_predicted_close !== null ? (() => {
                            const prob = predictionData.lstm_predicted_close;
                            const isBullish = prob >= 0.5;
                            const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                            const label = lang === "tr" ? "Olasılık" : "Probability";
                            return (
                              <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                              </span>
                            );
                          })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                        </div>

                        {/* Linear Regression Box */}
                        <div style={getBoxStyle("linear_regression", "rgba(59, 130, 246, 0.04)", "1px solid rgba(59, 130, 246, 0.15)")}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#3b82f6", boxShadow: "0 0 8px #3b82f6" }}></span>
                            <span style={{ fontSize: "13px", fontWeight: "600", color: "#dbeafe" }}>
                              {lang === "tr" ? "Lineer Regresyon" : "Linear Regression"}
                              {getBestModel()?.key === "linear_regression" && (
                                <span style={{
                                  marginLeft: "6px",
                                  padding: "2px 6px",
                                  background: "#f59e0b",
                                  color: "#000",
                                  borderRadius: "10px",
                                  fontSize: "9px",
                                  fontWeight: "900",
                                  textTransform: "uppercase"
                                }}>
                                  {lang === "tr" ? "👑 EN BAŞARILI" : "👑 BEST MODEL"}
                                </span>
                              )}
                            </span>
                          </div>
                          {predictionData && predictionData.lr_predicted_close !== null ? (() => {
                            const prob = predictionData.lr_predicted_close;
                            const isBullish = prob >= 0.5;
                            const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                            const label = lang === "tr" ? "Olasılık" : "Probability";
                            return (
                              <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                              </span>
                            );
                          })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                        </div>

                        {/* PatchTST Box (Visible for all symbols) */}
                        {true && (
                          <div style={getBoxStyle("patchtst", "rgba(245, 158, 11, 0.04)", "1px solid rgba(245, 158, 11, 0.2)")}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b", boxShadow: "0 0 8px #f59e0b" }}></span>
                              <span style={{ fontSize: "13px", fontWeight: "600", color: "#fef3c7" }}>
                                PatchTST
                                {getBestModel()?.key === "patchtst" && (
                                  <span style={{
                                    marginLeft: "6px",
                                    padding: "2px 6px",
                                    background: "#f59e0b",
                                    color: "#000",
                                    borderRadius: "10px",
                                    fontSize: "9px",
                                    fontWeight: "900",
                                    textTransform: "uppercase"
                                  }}>
                                    {lang === "tr" ? "👑 EN BAŞARILI" : "👑 BEST MODEL"}
                                  </span>
                                )}
                              </span>
                            </div>
                            {predictionData && predictionData.patchtst_predicted_close !== null ? (() => {
                              const prob = predictionData.patchtst_predicted_close;
                              const isBullish = prob >= 0.5;
                              const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                              const label = lang === "tr" ? "Olasılık" : "Probability";
                              return (
                                <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                  {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                                </span>
                              );
                            })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                          </div>
                        )}

                        {/* Support/Resistance Box */}
                        {true && (
                          <div style={getBoxStyle("support_resistance", "rgba(20, 184, 166, 0.04)", "1px solid rgba(20, 184, 166, 0.2)")}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#14b8a6", boxShadow: "0 0 8px #14b8a6" }}></span>
                              <span style={{ fontSize: "13px", fontWeight: "600", color: "#ccfbf1" }}>
                                {lang === "tr" ? "Destek/Direnç" : "Support/Resistance"}
                                {getBestModel()?.key === "support_resistance" && (
                                  <span style={{
                                    marginLeft: "6px",
                                    padding: "2px 6px",
                                    background: "#f59e0b",
                                    color: "#000",
                                    borderRadius: "10px",
                                    fontSize: "9px",
                                    fontWeight: "900",
                                    textTransform: "uppercase"
                                  }}>
                                    {lang === "tr" ? "👑 EN BAŞARILI" : "👑 BEST MODEL"}
                                  </span>
                                )}
                              </span>
                            </div>
                            {predictionData && predictionData.sr_predicted_close !== null && predictionData.sr_predicted_close !== undefined ? (() => {
                              const prob = predictionData.sr_predicted_close;
                              const isBullish = prob >= 0.5;
                              const conf = isBullish ? prob * 100 : (1 - prob) * 100;
                              const label = lang === "tr" ? "Olasılık" : "Probability";
                              return (
                                <span style={{ fontSize: "14px", fontWeight: "800", color: isBullish ? "#10b981" : "#ef4444" }}>
                                  {isBullish ? "▲" : "▼"} {isBullish ? "BULLISH" : "BEARISH"} ({label}: {conf.toFixed(1)}%)
                                </span>
                              );
                            })() : <span style={{ fontSize: "16px", fontWeight: "800", color: "var(--text-muted)" }}>---</span>}
                          </div>
                        )}
                      </div>

                      <div style={{ fontSize: "12px", color: "var(--text-muted)", textAlign: "center", width: "100%" }}>
                        {t("expected_close")}: {predictionData ? predictionData.expected_close_time : "---"}
                      </div>
                      
                      {predictionData && (
                        <div style={{ marginTop: "18px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "14px", display: "flex", flexDirection: "column", gap: "8px" }}>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "500", textTransform: "uppercase", marginBottom: "4px", display: "block" }}>
                            {lang === "tr" ? "Model Sinyalleri & Getiri Oranları" : "Model Signals & Expected Changes"}:
                          </span>

                          {/* Analyzeio Signal */}
                          {predictionData && predictionData.analyzeio_predicted_close !== null && (() => {
                            const changeVal = (predictionData.analyzeio_predicted_close - 0.5) * 100;
                            const isBullish = changeVal >= 0;
                            const confidence = isBullish ? (changeVal + 50) : (50 - changeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#10b981" }}></span>
                                  Analyzeio:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}

                          {/* XGBoost Signal */}
                          {xgbChangeVal !== null && (() => {
                            const isBullish = xgbChangeVal >= 0;
                            const confidence = isBullish ? (xgbChangeVal + 50) : (50 - xgbChangeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#a855f7" }}></span>
                                  XGBoost:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}

                          {/* LSTM Signal */}
                          {lstmChangeVal !== null && (() => {
                            const isBullish = lstmChangeVal >= 0;
                            const confidence = isBullish ? (lstmChangeVal + 50) : (50 - lstmChangeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#0ea5e9" }}></span>
                                  LSTM:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}

                          {/* Linear Regression Signal */}
                          {lrChangeVal !== null && (() => {
                            const isBullish = lrChangeVal >= 0;
                            const confidence = isBullish ? (lrChangeVal + 50) : (50 - lrChangeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#3b82f6" }}></span>
                                  {lang === "tr" ? "Lineer Reg." : "Linear Reg."}:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}

                          {/* PatchTST Signal */}
                          {predictionData && predictionData.patchtst_predicted_close !== null && (() => {
                            const changeVal = (predictionData.patchtst_predicted_close - 0.5) * 100;
                            const isBullish = changeVal >= 0;
                            const confidence = isBullish ? (changeVal + 50) : (50 - changeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#f59e0b" }}></span>
                                  PatchTST:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}

                          {/* Support/Resistance Signal */}
                          {srChangeVal !== null && (() => {
                            const isBullish = srChangeVal >= 0;
                            const confidence = isBullish ? (srChangeVal + 50) : (50 - srChangeVal);
                            return (
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                                <span style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
                                  <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#14b8a6" }}></span>
                                  {lang === "tr" ? "Destek/Direnç" : "Support/Resistance"}:
                                </span>
                                <div style={{ display: "flex", alignItems: "center", gap: "4px", fontWeight: "700" }}>
                                  {isBullish ? (
                                    <>
                                      <TrendingUp style={{ color: "var(--accent-success)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-success)" }}>{confidence.toFixed(1)}% ({t("bullish")})</span>
                                    </>
                                  ) : (
                                    <>
                                      <TrendingDown style={{ color: "var(--accent-danger)", width: "14px", height: "14px" }} />
                                      <span style={{ color: "var(--accent-danger)" }}>{confidence.toFixed(1)}% ({t("bearish")})</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      )}
                      

                    </>
                  )}
                </div>

                {/* All-Bullish Consensus Card */}
                <div className="glass-panel" style={{ display: "flex", flexDirection: "column", padding: "20px" }}>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <TrendingUp style={{ color: "var(--accent-success)", width: "18px", height: "18px" }} />
                    {lang === "tr" ? "Boğa Konsensüsü (5/5) Varlıklar" : "All-Bullish Consensus Assets"}
                  </h3>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "0 0 15px 0", lineHeight: "1.4" }}>
                    {lang === "tr" 
                      ? "Tüm 5 yapay zeka modelinin (XGBoost, LSTM, LR, PatchTST, S&R) yükseliş yönlü (>=%50 olasılık) tahmin ürettiği varlıklar." 
                      : "Assets where all 5 AI models (XGBoost, LSTM, LR, PatchTST, S&R) predict bullish direction (>=50% probability)."}
                  </p>
                  
                  {screenerLoading ? (
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "10px 0" }}>
                      <div className="spinner" style={{ width: "16px", height: "16px", marginRight: "8px" }}></div>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                        {lang === "tr" ? "Yükleniyor..." : "Loading..."}
                      </span>
                    </div>
                  ) : (() => {
                    const allBullish = screenerData.filter(item => {
                      return item.xgb_pred !== null && item.xgb_pred !== undefined && item.xgb_pred >= 0.5 &&
                             item.lstm_pred !== null && item.lstm_pred !== undefined && item.lstm_pred >= 0.5 &&
                             item.lr_pred !== null && item.lr_pred !== undefined && item.lr_pred >= 0.5 &&
                             item.patchtst_pred !== null && item.patchtst_pred !== undefined && item.patchtst_pred >= 0.5 &&
                             item.sr_pred !== null && item.sr_pred !== undefined && item.sr_pred >= 0.5;
                    });
                    
                    if (allBullish.length === 0) {
                      return (
                        <div style={{ padding: "10px 0", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                          {lang === "tr" ? "Şu anda 5/5 boğa konsensüsüne sahip varlık bulunmuyor." : "No assets currently have a 5/5 bullish consensus."}
                        </div>
                      );
                    }
                    
                    return (
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "325px", overflowY: "auto", paddingRight: "4px" }}>
                        {allBullish.map(item => {
                          const avgProb = ((item.xgb_pred + item.lstm_pred + item.lr_pred + item.patchtst_pred + item.sr_pred) / 5.0) * 100;
                          return (
                            <div 
                              key={item.id}
                              onClick={() => selectSymbol(item.symbol)}
                              style={{ 
                                display: "flex", 
                                justifyContent: "space-between", 
                                alignItems: "center", 
                                padding: "10px 14px", 
                                background: "rgba(20, 184, 166, 0.04)", 
                                border: "1px solid rgba(20, 184, 166, 0.15)",
                                borderRadius: "var(--border-radius-md)",
                                cursor: "pointer",
                                transition: "all 0.2s"
                              }}
                              className="all-bullish-item"
                            >
                              <div style={{ display: "flex", flexDirection: "column" }}>
                                <span style={{ fontWeight: "700", color: "#ccfbf1", fontSize: "14px" }}>{item.symbol}</span>
                                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{item.name || item.symbol}</span>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                                  {lang === "tr" ? "Ort. Olasılık" : "Avg Prob"}:
                                </span>
                                <span style={{ fontSize: "13px", fontWeight: "800", color: "#10b981" }}>
                                  ▲ {avgProb.toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
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

                {/* News Sentiment Analysis Card */}
                <div className="glass-panel" style={{ marginTop: "10px" }}>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <MessageSquare style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} /> {t("news_sentiment")}
                  </h3>
                  
                  {newsLoading ? (
                    <div style={{ display: "flex", justifyContent: "center", padding: "20px" }}>
                      <RefreshCw className="animate-spin" style={{ color: "var(--accent-primary)" }} />
                    </div>
                  ) : !newsData ? (
                    <div style={{ fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center" }}>{t("no_news")}</div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
                      {/* Sentiment Meter */}
                      <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "14px", borderRadius: "var(--border-radius-md)", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px" }}>
                          <span>{t("news_gauge")}</span>
                          <span style={{ fontWeight: "700", color: newsData.sentiment_class === "BULLISH" ? "var(--accent-success)" : newsData.sentiment_class === "BEARISH" ? "var(--accent-danger)" : "var(--text-muted)" }}>
                            {t(`rating_${newsData.sentiment_class.toLowerCase()}`)} ({newsData.sentiment_score.toFixed(2)})
                          </span>
                        </div>
                        {/* Meter Bar */}
                        <div style={{ height: "6px", width: "100%", background: "rgba(255, 255, 255, 0.1)", borderRadius: "3px", overflow: "hidden", position: "relative" }}>
                          <div 
                            style={{ 
                              height: "100%", 
                              width: `${((newsData.sentiment_score + 1) / 2) * 100}%`, 
                              background: newsData.sentiment_class === "BULLISH" ? "var(--accent-success)" : newsData.sentiment_class === "BEARISH" ? "var(--accent-danger)" : "var(--accent-warning)", 
                              borderRadius: "3px",
                              transition: "width 0.5s ease-in-out" 
                            }} 
                          />
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "9px", color: "var(--text-muted)", marginTop: "4px" }}>
                          <span>{t("rating_bearish")} (-1.0)</span>
                          <span>{t("rating_neutral")} (0.0)</span>
                          <span>{t("rating_bullish")} (+1.0)</span>
                        </div>
                      </div>

                      {/* Articles list */}
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {newsData.articles.length === 0 ? (
                          <div style={{ fontSize: "12px", color: "var(--text-muted)", fontStyle: "italic", textAlign: "center" }}>{t("no_news")}</div>
                        ) : (
                          newsData.articles.map((art, idx) => {
                            const formatRelativeTime = (epochSec) => {
                              if (!epochSec) return "";
                              const now = Math.floor(Date.now() / 1000);
                              const diff = now - epochSec;
                              if (diff < 60) return lang === "tr" ? "şimdi" : "just now";
                              const mins = Math.floor(diff / 60);
                              if (mins < 60) return lang === "tr" ? `${mins} dk önce` : `${mins}m ago`;
                              const hours = Math.floor(mins / 60);
                              if (hours < 24) return lang === "tr" ? `${hours} saat önce` : `${hours}h ago`;
                              const days = Math.floor(hours / 24);
                              return lang === "tr" ? `${days} gün önce` : `${days}d ago`;
                            };

                            return (
                              <a 
                                key={idx}
                                href={art.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="watchlist-item"
                                style={{ textDecoration: "none", color: "inherit", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "6px", padding: "10px 14px", margin: 0 }}
                              >
                                <span style={{ fontSize: "13px", fontWeight: "600", color: "#fff", lineHeight: "1.4", textAlign: "left" }}>{art.title}</span>
                                <div style={{ display: "flex", width: "100%", justifyContent: "space-between", alignItems: "center" }}>
                                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{art.publisher} • {formatRelativeTime(art.time)}</span>
                                  <span 
                                    className={`badge ${art.rating === "BULLISH" ? "badge-success" : art.rating === "BEARISH" ? "badge-danger" : "badge-warning"}`} 
                                    style={{ fontSize: "9px", padding: "2px 6px" }}
                                  >
                                    {t(`rating_${art.rating.toLowerCase()}`)} ({art.score > 0 ? `+${art.score.toFixed(1)}` : art.score.toFixed(1)})
                                  </span>
                                </div>
                              </a>
                            );
                          })
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Model Information & Metrics (Comparison Table) */}
                <div className="glass-panel">
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
                    <LineChart style={{ color: "var(--accent-primary)", width: "18px", height: "18px" }} />
                    {lang === "tr" ? "Model Analitiği & Karşılaştırma" : "Model Analytics & Comparison"}
                  </h3>
                  
                  <div style={{ overflowX: "auto", marginTop: "15px" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", color: "var(--text-muted)" }}>
                          <th style={{ padding: "8px 4px", fontWeight: "600" }}>{lang === "tr" ? "Model" : "Model"}</th>
                          <th style={{ padding: "8px 4px", fontWeight: "600", textAlign: "right" }}>{lang === "tr" ? "Yön" : "Direction"}</th>
                          <th style={{ padding: "8px 4px", fontWeight: "600", textAlign: "right" }}>{lang === "tr" ? "Olasılık" : "Probability"}</th>
                          <th style={{ padding: "8px 4px", fontWeight: "600", textAlign: "right" }}>Log-Loss</th>
                          <th style={{ padding: "8px 4px", fontWeight: "600", textAlign: "right" }}>{lang === "tr" ? "Yönsel İsabet" : "Dir. Accuracy"}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* Analyzeio row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(16, 185, 129, 0.03)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 6px #10b981" }}></span>
                            <span style={{ fontWeight: "700", color: "#a7f3d0" }}>Analyzeio</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.analyzeio_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.analyzeio_predicted_close !== null
                              ? (predictionData.analyzeio_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.analyzeio_predicted_close !== null
                              ? `${(predictionData.analyzeio_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.analyzeio_metrics && predictionData.analyzeio_metrics.logloss !== undefined && predictionData.analyzeio_metrics.logloss !== null ? predictionData.analyzeio_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.analyzeio_metrics && predictionData.analyzeio_metrics.directional_accuracy !== null ? `${predictionData.analyzeio_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>

                        {/* XGBoost row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#a855f7" }}></span>
                            <span style={{ fontWeight: "600", color: "#f3e8ff" }}>XGBoost</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.xgb_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.xgb_predicted_close !== null
                              ? (predictionData.xgb_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.xgb_predicted_close !== null
                              ? `${(predictionData.xgb_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.xgb_metrics && predictionData.xgb_metrics.logloss !== undefined && predictionData.xgb_metrics.logloss !== null ? predictionData.xgb_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.xgb_metrics && predictionData.xgb_metrics.directional_accuracy !== null ? `${predictionData.xgb_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>

                        {/* LSTM row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#0ea5e9" }}></span>
                            <span style={{ fontWeight: "600", color: "#e0f2fe" }}>LSTM</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.lstm_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.lstm_predicted_close !== null
                              ? (predictionData.lstm_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.lstm_predicted_close !== null
                              ? `${(predictionData.lstm_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.lstm_metrics && predictionData.lstm_metrics.logloss !== undefined && predictionData.lstm_metrics.logloss !== null ? predictionData.lstm_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.lstm_metrics && predictionData.lstm_metrics.directional_accuracy !== null ? `${predictionData.lstm_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>

                        {/* Linear Regression row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#3b82f6" }}></span>
                            <span style={{ fontWeight: "600", color: "#dbeafe" }}>{lang === "tr" ? "Lineer Reg." : "Linear Reg."}</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.lr_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.lr_predicted_close !== null
                              ? (predictionData.lr_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.lr_predicted_close !== null
                              ? `${(predictionData.lr_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.lr_metrics && predictionData.lr_metrics.logloss !== undefined && predictionData.lr_metrics.logloss !== null ? predictionData.lr_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.lr_metrics && predictionData.lr_metrics.directional_accuracy !== null ? `${predictionData.lr_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>

                        {/* PatchTST row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#f59e0b" }}></span>
                            <span style={{ fontWeight: "600", color: "#fef3c7" }}>PatchTST</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.patchtst_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.patchtst_predicted_close !== null
                              ? (predictionData.patchtst_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.patchtst_predicted_close !== null
                              ? `${(predictionData.patchtst_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>


                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.patchtst_metrics && predictionData.patchtst_metrics.logloss !== undefined && predictionData.patchtst_metrics.logloss !== null ? predictionData.patchtst_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.patchtst_metrics && predictionData.patchtst_metrics.directional_accuracy !== null ? `${predictionData.patchtst_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>

                        {/* Support/Resistance row */}
                        <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "10px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#14b8a6" }}></span>
                            <span style={{ fontWeight: "600", color: "#ccfbf1" }}>{lang === "tr" ? "Destek/Direnç" : "Support/Resistance"}</span>
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "700", color: predictionData && predictionData.sr_predicted_close >= 0.5 ? "var(--accent-success)" : "var(--accent-danger)" }}>
                            {predictionData && predictionData.sr_predicted_close !== null && predictionData.sr_predicted_close !== undefined
                              ? (predictionData.sr_predicted_close >= 0.5 ? "▲ BULLISH" : "▼ BEARISH")
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text)" }}>
                            {predictionData && predictionData.sr_predicted_close !== null && predictionData.sr_predicted_close !== undefined
                              ? `${(predictionData.sr_predicted_close * 100).toFixed(1)}%`
                              : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", color: "var(--text-muted)" }}>
                            {predictionData && predictionData.sr_metrics && predictionData.sr_metrics.logloss !== undefined && predictionData.sr_metrics.logloss !== null ? predictionData.sr_metrics.logloss.toFixed(3) : "---"}
                          </td>
                          <td style={{ padding: "10px 4px", textAlign: "right", fontWeight: "600", color: "var(--accent-success)" }}>
                            {predictionData && predictionData.sr_metrics && predictionData.sr_metrics.directional_accuracy !== null ? `${predictionData.sr_metrics.directional_accuracy.toFixed(1)}%` : "---"}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  
                  <div style={{ marginTop: "18px", fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid rgba(255, 255, 255, 0.05)", paddingTop: "12px" }}>
                    {lang === "tr" 
                      ? `* Analitik verileri, her modelin geçmiş %20 out-of-sample test seti üzerindeki performansını (hata payı ve yön tahmini isabetini) gösterir.`
                      : `* Analytics show backtest performance (error metrics and directional accuracy) calculated over the last 20% out-of-sample test set for each model.`}
                  </div>
                </div>


              </div>
            </div>
            
            {/* AI Platform SEO Methodology & Overview Panel */}
            <div className="glass-panel" style={{ 
              marginTop: "20px", 
              padding: "20px", 
              borderRadius: "var(--border-radius-lg)", 
              border: "1px solid rgba(255, 255, 255, 0.05)",
              background: "rgba(255, 255, 255, 0.01)"
            }}>
              {lang === "tr" ? (
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "8px" }}>
                    🧠 Yapay Zeka Destekli Grafik ve Teknik Analiz Platformu
                  </h3>
                  <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: "1.6", marginBottom: "15px" }}>
                    <strong>Analyzeio</strong>, finansal piyasalardaki varlıkların (BIST Hisseleri, NASDAQ, Kripto Paralar ve Forex) fiyat yönünü tahmin etmek ve teknik analiz süreçlerini kolaylaştırmak amacıyla geliştirilmiş yapay zeka destekli bir SaaS platformudur.
                  </p>
                  <ul style={{ fontSize: "12.5px", color: "var(--text-muted)", lineHeight: "1.6", paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Makine ve Derin Öğrenme Modelleri:</strong> Platform; geçmiş fiyat hareketlerini, hacim verilerini ve teknik indikatörleri analiz etmek için <strong>LSTM (Uzun Kısa Vadeli Bellek)</strong>, <strong>PatchTST (Transformer)</strong>, <strong>XGBoost</strong>, <strong>Lojistik Regresyon</strong> ve <strong>Destek/Direnç</strong> modellerini kullanır.
                    </li>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Gelişmiş Ensemble (Topluluk) Algoritması:</strong> Tahmin motorumuz, canlı veriler üzerindeki başarı oranı %50'nin altına düşen zayıf modelleri otomatik olarak susturan <strong>Sert Baraj (Hard Thresholding)</strong> filtresini uygulayarak en yüksek tutarlılıkta yön kararı verir.
                    </li>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Otomatik Destek & Direnç:</strong> Grafik üzerinde anlık olarak hesaplanan 5 adet destek ve 5 adet direnç seviyesi, yatırımcılar için karar destek mekanizması oluşturur.
                    </li>
                  </ul>
                </div>
              ) : (
                <div>
                  <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "15px", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "8px" }}>
                    🧠 AI-Backed Graphical & Technical Analysis Platform
                  </h3>
                  <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: "1.6", marginBottom: "15px" }}>
                    <strong>Analyzeio</strong> is an AI-backed graphical and technical analysis SaaS platform designed to forecast price directions and streamline technical analysis for financial assets including stocks (BIST, NASDAQ), cryptocurrencies, and forex pairs.
                  </p>
                  <ul style={{ fontSize: "12.5px", color: "var(--text-muted)", lineHeight: "1.6", paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Machine & Deep Learning Models:</strong> The platform leverages <strong>LSTM (Long Short-Term Memory)</strong>, <strong>PatchTST (Transformer)</strong>, <strong>XGBoost</strong>, <strong>Logistic Regression</strong>, and <strong>Support/Resistance</strong> models to analyze historical price action and technical indicators.
                    </li>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Advanced Ensemble Methodology:</strong> Our forecasting engine utilizes a **Hard Thresholding Ensemble** filter that silences underperforming models (below 50% accuracy on live tests) to deliver highly robust directional predictions.
                    </li>
                    <li>
                      <strong style={{ color: "var(--text-main)" }}>Automatic Support & Resistance:</strong> Five support and five resistance overlay levels are dynamically calculated and rendered on the charts to provide robust decision support.
                    </li>
                  </ul>
                </div>
              )}
            </div>

            {/* Legal Disclaimer Box */}
            <div className="glass-panel" style={{ 
              marginTop: "20px", 
              padding: "15px 20px", 
              borderRadius: "var(--border-radius-md)", 
              border: "1px solid rgba(255, 255, 255, 0.05)",
              background: "rgba(0, 0, 0, 0.2)"
            }}>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#ef4444" }}></span>
                <h4 style={{ fontSize: "12px", fontWeight: "700", color: "#fca5a5", margin: 0, textTransform: "uppercase" }}>
                  {lang === "tr" ? "Yasal Uyarı & Bilgilendirme" : "Legal Disclaimer & Information"}
                </h4>
              </div>
              <p style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.6", margin: 0 }}>
                {lang === "tr" 
                  ? "analyzeio, yapay zeka destekli grafik ve teknik analiz hizmeti sunan bir SaaS (yazılım) platformudur. Bu web sitesinde yer alan tüm tahminler, analizler, göstergeler ve algoritmik modelleme sonuçları sadece teknik veri analizi ve bilgilendirme amaçlı olup, kesinlikle yatırım danışmanlığı, finansal tavsiye veya al-sat sinyali niteliği taşımamaktadır. Kullanıcıların bu verilere dayanarak alacağı tüm yatırım kararları ve doğabilecek finansal sonuçlar tamamen kendi sorumluluklarındadır." 
                  : "analyzeio is an AI-backed graphical and technical analysis SaaS (software) platform. All predictions, analyses, indicators, and algorithmic modeling results on this website are for technical data analysis and informational purposes only, and absolutely do not constitute investment advice, financial advisory, or buy/sell signals. Any investment decisions made by users based on this data and any resulting financial outcomes are entirely their own responsibility."}
              </p>
            </div>
          </>
        )}
      </main>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.7)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "400px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "20px" }}>{t("update_password_title")}</h3>
            
            {isVerifyingPasswordChange ? (
              <form onSubmit={handleConfirmPasswordChange} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
                <div style={{ fontSize: "13px", color: "var(--text-main)", lineHeight: "1.5", textAlign: "center" }}>
                  {lang === "tr" 
                    ? "Lütfen e-posta adresinize gönderilen 6 haneli şifre değiştirme doğrulama kodunu girin." 
                    : "Please enter the 6-digit password change verification code sent to your email."}
                </div>
                <input
                  type="text"
                  placeholder={lang === "tr" ? "Doğrulama Kodu" : "Verification Code"}
                  className="input-field"
                  value={passwordVerificationCode}
                  onChange={e => setPasswordVerificationCode(e.target.value)}
                  style={{ textAlign: "center", letterSpacing: "4px", fontWeight: "bold" }}
                  maxLength={6}
                  required
                />
                
                {passwordError && <div style={{ color: "var(--accent-danger)", fontSize: "13px" }}>{passwordError}</div>}
                {passwordSuccess && <div style={{ color: "var(--accent-success)", fontSize: "13px" }}>{passwordSuccess}</div>}
                
                <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                  <button type="submit" className="btn-primary">{lang === "tr" ? "Doğrula ve Güncelle" : "Verify & Update"}</button>
                  <button 
                    type="button" 
                    onClick={() => { 
                      setIsVerifyingPasswordChange(false); 
                      setPasswordError(""); 
                      setPasswordSuccess(""); 
                      setPasswordVerificationCode("");
                    }} 
                    className="btn-secondary"
                  >
                    {lang === "tr" ? "Geri Dön" : "Go Back"}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleChangePasswordRequest} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
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
                  <button 
                    type="button" 
                    onClick={() => { 
                      setShowPasswordModal(false); 
                      setPasswordError(""); 
                      setPasswordSuccess(""); 
                      setOldPassword("");
                      setNewPassword("");
                      setIsVerifyingPasswordChange(false);
                    }} 
                    className="btn-secondary"
                  >
                    {t("cancel_btn")}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* About Us Modal */}
      {showAboutModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "20px" }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "500px", maxHeight: "80vh", overflowY: "auto", position: "relative" }}>
            <button 
              onClick={() => setShowAboutModal(false)} 
              style={{ position: "absolute", top: "15px", right: "15px", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
            >
              ✕
            </button>
            <h3 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "15px", color: "var(--accent-primary)" }}>
              {lang === "tr" ? "Hakkımızda" : "About Us"}
            </h3>
            <div style={{ fontSize: "14px", lineHeight: "1.6", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "12px" }}>
              <p>
                {lang === "tr" 
                  ? "analyzeio, hisse senetleri ve kripto para birimleri için gelişmiş XGBoost ve LSTM tabanlı makine öğrenimi tahmin modelleri sunan gelişmiş bir piyasa tahmin ve teknik analiz platformudur."
                  : "analyzeio is an advanced market prediction and technical analysis platform offering optimized XGBoost and LSTM machine learning models for stocks and cryptocurrencies."}
              </p>
              <p>
                {lang === "tr"
                  ? "Sistemimiz, her bir varlık için son verileri indirir, RSI, MACD, Bollinger Bantları ve EMA gibi 19 temel teknik göstergeyi gerçek zamanlı hesaplar, tahmin modellerini optimize ederek bir sonraki işlem periyodunun kapanış fiyatını tahmin eder."
                  : "Our system downloads the latest price action for each asset, computes 19 key technical indicators (including RSI, MACD, Bollinger Bands, and EMAs) in real-time, and optimizes prediction models to estimate the next period's close price."}
              </p>
              <p>
                {lang === "tr"
                  ? "Tahmin doğruluğunu şeffaf bir şekilde ölçmek için geriye dönük test (backtest) hata oranlarını (RMSE, MAPE) ve yönsel isabet oranlarını sürekli olarak güncelliyor ve kullanıcılarımıza sunuyoruz."
                  : "We continuously calculate and show backtest error metrics (RMSE, MAPE) and directional accuracy logs, offering complete transparency into our predictive accuracy."}
              </p>
            </div>
            <button 
              onClick={() => setShowAboutModal(false)} 
              className="btn-primary" 
              style={{ marginTop: "20px", width: "100%" }}
            >
              {lang === "tr" ? "Kapat" : "Close"}
            </button>
          </div>
        </div>
      )}

      {/* Privacy Policy Modal */}
      {showPrivacyModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "20px" }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "550px", maxHeight: "80vh", overflowY: "auto", position: "relative" }}>
            <button 
              onClick={() => setShowPrivacyModal(false)} 
              style={{ position: "absolute", top: "15px", right: "15px", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
            >
              ✕
            </button>
            <h3 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "15px", color: "var(--accent-primary)" }}>
              {lang === "tr" ? "Gizlilik Politikası" : "Privacy Policy"}
            </h3>
            <div style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--text-main)", display: "flex", flexDirection: "column", gap: "12px" }}>
              <p><strong>1. {lang === "tr" ? "Veri Güvenliği" : "Data Security"}</strong></p>
              <p>
                {lang === "tr"
                  ? "Kullanıcı hesaplarının güvenliği için e-posta adresleri ve şifreler veritabanımızda tek yönlü kriptografik hashing (bcrypt) ile şifrelenmiş olarak saklanır. Şifreleriniz kesinlikle düz metin olarak kaydedilmez."
                  : "For account security, email addresses and passwords are stored in our database encrypted using secure one-way cryptographic hashing (bcrypt). We never store passwords in plaintext."}
              </p>
              <p><strong>2. {lang === "tr" ? "Toplanan Veriler" : "Data Collection"}</strong></p>
              <p>
                {lang === "tr"
                  ? "Sadece hesabınızı doğrulamak, şifre sıfırlama işlemlerini gerçekleştirmek ve izleme listenizi (watchlist) saklamak amacıyla gerekli olan minimum bilgileri (kullanıcı adı, e-posta) topluyoruz."
                  : "We collect only the minimum required information (username, email) necessary to verify your account, perform password resets, and store your watchlist."}
              </p>
              <p><strong>3. {lang === "tr" ? "Çerezler (Cookies)" : "Cookies"}</strong></p>
              <p>
                {lang === "tr"
                  ? "Çerezler, yalnızca oturum açma durumunuzu güvenli bir şekilde doğrulamak amacıyla (JWT token saklama için) tarayıcınızda geçici olarak tutulur. Reklam veya izleme çerezleri kullanılmaz."
                  : "Cookies are used temporarily in your browser solely for secure authentication (JWT token storage). We do not use advertising or tracking cookies."}
              </p>
              <p><strong>4. {lang === "tr" ? "Üçüncü Taraf Verileri" : "Third Party Data"}</strong></p>
              <p>
                {lang === "tr"
                  ? "Piyasa verileri Yahoo Finance API'si aracılığıyla çekilmekte olup kullanıcı bilgileriniz hiçbir üçüncü taraf veri sağlayıcısı ile paylaşılmaz."
                  : "Market data is retrieved via the Yahoo Finance API, and your user information is never shared with any third-party data providers."}
              </p>
            </div>
            <button 
              onClick={() => setShowPrivacyModal(false)} 
              className="btn-primary" 
              style={{ marginTop: "20px", width: "100%" }}
            >
              {lang === "tr" ? "Kapat" : "Close"}
            </button>
          </div>
        </div>
      )}

      {/* Contact Us Modal */}
      {showContactModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(5px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "20px" }}>
          <div className="glass-panel" style={{ width: "90%", maxWidth: "450px", position: "relative" }}>
            <button 
              onClick={() => { setShowContactModal(false); setContactStatus(""); }} 
              style={{ position: "absolute", top: "15px", right: "15px", background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
            >
              ✕
            </button>
            <h3 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "15px", color: "var(--accent-primary)" }}>
              {lang === "tr" ? "İletişime Geçin" : "Contact Us"}
            </h3>
            
            {contactStatus ? (
              <div style={{ textAlign: "center", padding: "20px 0" }}>
                <span style={{ fontSize: "40px" }}>✉️</span>
                <p style={{ color: "var(--accent-success)", fontWeight: "600", fontSize: "15px", marginTop: "10px" }}>{contactStatus}</p>
                <button 
                  onClick={() => { setShowContactModal(false); setContactStatus(""); }} 
                  className="btn-primary" 
                  style={{ marginTop: "15px", width: "100%" }}
                >
                  {lang === "tr" ? "Tamam" : "Okay"}
                </button>
              </div>
            ) : (
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  setContactStatus(lang === "tr" ? "Mesajınız başarıyla iletildi. En kısa sürede geri dönüş yapacağız!" : "Your message has been sent successfully. We will get back to you shortly!");
                  setContactEmail("");
                  setContactSubject("");
                  setContactMessage("");
                }} 
                style={{ display: "flex", flexDirection: "column", gap: "12px" }}
              >
                <div style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "5px" }}>
                  {lang === "tr" 
                    ? "Sorularınız, iş ortaklığı teklifleriniz veya geri bildirimleriniz için bize yazın." 
                    : "Write to us for questions, partnership proposals, or feedback."}
                </div>
                
                <input 
                  type="email" 
                  placeholder={lang === "tr" ? "E-posta Adresiniz" : "Your Email Address"}
                  className="input-field"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  required
                />
                
                <input 
                  type="text" 
                  placeholder={lang === "tr" ? "Konu" : "Subject"}
                  className="input-field"
                  value={contactSubject}
                  onChange={(e) => setContactSubject(e.target.value)}
                  required
                />
                
                <textarea 
                  placeholder={lang === "tr" ? "Mesajınız..." : "Your Message..."}
                  className="input-field"
                  rows="4"
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  style={{ resize: "none" }}
                  required
                />
                
                <button type="submit" className="btn-primary" style={{ marginTop: "5px" }}>
                  {lang === "tr" ? "Gönder" : "Send Message"}
                </button>
                
                <div style={{ fontSize: "11px", color: "var(--text-dark)", textAlign: "center", marginTop: "5px" }}>
                  {lang === "tr" ? "Doğrudan Destek: " : "Direct Support: "} 
                  <a href="mailto:support@analyzeio.com" style={{ color: "var(--accent-primary)", textDecoration: "none" }}>support@analyzeio.com</a>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Admin Panel Modal */}
      {showAdminModal && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.85)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "20px" }}>
          <div className="glass-panel" style={{ width: "100%", maxWidth: "800px", maxHeight: "85vh", display: "flex", flexDirection: "column", padding: "25px", overflow: "hidden" }}>
            
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "15px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <Shield style={{ color: "#f59e0b", width: "22px", height: "22px" }} />
                <h3 style={{ fontSize: "20px", fontWeight: "700", margin: 0, color: "#f59e0b" }}>Admin Control Panel</h3>
              </div>
              <button 
                onClick={() => setShowAdminModal(false)} 
                className="btn-secondary" 
                style={{ minWidth: "auto", padding: "6px 12px", fontSize: "12px" }}
              >
                ✕ Close
              </button>
            </div>
            
            {/* Tabs */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "20px" }}>
              <button 
                onClick={() => setAdminActiveTab("users")} 
                className={adminActiveTab === "users" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "users" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                👥 Users ({adminUsers.length})
              </button>
              <button 
                onClick={() => setAdminActiveTab("auto_train")} 
                className={adminActiveTab === "auto_train" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "auto_train" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                🤖 Auto-Train ({autoTrainSymbols.length})
              </button>
              <button 
                onClick={() => setAdminActiveTab("models")} 
                className={adminActiveTab === "models" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "models" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                🧠 Cache ({adminStats ? adminStats.total_cached_models : 0})
              </button>
              <button 
                onClick={() => setAdminActiveTab("mock_trading")} 
                className={adminActiveTab === "mock_trading" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "mock_trading" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                💸 Trading
              </button>
              <button 
                onClick={() => setAdminActiveTab("system_logs")} 
                className={adminActiveTab === "system_logs" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "system_logs" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                📋 Logs
              </button>
              <button 
                onClick={() => setAdminActiveTab("performance")} 
                className={adminActiveTab === "performance" ? "btn-primary" : "btn-secondary"}
                style={{ 
                  flex: "1 1 120px", 
                  background: adminActiveTab === "performance" ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" : "rgba(255, 255, 255, 0.03)",
                  border: "none",
                  fontWeight: "600",
                  padding: "8px 12px",
                  fontSize: "12px",
                  whiteSpace: "nowrap"
                }}
              >
                📈 Performance
              </button>
            </div>
            
            {/* Main Content Area (Scrollable) */}
            <div style={{ flex: 1, overflowY: "auto", paddingRight: "5px" }}>
              {adminLoading ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "50px 0", gap: "15px" }}>
                  <RefreshCw className="animate-spin" style={{ color: "#f59e0b", width: "32px", height: "32px" }} />
                  <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>Loading Admin Data...</span>
                </div>
              ) : adminActiveTab === "users" ? (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", minWidth: "600px", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", color: "var(--text-muted)" }}>
                        <th style={{ padding: "10px" }}>ID</th>
                        <th style={{ padding: "10px" }}>Username</th>
                        <th style={{ padding: "10px" }}>Email</th>
                        <th style={{ padding: "10px" }}>Membership</th>
                        <th style={{ padding: "10px", textAlign: "right" }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminUsers.map(u => (
                        <tr key={u.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                          <td style={{ padding: "12px 10px", color: "var(--text-muted)" }}>{u.id}</td>
                          <td style={{ padding: "12px 10px", fontWeight: "600" }}>{u.username}</td>
                          <td style={{ padding: "12px 10px" }}>{u.email}</td>
                          <td style={{ padding: "12px 10px" }}>
                            {u.is_premium ? (
                              <span style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b", padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "700" }}>
                                ★ Premium
                              </span>
                            ) : (
                              <span style={{ background: "rgba(255, 255, 255, 0.05)", color: "var(--text-muted)", padding: "2px 8px", borderRadius: "10px", fontSize: "11px" }}>
                                Standard
                              </span>
                            )}
                          </td>
                          <td style={{ padding: "12px 10px", textAlign: "right" }}>
                            <button
                              onClick={() => handleAdminTogglePremium(u.id)}
                              className="btn-secondary"
                              style={{
                                padding: "4px 10px",
                                fontSize: "11px",
                                minWidth: "auto",
                                borderColor: u.is_premium ? "rgba(239, 68, 68, 0.4)" : "rgba(245, 158, 11, 0.4)",
                                color: u.is_premium ? "var(--accent-danger)" : "#f59e0b"
                              }}
                            >
                              {u.is_premium ? "Revoke Premium" : "Grant Premium"}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : adminActiveTab === "auto_train" ? (
                <div>
                  {/* Add symbol form */}
                  <form onSubmit={handleAddAutoTrainSymbol} style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
                    <input 
                      type="text" 
                      placeholder="e.g. SOL-USD, AAPL, Gold" 
                      value={newAutoTrainSymbol}
                      onChange={(e) => setNewAutoTrainSymbol(e.target.value)}
                      style={{ 
                        flex: 1, 
                        background: "rgba(255, 255, 255, 0.03)", 
                        border: "1px solid rgba(255, 255, 255, 0.08)", 
                        borderRadius: "6px", 
                        padding: "8px 12px", 
                        color: "var(--text-main)",
                        fontSize: "13px"
                      }} 
                    />
                    <button 
                      type="submit" 
                      className="btn-primary"
                      style={{ 
                        background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)", 
                        border: "none", 
                        padding: "8px 16px",
                        fontSize: "13px",
                        fontWeight: "600",
                        minWidth: "120px"
                      }}
                    >
                      + Add Asset
                    </button>
                  </form>

                  <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>
                    Auto-Trained Assets List ({autoTrainSymbols.length})
                  </h4>

                  <div style={{ overflowX: "auto", maxHeight: "400px" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", textAlign: "left" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", color: "var(--text-muted)" }}>
                          <th style={{ padding: "10px" }}>Asset Symbol</th>
                          <th style={{ padding: "10px" }}>Model Status</th>
                          <th style={{ padding: "10px" }}>Last Trained At</th>
                          <th style={{ padding: "10px", textAlign: "right" }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {autoTrainSymbols.length === 0 ? (
                          <tr>
                            <td colSpan={4} style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontStyle: "italic" }}>
                              No auto-trained assets found.
                            </td>
                          </tr>
                        ) : (
                          autoTrainSymbols.map((item) => (
                            <tr key={item.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                              <td style={{ padding: "12px 10px" }}>
                                <strong style={{ fontSize: "13.5px", color: "var(--text-main)" }}>{item.symbol}</strong>
                              </td>
                              <td style={{ padding: "12px 10px" }}>
                                {item.is_trained ? (
                                  <span style={{ background: "rgba(16, 185, 129, 0.15)", color: "var(--accent-success)", padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "700" }}>
                                    ✓ Trained
                                  </span>
                                ) : (
                                  <span style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b", padding: "2px 8px", borderRadius: "10px", fontSize: "11px", fontWeight: "700" }}>
                                    ⏳ Pending Data
                                  </span>
                                )}
                              </td>
                              <td style={{ padding: "12px 10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                                {item.last_trained_at || "Never (Needs 1st run)"}
                              </td>
                              <td style={{ padding: "12px 10px", textAlign: "right" }}>
                                <button 
                                  onClick={() => handleDeleteAutoTrainSymbol(item.symbol)}
                                  className="btn-secondary"
                                  style={{ 
                                    padding: "4px 8px", 
                                    fontSize: "11px",
                                    minWidth: "auto",
                                    borderColor: "rgba(239, 68, 68, 0.4)",
                                    color: "var(--accent-danger)"
                                  }}
                                  title="Remove from Auto-Train List"
                                >
                                  Remove
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : adminActiveTab === "models" ? (
                <div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "15px", marginBottom: "20px" }}>
                    <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>Total Users</span>
                      <strong style={{ fontSize: "20px", color: "var(--text-main)" }}>{adminStats ? adminStats.total_users : 0}</strong>
                    </div>
                    <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      <span style={{ fontSize: "12px", color: "#f59e0b", display: "block", marginBottom: "5px" }}>Premium Members</span>
                      <strong style={{ fontSize: "20px", color: "#f59e0b" }}>{adminStats ? adminStats.premium_users : 0}</strong>
                    </div>
                  </div>
                  
                  <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>
                    Cached Model Files ({adminStats ? adminStats.cached_models.length : 0})
                  </h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {adminStats && adminStats.cached_models.length === 0 ? (
                      <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontStyle: "italic" }}>
                        No trained models found in cache folder.
                      </div>
                    ) : (
                      adminStats && adminStats.cached_models.map((filename, idx) => (
                        <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(255, 255, 255, 0.01)", padding: "8px 12px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.03)", fontSize: "12.5px" }}>
                          <span style={{ fontFamily: "monospace", color: "var(--text-main)" }}>{filename}</span>
                          <span className="badge badge-success" style={{ fontSize: "10px", padding: "2px 8px" }}>Active</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ) : adminActiveTab === "system_logs" ? (
                <div>
                  <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>
                    🤖 Auto-Train Daemon Logs
                  </h4>
                  <div style={{ 
                    background: "#0a0c16", 
                    padding: "15px", 
                    borderRadius: "8px", 
                    border: "1px solid rgba(255, 255, 255, 0.08)", 
                    fontFamily: "monospace", 
                    fontSize: "12px", 
                    color: "#a7f3d0", 
                    height: "250px", 
                    overflowY: "auto", 
                    marginBottom: "25px",
                    whiteSpace: "pre-wrap"
                  }}>
                    {daemonLogs && daemonLogs.daemon_out && daemonLogs.daemon_out.length > 0 
                      ? daemonLogs.daemon_out.join("") 
                      : "Loading daemon logs or log file is empty..."}
                  </div>

                  <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>
                    🌐 Web API Logs
                  </h4>
                  <div style={{ 
                    background: "#0a0c16", 
                    padding: "15px", 
                    borderRadius: "8px", 
                    border: "1px solid rgba(255, 255, 255, 0.08)", 
                    fontFamily: "monospace", 
                    fontSize: "12px", 
                    color: "#93c5fd", 
                    height: "250px", 
                    overflowY: "auto", 
                    whiteSpace: "pre-wrap"
                  }}>
                    {daemonLogs && daemonLogs.out && daemonLogs.out.length > 0 
                      ? daemonLogs.out.join("") 
                      : "Loading API logs or log file is empty..."}
                  </div>
                </div>
              ) : adminActiveTab === "performance" ? (
                <div>
                  {!adminPerformance ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "50px 0", gap: "15px" }}>
                      <RefreshCw className="animate-spin" style={{ color: "#f59e0b", width: "32px", height: "32px" }} />
                      <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>
                        {lang === "tr" ? "Performans verileri yükleniyor..." : "Loading performance statistics..."}
                      </span>
                    </div>
                  ) : (
                    <div>
                      {/* Summary Statistics Dashboard */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "15px", marginBottom: "20px" }}>
                        <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                          <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>
                            {lang === "tr" ? "Yön Tutarlılık Oranı" : "Directional Accuracy"}
                          </span>
                          <strong style={{ fontSize: "20px", color: "#10b981" }}>
                            {adminPerformance.stats.accuracy_percent}%
                          </strong>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                            {lang === "tr" 
                              ? `${adminPerformance.stats.correct_count} / ${adminPerformance.stats.total_evaluated} Doğru Tahmin`
                              : `${adminPerformance.stats.correct_count} / ${adminPerformance.stats.total_evaluated} Correct Predictions`}
                          </span>
                        </div>
                        <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                          <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>
                            {lang === "tr" ? "Değerlendirilen Sembol Sayısı" : "Total Evaluated Assets"}
                          </span>
                          <strong style={{ fontSize: "20px", color: "var(--text-main)" }}>
                            {adminPerformance.stats.total_evaluated}
                          </strong>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                            {lang === "tr" ? "En son kapanışı tamamlanmış olanlar" : "Symbols with completed predictions"}
                          </span>
                        </div>
                        <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                          <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>
                            {lang === "tr" ? "Boğa / Ayı Dağılımı" : "Predicted Outlook Split"}
                          </span>
                          <strong style={{ fontSize: "18px", color: "#f59e0b" }}>
                            ▲ {adminPerformance.stats.bullish_pred_count} / ▼ {adminPerformance.stats.bearish_pred_count}
                          </strong>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginTop: "2px" }}>
                            {lang === "tr" ? "Model Tahmin Dağılımları" : "Bullish vs Bearish forecasts"}
                          </span>
                        </div>
                      </div>

                      {/* Filter Bar */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginBottom: "15px", alignItems: "center" }}>
                        <input 
                          type="text"
                          placeholder={lang === "tr" ? "Sembol Ara (örn: BTC)..." : "Search Symbol (e.g. BTC)..."}
                          value={adminPerfSearch}
                          onChange={(e) => setAdminPerfSearch(e.target.value)}
                          className="input-field"
                          style={{ flex: "1 1 180px", margin: 0, padding: "8px 12px", fontSize: "13px" }}
                        />
                        <select
                          value={adminPerfFilter}
                          onChange={(e) => setAdminPerfFilter(e.target.value)}
                          className="input-field"
                          style={{ flex: "1 1 180px", margin: 0, padding: "8px 12px", fontSize: "13px", background: "var(--bg-dark)" }}
                        >
                          <option value="all">{lang === "tr" ? "Tüm Tahminler" : "All Predictions"}</option>
                          <option value="correct">{lang === "tr" ? "✓ Doğru Tahminler" : "✓ Correct Predictions"}</option>
                          <option value="wrong">{lang === "tr" ? "✗ Yanlış Tahminler" : "✗ Wrong Predictions"}</option>
                          <option value="bullish">{lang === "tr" ? "▲ Boğa Tahminleri" : "▲ Bullish Predictions"}</option>
                          <option value="bearish">{lang === "tr" ? "▼ Ayı Tahminleri" : "▼ Bearish Predictions"}</option>
                        </select>
                      </div>

                      {/* Details Table */}
                      <div style={{ overflowX: "auto", maxHeight: "400px", background: "rgba(0,0,0,0.15)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                        {(() => {
                          const filteredDetails = adminPerformance.details.filter(item => {
                            const matchesSearch = item.symbol.toLowerCase().includes(adminPerfSearch.toLowerCase());
                            if (!matchesSearch) return false;
                            
                            if (adminPerfFilter === "correct") return item.is_correct;
                            if (adminPerfFilter === "wrong") return !item.is_correct;
                            if (adminPerfFilter === "bullish") return item.predicted_direction === "UP";
                            if (adminPerfFilter === "bearish") return item.predicted_direction === "DOWN";
                            return true;
                          });

                          if (filteredDetails.length === 0) {
                            return (
                              <div style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)", fontStyle: "italic", fontSize: "13px" }}>
                                {lang === "tr" ? "Filtrelere uygun veri bulunamadı." : "No records match the selected filters."}
                              </div>
                            );
                          }

                          return (
                            <table style={{ width: "100%", minWidth: "700px", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                              <thead>
                                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", color: "var(--text-muted)", background: "rgba(255,255,255,0.02)" }}>
                                  <th style={{ padding: "10px" }}>{lang === "tr" ? "Sembol" : "Symbol"}</th>
                                  <th style={{ padding: "10px" }}>{lang === "tr" ? "Hedef Tarih" : "Target Date"}</th>
                                  <th style={{ padding: "10px", textAlign: "right" }}>{lang === "tr" ? "Model Tahmini" : "Predicted Direction"}</th>
                                  <th style={{ padding: "10px", textAlign: "right" }}>{lang === "tr" ? "Önceki Kapanış" : "Prev Close"}</th>
                                  <th style={{ padding: "10px", textAlign: "right" }}>{lang === "tr" ? "Gerçekleşen Kapanış" : "Actual Close"}</th>
                                  <th style={{ padding: "10px", textAlign: "center" }}>{lang === "tr" ? "Sonuç" : "Result"}</th>
                                </tr>
                              </thead>
                              <tbody>
                                {filteredDetails.map((item, index) => {
                                  const predUp = item.predicted_direction === "UP";
                                  const actualUp = item.actual_direction === "UP";
                                  const isBullish = item.predicted_close >= 0.5;
                                  const conf = isBullish ? item.predicted_close * 100 : (1 - item.predicted_close) * 100;
                                  
                                  return (
                                    <tr key={index} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                                      <td style={{ padding: "10px", fontWeight: "700", color: "#fef3c7" }}>
                                        {item.symbol}
                                      </td>
                                      <td style={{ padding: "10px", color: "var(--text-muted)" }}>
                                        {item.prediction_date}
                                      </td>
                                      <td style={{ padding: "10px", textAlign: "right", fontWeight: "700", color: predUp ? "#10b981" : "#ef4444" }}>
                                        {predUp ? "▲ BULLISH" : "▼ BEARISH"} ({conf.toFixed(1)}%)
                                      </td>
                                      <td style={{ padding: "10px", textAlign: "right", color: "var(--text-muted)" }}>
                                        ${item.last_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                      </td>
                                      <td style={{ padding: "10px", textAlign: "right", fontWeight: "600", color: actualUp ? "#10b981" : "#ef4444" }}>
                                        ${item.actual_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({actualUp ? "▲" : "▼"})
                                      </td>
                                      <td style={{ padding: "10px", textAlign: "center" }}>
                                        <span className={`badge ${item.is_correct ? "badge-success" : "badge-danger"}`} style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "12px", fontWeight: "700" }}>
                                          {item.is_correct ? (lang === "tr" ? "✓ Doğru" : "✓ Correct") : (lang === "tr" ? "✗ Yanlış" : "✗ Wrong")}
                                        </span>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {/* Mock Trading Tab Contents */}
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "15px", marginBottom: "20px" }}>
                    <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>Cash Balance</span>
                      <strong style={{ fontSize: "22px", color: "#10b981" }}>
                        ${mockTradingState ? mockTradingState.balance.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 }) : "2,000.00"}
                      </strong>
                    </div>
                    <div style={{ flex: "1 1 180px", background: "rgba(255, 255, 255, 0.02)", padding: "15px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                      <span style={{ fontSize: "12px", color: "var(--text-muted)", display: "block", marginBottom: "5px" }}>Active Position</span>
                      {mockTradingState && mockTradingState.position ? (
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <strong style={{ fontSize: "16px", color: "#f59e0b" }}>
                            {mockTradingState.position.symbol} ({mockTradingState.position.qty.toFixed(4)} Units)
                          </strong>
                          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                            at ${mockTradingState.position.entry_price.toLocaleString("en-US", { minimumFractionDigits: 3 })}
                          </span>
                        </div>
                      ) : (
                        <strong style={{ fontSize: "16px", color: "var(--text-muted)", fontStyle: "italic" }}>
                          No Active Position (Cash)
                        </strong>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
                    <h4 style={{ fontSize: "14px", fontWeight: "700", margin: 0, textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>
                      Simulation Progress & Transaction Logs
                    </h4>
                    <button 
                      onClick={handleResetMockTrading} 
                      className="btn-secondary" 
                      style={{ 
                        fontSize: "11px", 
                        padding: "4px 10px", 
                        borderColor: "rgba(239, 68, 68, 0.3)", 
                        color: "var(--accent-danger)",
                        minWidth: "auto"
                      }}
                    >
                      Reset Simulation
                    </button>
                  </div>

                  <div style={{ 
                    maxHeight: "350px", 
                    overflowY: "auto", 
                    background: "rgba(0,0,0,0.2)", 
                    borderRadius: "8px", 
                    border: "1px solid rgba(255,255,255,0.05)", 
                    padding: "10px 15px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px"
                  }}>
                    {mockTradingState && mockTradingState.logs && mockTradingState.logs.length === 0 ? (
                      <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontStyle: "italic" }}>
                        No logs generated yet.
                      </div>
                    ) : (
                      mockTradingState && [...mockTradingState.logs].reverse().map((log, idx) => (
                        <div key={idx} style={{ 
                          fontSize: "12px", 
                          lineHeight: "1.4", 
                          paddingBottom: "8px", 
                          borderBottom: "1px solid rgba(255,255,255,0.03)", 
                          color: "var(--text-main)" 
                        }}>
                          <span style={{ color: "#f59e0b", fontWeight: "600", marginRight: "8px", fontFamily: "monospace" }}>
                            [{log.timestamp}]
                          </span>
                          <span>{log.event}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            
          </div>
        </div>
      )}
      {renderAuthModal()}
    </div>
  );
}
