import os, sqlite3, requests, time, re, html, uuid
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import FastAPI, Request, Form, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from apscheduler.schedulers.background import BackgroundScheduler
from starlette.staticfiles import StaticFiles

# =========================
# Config (env overrides available)
# =========================
DB_PATH = "data/app.db"

# Polling / caching
POLL_SECONDS       = int(os.getenv("POLL_SECONDS", "60"))     # stock alert poll
SHOWCASE_REFRESH   = int(os.getenv("SHOWCASE_REFRESH", "300"))
PREDICT_SECONDS    = int(os.getenv("PREDICT_SECONDS", "3600"))
SURF_REFRESH       = int(os.getenv("SURF_REFRESH", "600"))    # waves

# Alert cooldown (minutes) between repeats per symbol
COOLDOWN_MIN       = int(os.getenv("COOLDOWN_MIN", "0"))

# Symbols shown in "Showcase" table (comma list)
SHOWCASE_SYMBOLS   = [s.strip().upper() for s in os.getenv(
    "SHOWCASE_SYMBOLS",
    "AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,SPY"
).split(",") if s.strip()]

# File uploads for Journal
UPLOAD_DIR         = os.getenv("UPLOAD_DIR", "data/uploads")

# Providers (set tokens in .env)
FINNHUB = os.getenv("FINNHUB_TOKEN")                      # primary
ALPHA   = os.getenv("ALPHA_VANTAGE_KEY")                  # fallback

# Optional notifiers
TWILIO_SID=os.getenv("TWILIO_SID")
TWILIO_TOKEN=os.getenv("TWILIO_TOKEN")
TWILIO_FROM=os.getenv("TWILIO_FROM")
ALERT_PHONE=os.getenv("ALERT_PHONE")

TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")

DISCORD_WEBHOOK_URL=os.getenv("DISCORD_WEBHOOK_URL")

# Alpha throttle (fallback only — respect 5 req/min free tier)
ALPHA_MIN_INTERVAL = float(os.getenv("ALPHA_MIN_INTERVAL", "13"))
LAST_ALPHA_CALL = 0.0
def alpha_get(url, timeout=12):
    global LAST_ALPHA_CALL
    wait = ALPHA_MIN_INTERVAL - (time.time() - LAST_ALPHA_CALL)
    if wait > 0:
        time.sleep(wait)
    r = requests.get(url, timeout=timeout)
    LAST_ALPHA_CALL = time.time()
    return r

# =========================
# App & templating
# =========================
app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

os.makedirs("data", exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# =========================
# DB bootstrap / migrations
# =========================
with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()

    # Stocks & alerts
    c.execute("""CREATE TABLE IF NOT EXISTS stocks(
      id INTEGER PRIMARY KEY,
      symbol TEXT NOT NULL,
      target REAL NOT NULL,
      direction TEXT CHECK(direction IN ('above','below')) NOT NULL,
      enabled INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY,
      symbol TEXT, price REAL, target REAL, direction TEXT,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS latest_prices(
      symbol TEXT PRIMARY KEY,
      price REAL,
      high REAL,
      low REAL,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    # ensure columns exist
    cols = {r[1] for r in c.execute("PRAGMA table_info(latest_prices)")}
    if "high" not in cols: c.execute("ALTER TABLE latest_prices ADD COLUMN high REAL")
    if "low"  not in cols: c.execute("ALTER TABLE latest_prices ADD COLUMN low REAL")

    c.execute("""CREATE TABLE IF NOT EXISTS predictions(
      symbol TEXT PRIMARY KEY,
      pred_next REAL,
      src_days INTEGER,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # Timestamped notes
    c.execute("""CREATE TABLE IF NOT EXISTS notes(
      id INTEGER PRIMARY KEY,
      content TEXT,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # Legacy single pad (kept for migration)
    c.execute("""CREATE TABLE IF NOT EXISTS pad(
      id INTEGER PRIMARY KEY CHECK (id=1),
      content TEXT DEFAULT '',
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("INSERT OR IGNORE INTO pad(id, content) VALUES(1, '')")

    # Multi-tab notepad
    c.execute("""CREATE TABLE IF NOT EXISTS pad_tabs(
      id INTEGER PRIMARY KEY,
      name TEXT UNIQUE NOT NULL,
      content TEXT DEFAULT '',
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    if c.execute("SELECT COUNT(*) FROM pad_tabs").fetchone()[0] == 0:
        old = c.execute("SELECT content FROM pad WHERE id=1").fetchone()
        initial = (old[0] if old else '')
        c.execute("INSERT INTO pad_tabs(name,content) VALUES(?,?)", ("General", initial))

    # TradingView symbols (for the widget)
    c.execute("""CREATE TABLE IF NOT EXISTS tv_symbols(
      tv_symbol TEXT PRIMARY KEY,   -- e.g. NASDAQ:AAPL or BINANCE:BTCUSDT
      label    TEXT                 -- display label, e.g. AAPL / BTC
    )""")
    cnt = c.execute("SELECT COUNT(*) FROM tv_symbols").fetchone()[0]
    if cnt == 0:
        defaults = [
          ("NASDAQ:AAPL","AAPL"), ("NASDAQ:MSFT","MSFT"), ("NASDAQ:NVDA","NVDA"),
          ("NASDAQ:GOOGL","GOOGL"), ("NASDAQ:AMZN","AMZN"), ("NASDAQ:META","META"),
          ("NASDAQ:TSLA","TSLA"), ("AMEX:SPY","SPY"),
          ("NASDAQ:AVGO","AVGO"), ("NASDAQ:AMD","AMD"), ("NASDAQ:COST","COST"),
          ("NASDAQ:NFLX","NFLX"), ("NYSE:JPM","JPM"), ("NYSE:V","V"),
          ("NYSE:MA","MA"), ("NYSE:UNH","UNH"), ("NYSE:XOM","XOM"),
          ("NYSE:JNJ","JNJ"), ("NYSE:PG","PG"), ("NYSE:HD","HD"),
          ("BINANCE:BTCUSDT","BTC"), ("BINANCE:ETHUSDT","ETH"), ("BINANCE:SOLUSDT","SOL")
        ]
        c.executemany("INSERT OR IGNORE INTO tv_symbols(tv_symbol,label) VALUES(?,?)", defaults)

    # Surf
    c.execute("""CREATE TABLE IF NOT EXISTS surf_spots(
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      lat REAL NOT NULL,
      lon REAL NOT NULL,
      provider TEXT DEFAULT 'open-meteo'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS surf_cache(
      spot_id INTEGER PRIMARY KEY,
      height_m REAL,
      period_s REAL,
      direction_deg REAL,
      ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(spot_id) REFERENCES surf_spots(id) ON DELETE CASCADE
    )""")

    # Journal (calendar entries + images)
    c.execute("""CREATE TABLE IF NOT EXISTS journal_entries(
      id INTEGER PRIMARY KEY,
      date TEXT NOT NULL,        -- YYYY-MM-DD
      title TEXT,
      time TEXT,                 -- HH:MM
      location TEXT,
      notes TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal_images(
      id INTEGER PRIMARY KEY,
      entry_id INTEGER NOT NULL,
      filename TEXT NOT NULL,    -- stored filename (under UPLOAD_DIR)
      orig_name TEXT,
      size INTEGER,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
    )""")

    conn.commit()

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# =========================
# Helpers
# =========================
URL_RE = re.compile(r'(?P<url>(?:https?://|www\.)[^\s<>"\]]+)', re.IGNORECASE)

def linkify(text: str) -> str:
    if not text: return ""
    out, last = [], 0
    for m in URL_RE.finditer(text):
        out.append(html.escape(text[last:m.start()]))
        url = m.group('url')
        href = url if url.lower().startswith(('http://','https://')) else f'https://{url}'
        out.append(f'<a href="{html.escape(href)}" target="_blank" rel="noopener nofollow">{html.escape(url)}</a>')
        last = m.end()
    out.append(html.escape(text[last:]))
    return ''.join(out).replace('\n', '<br>')

# -------- Stocks --------
def fetch_quote(symbol: str):
    # Finnhub — current candlestick quote
    if FINNHUB:
        try:
            r = requests.get("https://finnhub.io/api/v1/quote",
                             params={"symbol": symbol, "token": FINNHUB},
                             timeout=10).json()
            p,h,l = r.get("c"), r.get("h"), r.get("l")
            if any(v is not None for v in (p,h,l)):
                return (float(p) if p is not None else None,
                        float(h) if h is not None else None,
                        float(l) if l is not None else None)
        except Exception:
            pass
    # Alpha Vantage fallback
    if ALPHA:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA}"
            q = alpha_get(url).json().get("Global Quote", {})
            p = q.get("05. price"); h = q.get("03. high"); l = q.get("04. low")
            return (float(p) if p else None,
                    float(h) if h else None,
                    float(l) if l else None)
        except Exception:
            pass
    return (None, None, None)

def upsert_latest(conn, symbol: str, price, high, low):
    if price is None and high is None and low is None: return
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO latest_prices(symbol, price, high, low, ts)
      VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(symbol) DO UPDATE SET
        price=COALESCE(excluded.price,price),
        high =COALESCE(excluded.high ,high ),
        low  =COALESCE(excluded.low  ,low  ),
        ts=CURRENT_TIMESTAMP
    """, (symbol, price, high, low))
    conn.commit()

def linear_regression_next(values):
    n = len(values)
    if n < 5: return None
    xsum = n*(n+1)/2
    xxsum = n*(n+1)*(2*n+1)/6
    ysum = sum(values)
    xysum = sum((i+1)*v for i,v in enumerate(values))
    denom = (n*xxsum - xsum*xsum)
    if denom == 0: return None
    slope = (n*xysum - xsum*ysum) / denom
    intercept = (ysum/n) - slope*(xsum/n)
    return intercept + slope*(n+1)

def fetch_predict_15(symbol: str):
    # Finnhub daily candles -> last 15 closes -> linear regression
    if FINNHUB:
        try:
            now = int(time.time())
            frm = now - 60*60*24*40
            js = requests.get("https://finnhub.io/api/v1/stock/candle",
                              params={"symbol": symbol, "resolution": "D", "from": frm, "to": now, "token": FINNHUB},
                              timeout=12).json()
            if js.get("s") == "ok":
                closes = (js.get("c") or [])[-15:]
                if len(closes) >= 5:
                    pred = linear_regression_next(closes) or (sum(closes)/len(closes))
                    with db() as conn:
                        cur = conn.cursor()
                        cur.execute("""
                          INSERT INTO predictions(symbol, pred_next, src_days, ts)
                          VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                          ON CONFLICT(symbol) DO UPDATE SET pred_next=excluded.pred_next, src_days=excluded.src_days, ts=CURRENT_TIMESTAMP
                        """, (symbol, float(pred), len(closes)))
                        conn.commit()
                    return float(pred)
        except Exception:
            pass
    # Alpha fallback
    if ALPHA:
        try:
            js = alpha_get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA}").json()
            series = js.get("Time Series (Daily)", {}) or {}
            closes = []
            for d in sorted(series.keys()):
                v = series[d].get("4. close")
                if v: closes.append(float(v))
            closes = closes[-15:]
            if len(closes) >= 5:
                pred = linear_regression_next(closes) or (sum(closes)/len(closes))
                with db() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                      INSERT INTO predictions(symbol, pred_next, src_days, ts)
                      VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                      ON CONFLICT(symbol) DO UPDATE SET pred_next=excluded.pred_next, src_days=excluded.src_days, ts=CURRENT_TIMESTAMP
                    """, (symbol, float(pred), len(closes)))
                    conn.commit()
                return float(pred)
        except Exception:
            pass
    return None

# -------- Notifiers --------
def send_sms(msg: str):
    if not all([TWILIO_SID,TWILIO_TOKEN,TWILIO_FROM,ALERT_PHONE]): return
    try:
        requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
                      data={"From": TWILIO_FROM, "To": ALERT_PHONE, "Body": msg},
                      auth=(TWILIO_SID,TWILIO_TOKEN), timeout=10)
    except Exception:
        pass

def send_telegram(msg: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID): return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
    except Exception:
        pass

def send_discord(msg: str):
    if not DISCORD_WEBHOOK_URL: return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except Exception:
        pass

def notify(msg: str):
    send_sms(msg); send_telegram(msg); send_discord(msg)

# -------- Surf helpers (Open-Meteo Marine) --------
def fetch_surf(lat: float, lon: float):
    """Nearest-hour wave height/period/direction."""
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period,wave_direction",
            "forecast_days": 1,
            "past_days": 0,
            "timezone": "UTC",
        }
        js = requests.get(url, params=params, timeout=12).json()
        hourly = js.get("hourly") or {}
        times = hourly.get("time") or []
        h = hourly.get("wave_height") or []
        p = hourly.get("wave_period") or []
        d = hourly.get("wave_direction") or []
        if not times or not h:
            return (None, None, None, None)
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        idx = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]) - now))
        height = h[idx] if idx < len(h) else None
        period = p[idx] if idx < len(p) else None
        direc  = d[idx] if idx < len(d) else None
        tstamp = times[idx]
        return (height, period, direc, tstamp)
    except Exception:
        return (None, None, None, None)

def update_surf():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id,lat,lon FROM surf_spots ORDER BY id")
        spots = cur.fetchall()
        for sid, lat, lon in spots:
            hm, ps, dg, ts = fetch_surf(lat, lon)
            if hm is None and ps is None and dg is None:
                continue
            cur2 = conn.cursor()
            cur2.execute("""
              INSERT INTO surf_cache(spot_id, height_m, period_s, direction_deg, ts)
              VALUES(?, ?, ?, ?, ?)
              ON CONFLICT(spot_id) DO UPDATE SET
                height_m=excluded.height_m, period_s=excluded.period_s,
                direction_deg=excluded.direction_deg, ts=excluded.ts
            """, (sid, hm, ps, dg, ts))
            conn.commit()

# =========================
# Schedulers
# =========================
def check_alerts():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, symbol, target, direction FROM stocks WHERE enabled=1")
        for _id, sym, tgt, direction in cur.fetchall():
            price, high, low = fetch_quote(sym)
            upsert_latest(conn, sym, price, high, low)
            if price is None: continue
            hit = (price >= tgt) if direction == "above" else (price <= tgt)
            if hit:
                cur.execute("SELECT ts FROM alerts WHERE symbol=? ORDER BY ts DESC LIMIT 1", (sym,))
                row = cur.fetchone()
                ok = True
                if row and COOLDOWN_MIN>0:
                    # sqlite gives 'YYYY-MM-DD HH:MM:SS'
                    last = datetime.fromisoformat(row[0])
                    ok = (datetime.utcnow() - last) >= timedelta(minutes=COOLDOWN_MIN)
                if ok:
                    cur.execute("INSERT INTO alerts(symbol,price,target,direction) VALUES(?,?,?,?)",
                                (sym, price, tgt, direction))
                    conn.commit()
                    notify(f"[cameronpad] {sym} {direction} {tgt} (last {price:.2f})")

def update_showcase():
    with db() as conn:
        for sym in SHOWCASE_SYMBOLS:
            p,h,l = fetch_quote(sym)
            upsert_latest(conn, sym, p, h, l)

def update_predictions():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM stocks WHERE enabled=1")
        syms = {r[0] for r in cur.fetchall()} | set(SHOWCASE_SYMBOLS)
    for s in syms:
        fetch_predict_15(s)

sched = BackgroundScheduler()
sched.add_job(check_alerts,      "interval", seconds=POLL_SECONDS,     max_instances=1, coalesce=True)
sched.add_job(update_showcase,   "interval", seconds=SHOWCASE_REFRESH, max_instances=1, coalesce=True)
sched.add_job(update_predictions,"interval", seconds=PREDICT_SECONDS,  max_instances=1, coalesce=True)
sched.add_job(update_surf,       "interval", seconds=SURF_REFRESH,     max_instances=1, coalesce=True)
sched.start()

# =========================
# Routes
# =========================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with db() as conn:
        cur = conn.cursor()

        # stocks & alerts
        cur.execute("SELECT id,symbol,target,direction,enabled FROM stocks ORDER BY symbol")
        stocks = cur.fetchall()
        cur.execute("SELECT id,symbol,price,target,direction,ts FROM alerts ORDER BY ts DESC LIMIT 100")
        alerts = cur.fetchall()

        # timestamped notes
        cur.execute("SELECT id,content,ts FROM notes ORDER BY ts DESC")
        notes = cur.fetchall()

        # Big Notepad tabs
        cur.execute("SELECT id,name FROM pad_tabs ORDER BY id")
        pad_tabs = cur.fetchall()
        sel = request.query_params.get('pad')
        pad_id = int(sel) if (sel and sel.isdigit()) else (pad_tabs[0][0] if pad_tabs else 1)
        cur.execute("SELECT name,content,updated_at FROM pad_tabs WHERE id=?", (pad_id,))
        prow = cur.fetchone() or ("General", "", None)
        pad_name, pad_content, pad_updated = prow[0], prow[1], prow[2]
        pad_html = linkify(pad_content or "")

        # TradingView symbols
        cur.execute("SELECT tv_symbol, label FROM tv_symbols ORDER BY tv_symbol")
        tv_syms = cur.fetchall()

        # Surf spots
        cur.execute("SELECT id,name,lat,lon FROM surf_spots ORDER BY name")
        surf_spots = cur.fetchall()

    today_iso = date.today().isoformat()
    tpl = env.get_template("index.html")
    return tpl.render(
        # stocks/alerts/notes
        stocks=stocks, alerts=alerts, notes=notes,
        poll=POLL_SECONDS,

        # pad tabs
        pad_tabs=pad_tabs, pad_id=pad_id, pad_name=pad_name,
        pad_content=pad_content, pad_updated=pad_updated, pad_html=pad_html,

        # tv + showcase + surf
        tv_syms=tv_syms, showcase=SHOWCASE_SYMBOLS,
        surf_spots=surf_spots, surf_refresh=SURF_REFRESH,

        # journal
        today_iso=today_iso
    )

# --- APIs for dynamic refresh ---
@app.get("/api/quotes")
def api_quotes():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT s.symbol, lp.price, lp.high, lp.low, lp.ts
          FROM stocks s
          LEFT JOIN latest_prices lp ON lp.symbol = s.symbol
          WHERE s.enabled=1
          ORDER BY s.symbol
        """)
        rows = cur.fetchall()
        data = []
        for sym, price, high, low, ts in rows:
            cur2 = conn.cursor()
            cur2.execute("SELECT pred_next FROM predictions WHERE symbol=?", (sym,))
            r = cur2.fetchone()
            pred = r[0] if r else None
            data.append({"symbol": sym, "price": price, "high": high, "low": low, "pred": pred, "ts": ts})
    return JSONResponse({"quotes": data})

@app.get("/api/showcase")
def api_showcase():
    with db() as conn:
        out=[]
        for sym in SHOWCASE_SYMBOLS:
            cur = conn.cursor()
            cur.execute("SELECT price, high, low, ts FROM latest_prices WHERE symbol=?", (sym,))
            r = cur.fetchone()
            out.append({"symbol": sym,
                        "price": r[0] if r else None,
                        "high":  r[1] if r else None,
                        "low":   r[2] if r else None,
                        "ts":    r[3] if r else None})
    return JSONResponse({"quotes": out})

@app.get("/api/surf")
def api_surf():
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT s.id, s.name, s.lat, s.lon, c.height_m, c.period_s, c.direction_deg, c.ts
          FROM surf_spots s
          LEFT JOIN surf_cache c ON c.spot_id = s.id
          ORDER BY s.name
        """)
        rows = cur.fetchall()
        data = []
        for sid, name, lat, lon, hm, ps, dg, ts in rows:
            data.append({
                "id": sid, "name": name, "lat": lat, "lon": lon,
                "height_m": hm, "period_s": ps, "direction_deg": dg, "ts": ts
            })
    return JSONResponse({"spots": data})

# Journal API
@app.get("/api/journal")
def api_journal(date: str):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("""SELECT id,title,time,location,notes,created_at
                       FROM journal_entries WHERE date=?
                       ORDER BY COALESCE(time,'23:59'), id""", (date,))
        entries = []
        for eid, title, tm, loc, notes, created in cur.fetchall():
            cur2 = conn.cursor()
            cur2.execute("SELECT id,filename,orig_name,size FROM journal_images WHERE entry_id=? ORDER BY id", (eid,))
            imgs = [{"id": iid, "url": f"/uploads/{fn}", "name": oname, "size": size}
                    for iid, fn, oname, size in cur2.fetchall()]
            entries.append({
                "id": eid, "title": title or "", "time": tm or "", "location": loc or "",
                "notes": notes or "", "created_at": created, "images": imgs
            })
    return JSONResponse({"entries": entries})

# --- Admin helpers ---
@app.post("/admin/fetch-now")
def admin_fetch_now():
    check_alerts(); update_showcase(); update_predictions(); update_surf()
    return {"ok": True}

@app.post("/admin/test-notify")
def admin_test_notify(msg: str = "Test: cameronpad Discord alert ✅"):
    notify(msg)
    return RedirectResponse("/", status_code=303)

@app.post("/admin/fetch-now-ui")
def admin_fetch_now_ui():
    check_alerts(); update_showcase(); update_predictions(); update_surf()
    return RedirectResponse("/", status_code=303)

@app.head("/")
def head_root():
    return Response(status_code=200)

# --- Stocks ---
@app.post("/stocks/add")
def add_stock(symbol: str = Form(...), target: float = Form(...), direction: str = Form(...)):
    with db() as conn:
        conn.execute("INSERT INTO stocks(symbol,target,direction) VALUES(?,?,?)",
                     (symbol.upper().strip(), target, direction))
        conn.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/stocks/toggle")
def toggle_stock(id: int = Form(...)):
    with db() as conn:
        conn.execute("UPDATE stocks SET enabled=1-enabled WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/stocks/delete")
def del_stock(id: int = Form(...)):
    with db() as conn:
        conn.execute("DELETE FROM stocks WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/", status_code=303)

# --- Notes ---
@app.post("/notes/add")
def add_note(content: str = Form(...)):
    with db() as conn:
        conn.execute("INSERT INTO notes(content) VALUES(?)", (content,))
        conn.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/notes/delete")
def del_note(id: int = Form(...)):
    with db() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/", status_code=303)

# --- TradingView symbol overview list ---
@app.post("/tv/add")
def tv_add(tv_symbol: str = Form(...), label: str = Form("")):
    s = tv_symbol.strip().upper()
    l = (label.strip() or s.split(":")[-1])[:20]
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO tv_symbols(tv_symbol,label) VALUES(?,?)", (s, l))
        conn.commit()
    return RedirectResponse("/#stocks", status_code=303)

@app.post("/tv/delete")
def tv_delete(tv_symbol: str = Form(...)):
    s = tv_symbol.strip().upper()
    with db() as conn:
        conn.execute("DELETE FROM tv_symbols WHERE tv_symbol=?", (s,))
        conn.commit()
    return RedirectResponse("/#stocks", status_code=303)

# --- Surf management ---
@app.post("/surf/add")
def surf_add(name: str = Form(...), lat: float = Form(...), lon: float = Form(...)):
    name = name.strip()
    with db() as conn:
        conn.execute("INSERT INTO surf_spots(name,lat,lon) VALUES(?,?,?)", (name, lat, lon))
        conn.commit()
    return RedirectResponse("/#surf", status_code=303)

@app.post("/surf/delete")
def surf_delete(id: int = Form(...)):
    with db() as conn:
        conn.execute("DELETE FROM surf_spots WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/#surf", status_code=303)

# --- Big Notepad (tabs) ---
@app.post("/pad/save")
def save_pad(content: str = Form(...), tab_id: int = Form(...)):
    with db() as conn:
        conn.execute(
            "UPDATE pad_tabs SET content=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (content, tab_id),
        )
        conn.commit()
    return RedirectResponse(f"/?pad={tab_id}#notes", status_code=303)

@app.post("/pad/tab/add")
def pad_tab_add(name: str = Form(...)):
    name = (name or "").strip()[:50] or "Untitled"
    with db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO pad_tabs(name) VALUES(?)", (name,))
        tab_id = cur.lastrowid
        conn.commit()
    return RedirectResponse(f"/?pad={tab_id}#notes", status_code=303)

@app.post("/pad/tab/rename")
def pad_tab_rename(id: int = Form(...), name: str = Form(...)):
    name = (name or "").strip()[:50] or "Untitled"
    with db() as conn:
        conn.execute("UPDATE pad_tabs SET name=? WHERE id=?", (name, id))
        conn.commit()
    return RedirectResponse(f"/?pad={id}#notes", status_code=303)

@app.post("/pad/tab/delete")
def pad_tab_delete(id: int = Form(...)):
    with db() as conn:
        conn.execute("DELETE FROM pad_tabs WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/#notes", status_code=303)

# --- Journal (calendar + uploads) ---
@app.post("/journal/add")
async def journal_add(
    date: str = Form(...),
    title: str = Form(""),
    time_str: str = Form("", alias="time"),
    location: str = Form(""),
    notes: str = Form(""),
    photos: Optional[List[UploadFile]] = File(None),
):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO journal_entries(date,title,time,location,notes) VALUES(?,?,?,?,?)",
                    (date, title.strip(), time_str.strip(), location.strip(), notes))
        entry_id = cur.lastrowid
        conn.commit()
        if photos:
            for f in photos:
                try:
                    content = await f.read()
                    ext = os.path.splitext(f.filename or "")[1][:10] or ".bin"
                    name = f"{uuid.uuid4().hex}{ext}"
                    dest = os.path.join(UPLOAD_DIR, name)
                    with open(dest, "wb") as out:
                        out.write(content)
                    size = len(content)
                    conn.execute("INSERT INTO journal_images(entry_id, filename, orig_name, size) VALUES(?,?,?,?)",
                                 (entry_id, name, f.filename, size))
                    conn.commit()
                except Exception:
                    continue
    return RedirectResponse("/#journal", status_code=303)

@app.post("/journal/delete")
def journal_delete(id: int = Form(...)):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT filename FROM journal_images WHERE entry_id=?", (id,))
        for (fn,) in cur.fetchall():
            try:
                os.remove(os.path.join(UPLOAD_DIR, fn))
            except Exception:
                pass
        conn.execute("DELETE FROM journal_entries WHERE id=?", (id,))
        conn.commit()
    return RedirectResponse("/#journal", status_code=303)

@app.post("/journal/image/delete")
def journal_image_delete(id: int = Form(...)):
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT filename FROM journal_images WHERE id=?", (id,))
        row = cur.fetchone()
        if row:
            fn = row[0]
            try:
                os.remove(os.path.join(UPLOAD_DIR, fn))
            except Exception:
                pass
            conn.execute("DELETE FROM journal_images WHERE id=?", (id,))
            conn.commit()
    return RedirectResponse("/#journal", status_code=303)
