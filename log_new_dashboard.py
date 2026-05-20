import streamlit as st
import sqlite3
import pandas as pd
import os
import re
from datetime import datetime
from streamlit_condition_tree import condition_tree, config_from_dataframe

DB_PATH = "logs.db"
BATCH_SIZE = 10000


# ---------------- DATABASE ENGINE ----------------
def init_db(drop_first=False):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=OFF;")
    if drop_first:
        conn.execute("DROP TABLE IF EXISTS logs")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT, ip TEXT, method TEXT, url TEXT, 
        status TEXT, size INTEGER, referer TEXT, 
        user_agent TEXT, ua_type TEXT, domain TEXT
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ua_type ON logs(ua_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dt ON logs(datetime)")
    conn.commit()
    return conn


# ---------------- RELIABLE PARSER ----------------
def normalize_dt(dt):
    try:
        return datetime.strptime(dt.split()[0], "%d/%b/%Y:%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except:
        return None


def classify_ua(ua):
    ua = (ua or "").lower()
    bot_keywords = ["bot", "spider", "crawler", "yandex", "google", "ahrefs", "semrush", "dotbot", "mj12", "bing",
                    "archive", "adsbot"]
    return "Bot" if any(k in ua for k in bot_keywords) else "User"


def fast_parse(line):
    try:
        regex = r'^(\S+) \S+ \S+ \[(.*?)\] "(\S+) (.*?) \S+" (\d+) (\d+) "(.*?)" "(.*?)"'
        match = re.match(regex, line)
        if not match: return None
        ip, dt_raw, method, url, status, size, referer, ua = match.groups()
        domain = "unknown"
        parts = line.split('"')
        if len(parts) > 8:
            last_part = parts[-1].strip()
            if last_part: domain = last_part.split()[-1]
        return (normalize_dt(dt_raw), ip, method, url, status, int(size or 0), referer, ua, classify_ua(ua), domain)
    except:
        return None


# ---------------- DATA INGESTION ----------------
def ingest_file(path, progress_bar):
    conn = init_db(drop_first=True)
    cur = conn.cursor()
    batch, total, file_size, processed_bytes = [], 0, os.path.getsize(path), 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            processed_bytes += len(line.encode("utf-8"))
            parsed = fast_parse(line)
            if parsed:
                batch.append(parsed)
                total += 1
            if len(batch) >= BATCH_SIZE:
                cur.executemany(
                    "INSERT INTO logs (datetime, ip, method, url, status, size, referer, user_agent, ua_type, domain) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    batch)
                conn.commit()
                batch.clear()
                progress_bar.progress(min(processed_bytes / file_size, 1.0))
    if batch:
        cur.executemany(
            "INSERT INTO logs (datetime, ip, method, url, status, size, referer, user_agent, ua_type, domain) VALUES (?,?,?,?,?,?,?,?,?,?)",
            batch)
        conn.commit()
    conn.close()
    return total


# ---------------- UI LAYOUT ----------------
st.set_page_config(layout="wide", page_title="Log Analyzer Pro")
st.title("📊 Log Analyzer Pro")

conn = init_db()

with st.sidebar:
    st.header("⚙️ Управление")
    log_files = [f for f in os.listdir('.') if f.endswith('.log')]
    selected_file = st.selectbox("Файл лога", [""] + log_files)
    if st.button("🚀 Импорт данных"):
        if selected_file:
            progress = st.progress(0)
            count = ingest_file(selected_file, progress)
            st.success(f"Загружено: {count}")
            st.rerun()

# --- КОНСТРУКТОР ФИЛЬТРОВ ---
st.subheader("🔍 Конструктор условий")

# Конфигурация полей для фильтра
config = config_from_dataframe(
    pd.DataFrame(columns=["user_agent", "url", "referer", "status", "ip", "ua_type", "domain"]))

# Согласно доке: используем return_type='sql'
sql_query = condition_tree(
    config,
    return_type='sql',
    placeholder="Добавьте условия (используйте 'Contains' для поиска текста)",
    always_show_buttons=True
)

if st.button("🔥 ПРИМЕНИТЬ ФИЛЬТРЫ", type="primary", use_container_width=True):
    if sql_query:
        # SQLite не поддерживает ILIKE, меняем на LIKE
        st.session_state.applied_where = f"WHERE {sql_query.replace('ILIKE', 'LIKE')}"
    else:
        st.session_state.applied_where = "WHERE 1=1"
    st.rerun()

if "applied_where" not in st.session_state:
    st.session_state.applied_where = "WHERE 1=1"

where_clause = st.session_state.applied_where

# ---------------- ТАБЫ ----------------
t_ov, t_traffic, t_rare_bots, t_raw = st.tabs(["📈 Обзор", "🚗 Трафик", "🕷️ Анализ Ботов", "📄 Данные"])

with t_ov:
    try:
        m = pd.read_sql(f"SELECT COUNT(*) as total, COUNT(DISTINCT ip) as ips FROM logs {where_clause}", conn)
        c1, c2 = st.columns(2)
        c1.metric("Запросы", f"{m.iloc[0, 0]:,}")
        c2.metric("Уникальные IP", f"{m.iloc[0, 1]:,}")
    except Exception as e:
        st.error(f"Ошибка SQL: {e}")

with t_traffic:
    try:
        traffic_data = pd.read_sql(
            f"SELECT substr(datetime,1,13) as hr, COUNT(*) as count FROM logs {where_clause} GROUP BY hr", conn)
        if not traffic_data.empty: st.line_chart(traffic_data.set_index("hr"))
        st.write("### Топ URL")
        urls = pd.read_sql(
            f"SELECT url, COUNT(*) as count FROM logs {where_clause} GROUP BY url ORDER BY count DESC LIMIT 50", conn)
        st.dataframe(urls, use_container_width=True)
    except:
        st.info("Нет данных")

with t_rare_bots:
    st.write("### Список ботов")
    # Комбинируем фильтр дерева и признак бота
    clean_filter = where_clause.replace("WHERE ", "", 1)
    bot_where = f"WHERE ({clean_filter}) AND ua_type = 'Bot'"

    try:
        df_bots = pd.read_sql(
            f"SELECT user_agent, COUNT(*) as hits FROM logs {bot_where} GROUP BY user_agent ORDER BY hits DESC", conn)
        if df_bots.empty:
            st.info("Боты не найдены.")
        else:
            event = st.dataframe(df_bots, use_container_width=True, hide_index=True, on_select="rerun",
                                 selection_mode="single-row")
            selection = event.selection.get("rows", [])
            if selection:
                selected_ua = df_bots.iloc[selection[0]]["user_agent"]
                st.divider()
                st.code(selected_ua)
                cd1, cd2 = st.columns([1, 2])
                with cd1:
                    st.table(pd.read_sql(
                        "SELECT ip, COUNT(*) as count FROM logs WHERE user_agent = ? GROUP BY ip ORDER BY count DESC LIMIT 10",
                        conn, params=[selected_ua]))
                with cd2:
                    bot_time = pd.read_sql(
                        "SELECT substr(datetime,1,13) as hr, COUNT(*) as count FROM logs WHERE user_agent = ? GROUP BY hr ORDER BY hr ASC",
                        conn, params=[selected_ua])
                    if not bot_time.empty: st.area_chart(bot_time.set_index("hr"))
    except:
        st.info("Ошибка в условиях фильтрации")

with t_raw:
    st.markdown(f"**SQL Фильтр:** `{where_clause}`")
    try:
        raw_data = pd.read_sql(f"SELECT * FROM logs {where_clause} ORDER BY datetime DESC LIMIT 100", conn)
        st.dataframe(raw_data, use_container_width=True)
    except:
        st.error("Некорректный SQL запрос")