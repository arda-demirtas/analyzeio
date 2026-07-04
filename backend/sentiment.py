import requests
from typing import List, Dict, Any

def analyze_text_sentiment(title: str, summary: str = "") -> float:
    """
    Calculates a sentiment score between -1.0 (very bearish) and 1.0 (very bullish)
    using key financial sentiment words.
    """
    pos_words = {
        "bullish", "growth", "high", "gain", "breakout", "surpass", "profit", 
        "positive", "strong", "rise", "soar", "rally", "jump", "buy", "upward",
        "boğa", "yükseliş", "artış", "kâr", "güçlü", "rekor", "al", "kazanç", "pozitif"
    }
    neg_words = {
        "bearish", "fall", "drop", "loss", "crash", "negative", "weak", "down", 
        "decline", "slide", "plummet", "slump", "sell", "downward", "worry",
        "ayı", "düşüş", "kayıp", "zayıf", "düşük", "sat", "korku", "risk", "negatif"
    }
    
    score = 0.0
    text = (title + " " + summary).lower()
    
    pos_count = sum(1 for w in pos_words if w in text)
    neg_count = sum(1 for w in neg_words if w in text)
    
    total = pos_count + neg_count
    if total > 0:
        score = (pos_count - neg_count) / total
    return score

def fetch_symbol_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Queries Yahoo Finance Search API to retrieve news articles for the symbol,
    and runs NLP sentiment analysis on each article.
    """
    symbol_upper = symbol.upper().strip()
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol_upper}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    articles = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw_news = data.get("news", [])
            for item in raw_news:
                title = item.get("title", "")
                publisher = item.get("publisher", "Yahoo Finance")
                link = item.get("link", "")
                pub_time = item.get("providerPublishTime", 0)
                
                # Perform sentiment analysis
                score = analyze_text_sentiment(title)
                
                # Determine rating text and color badge
                if score >= 0.1:
                    rating = "BULLISH"
                elif score <= -0.1:
                    rating = "BEARISH"
                else:
                    rating = "NEUTRAL"
                    
                articles.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "time": pub_time,
                    "score": score,
                    "rating": rating
                })
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        
    return articles

def get_fundamental_analysis(symbol: str, name: str, lang: str = "en") -> Dict[str, Any]:
    """
    Searches the web for recent news regarding the asset, computes headline sentiment,
    and returns a recommendation and list of articles.
    """
    # Use name (e.g. Bitcoin) for search, fallback to symbol
    search_query = name if name else symbol
    
    # Clean up generic suffixes to make the search query more relevant
    search_query = search_query.replace(" USD", "").replace(" Inc.", "").replace(" Corporation", "").replace(" Futures", "")
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_query}&newsCount=6"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    articles = []
    sentiment_score = 0.0
    sentiment_class = "Neutral"
    
    recommendation = "No recent fundamental news articles could be analyzed for this asset."
    if lang == "tr":
        recommendation = "Bu varlık için yakın zamanda yayınlanmış temel analiz haber makalesi analiz edilemedi."
    elif lang == "de":
        recommendation = "Für diesen Vermögenswert konnten keine aktuellen fundamentalen Nachrichtenartikel analysiert werden."
    elif lang == "ru":
        recommendation = "Не удалось проанализировать недавние фундаментальные новости для этого актива."
    elif lang == "zh":
        recommendation = "无法分析该资产的近期基本面新闻文章。"
    elif lang == "es":
        recommendation = "No se pudieron analizar artículos de noticias fundamentales recientes para este activo."
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw_news = data.get("news", [])
            
            # Simple financial sentiment dictionary
            pos_words = {
                "surge", "bullish", "growth", "rise", "gain", "profit", "upbeat", "upgrade", 
                "outperform", "soar", "rally", "boost", "positive", "high", "buy", "jump", 
                "climb", "higher", "strong", "recovery", "success", "optimistic", "green", 
                "breakout", "alliance", "partner", "acquire", "expanded", "soaring"
            }
            neg_words = {
                "plunge", "bearish", "decline", "fall", "loss", "drop", "downbeat", "downgrade", 
                "underperform", "plummet", "crash", "slump", "negative", "low", "sell", "sink", 
                "slide", "lower", "weak", "panic", "failure", "pessimistic", "red", "breakdown", 
                "worry", "concern", "fear", "lawsuit", "dispute", "investigation", "chilling"
            }
            
            total_score = 0.0
            valid_articles = 0
            
            for item in raw_news:
                title = item.get("title")
                publisher = item.get("publisher")
                link = item.get("link")
                if not title or not link:
                    continue
                    
                # Clean title for sentiment check
                clean_title = title.lower()
                # Remove common punctuation
                for char in [".", ",", "!", "?", "'", "\"", ":", ";", "(", ")", "-", "_", "$", "%"]:
                    clean_title = clean_title.replace(char, " ")
                
                words = clean_title.split()
                pos_count = sum(1 for w in words if w in pos_words)
                neg_count = sum(1 for w in words if w in neg_words)
                
                # Single headline score
                denom = pos_count + neg_count
                art_score = (pos_count - neg_count) / denom if denom > 0 else 0.0
                
                # Determine article sentiment
                if art_score > 0.0:
                    art_sentiment = "Bullish"
                elif art_score < 0.0:
                    art_sentiment = "Bearish"
                else:
                    art_sentiment = "Neutral"
                    
                articles.append({
                    "title": title,
                    "publisher": publisher if publisher else "Web News",
                    "link": link,
                    "sentiment": art_sentiment
                })
                
                total_score += art_score
                valid_articles += 1
                
            if valid_articles > 0:
                sentiment_score = total_score / valid_articles
                
            # Classify overall sentiment and construct localized recommendations
            if sentiment_score > 0.12:
                sentiment_class = "Bullish"
                if lang == "tr":
                    recommendation = (
                        f"Son haber kapsamına göre {search_query} için temel analiz olumlu piyasa duyarlılığı gösteriyor. "
                        f"Olumlu etkenler, kazanç raporları veya piyasa ortaklıkları kısa vadeli olumlu bir görünüme işaret ediyor. "
                        f"Genellikle alım yapmak veya pozisyonları korumak önerilir."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die Fundamentalanalyse zeigt auf Basis der jüngsten Berichterstattung eine positive Marktstimmung für {search_query}. "
                        f"Positive Treiber, Gewinnberichte oder Marktallianzen deuten auf einen günstigen kurzfristigen Ausblick hin. "
                        f"Kauf oder Halten von Positionen wird generell empfohlen."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальный анализ выявляет позитивные рыночные настроения для {search_query} на основе недавних новостей. "
                        f"Положительные драйверы, отчеты о доходах или рыночные альянсы указывают на благоприятный краткосрочный прогноз. "
                        f"Обычно рекомендуется покупать или удерживать позиции."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"基于近期新闻报道，{search_query} 的基本面分析显示出积极的市场情绪。利好驱动因素、财报业绩或市场合作预示着短期前景良好。一般建议买入或持有仓位。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"El análisis fundamental revela un sentimiento de mercado positivo para {search_query} según la cobertura de noticias reciente. "
                        f"Los factores impulsores positivos, los informes de ganancias o las alianzas de mercado sugieren una perspectiva favorable a corto plazo. "
                        f"Generalmente se recomienda comprar o mantener posiciones."
                    )
                else:
                    recommendation = (
                        f"Fundamental analysis reveals positive market sentiment for {search_query} "
                        f"based on recent news coverage. Positive drivers, earnings reports, or market "
                        f"alliances suggest a favorable short-term outlook. Buying or holding positions "
                        f"is generally recommended."
                    )
            elif sentiment_score < -0.12:
                sentiment_class = "Bearish"
                if lang == "tr":
                    recommendation = (
                        f"Son olumsuz haber başlıkları nedeniyle {search_query} için temel analiz olumsuz duyarlılığa işaret ediyor. "
                        f"Olası düzenleyici endişeler, satışlar veya sektördeki düşüş trendleri temkinli olmayı gerektiriyor. "
                        f"Alım yapılması önerilmez; zarar durdurma seviyelerini daraltmayı veya maruziyeti azaltmayı düşünebilirsiniz."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die Fundamentalanalyse deutet aufgrund jüngster negativer Schlagzeilen auf eine negative Stimmung für {search_query} hin. "
                        f"Potenzielle regulatorische Bedenken, Ausverkäufe oder Abwärtstrends im Sektor mahnen zur Vorsicht. "
                        f"Ein Nachkauf wird nicht empfohlen; erwägen Sie die Verengung von Stop-Loss-Marken oder die Reduzierung des Risikos."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальный анализ указывает на негативные настроения по {search_query} из-за недавних неблагоприятных новостей. "
                        f"Возможные регуляторные проблемы, распродажи или нисходящие тренды в секторе призывают к осторожности. "
                        f"Накапливать актив не рекомендуется; подумайте о подтягивании стоп-лоссов или снижении рисков."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"由于近期负面新闻，{search_query} 的基本面分析显示出消极情绪。潜在的监管担忧、抛售或行业下行趋势提示需要保持谨慎。不建议加仓；可考虑收紧止损或降低风险敞口。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"El análisis fundamental indica un sentimiento negativo para {search_query} debido a los titulares de noticias adversos recientes. "
                        f"Las posibles preocupaciones regulatorias, las liquidaciones o las tendencias bajistas en el sector aconsejan precaución. "
                        f"No se recomienda acumular; considere ajustar los stop-loss o reducir la exposición."
                    )
                else:
                    recommendation = (
                        f"Fundamental analysis indicates negative sentiment for {search_query} "
                        f"due to recent adverse news headlines. Potential regulatory concerns, selloffs, "
                        f"or downtrends in the sector advise caution. Accumulating is not recommended; "
                        f"consider tightening stop-losses or reducing exposure."
                    )
            else:
                sentiment_class = "Neutral"
                if lang == "tr":
                    recommendation = (
                        f"{search_query} için temel haber göstergeleri şu anda dengeli veya nötr durumda. "
                        f"Haber başlıkları olumlu ve temkinli göstergelerin bir karışımını sunuyor. "
                        f"Ticaret kararları için bir 'Bekle' stratejisi veya bunun teknik göstergelerle birleştirilmesi önerilir."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die fundamentalen Nachrichtenindikatoren sind für {search_query} derzeit ausgeglichen oder neutral. "
                        f"Die Schlagzeilen präsentieren eine Mischung aus positiven und vorsichtigen Kennzahlen. "
                        f"Für Handelsentscheidungen wird eine 'Halten'-Strategie oder die Kombination mit technischen Indikatoren empfohlen."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальные новостные индикаторы по {search_query} в настоящее время сбалансированы или нейтральны. "
                        f"Заголовки новостей представляют собой смесь положительных и осторожных показателей. "
                        f"Для торговых решений рекомендуется стратегия 'Удерживать' или сочетание этого с техническими индикаторами."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"目前 {search_query} 的基本面新闻指标处于均衡或中性状态。新闻头条呈现出利好与谨慎指标的交织。建议采取“观望/持有”策略，或结合技术指标进行交易决策。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"Los indicadores de noticias fundamentales son actualmente equilibrados o neutrales para {search_query}. "
                        f"Los titulares de las noticias presentan una mezcla de métricas positivas y cautelosas. "
                        f"Se aconseja una estrategia de 'Mantener' o combinar esto con indicadores técnicos para las decisiones operativas."
                    )
                else:
                    recommendation = (
                        f"Fundamental news indicators are currently balanced or neutral for {search_query}. "
                        f"The news headlines present a mix of positive and cautious metrics. A 'Hold' "
                        f"strategy or combining this with technical indicators is advised for trading decisions."
                    )
    except Exception as e:
        print(f"Error fetching news for fundamental analysis: {e}")
        
    return {
        "sentiment_score": sentiment_score,
        "sentiment_class": sentiment_class,
        "recommendation": recommendation,
        "articles": articles
    }
