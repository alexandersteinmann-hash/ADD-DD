import streamlit as st
import uuid

st.set_page_config(page_title="DD Server- & Tausch-Manager", page_icon="👑", layout="centered")

# --- GLOBALER SPEICHER ---
@st.cache_resource
def get_global_data():
    return {
        "servers": {
            "7f1e42af": {
                "name": "ADD",
                "creator": "alex",
                "admins": ["alex"],
                "members": ["alex"],
                "balances": {"alex": 1000},
                "requests": [],
                "updates": []
            }
        }
    }

global_data = get_global_data()
all_servers = global_data["servers"]

# --- EINFACHE ANMELDUNG (OHNE PASSWORT) ---
if "current_user" not in st.session_state or not st.session_state.current_user:
    st.title("👑 DD Server, Rechte & Tausch-System")
    st.subheader("Anmelden / Benutzer wählen")
    username = st.text_input("Gib deinen Benutzernamen ein:").strip().lower()
    
    if st.button("Einloggen") and username:
        st.session_state.current_user = username
        st.rerun()
    st.stop()

# --- SIDEBAR (LOGOUT & SERVER ERSTELLEN) ---
st.sidebar.write(f"Eingeloggt als: *{st.session_state.current_user}*")
if st.sidebar.button("Abmelden"):
    st.session_state.current_user = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🏗️ Neuen Server erstellen")
new_server_name = st.sidebar.text_input("Name des neuen Servers:")
if st.sidebar.button("Server erstellen") and new_server_name:
    # Eindeutige ID generieren (erste 8 Zeichen)
    new_sid = str(uuid.uuid4())[:8]
    all_servers[new_sid] = {
        "name": new_server_name,
        "creator": st.session_state.current_user,
        "admins": [st.session_state.current_user],
        "members": [st.session_state.current_user],
        "balances": {st.session_state.current_user: 1000},
        "requests": [],
        "updates": []
    }
    st.sidebar.success(f"Server '{new_server_name}' erfolgreich erstellt!")
    st.session_state.selected_server_id = new_sid
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

# --- SERVER AUSWÄHLEN / MANUELL BEITRETEN ---
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
    st.info("Du bist noch auf keinem Server. Erstelle links einen neuen Server oder nutze einen Einladungs-Link.")
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
    
    # Server-Updates anzeigen
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
            anfrage_betrag = st.number_input("Gewünschter Betrag in DD:", min_value=1, value=10)
            if st.button("Anfrage senden"):
                server["requests"].append({"von": st.session_state.current_user, "an": ziel_person, "betrag": anfrage_betrag})
                st.success(f"Anfrage über {anfrage_betrag} DD an {ziel_person} gesendet!")
                st.rerun()

    elif tausch_modus == "Offene Anfragen an mich":
        meine_anfragen = [r for r in server["requests"] if r["an"] == st.session_state.current_user]
        if not meine_anfragen:
            st.info("Du hast keine offenen Anfragen.")
        else:
            for idx, req in enumerate(meine_anfragen):
                st.write(f"📌 *{req['von']}* fragt nach *{req['betrag']} DD*.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Annehmen #{idx}"):
                        if server["balances"].get(st.session_state.current_user, 0) >= req["betrag"]:
                            server["balances"][st.session_state.current_user] -= req["betrag"]
                            server["balances"][req["von"]] = server["balances"].get(req["von"], 0) + req["betrag"]
                            server["requests"].remove(req)
                            st.success("Anfrage angenommen und überwiesen!")
                            st.rerun()
                        else:
                            st.error("Du hast nicht genug DD!")
                with col2:
                    if st.button(f"Ablehnen #{idx}"):
                        server["requests"].remove(req)
                        st.success("Anfrage abgelehnt.")
                        st.rerun()

# --- 3. VERWALTUNG & FINANZEN ---
with tab_admin:
    st.header("🛡️ Verwaltung & Finanzen")
    if is_creator or is_admin:
        
        # Server-Updates posten
        st.subheader("📢 Server-Update / Ankündigung posten")
        new_update_text = st.text_area("Update-Text für alle Mitglieder eingeben:")
        if st.button("Update veröffentlichen") and new_update_text:
            server["updates"].append(f"*{st.session_state.current_user}:* {new_update_text}")
            st.success("Update erfolgreich veröffentlicht! Es wird nun im Dashboard angezeigt.")
            st.rerun()

        st.markdown("---")
        st.subheader("💰 Kontostand anpassen")
        target_member = st.selectbox("Mitglied auswählen:", server["members"], key="bal_member")
        new_balance = st.number_input("Neuer Kontostand (DD):", value=int(server["balances"].get(target_member, 0)), key="bal_val")
        if st.button("Kontostand aktualisieren"):
            server["balances"][target_member] = new_balance
            st.success(f"Kontostand von {target_member} aktualisiert!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("👑 Rechte & Admins verwalten")
        non_admins = [m for m in server["members"] if m not in server["admins"] and m != server["creator"]]
        if non_admins:
            new_admin = st.selectbox("Zum Admin befördern:", non_admins, key="new_admin_box")
            if st.button("Als Admin hinzufügen"):
                server["admins"].append(new_admin)
                st.success(f"{new_admin} ist nun Admin!")
                st.rerun()
                
        current_admins_to_demote = [m for m in server["admins"] if m != server["creator"]]
        if current_admins_to_demote:
            demote_admin = st.selectbox("Admin-Rechte entziehen:", current_admins_to_demote, key="demote_box")
            if st.button("Zum normalen Mitglied machen"):
                server["admins"].remove(demote_admin)
                st.success(f"{demote_admin} ist jetzt ein normales Mitglied.")
                st.rerun()

        st.markdown("---")
        st.subheader("✏️ Namen von Mitgliedern ändern")
        rename_target = st.selectbox("Mitglied zum Umbenennen:", server["members"], key="rename_box")
        new_name = st.text_input("Neuer Name:", value=rename_target).strip().lower()
        if st.button("Namen speichern") and new_name:
            if new_name in server["members"]:
                st.error("Dieser Name bereits auf dem Server vergeben!")
            else:
                idx = server["members"].index(rename_target)
                server["members"][idx] = new_name
                
                if rename_target == server["creator"]:
                    server["creator"] = new_name
                if rename_target in server["admins"]:
                    server["admins"].remove(rename_target)
                    server["admins"].append(new_name)
                    
                bal_val = server["balances"].pop(rename_target, 1000)
                server["balances"][new_name] = bal_val
                
                if st.session_state.current_user == rename_target:
                    st.session_state.current_user = new_name
                    
                st.success(f"Erfolgreich in {new_name} umbenannt!")
                st.rerun()

        if is_creator:
            st.markdown("---")
            st.subheader("🚫 Mitglied kicken (Nur Ersteller)")
            kickable = [m for m in server["members"] if m != server["creator"]]
            if kickable:
                to_kick = st.selectbox("Mitglied entfernen:", kickable, key="kick_box")
                if st.button("Mitglied kicken"):
                    server["members"].remove(to_kick)
                    if to_kick in server["admins"]:
                        server["admins"].remove(to_kick)
                    if to_kick in server["balances"]:
                        del server["balances"][to_kick]
                    st.success(f"{to_kick} wurde vom Server gekickt.")
                    st.rerun()
            else:
                st.info("Keine anderen Mitglieder zum Kicken da.")
    else:
        st.warning("Du hast keine Administrator-Rechte auf diesem Server.")
