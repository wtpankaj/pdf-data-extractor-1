import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd
import io

def extract_details(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # 1. Order ID
    order_id_match = re.search(r"Order Id:\s*(\w+)", text)
    order_id = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Seller Registered Address
    seller_match = re.search(r"Seller Registered Address:\s*([^,.\n\r]+)", text)
    seller = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Product SKU
    sku = "Not Found"
    sku_match_1 = re.search(r"\|\s*([^|]+?)\s*\|\s*10 day", text)
    sku_match_2 = re.search(r"([A-Z0-9-]+)\s*\|\s*IMEI", text)

    if sku_match_1:
        sku = sku_match_1.group(1).strip()
    elif sku_match_2:
        sku = sku_match_2.group(1).strip()

    # 4. Shipping Address
    ship_match = re.search(
        r"Shipping ADDRESS\s*([\s\S]*?)(?=\s*(?:The following table|Product|Seller Registered Address|FSSAI|Billing Address))", 
        text, 
        re.IGNORECASE
    )
    
    shipping_address = "Not Found"
    if ship_match:
        raw_address = ship_match.group(1)
        
        if "FSSAI" in raw_address:
            raw_address = raw_address.split("FSSAI")[0]
        if "Seller Registered Address" in raw_address:
            raw_address = raw_address.split("Seller Registered Address")[0]
            
        raw_address = re.sub(r"Order Id:.*", "", raw_address)
        shipping_address = " ".join(raw_address.split())

    # Return with specific column order
    return {
        "Shipping Address": shipping_address,
        "Order Id": order_id,
        " ": "",  # Blank Column
        "Seller Registered Address": seller,
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
    
    # Create DataFrame
    df = pd.DataFrame(data_list)
    
    # Show Table
    st.table(df)

    # Excel Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        
    st.download_button(
        label="Download Excel",
        data=buffer.getvalue(),
        file_name="extracted_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
