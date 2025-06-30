import streamlit as st
st.set_page_config(page_title="Legal Automation Hub", layout="wide")

import pandas as pd
import os
import zipfile
import io
import tempfile
from docx import Document
from datetime import datetime

st.markdown("""
<style>
.stButton > button {
    background-color: #B08B48;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.stTextInput > div > input {
    border: 1px solid #0A1D3B;
}
.stTextArea > div > textarea {
    border: 1px solid #0A1D3B;
}
</style>
""", unsafe_allow_html=True)

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

# === Branding: Logo inside navy header bar ===
import base64

def load_logo_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

logo_base64 = load_logo_base64("sggh_logo.png")

st.markdown(f"""
<div style="background-color: #0A1D3B; padding: 2rem 0; text-align: center;">
    <img src="data:image/png;base64,{logo_base64}" width="360" style="margin-bottom: 1rem;" />
    <h1 style="color: white; font-size: 2.2rem; margin: 0;">Stinar Gould Grieco & Hensley</h1>
</div>
""", unsafe_allow_html=True)

# === Sidebar Navigation - Only visible after login ===
with st.sidebar:
    st.markdown("### ⚖️ Legal Automation Hub")
    tool = st.radio("Choose Tool", [
        "📖 Instructions & Support",
        "📄 Batch Doc Generator",
        "📬 FOIA Requests",
        "📂 Demands",
        "🚧 Complaint (In Progress)",
        "🚧 Subpoenas (In Progress)",
    ])

# === Routing ===
if tool == "📄 Batch Doc Generator":
    st.header("📄 Batch Document Generator")

    TEMPLATE_FOLDER = os.path.join("templates", "batch_docs")
    os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

    try:
        campaign_df = pd.read_csv("campaigns.csv")
        CAMPAIGN_OPTIONS = sorted(campaign_df["Campaign"].dropna().unique())
    except Exception as e:
        CAMPAIGN_OPTIONS = []
        st.error(f"❌ Failed to load campaigns.csv: {e}")

    st.markdown("""
    > **How it works:**  
    > 1. Upload a template with `{placeholders}`  
    > 2. Upload Excel with matching column headers  
    > 3. Enter filename format, generate, and download

    ✅ Validates fields  
    📁 Version-safe template naming  
    🔐 No coding required
    """)

    st.subheader("🧾 Template Manager")
    template_mode = st.radio("Choose an action:", ["Upload New Template", "Select a Saved Template", "Template Options"])

    if template_mode == "Upload New Template":
        uploaded_template = st.file_uploader("Upload a .docx Template", type="docx")
        campaign_name = st.selectbox("🏷️ Select Campaign for This Template", CAMPAIGN_OPTIONS)
        doc_type = st.text_input("📄 Enter Document Type (e.g., HIPAA, Notice, Demand)")

        if uploaded_template and campaign_name and doc_type:
            if st.button("Save Template"):
                campaign_safe = campaign_name.replace(" ", "").replace("/", "-")
                doc_type_safe = doc_type.replace(" ", "")
                base_name = f"TEMPLATE_{doc_type_safe}_{campaign_safe}"
                version = 1
                while os.path.exists(os.path.join(TEMPLATE_FOLDER, f"{base_name}_v{version}.docx")):
                    version += 1
                final_filename = f"{base_name}_v{version}.docx"
                save_path = os.path.join(TEMPLATE_FOLDER, final_filename)

                with open(save_path, "wb") as f:
                    f.write(uploaded_template.read())

                st.success(f"✅ Saved as {final_filename}")

    elif template_mode == "Select a Saved Template":
        st.subheader("📂 Select a Saved Template")
        excluded_templates = {"foia_template.docx", "demand_template.docx"}
        available_templates = [
            f for f in os.listdir(TEMPLATE_FOLDER)
            if f.endswith(".docx") and f not in excluded_templates
        ]

        search_query = st.text_input("🔍 Search templates by keyword or campaign").lower()
        filtered_templates = [f for f in available_templates if search_query in f.lower()]

        if not filtered_templates:
            st.warning("⚠️ No matching templates found.")
            st.stop()

        template_choice = st.selectbox("Choose Template", filtered_templates)
        template_path = os.path.join(TEMPLATE_FOLDER, template_choice)

        excel_file = st.file_uploader("Upload Excel Data (.xlsx)", type="xlsx")
        output_name_format = st.text_input("Enter filename format (e.g., HIPAA Notice ({{Client Name}}))")
        generate = st.button("Generate Documents")

        if excel_file:
            df = pd.read_excel(excel_file)
            if df.empty:
                st.error("⚠️ Your Excel file has no rows. Please check the file and try again.")
                st.stop()

            st.subheader("🔍 Preview First Row of Excel Data")
            st.dataframe(df.head(1))

            st.markdown("**Columns in Excel:**")
            st.code(", ".join(df.columns))

            preview_filename = output_name_format
            for key, val in df.iloc[0].items():
                preview_filename = preview_filename.replace(f"{{{{{key}}}}}", str(val))
            st.markdown("**📄 Preview Filename for First Row:**")
            st.code(preview_filename)

            # Optional: Preview document for first row
            if st.checkbox("👁️ Preview generated document for first row"):
                doc_preview = Document(template_path)
                row = df.iloc[0]
                for para in doc_preview.paragraphs:
                    for key, val in row.items():
                        if pd.api.types.is_datetime64_any_dtype([val]) or isinstance(val, pd.Timestamp):
                            val = val.strftime("%-m/%-d/%Y")
                        placeholder = f"{{{{{key}}}}}"
                        for run in para.runs:
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, str(val))

                for table in doc_preview.tables:
                    for cell in table._cells:
                        for para in cell.paragraphs:
                            for run in para.runs:
                                for key, val in row.items():
                                    if pd.api.types.is_datetime64_any_dtype([val]) or isinstance(val, pd.Timestamp):
                                        val = val.strftime("%-m/%-d/%Y")
                                    placeholder = f"{{{{{key}}}}}"
                                    if placeholder in run.text:
                                        run.text = run.text.replace(placeholder, str(val))

                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_doc:
                    doc_preview.save(tmp_doc.name)
                    tmp_doc.seek(0)
                    st.download_button("📥 Download Preview Document", tmp_doc.read(), file_name="Preview.docx")

        if generate and excel_file and output_name_format:
            df = pd.read_excel(excel_file)
            if df.empty:
                st.error("⚠️ Your Excel file has no rows. Please check the file and try again.")
                st.stop()

            left, right = "{{", "}}"
            with tempfile.TemporaryDirectory() as temp_dir:
                word_dir = os.path.join(temp_dir, "Word Documents")
                os.makedirs(word_dir)

                for idx, row in df.iterrows():
                    doc = Document(template_path)

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

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_out:
                    for file in os.listdir(word_dir):
                        full_path = os.path.join(word_dir, file)
                        arcname = os.path.join("Word Documents", file)
                        zip_out.write(full_path, arcname=arcname)

                st.success("✅ Word documents generated!")
                st.download_button(
                    label="📦 Download All (Word Only – PDF not supported on Streamlit Cloud)",
                    data=zip_buffer.getvalue(),
                    file_name="word_documents.zip",
                    mime="application/zip"
                )

