import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, date
import os
import random

# --- VIBE & DESIGN ---
st.set_page_config(page_title="Slam Dunk Tracker", page_icon="🏀", layout="wide")

st.markdown("""
    <style>
    .main-title { font-family: 'Impact', sans-serif; color: #FF5722; font-size: 3.5rem !important; text-transform: uppercase; text-shadow: 2px 2px 5px rgba(255, 87, 34, 0.4); text-align: center; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 40px; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #FF5722 !important; font-weight: 900; }
    .stButton>button { background-color: #FF5722; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #e64a19; color: white; transform: scale(1.02); }
    .record-card { background: #1e293b; border-left: 4px solid #FF5722; padding: 15px; border-radius: 8px; margin-bottom: 10px; color: #f8fafc !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .record-card h4 { color: #FF5722 !important; margin-top: 0; }
    .record-card p { color: #f8fafc !important; margin-bottom: 5px; }
    .highlight-banner { background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-left: 5px solid #FF5722; color: white; padding: 15px 20px; border-radius: 10px; font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
    .player-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #FF5722; border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 20px; color: white; }
    .pro-card-container { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 15px; padding: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.5); color: #f8fafc; }
    .pro-card-stats { display: flex; justify-content: space-around; text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #334155; flex-wrap: wrap; gap: 15px; }
    .pro-stat-val { font-size: 26px; font-weight: 900; color: #FF5722; }
    .pro-stat-label { color: #94a3b8; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }
    .form-circle { display: inline-block; width: 25px; height: 25px; border-radius: 50%; text-align: center; line-height: 25px; font-weight: bold; margin-right: 5px; font-size: 12px; }
    .form-w { background-color: #4CAF50; color: white; }
    .form-l { background-color: #F44336; color: white; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = 'office_hoops_v2.db'
UPLOAD_DIR = 'avatars'
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(matches)")
    cols = [col[1] for col in c.fetchall()]
    if 'player1' in cols:
        c.execute("DROP TABLE matches")
        c.execute("DROP TABLE IF EXISTS match_scores")
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (username TEXT PRIMARY KEY, nickname TEXT, avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, mode TEXT, is_historical BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS match_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER, player_name TEXT, shots INTEGER, hits INTEGER, pts REAL, shot_data TEXT)''')
    c.execute("SELECT * FROM users WHERE username='Admin'")
    if not c.fetchone(): c.execute("INSERT INTO users VALUES (?, ?, ?)", ('Admin', hashlib.sha256(b'admin123').hexdigest(), 'admin'))
    conn.commit()
    conn.close()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    data = c.fetchall()
    conn.close()
    return data

def format_date_eu(date_str):
    if not date_str: return ""
    try: return datetime.strptime(str(date_str)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except: return str(date_str)

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': '', 'role': ''})

init_db()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/889/889442.png", width=100)
    st.title("Locker Room 🚪")
    if not st.session_state['logged_in']:
        menu = ["Login", "Registrieren"]
        choice = st.selectbox("Menü", menu)
        user = st.text_input("Player Name")
        pw = st.text_input("Passwort", type='password')
        if choice == "Registrieren" and st.button("Account anlegen"):
            try:
                run_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (user, hashlib.sha256(pw.encode()).hexdigest(), 'user'))
                run_query("INSERT OR IGNORE INTO profiles (username, nickname, avatar) VALUES (?, ?, ?)", (user, user, ""))
                st.success("Erfolgreich! Logg dich jetzt ein.")
            except: st.error("Name schon vergeben!")
        elif choice == "Login" and st.button("Login"):
            res = run_query("SELECT password, role FROM users WHERE username=?", (user,))
            if res and res[0][0] == hashlib.sha256(pw.encode()).hexdigest():
                st.session_state.update({'logged_in': True, 'username': user, 'role': res[0][1]})
                st.rerun()
            else: st.warning("Falsche Daten!")
    else:
        st.success(f"Eingeloggt: {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

st.markdown("<h1 class='main-title'>🏀 Office Slam Dunk Tracker</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>High-End Büro-Basketball Analytics</p>", unsafe_allow_html=True)

if st.session_state['logged_in']:
    conn = sqlite3.connect(DB_FILE)
    df_matches = pd.read_sql("SELECT * FROM matches", conn)
    df_scores = pd.read_sql("SELECT * FROM match_scores", conn)
    conn.close()
    
    df_all = pd.DataFrame()
    if not df_matches.empty and not df_scores.empty:
        df_all = pd.merge(df_scores, df_matches, left_on='match_id', right_on='id').sort_values(by=['date', 'match_id'])
    
    p_stats = {}
    h2h = {}
    streaks = {}

    if not df_all.empty:
        for m_id, group in df_all.groupby('match_id', sort=False):
            max_pts = group['pts'].max()
            winners = group[group['pts'] == max_pts]['player_name'].tolist()
            
            for i, row1 in group.iterrows():
                p1 = row1['player_name']
                
                if p1 not in p_stats:
                    p_stats[p1] = {'hits': 0, 'wins': 0, 'bonus': 0, 'games': 0, 'pts': 0, 'shots': 0, 'no_scores': 0}
                p_stats[p1]['hits'] += row1['hits']
                p_stats[p1]['bonus'] += max(0, row1['pts'] - row1['hits'])
                p_stats[p1]['games'] += 1
                p_stats[p1]['pts'] += row1['pts']
                p_stats[p1]['shots'] += row1['shots']
                if row1['pts'] == 0: p_stats[p1]['no_scores'] += 1
                if p1 in winners: p_stats[p1]['wins'] += (1 / len(winners))

                if p1 not in h2h: h2h[p1] = {}
                for j, row2 in group.iterrows():
                    p2 = row2['player_name']
                    if p1 == p2: continue
                    if p2 not in h2h[p1]: h2h[p1][p2] = {'W': 0, 'L': 0, 'T': 0}
                    if row1['pts'] > row2['pts']: h2h[p1][p2]['W'] += 1
                    elif row1['pts'] < row2['pts']: h2h[p1][p2]['L'] += 1
                    else: h2h[p1][p2]['T'] += 1

                if p1 not in streaks:
                    streaks[p1] = {'type': None, 'len': 0, 'max_W': 0, 'max_W_breaker': "", 'max_L': 0, 'last_5': []}
                
                is_win = (p1 in winners)
                streaks[p1]['last_5'].append('W' if is_win else 'L')
                if len(streaks[p1]['last_5']) > 5: streaks[p1]['last_5'].pop(0)
                
                if is_win:
                    if streaks[p1]['type'] == 'W': streaks[p1]['len'] += 1
                    else: streaks[p1]['type'] = 'W'; streaks[p1]['len'] = 1
                    if streaks[p1]['len'] > streaks[p1]['max_W']:
                        streaks[p1]['max_W'] = streaks[p1]['len']
                else:
                    if streaks[p1]['type'] == 'W' and streaks[p1]['len'] > 0:
                        if streaks[p1]['len'] == streaks[p1]['max_W']:
                            streaks[p1]['max_W_breaker'] = ", ".join(winners)
                    if streaks[p1]['type'] == 'L': streaks[p1]['len'] += 1
                    else: streaks[p1]['type'] = 'L'; streaks[p1]['len'] = 1
                    if streaks[p1]['len'] > streaks[p1]['max_L']:
                        streaks[p1]['max_L'] = streaks[p1]['len']

        highlights = []
        for p, d in p_stats.items():
            nick = run_query("SELECT nickname FROM profiles WHERE username=?", (p,))
            nick = nick[0][0] if nick and nick[0][0] else p
            if (int(d['hits']) // 50) * 50 > 0 and (d['hits'] % 50) <= 15: 
                highlights.append(f"🎯 **Meilenstein erreicht!** {nick} hat die legendäre **{(int(d['hits']) // 50) * 50}-Treffer-Marke** durchbrochen!")
            if (int(d['games']) // 25) * 25 > 0 and (d['games'] % 25) <= 3:
                highlights.append(f"🏟️ **Jubiläum!** {nick} absolvierte soeben sein **{(int(d['games']) // 25) * 25}. Match**!")

        if highlights:
            for h in random.sample(highlights, min(2, len(highlights))):
                st.markdown(f"<div class='highlight-banner'>{h}</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("🏆 Matches Gesamt", len(df_matches))
        c2.metric("⚔️ Letzter Modus", df_all.iloc[-1]['mode'])
        c3.metric("🔥 Letztes Match", format_date_eu(df_all.iloc[-1]['date']))
        st.divider()

    tabs = st.tabs(["📊 Leaderboard & Records", "👤 Pro Player Profile", "📈 Vergleich", "📝 Court (Neues Match)", "⚙️ Admin & Import"])
    
    # ---------------- 1. LEADERBOARD ----------------
    with tabs[0]:
        st.subheader("👑 Hall of Fame & Ranglisten")
        if not df_all.empty:
            def get_ranked_stats(df_subset):
                sub_stats = {}
                for m_id, group in df_subset.groupby('match_id'):
                    max_pts = group['pts'].max()
                    winners = group[group['pts'] == max_pts]['player_name'].tolist()
                    for _, row in group.iterrows():
                        p = row['player_name']
                        if p not in sub_stats:
                            sub_stats[p] = {'games':0, 'wins':0, 'pts':0, 'hits':0, 'shots':0, 'bonus':0}
                        sub_stats[p]['games'] += 1
                        sub_stats[p]['pts'] += row['pts']
                        sub_stats[p]['hits'] += row['hits']
                        sub_stats[p]['shots'] += row['shots']
                        sub_stats[p]['bonus'] += max(0, row['pts'] - row['hits'])
                        if p in winners: sub_stats[p]['wins'] += (1 / len(winners))
                lst = []
                for p, d in sub_stats.items():
                    lst.append({
                        'Spieler': p, 'Spiele': d['games'], 'Siege': round(d['wins'], 1),
                        'Siegquote (%)': round((d['wins']/d['games'])*100 if d['games']>0 else 0, 1),
                        'Trefferquote (%)': round((d['hits']/d['shots'])*100 if d['shots']>0 else 0, 1),
                        'Trash-Bonus Quote (%)': round((d['bonus']/d['hits'])*100 if d['hits']>0 else 0, 1),
                        'Ø Punkte': round(d['pts']/d['games'] if d['games']>0 else 0, 1)
                    })
                return pd.DataFrame(lst).sort_values(by=['Siegquote (%)', 'Siege', 'Spiele', 'Ø Punkte'], ascending=[False, False, False, False]).reset_index(drop=True)

            rank_mode = st.radio("Ranglisten-Ansicht:", ["Gesamtrangliste"] + df_all['mode'].unique().tolist(), horizontal=True)
            df_ranking = get_ranked_stats(df_all) if rank_mode == "Gesamtrangliste" else get_ranked_stats(df_all[df_all['mode'] == rank_mode])
            if not df_ranking.empty: st.dataframe(df_ranking, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🔥 Streaks & Rekorde")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.markdown("<div class='record-card'><h4>🔥 Aktuelle Top Streaks</h4>", unsafe_allow_html=True)
                active_streaks = sorted([(p, d) for p, d in streaks.items() if d['type'] == 'W' and d['len'] > 1], key=lambda x: x[1]['len'], reverse=True)
                if active_streaks:
                    for p, d in active_streaks[:3]: st.markdown(f"<p><b>{p}</b>: {d['len']} Siege in Folge</p>", unsafe_allow_html=True)
                else: st.markdown("<p>Aktuell keine aktiven Siegesserien.</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_s2:
                st.markdown("<div class='record-card'><h4>🏆 All-Time Längste Siegesserien</h4>", unsafe_allow_html=True)
                top_streaks = sorted([(p, d) for p, d in streaks.items() if d['max_W'] > 0], key=lambda x: x[1]['max_W'], reverse=True)[:3]
                for p, d in top_streaks:
                    brk = f"(Beendet von {d['max_W_breaker']})" if d['max_W_breaker'] else "(Noch Aktiv!)"
                    st.markdown(f"<p><b>{p}</b>: {d['max_W']} Siege {brk}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            st.subheader("📜 Match-Historie")
            sort_order = st.radio("Sortierung:", ["Neueste zuerst", "Älteste zuerst"], horizontal=True)
            
            hist_rows = []
            for m_id, group in df_all.groupby('match_id'):
                date_val = group['date'].iloc[0]
                players_str = ", ".join([f"{r['player_name']} ({int(r['pts'])} Pkt, {int(r['hits'])} Tr)" for _, r in group.iterrows()])
                hist_rows.append({'Match-ID': int(m_id), 'Datum_raw': date_val, 'Datum': format_date_eu(date_val), 'Modus': group['mode'].iloc[0], 'Ergebnis': players_str})
            
            if hist_rows:
                df_show = pd.DataFrame(hist_rows)
                df_show = df_show.sort_values(by=['Match-ID'], ascending=(sort_order == "Älteste zuerst"))
                st.dataframe(df_show[['Datum', 'Modus', 'Ergebnis']], use_container_width=True, hide_index=True)

    # ---------------- 2. PRO PLAYER PROFILE ----------------
    with tabs[1]:
        st.subheader("👤 Pro Player Profile & Analytics")
        if not df_all.empty and p_stats:
            selected_player = st.selectbox("Wähle einen Athleten aus:", list(p_stats.keys()))
            
            nick_res = run_query("SELECT nickname, avatar FROM profiles WHERE username=?", (selected_player,))
            nickname = nick_res[0][0] if nick_res and nick_res[0][0] else selected_player
            avatar = nick_res[0][1] if nick_res and nick_res[0][1] else ""
            
            player_matches = df_all[df_all['player_name'] == selected_player].sort_values(by=['date', 'match_id']).reset_index(drop=True)
            hist_data, current_form_val, hist_avg_rate, form_str = [], 0, 0, ""
            
            if not player_matches.empty:
                d = p_stats[selected_player]
                win_rate = (d['wins'] / d['games']) * 100 if d['games'] > 0 else 0
                avg_pts = d['pts'] / d['games'] if d['games'] > 0 else 0
                hit_rate = (d['hits'] / d['shots']) * 100 if d['shots'] > 0 else 0
                bonus_rate = (d['bonus'] / d['hits'] * 100) if d['hits'] > 0 else 0
                
                form_html = "".join([f"<div class='form-circle {'form-w' if x=='W' else 'form-l'}'>{x}</div>" for x in streaks[selected_player]['last_5']])
                
                nemesis, favorite = "Niemand", "Niemand"
                if selected_player in h2h and h2h[selected_player]:
                    opp_l = max(h2h[selected_player].items(), key=lambda x: x[1]['L'])
                    opp_w = max(h2h[selected_player].items(), key=lambda x: x[1]['W'])
                    if opp_l[1]['L'] > 0: nemesis = f"{opp_l[0]} ({opp_l[1]['L']} Niederlagen)"
                    if opp_w[1]['W'] > 0: favorite = f"{opp_w[0]} ({opp_w[1]['W']} Siege)"

                for idx, row in player_matches.iterrows():
                    hist_data.append({'Match': f"M{idx+1:02d}", 'pts': row['pts'], 'hits': row['hits'], 'shots': row['shots'], 'bonus': max(0, row['pts']-row['hits'])})
                
                df_hist = pd.DataFrame(hist_data)
                df_hist['Roll_Hits'] = df_hist['hits'].rolling(window=5, min_periods=1).sum()
                df_hist['Roll_Shots'] = df_hist['shots'].rolling(window=5, min_periods=1).sum()
                df_hist['Form-Index (%)'] = (df_hist['Roll_Hits'] / df_hist['Roll_Shots']) * 100
                df_hist['Trefferquote Kumuliert (%)'] = (df_hist['hits'].cumsum() / df_hist['shots'].cumsum()) * 100
                df_hist['Trash-Bonus Quote Kumuliert (%)'] = (df_hist['bonus'].cumsum() / df_hist['hits'].cumsum() * 100).fillna(0)
                
                current_form_val = df_hist.iloc[-1]['Form-Index (%)']
                form_str = "🔥 ON FIRE" if current_form_val >= hit_rate else "🧊 COLD STREAK"

                st.markdown(f"""
                <div class='pro-card-container'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h1 style='margin: 0; font-size: 3rem; font-family: Impact;'>{nickname}</h1>
                            <p style='color: #FF5722; font-weight: bold; margin: 0;'>{form_str} (Form: {current_form_val:.1f}%)</p>
                        </div>
                        <div><div class='pro-stat-label' style='margin-bottom:5px;'>Letzte 5 Spiele</div><div>{form_html}</div></div>
                    </div>
                    <div class='pro-card-stats'>
                        <div><div class='pro-stat-val'>{win_rate:.1f}%</div><div class='pro-stat-label'>Siegquote</div></div>
                        <div><div class='pro-stat-val'>{avg_pts:.1f}</div><div class='pro-stat-label'>Ø Punkte</div></div>
                        <div><div class='pro-stat-val'>{hit_rate:.1f}%</div><div class='pro-stat-label'>Trefferquote</div></div>
                        <div><div class='pro-stat-val'>{bonus_rate:.1f}%</div><div class='pro-stat-label'>Trash-Bonus Quote</div></div>
                        <div><div class='pro-stat-val'>{int(d['games'])}</div><div class='pro-stat-label'>Matches</div></div>
                    </div>
                    <hr style='border-color: #334155;'>
                    <div style='display: flex; justify-content: space-around;'>
                        <div><span class='pro-stat-label'>Erzrivale:</span> <b>{nemesis}</b></div>
                        <div><span class='pro-stat-label'>Lieblingsgegner:</span> <b>{favorite}</b></div>
                    </div>
                </div><br>
                """, unsafe_allow_html=True)
                
                c_ch1, c_ch2 = st.columns(2)
                with c_ch1:
                    st.write("📈 **Trefferquote Kumuliert (All-Time):**")
                    st.line_chart(df_hist.set_index('Match')[['Trefferquote Kumuliert (%)']])
                with c_ch2:
                    st.write("🗑️ **Trash-Bonus Quote Kumuliert (All-Time):**")
                    st.line_chart(df_hist.set_index('Match')[['Trash-Bonus Quote Kumuliert (%)']])
                
                st.write("📊 **Form-Index (Letzte 5 Spiele):**")
                st.line_chart(df_hist.set_index('Match')[['Form-Index (%)']])

    # ---------------- 3. VERGLEICH (COMPARE) ----------------
    with tabs[2]:
        st.subheader("📈 Spieler-Vergleich")
        if not df_all.empty:
            all_players = df_all['player_name'].unique().tolist()
            comp_players = st.multiselect("Wähle Spieler zum Vergleichen:", all_players, default=all_players[:2] if len(all_players)>1 else all_players)
            
            if comp_players:
                comp_data = []
                for p in comp_players:
                    p_matches = df_all[df_all['player_name'] == p].sort_values(by=['date', 'match_id']).reset_index(drop=True)
                    cum_hits = 0; cum_shots = 0
                    for idx, r in p_matches.iterrows():
                        cum_hits += r['hits']
                        cum_shots += r['shots']
                        comp_data.append({'Match-Nr.': idx+1, 'Spieler': p, 'Kumulierte Trefferquote (%)': (cum_hits/cum_shots)*100 if cum_shots>0 else 0})
                
                df_comp = pd.DataFrame(comp_data)
                if not df_comp.empty:
                    df_pivot = df_comp.pivot(index='Match-Nr.', columns='Spieler', values='Kumulierte Trefferquote (%)')
                    df_pivot = df_pivot.ffill()
                    st.write("**Entwicklung der All-Time Trefferquote (nach Anzahl gespielter Matches):**")
                    st.line_chart(df_pivot)
                    st.caption("Die X-Achse zeigt das wievielte Match des jeweiligen Spielers es war. So kann man die Erfahrungs-Kurven exakt übereinanderlegen!")

    # ---------------- 4. COURT (NEUES MATCH) ----------------
    with tabs[3]:
        st.subheader("Trage das nächste Duell ein ✍️")
        
        if 'match_players_count' not in st.session_state: st.session_state.match_players_count = 2

        c_add, c_rem = st.columns(2)
        if c_add.button("➕ Weiteren Spieler hinzufügen", use_container_width=True): st.session_state.match_players_count += 1; st.rerun()
        if c_rem.button("➖ Spieler entfernen", use_container_width=True) and st.session_state.match_players_count > 2: st.session_state.match_players_count -= 1; st.rerun()

        st.divider()
        existing_players = sorted(df_all['player_name'].unique().tolist()) if not df_all.empty else []
        options = existing_players + ["➕ Neuer Spieler"]

        players_data = []
        for i in range(st.session_state.match_players_count):
            with st.container(border=True):
                st.markdown(f"#### 🏀 Spieler {i+1}")
                
                default_idx = existing_players.index(st.session_state['username']) if (i == 0 and st.session_state['username'] in existing_players) else 0
                sel = st.selectbox(f"Name (Spieler {i+1})", options, index=default_idx if options else 0, key=f"sel_{i}")
                
                p_name = st.text_input("Name eingeben:", key=f"newp_{i}") if sel == "➕ Neuer Spieler" else sel
                
                use_detailed = st.toggle("🎯 Wurf für Wurf eintragen", key=f"det_{i}")
                shots_val, hits_val, pts_val, shot_array = 10, 0, 0, []
                
                if use_detailed:
                    cols = st.columns(10)
                    for s in range(10):
                        res = cols[s].selectbox("Wurf", ["❌", "🏀", "🗑️"], index=None, placeholder=f"{s+1}. Wurf", key=f"w_{i}_{s}", label_visibility="collapsed")
                        shot_array.append(res)
                    reg_hits = sum(1 for x in shot_array if x in ["🏀", "🗑️"])
                    reg_bonus = sum(1 for x in shot_array if x == "🗑️")
                else:
                    c_a, c_b = st.columns(2)
                    reg_hits = c_a.number_input("Treffer (max 10)", min_value=0, max_value=10, key=f"rh_{i}")
                    reg_bonus = c_b.number_input("Davon Mülleimer 🗑️", min_value=0, max_value=int(reg_hits), key=f"rb_{i}")
                
                hits_val += reg_hits; pts_val += (reg_hits + reg_bonus)
                players_data.append({'name': p_name, 'shots': shots_val, 'hits': hits_val, 'pts': pts_val, 'shot_data': str(shot_array), 'use_det': use_detailed})

        st.divider()
        
        # --- AUTO OVERTIME LOGIC ---
        current_pts = [p['pts'] for p in players_data]
        max_pts = max(current_pts) if current_pts else 0
        tied_players = [i for i, pts in enumerate(current_pts) if pts == max_pts]
        
        ot_round = 0
        while len(tied_players) > 1 and max_pts > 0:
            ot_round += 1
            st.markdown(f"### 🚨 OVERTIME {ot_round}")
            st.warning(f"Gleichstand! Diese Spieler treten an: **{', '.join([players_data[i]['name'] for i in tied_players])}**")
            
            for i in tied_players:
                with st.container(border=True):
                    st.markdown(f"#### 🏀 {players_data[i]['name']}")
                    st.info(f"📊 Aktueller Gesamt-Punktestand: **{players_data[i]['pts']} Punkte**")
                    
                    use_det_ot = st.toggle(f"🎯 Detail-Eingabe (OT {ot_round})", value=players_data[i]['use_det'], key=f"det_ot_{i}_{ot_round}")
                    
                    if use_det_ot:
                        cols = st.columns(3)
                        ot_shots = []
                        for s in range(3):
                            res = cols[s].selectbox("Wurf", ["❌", "🏀", "🗑️"], index=None, placeholder=f"{s+1}. Wurf", key=f"w_ot_{i}_{ot_round}_{s}", label_visibility="collapsed")
                            ot_shots.append(res)
                        reg_hits = sum(1 for x in ot_shots if x in ["🏀", "🗑️"])
                        reg_bonus = sum(1 for x in ot_shots if x == "🗑️")
                    else:
                        c1, c2 = st.columns(2)
                        reg_hits = c1.number_input(f"OT Treffer", min_value=0, max_value=3, key=f"oth_{i}_{ot_round}")
                        reg_bonus = c2.number_input(f"OT Bonus", min_value=0, max_value=int(reg_hits), key=f"otb_{i}_{ot_round}")
                    
                    players_data[i]['hits'] += reg_hits
                    players_data[i]['pts'] += (reg_hits + reg_bonus)
                    players_data[i]['shots'] += 3

            current_pts = [players_data[i]['pts'] for i in tied_players]
            max_ot_pts = max(current_pts) if current_pts else 0
            new_tied_players = [i for i in tied_players if players_data[i]['pts'] == max_ot_pts]
            
            if len(new_tied_players) > 1:
                if not st.checkbox(f"✅ Ergebnisse für Overtime {ot_round} bestätigen, um fortzufahren", key=f"conf_ot_{ot_round}"):
                    break
                tied_players = new_tied_players
            else:
                break
                
        st.divider()
        if st.button("🔥 MATCH SPEICHERN", type="primary", use_container_width=True):
            if any(not p['name'] or not p['name'].strip() for p in players_data):
                st.error("Bitte alle Namen ausfüllen (bei 'Neuer Spieler' das Textfeld nutzen)!")
            else:
                mode = "1v" * (len(players_data)-1) + "1"
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                cur.execute("INSERT INTO matches (date, mode, is_historical) VALUES (?, ?, ?)", (str(date.today()), mode, False))
                m_id = cur.
