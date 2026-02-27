import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# -------------------------
# DATABASE CONNECTION
# -------------------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Create Tables
c.execute('''
CREATE TABLE IF NOT EXISTS technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    skill TEXT,
    skill_level INTEGER,
    open_tickets INTEGER,
    avg_resolution_time INTEGER,
    availability TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    required_skill TEXT,
    priority TEXT,
    assigned_to TEXT,
    status TEXT
)
''')

conn.commit()

# -------------------------
# SMART ALLOCATION FUNCTION
# -------------------------
def smart_allocate(required_skill):
    c.execute("SELECT * FROM technicians WHERE skill=? AND availability='Available'", (required_skill,))
    techs = c.fetchall()

    best_score = -999
    best_tech = None

    for tech in techs:
        _, name, skill, skill_level, open_tickets, avg_time, availability = tech

        score = (skill_level * 2) - (open_tickets * 1.5) - (avg_time / 10)

        if score > best_score:
            best_score = score
            best_tech = name

    return best_tech

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Smart ITSM", layout="wide")

st.title("🚀 Smart Technician Allocation System")

menu = ["Add Technician", "Create Ticket", "Dashboard"]
choice = st.sidebar.selectbox("Navigation", menu)

# -------------------------
# ADD TECHNICIAN
# -------------------------
if choice == "Add Technician":
    st.subheader("➕ Add Technician")

    name = st.text_input("Technician Name")
    skill = st.selectbox("Skill", ["Network", "Server", "Security", "Hardware", "Software"])
    skill_level = st.slider("Skill Level (1-5)", 1, 5)
    open_tickets = st.number_input("Current Open Tickets", 0)
    avg_time = st.number_input("Average Resolution Time (minutes)", 10)
    availability = st.selectbox("Availability", ["Available", "Busy"])

    if st.button("Add Technician"):
        c.execute("INSERT INTO technicians (name, skill, skill_level, open_tickets, avg_resolution_time, availability) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, skill, skill_level, open_tickets, avg_time, availability))
        conn.commit()
        st.success("Technician Added Successfully!")

# -------------------------
# CREATE TICKET
# -------------------------
elif choice == "Create Ticket":
    st.subheader("🎫 Create Ticket")

    title = st.text_input("Ticket Title")
    required_skill = st.selectbox("Required Skill", ["Network", "Server", "Security", "Hardware", "Software"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])

    if st.button("Generate & Assign Ticket"):
        assigned = smart_allocate(required_skill)

        if assigned:
            c.execute("INSERT INTO tickets (title, required_skill, priority, assigned_to, status) VALUES (?, ?, ?, ?, ?)",
                      (title, required_skill, priority, assigned, "Open"))
            conn.commit()
            st.success(f"Ticket Assigned to {assigned} 🚀")
        else:
            st.error("No Available Technician Found!")

# -------------------------
# DASHBOARD
# -------------------------
elif choice == "Dashboard":
    st.subheader("📊 Dashboard")

    tech_df = pd.read_sql_query("SELECT * FROM technicians", conn)
    ticket_df = pd.read_sql_query("SELECT * FROM tickets", conn)

    st.write("### 👨‍💻 Technician Overview")
    st.dataframe(tech_df)

    if not tech_df.empty:
        fig = px.bar(tech_df, x="name", y="open_tickets",
                     title="Technician Workload")
        st.plotly_chart(fig)

    st.write("### 🎫 Tickets")
    st.dataframe(ticket_df)
