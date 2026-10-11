import streamlit as st
import uuid

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="DD Server- & Tausch-Manager", page_icon="👑", layout="wide")

# --- DATENBANK-SIMULATION (Session State) ---
if "servers" not in st.session_state:
    st.session_state.servers = {}  # Struktur: {server_id: {name, creator, admins: [], members: [], balances: {}, pending_trades: []}}
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# --- LOGIN / USER-WAHL ---
st.title("👑 DD Server, Rechte & Tausch-System")

if not st.session_state.current_user:
    st.subheader("Anmelden / Benutzer wählen")
    username = st.text_input("Gib deinen Benutzernamen ein:").strip()
    if st.button("Einloggen") and username:
        st.session_state.current_user = username
        st.rerun()
    st.stop()

# Sidebar-Info & Logout
st.sidebar.write(f"Eingeloggt als: *{st.session_state.current_user}*")
if st.sidebar.button("Abmelden"):
    st.session_state.current_user = None
    st.rerun()

# --- URL-PARAMETER FÜR EINLADUNGEN ---
query_params = st.query_params
invite_server_id = query_params.get("invite")

if invite_server_id and invite_server_id in st.session_state.servers:
    server = st.session_state.servers[invite_server_id]
    user = st.session_state.current_user
    if user not in server["members"]:
        server["members"].append(user)
        server["balances"][user] = 0  # Startguthaben für neue Mitglieder: 0 DD
        st.success(f"🎉 Du bist erfolgreich dem Server *{server['name']}* beigetreten!")
        st.query_params.clear()

# --- SERVER ERSTELLEN ---
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Neuen Server erstellen")
new_server_name = st.sidebar.text_input("Server Name")
if st.sidebar.button("Server erstellen") and new_server_name:
    server_id = str(uuid.uuid4())[:8]
    st.session_state.servers[server_id] = {
        "name": new_server_name,
        "creator": st.session_state.current_user,   # DU bist der unantastbare Ersteller
        "admins": [st.session_state.current_user],  # Ersteller ist automatisch Admin
        "members": [st.session_state.current_user],
        "balances": {st.session_state.current_user: 1000}, # Startguthaben für den Gründer
        "pending_trades": []
    }
    st.sidebar.success(f"Server '{new_server_name}' erstellt!")

# --- SERVER AUSWÄHLEN ---
my_servers = {sid: s["name"] for sid, s in st.session_state.servers.items() if st.session_state.current_user in s["members"]}

if not my_servers:
    st.info("Du bist noch auf keinem Server. Erstelle links einen Server oder nutze einen Einladungslink!")
    st.stop()

selected_server_id = st.selectbox("Wähle deinen Server:", list(my_servers.keys()), format_func=lambda x: my_servers[x])
server = st.session_state.servers[selected_server_id]

# --- RECHTEPRÜFUNG ---
is_creator = st.session_state.current_user == server["creator"]
is_admin = st.session_state.current_user in server["admins"]

# --- NAVIGATIONSTABS ---
tab_dashboard, tab_tausch, tab_admin = st.tabs(["🏠 Übersicht", "🔄 DD untereinander tauschen", "🛡️ Verwaltung & Finanzen"])

# --- 1. ÜBERSICHT ---
with tab_dashboard:
    st.header(f"Server: {server['name']}")
    
    # Einladungslink generieren
    base_url = "http://localhost:8501" 
    st.info(f"🔗 *Einladungs-Link für diesen Server:* {base_url}?invite={selected_server_id}")
    
    st.subheader("👥 Mitglieder & Kontostände")
    for member in server["members"]:
        if member == server["creator"]:
            role = "👑 Ersteller"
        elif member in server["admins"]:
            role = "🛡️ Admin"
        else:
            role = "👤 Mitglied"
            
        bal = server["balances"].get(member, 0)
        st.write(f"- *{member}* ({role}): {bal} DD")

# --- 2. DD TAUSCHEN (MIT ZUSTIMMUNG ALLER BETROFFENEN) ---
with tab_tausch:
    st.header("🔄 DD-Transfer zwischen Usern")
    st.caption("Ein Tausch wird erst ausgeführt, wenn die empfangende Person zustimmt.")
    
    other_members = [m for m in server["members"] if m != st.s
