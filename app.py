import streamlit as st
import pdfplumber
import re
import pandas as pd

def extract_invoice_details(pdf_file):
    """
    Extracts Sold By, Order Id, Shipping Address, and SKU from the uploaded PDF file object.
    """
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        # Assuming the invoice is on the first page
        if len(pdf.pages) > 0:
            page = pdf.pages[0]
            text = page.extract_text()
            
    # Initialize dictionary
    data = {
        "File Name": pdf_file.name,
        "Sold By": None,
        "Order Id": None,
        "Shipping Address": None,
        "Product SKU": None
    }

    if not text:
        return data

    # 1. Extract 'Sold By'
    # Strategy: Look for "Sold By" and capture the next line.
    sold_by_match = re.search(r"Sold By\s*\n\s*(.*?)(?:,|\n)", text, re.IGNORECASE)
    if sold_by_match:
        data["Sold By"] = sold_by_match.group(1).strip()

    # 2. Extract 'Order Id'
    # Strategy: Look for "Order Id:" followed by the alphanumeric ID.
    order_match = re.search(r"Order Id:\s*([A-Za-z0-9]+)", text)
    if order_match:
        data["Order Id"] = order_match.group(1).strip()

    # 3. Extract 'Shipping Address'
    # Strategy: Capture text starting after "Shipping ADDRESS" until a new section starts.
    shipping_match = re.search(r"Shipping ADDRESS(.*?)(?=\nProduct|\nDescription|Qty|Gross|Seller|Billing|\Z)", text, re.DOTALL | re.IGNORECASE)
    if shipping_match:
        raw_address = shipping_match.group(1).strip()
        # Clean up lines to remove empty spaces
        cleaned_address = ", ".join([line.strip() for line in raw_address.split('\n') if line.strip()])
        data["Shipping Address"] = cleaned_address

    # 4. Extract 'Product SKU'
    # Strategy: Strictly take data between two "|"
    # Finds all occurrences of text between pipes: | TEXT |
    pipe_matches = re.findall(r"\|\s*([^|]+?)\s*\|", text)
    
    # Heuristic: The SKU is usually alphanumeric and might contain dashes (e.g., AFDT-42-W)
    sku_found = False
    for match in pipe_matches:
        clean_match = match.strip()
        # Check if it looks like an SKU (contains uppercase and digits/dashes, len > 3)
        if re.search(r"[A-Z0-9]+-[A-Z0-9]+", clean_match):
            data["Product SKU"] = clean_match
            sku_found = True
            break
            
    # Fallback if strict pipe strategy misses (e.g. if formatting is slightly off like "AFDT-42-W |")
    if not sku_found:
        # Look for SKU pattern explicitly near a pipe
        fallback = re.search(r"([A-Z0-9]+-[A-Z0-9-]+)\s*\|", text)
        if fallback:
             data["Product SKU"] = fallback.group(1).strip()

    return data

# --- Streamlit UI Layout ---
st.set_page_config(page_title="Invoice Data Extractor", layout="wide")

st.title("📄 Invoice Data Extractor")
st.write("Upload your Flipkart-style invoice PDFs to extract specific details.")

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    if st.button("Extract Data"):
        all_data = []
        progress_bar = st.progress(0)
        
        for i, pdf_file in enumerate(uploaded_files):
            # Update progress bar
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            
            # Extract data
            extracted_info = extract_invoice_details(pdf_file)
            all_data.append(extracted_info)
            
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Display Data
        st.success(f"Successfully processed {len(uploaded_files)} files!")
        st.dataframe(df, use_container_width=True)
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="extracted_invoice_data.csv",
            mime="text/csv",
        )
