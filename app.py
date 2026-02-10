import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Batch Data Extractor", layout="wide")
st.title("📄 Bulk PDF Data Extractor")
st.markdown("Upload up to 200 PDF files to extract: **Ship To, Order ID, Seller Name, and SKU**.")

# --- 2. EXTRACTION LOGIC ---
def extract_data_from_pdf(file_bytes):
    text = ""
    # Open PDF from memory
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Initialize data dictionary
    data = {
        "Ship To": "",
        "Order ID": "",
        "Seller Name": "",
        "SKU": ""
    }

    # --- REGEX PATTERNS ---
    
    # 1. ORDER ID
    # Captures ID after "Order ID:" or "Order Id:"
    order_match = re.search(r'(?i)Order\s*I[Dd]\s*[:.#]?\s*([A-Za-z0-9\-]+)', text)
    if order_match:
        data["Order ID"] = order_match.group(1).strip()

    # 2. SELLER NAME
    # Captures text for seller after "Sold By" or "Seller Name"
    # Handles cases where the name is on the next line
    seller_match = re.search(r'(?i)(?:Sold By|Seller Name)\s*[:.]?\s*\n?([^\n]+)', text)
    if seller_match:
        data["Seller Name"] = seller_match.group(1).strip()

    # 3. SKU
    # Captures text strictly between two pipe symbols "|"
    sku_match = re.search(r'\|\s*([^|]+?)\s*\|', text)
    if sku_match:
        data["SKU"] = sku_match.group(1).strip()
    else:
        # Fallback: Look for "SKU:" label if pipes are missing
        fallback_sku = re.search(r'(?i)SKU\s*[:.]?\s*([A-Za-z0-9\-\.]+)', text)
        if fallback_sku:
            data["SKU"] = fallback_sku.group(1).strip()

    # 4. SHIP TO
    # Captures text between "Ship to"/"Shipping Address" and the next section
    ship_match = re.search(r'(?i)(?:Shipping\s*ADDRESS|Ship\s*to)\s*[:.]?\s*(.*?)(?=(?i)(?:Product|Order|Tax|Invoice|$))', text, re.DOTALL)
    if ship_match:
        raw_address = ship_match.group(1).strip()
        clean_address = raw_address.replace("\n", ", ")
        data["Ship To"] = re.sub(r'\s+', ' ', clean_address).strip()

    return data

# --- 3. BATCH PROCESSING UI ---

uploaded_files = st.file_uploader(
    "Upload PDF files (Max 200)", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button(f"Start Extraction for {len(uploaded_files)} files"):
        
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pdf_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing file {i+1}...")
                
                file_bytes = pdf_file.read()
                extracted_info = extract_data_from_pdf(file_bytes)
                all_data.append(extracted_info)
                
            except Exception as e:
                st.error(f"Error reading {pdf_file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Organize Columns
        cols = ["Ship To", "Order ID", "Seller Name", "SKU"]
        df = df.reindex(columns=cols)
        
        st.success("Extraction Complete!")
        st.dataframe(df)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="extracted_data.csv",
            mime="text/csv",
        )
