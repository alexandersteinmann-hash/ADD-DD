import streamlit as st

st.set_page_config(page_title="DD Server- & Tausch-Manager", page_icon="👑", layout="centered")

# --- GLOBALER SPEICHER ---
@st.cache_resource
def get_global_data():
    return {
        "users": {"alex": "1234"},  # Benutzername und Passwort
        "servers": {
            "7f1e42af": {
                "name": "ADD",
                "creator": "alex",
                "admins": ["alex"],
                "members": ["alex"],
                "balances": {"alex": 1000},
                "requests": [],
                "updates": []  # Hier werden Server-Updates gespeichert
            }
        }
    }

global_data = get_global_data()
all_users = global_data["users"]
all_servers = global_data["servers"]

# --- ANMELDUNG & REGISTRIERUNG MIT PASSWORT ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.title("👑 DD Server, Rechte & Tausch-System")
    auth_mode = st.radio("Aktion wählen:", ["Anmelden", "Neues Konto erstellen"])
    
    username = st.text_input("Benutzername:").strip().lower()
    password = st.text_input("Passwort:", type="password")
    
    if auth_mode == "Anmelden":
        if st.button("Einloggen"):
            if username in all_users and all_users[username] == password:
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Falscher Benutzername oder falsches Passwort!")
    else:
        if st.button("Registrieren"):
            if not username or not password:
                st.warning("Bitte fülle alle Felder aus.")
            elif username in all_users:
                st.error("Dieser Benutzername ist bereits vergeben!")
            else:
                all_users[username] = password
                st.session_state.current_user = username
                st.success("Erfolgreich registriert!")
                st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"Eingeloggt als: *{st.session_state.current_user}*")
if st.sidebar.button("Abmelden"):
    st.session_state.current_user = None
    st.rerun()

# --- EINLADUNGS-LINK SICHER VERARBEITEN ---
try:
    query_params = st.query_params
    invite_server_id = query_params.get("invite")
    if isinstance(invite_server_id, list):
        invite_server_id = invite_server_id[0]
except Exception:
    invite_server_id = None

if invite_server_id and invite_server_id in all_servers:
    target_server = all_servers[invite_server_id]
    if st.session_state.current_user not in target_server["members"]:
        target_server["members"].append(st.session_state.current_user)
        target_server["balances"][st.session_state.current_user] = 1000
    st.session_state.selected_server_id = invite_server_id

# --- SERVER AUSWÄHLEN / BEITRETEN ---
my_servers = {sid: s["name"] for sid, s in all_servers.items() if st.session_state.current_user in s["members"]}

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Server per ID beitreten")
join_id = st.sidebar.text_input("Einladungs-ID / Code eingeben:")
if st.sidebar.button("Server beitreten"):
    if join_id in all_servers:
        if st.session_state.current_user not in all_servers[join_id]["members"]:
            all_servers[join_id]["members"].append(st.session_state.current_user)
            all_servers[join_id]["balances"][st.session_state.current_user] = 1000
            st.sidebar.success(f"Erfolgreich Server '{all_servers[join_id]['name']}' beigetreten!")
            st.session_state.selected_server_id = join_id
            st.rerun()
    else:
        st.sidebar.error("Ungültige Server-ID!")

if not my_servers:
    st.info("Du bist noch auf keinem Server. Tritt oben links per ID bei oder erstelle einen Server.")
    st.stop()

if "selected_server_id" not in st.session_state or st.session_state.selected_server_id not in my_servers:
    st.session_state.selected_server_id = list(my_servers.keys())[0]

selected_server_id = st.selectbox(
    "Wähle deinen Server:",
    list(my_servers.keys()),
    index=list(my_servers.keys()).index(st.session_state.selected_server_id),
    format_func=lambda x: my_servers[x]
)

server = all_servers[selected_server_id]
is_creator = (st.session_state.current_user == server["creator"])
is_admin = (st.session_state.current_user in server["admins"])

# Sicherstellen, dass Listen existieren
if "requests" not in server:
    server["requests"] = []
if "updates" not in server:
    server["updates"] = []

# --- NAVIGATIONSTABS ---
tab_dashboard, tab_tausch, tab_admin = st.tabs(["🏠 Übersicht", "🔄 DD tauschen & anfragen", "🛡️ Verwaltung & Finanzen"])

# --- 1. ÜBERSICHT ---
with tab_dashboard:
    st.header(f"Server: {server['name']}")
    st.markdown(f"🔗 *Einladungs-Link für diesen Server:* [Diesen Server teilen](?invite={selected_server_id})")
    
    # Server-Updates / Ankündigungen anzeigen
    if server["updates"]:
        st.markdown("---")
        st.subheader("📢 Aktuelle Server-Updates & News")
        for update_text in reversed(server["updates"]):
            st.info(update_text)
            
    st.markdown("---")
    st.subheader("👥 Mitglieder & Kontostände")
    for member in server["members"]:
        if member == server["creator"]:
            role = "👑 Ersteller"
        elif member in server["admins"]:
            role = "🛡️ Admin"
        else:
            role = "👤 Mitglied"
        
        bal = server["balances"].get(member, 0)
        st.write(f"- {member} ({role}): *{bal} DD*")

# --- 2. DD TAUSCHEN & ANFRAGEN ---
with tab_tausch:
    st.header("🔄 DD-Transfer & Anfragen")
    
    tausch_modus = st.radio("Aktion wählen:", ["Geld überweisen", "Geld anfragen", "Offene Anfragen an mich"])
    other_members = [m for m in server["members"] if m != st.session_state.current_user]

    if tausch_modus == "Geld überweisen":
        if not other_members:
            st.info("Keine anderen Mitglieder da.")
        else:
            empfaenger = st.selectbox("Empfänger:", other_members)
            betrag = st.number_input("Betrag in DD:", min_value=1, value=10)
            if st.button("DD überweisen"):
                sender = st.session_state.current_user
                if server["balances"].get(sender, 0) >= betrag:
                    server["balances"][sender] -= betrag
                    server["balances"][empfaenger] = server["balances"].get(empfaenger, 0) + betrag
                    st.success(f"{betrag} DD an {empfaenger} überwiesen!")
                    st.rerun()
                else:
                    st.error("Nicht genügend Guthaben!")

    elif tausch_modus == "Geld anfragen":
        if not other_members:
            st.info("Niemand da, den du fragen könntest.")
        else:
            ziel_person = st.selectbox("Anfragen bei:", other_members)
            anfrage_bet
