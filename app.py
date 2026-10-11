import streamlit as st

st.set_page_config(page_title="DD Server- & Tausch-Manager", page_icon="👑", layout="centered")

# --- GLOBALER SPEICHER (Damit alle Nutzer auf dieselben Server zugreifen) ---
@st.cache_resource
def get_global_data():
    # Standard-Server "ADD" anlegen
    return {
        "servers": {
            "7f1e42af": {
                "name": "ADD",
                "creator": "alex",
                "admins": ["alex"],
                "members": ["alex"],
                "balances": {"alex": 1000}
            }
        }
    }

global_data = get_global_data()
all_servers = global_data["servers"]

# --- ANMELDUNG / BENUTZERNAME ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.title("👑 DD Server, Rechte & Tausch-System")
    st.subheader("Anmelden / Benutzer wählen")
    username = st.text_input("Gib deinen Benutzernamen ein:").strip().lower()
    
    if st.button("Einloggen") and username:
        st.session_state.current_user = username
        st.rerun()
    st.stop()

# --- SIDEBAR (LOGOUT & BENUTZER-INFO) ---
st.sidebar.write(f"Eingeloggt als: *{st.session_state.current_user}*")
if st.sidebar.button("Abmelden"):
    st.session_state.current_user = None
    st.rerun()

# --- EINLADUNGS-LINK VERARBEITEN (Auto-Beitritt) ---
query_params = st.query_params
invite_server_id = query_params.get("invite")

if invite_server_id and invite_server_id in all_servers:
    target_server = all_servers[invite_server_id]
    # Falls der Nutzer noch nicht Mitglied ist, automatisch hinzufügen & 1000 DD Startguthaben geben
    if st.session_state.current_user not in target_server["members"]:
        target_server["members"].append(st.session_state.current_user)
        target_server["balances"][st.session_state.current_user] = 1000
    st.session_state.selected_server_id = invite_server_id

# --- SERVER AUSWÄHLEN / BEITRETEN MANUELL ---
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

# Aktiven Server festlegen
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

# --- NAVIGATIONSTABS ---
tab_dashboard, tab_tausch, tab_admin = st.tabs(["🏠 Übersicht", "🔄 DD untereinander tauschen", "🛡️ Verwaltung & Finanzen"])

# --- 1. ÜBERSICHT ---
with tab_dashboard:
    st.header(f"Server: {server['name']}")
    
    # Einladungs-Link anzeigen
    st.markdown(f"🔗 *Einladungs-Link für diesen Server:* ?invite={selected_server_id}")
    st.caption("Einfach den Link kopieren und weiterschicken. Neue Personen treten direkt diesem Server bei!")

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

# --- 2. DD TAUSCHEN ---
with tab_tausch:
    st.header("🔄 DD-Transfer zwischen Usern")
    other_members = [m for m in server["members"] if m != st.session_state.current_user]
    if not other_members:
        st.info("Es sind noch keine anderen Mitglieder auf diesem Server.")
    else:
        empfaenger = st.selectbox("Empfänger auswählen:", other_members)
        betrag = st.number_input("Betrag in DD:", min_value=1, value=10)
        if st.button("DD überweisen"):
            sender = st.session_state.current_user
            if server["balances"].get(sender, 0) >= betrag:
                server["balances"][sender] -= betrag
                server["balances"][empfaenger] = server["balances"].get(empfaenger, 0) + betrag
                st.success(f"{betrag} DD erfolgreich an {empfaenger} überwiesen!")
                st.rerun()
            else:
                st.error("Nicht genügend DD Guthaben!")

# --- 3. VERWALTUNG & FINANZEN ---
with tab_admin:
    st.header("🛡️ Verwaltung & Finanzen")
    if is_creator or is_admin:
        st.subheader("💰 Kontostand jedes Mitglieds anpassen")
        
        # JEDES Mitglied wählbar (auch du selbst!)
        target_member = st.selectbox("Mitglied auswählen:", server["members"])
        new_balance = st.number_input("Neuer Kontostand (DD):", value=int(server["balances"].get(target_member, 0)))
        
        if st.button("Kontostand aktualisieren"):
            server["balances"][target_member] = new_balance
            st.success(f"Kontostand von {target_member} auf {new_balance} DD gesetzt!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("👑 Rechte verwalten")
        non_admins = [m for m in server["members"] if m not in server["admins"]]
        if non_admins:
            new_admin = st.selectbox("Zum Admin befördern:", non_admins)
            if st.button("Als Admin hinzufügen"):
                server["admins"].append(new_admin)
                st.success(f"{new_admin} ist nun Admin!")
                st.rerun()
    else:
        st.warning("Du hast keine Administrator-Rechte auf diesem Server.")
