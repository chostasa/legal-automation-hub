import streamlit as st
import pandas as pd
import os
import zipfile
import io
import streamlit as st

# === Simple login ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Password", type="password")
    if password == st.secrets["password"]:
        st.session_state.authenticated = True
        st.experimental_rerun()
    else:
        st.stop()

st.title(tool)  # Optional: display selected tool name as header

# Password protection
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False


    if "password_correct" not in st.session_state:
        st.text_input("Enter password:", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        st.stop()

check_password()

from scripts.generate_demand import run as run_demand
from scripts.generate_foia import run as run_foia

st.set_page_config(page_title="Legal Automation Hub", layout="wide")
st.title("⚖️ Legal Automation Hub")

# Sidebar Navigation
st.sidebar.title("Tools")
page = st.sidebar.radio("Select a Tool", ["Demands", "FOIA Requests", "Instructions & Support"])

# === Sidebar Tools ===
with st.sidebar:
    st.markdown("### 🗂️ Legal Automation Hub")
    tool = st.radio("Select a Tool", [
        "🚧 Complaint (In Progress)",
        "🚧 HIPAAs (In Progress)",
        "🚧 FOIAs (In Progress)",
        "🚧 Subpoenas (In Progress)",
        "📂 Demands",
        "📑 FOIA Requests",
        "📖 Instructions & Support"
    ])

# --- Demands Section ---
if page == "Demands":
    st.header("📑 Generate Demand Letters")

    st.subheader("📋 Fill in Demand Letter Info")

    with st.form("demand_form"):
        client_name = st.text_input("Client Name")
        defendant = st.text_input("Defendant")
        incident_date = st.date_input("Incident Date")
        location = st.text_input("Location")
        summary = st.text_area("Summary of Incident")
        damages = st.text_area("Damages")

        submitted = st.form_submit_button("Generate Demand Letter")

    if submitted:
        import pandas as pd
        from datetime import datetime

        df = pd.DataFrame([{
            "Client Name": client_name,
            "Defendant": defendant,
            "IncidentDate": incident_date.strftime("%B %d, %Y"),
            "Location": location,
            "Summary": summary,
            "Damages": damages
        }])

        try:
            output_paths = run_demand(df)
            st.success("✅ Letter generated!")

            for path in output_paths:
                filename = os.path.basename(path)
                with open(path, "rb") as f:
                    st.download_button(
                        label=f"Download {filename}",
                        data=f,
                        file_name=filename
                    )
        except Exception as e:
            st.error(f"❌ Error: {e}")

# --- FOIA Section ---
elif page == "FOIA Requests":
    st.header("📨 Generate FOIA Letters")

    with st.form("foia_form"):
        client_id = st.text_input("Client ID")
        defendant_name = st.text_input("Defendant Name")
        abbreviation = st.text_input("Defendant Abbreviation (for file name)")
        address_line1 = st.text_input("Defendant Address Line 1")
        address_line2 = st.text_input("Defendant Address Line 2 (City, State, Zip)")
        date_of_incident = st.date_input("Date of Incident")
        location = st.text_input("Location of Incident")
        case_synopsis = st.text_area("Case Synopsis")
        potential_requests = st.text_area("Potential Requests (can be reused from another)")
        explicit_instructions = st.text_area("Explicit Instructions (optional)")
        case_type = st.text_input("Case Type")
        facility = st.text_input("Facility or System")
        defendant_role = st.text_input("Defendant Role")

        submitted = st.form_submit_button("Generate FOIA Letter")

    if submitted:
        try:
            # Build DataFrame from form data
            df = pd.DataFrame([{
                "Client ID": client_id,
                "Defendant Name": defendant_name,
                "Defendant Abbreviation": abbreviation,
                "Defendant Line 1 (address)": address_line1,
                "Defendant Line 2 (City,state, zip)": address_line2,
                "DOI": date_of_incident,
                "location of incident": location,
                "Case Synopsis": case_synopsis,
                "Potential Requests": potential_requests,
                "Explicit instructions": explicit_instructions,
                "Case Type": case_type,
                "Facility or System": facility,
                "Defendant Role": defendant_role
            }])

            output_paths = run_foia(df)
            st.success("✅ FOIA letter generated!")

            for path in output_paths:
                filename = os.path.basename(path)
                with open(path, "rb") as f:
                    st.download_button(f"Download {filename}", f, file_name=filename)

        except Exception as e:
            st.error(f"❌ Error: {e}")

# --- Instructions & Support Section ---
elif page == "Instructions & Support":
    st.header("📘 Instructions")
    st.markdown("""
    Upload your Excel files with the following columns:

    ### 📁 Demands:
    - Client Name
    - Incident Date
    - Summary
    - Damages

    ### 📨 FOIA:
    - Client ID
    - Case Synopsis
    - Potential Requests
    - Case Type
    - Facility or System
    - Defendant Role

    Click **Generate** to create your letters and download the results.
    """)

    st.subheader("🐞 Report a Bug")
    with st.form("report_form"):
        issue = st.text_area("Describe the issue:")
        submitted = st.form_submit_button("Submit")
        if submitted:
            with open("error_reports.txt", "a", encoding="utf-8") as f:
                f.write(issue + "\n---\n")
            st.success("✅ Issue submitted. Thank you!")