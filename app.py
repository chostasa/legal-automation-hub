import streamlit as st
st.set_page_config(page_title="Legal Automation Hub", layout="wide")

import pandas as pd
import os
import zipfile
import io
import tempfile
import pypandoc
from docx import Document

# === Simple login ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Password", type="password")
    if password == st.secrets["password"]:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

# === Sidebar Navigation - Only visible after login ===
with st.sidebar:
    st.markdown("### 📂 Legal Automation Hub")
    tool = st.radio("Choose Tool", [
        "📂 Demands",
        "📁 FOIA Requests",
        "📄 Batch Doc Generator",
        "📖 Instructions & Support"
        "🚧 Complaint (In Progress)",
        "🚧 Subpoenas (In Progress)",
    ])

# === Routing ===
if tool == "📂 Demands":
    st.header("📁 Generate Demand Letters")
    with st.form("demand_form"):
        client_name = st.text_input("Client Name")
        defendant = st.text_input("Defendant")
        incident_date = st.date_input("Incident Date")
        location = st.text_input("Location")
        summary = st.text_area("Summary of Incident")
        damages = st.text_area("Damages")

        submitted = st.form_submit_button("Generate Demand Letter")

    if submitted:
        df = pd.DataFrame([{
            "Client Name": client_name,
            "Defendant": defendant,
            "IncidentDate": incident_date.strftime("%B %d, %Y"),
            "Location": location,
            "Summary": summary,
            "Damages": damages
        }])

        try:
            output_paths = run_demand(df)  # <-- make sure this function is defined/imported
            st.success("✅ Letter generated!")
            for path in output_paths:
                filename = os.path.basename(path)
                with open(path, "rb") as f:
                    st.download_button(label=f"Download {filename}", data=f, file_name=filename)
        except Exception as e:
            st.error(f"❌ Error: {e}")

elif tool == "📁 FOIA Requests":
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
        potential_requests = st.text_area("Potential Requests")
        explicit_instructions = st.text_area("Explicit Instructions (optional)")
        case_type = st.text_input("Case Type")
        facility = st.text_input("Facility or System")
        defendant_role = st.text_input("Defendant Role")

        submitted = st.form_submit_button("Generate FOIA Letter")

    if submitted:
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

        try:
            output_paths = run_foia(df)  # <-- make sure this function is defined/imported
            st.success("✅ FOIA letter generated!")
            for path in output_paths:
                filename = os.path.basename(path)
                with open(path, "rb") as f:
                    st.download_button(label=f"Download {filename}", data=f, file_name=filename)
        except Exception as e:
            st.error(f"❌ Error: {e}")

elif tool == "📄 Batch Doc Generator":
    st.header("📄 Batch Document Generator")

    st.markdown("Upload a Word `.docx` template with placeholders (like `{{Name}}`) that exactly match your Excel column headers.")

    template_file = st.file_uploader("Upload Word Template (.docx)", type="docx")
    excel_file = st.file_uploader("Upload Excel Data (.xlsx)", type="xlsx")

    output_name_format = st.text_input("Enter filename format (e.g., HIPAA Notice to Saint Francis ({{Name}}))")

    generate = st.button("Generate Documents")

    if generate and template_file and excel_file and output_name_format:
        df = pd.read_excel(excel_file)
        left, right = "{{", "}}"

        with tempfile.TemporaryDirectory() as temp_dir:
            word_dir = os.path.join(temp_dir, "Word Documents")
            pdf_dir = os.path.join(temp_dir, "PDFs")
            os.makedirs(word_dir)
            os.makedirs(pdf_dir)

            for idx, row in df.iterrows():
                doc = Document(template_file)

                for para in doc.paragraphs:
                    for key, val in row.items():
                        if pd.api.types.is_datetime64_any_dtype([val]) or isinstance(val, pd.Timestamp):
                            val = val.strftime("%-m/%-d/%Y")
                        placeholder = f"{left}{key}{right}"
                        for run in para.runs:
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, str(val))

                for table in doc.tables:
                    for cell in table._cells:
                        for para in cell.paragraphs:
                            for run in para.runs:
                                for key, val in row.items():
                                    if pd.api.types.is_datetime64_any_dtype([val]) or isinstance(val, pd.Timestamp):
                                        val = val.strftime("%-m/%-d/%Y")
                                    placeholder = f"{left}{key}{right}"
                                    if placeholder in run.text:
                                        run.text = run.text.replace(placeholder, str(val))

                name_for_file = output_name_format
                for key, val in row.items():
                    if pd.api.types.is_datetime64_any_dtype([val]) or isinstance(val, pd.Timestamp):
                        val = val.strftime("%-m/%-d/%Y")
                    name_for_file = name_for_file.replace(f"{left}{key}{right}", str(val))
                filename = name_for_file + ".docx"

                doc_path = os.path.join(word_dir, filename)
                doc.save(doc_path)

                pdf_path = os.path.join(pdf_dir, filename.replace(".docx", ".pdf"))
                pypandoc.convert_file(doc_path, 'pdf', outputfile=pdf_path)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_out:
                for folder in [word_dir, pdf_dir]:
                    for file in os.listdir(folder):
                        full_path = os.path.join(folder, file)
                        arcname = os.path.join(os.path.basename(folder), file)
                        zip_out.write(full_path, arcname=arcname)

            st.success("✅ Documents generated!")
            st.download_button(
                label="📦 Download All (Word + PDFs)",
                data=zip_buffer.getvalue(),
                file_name="merged_documents.zip",
                mime="application/zip"
            )

elif tool == "📖 Instructions & Support":
    st.header("📘 Instructions")
    st.markdown("""
    Fill in the applicable fields:

    ### 📂 Demands:
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

else:
    st.warning("🚧 This section is currently under development.")