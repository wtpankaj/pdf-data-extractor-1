import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd

def extract_details(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # 1. Order ID
    # Captures the alphanumeric string immediately following "Order Id:"
    order_id_match = re.search(r"Order Id:\s*(\w+)", text)
    order_id = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Seller Registered Address
    # Captures text starting after "Address:" until the first comma, period, or newline
    seller_match = re.search(r"Seller Registered Address:\s*([^,.\n\r]+)", text)
    seller = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Product SKU
    # Captures the text strictly between the last pipe "|" and "10 day"
    sku_match = re.search(r"\|\s*([^|]+?)\s*\|\s*10 day", text)
    sku = sku_match.group(1).strip() if sku_match else "Not Found"

    # 4. Shipping Address
    # Captures text starting from "Shipping ADDRESS" until it hits any footer keywords
    # The lookahead (?=...) ensures we stop BEFORE these keywords appear
    ship_match = re.search(
        r"Shipping ADDRESS\s*([\s\S]*?)(?=\s*(?:The following table|Product|Seller Registered Address|FSSAI|Billing Address))", 
        text, 
        re.IGNORECASE
    )
    
    shipping_address = "Not Found"
    if ship_match:
        # Clean the extracted block
        raw_address = ship_match.group(1)
        # Final safety filter: Explicitly cut off if keywords managed to sneak in
        if "FSSAI" in raw_address:
            raw_address = raw_address.split("FSSAI")[0]
        if "Seller Registered Address" in raw_address:
            raw_address = raw_address.split("Seller Registered Address")[0]
            
        # Remove Order ID if it leaked into the address block
        raw_address = re.sub(r"Order Id:.*", "", raw_address)
        
        # Normalize whitespace (replace newlines with spaces)
        shipping_address = " ".join(raw_address.split())

    return {
        "Order Id": order_id,
        "Seller Registered Address": seller,
        "Shipping Address": shipping_address,
        "Product SKU": sku
    }

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("📄 Invoice Data Extraction")

uploaded_files = st.file_uploader("Upload Invoice PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    data_list = []
    for uploaded_file in uploaded_files:
        details = extract_details(uploaded_file.read())
        data_list.append(details)
    
    df = pd.DataFrame(data_list)
    st.table(df)
