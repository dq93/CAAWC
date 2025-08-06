import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import pandas as pd
import io
import re

# === CONFIG ===
checkbox_fields = [
    "Asset Development/Financial Literacy", "Child Care", "Education",
    "Elder Care/Senior services", "Employment", "Energy", "Food Security",
    "Health Insurance", "Housing", "Income", "Transportation", "Other"
]
checkbox_pattern = re.compile(r"[✓✔☑■Xx]")

# === FUNCTIONS ===
def extract_text(file):
    ext = file.name.lower()
    full_text = ""
    
    if ext.endswith(".pdf"):
        images = convert_from_bytes(file.read())
        for img in images:
            full_text += pytesseract.image_to_string(img) + "\n"
    elif ext.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(file)
        full_text = pytesseract.image_to_string(image)
    else:
        raise ValueError("Unsupported file format.")
    
    return full_text

def parse_client_info(text):
    client_info = {
        "Client Name": "",
        "Client ID": "",
        "Telephone": "",
        "Case Manager Name": "",
        "Case Manager Phone": "",
        "Needs": [],
        "Strengths": "",
        "Barriers": ""
    }

    lines = text.split("\n")
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if "Client Name" in line_clean:
            client_info["Client Name"] = line_clean.split(":")[-1].strip()
        elif "Client ID" in line_clean:
            parts = line_clean.split()
            if len(parts) >= 3:
                client_info["Client ID"] = parts[2]
                client_info["Telephone"] = parts[-1]
        elif "Case Manager Name" in line_clean:
            client_info["Case Manager Name"] = line_clean.split(":")[-1].strip()
        elif "Case Manager Tele" in line_clean or "Case Manager Phone" in line_clean:
            client_info["Case Manager Phone"] = line_clean.split(":")[-1].strip()
        elif any(field in line_clean for field in checkbox_fields):
            for field in checkbox_fields:
                if field in line_clean and checkbox_pattern.search(line_clean):
                    client_info["Needs"].append(field)
        elif "Client Strengths" in line_clean:
            client_info["Strengths"] = lines[i + 1].strip() if i + 1 < len(lines) else ""
        elif "Client Concerns" in line_clean or "Barriers" in line_clean:
            client_info["Barriers"] = lines[i + 1].strip() if i + 1 < len(lines) else ""

    return client_info

def generate_excel(client_info):
    df = pd.DataFrame({
        "Field": list(client_info.keys()),
        "Value": [", ".join(v) if isinstance(v, list) else v for v in client_info.values()]
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Client Info")
        worksheet = writer.sheets["Client Info"]
        worksheet.set_column("A:A", 25)
        worksheet.set_column("B:B", 50)

    output.seek(0)
    return output

# === STREAMLIT UI ===
st.set_page_config(page_title="Client Intake OCR", layout="centered")

st.title("📋 Client Intake OCR Scanner")

uploaded_file = st.file_uploader("Upload Image or PDF", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    try:
        with st.spinner("🕵️ Extracting text..."):
            raw_text = extract_text(uploaded_file)
            client_info = parse_client_info(raw_text)

        st.success("✅ Text Extracted Successfully!")

        st.subheader("🔍 Extracted Information")
        for field, value in client_info.items():
            st.markdown(f"**{field}:** {', '.join(value) if isinstance(value, list) else value}")

        excel_file = generate_excel(client_info)
        st.download_button(
            label="📥 Download as Excel",
            data=excel_file,
            file_name="client_info.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")