import streamlit as st
import fitz  # PyMuPDF
import re
import pandas as pd

def extract_details(pdf_bytes):
    # Open the PDF from memory
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # 1. Extract Order ID
    order_id_match = re.search(r"Order Id:\s*(\w+)", text)
    order_id = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Extract Seller Registered Address (First line only)
    # Searches for the line starting with 'Seller Registered Address:'
    seller_match = re.search(r"Seller Registered Address:\s*([^.\n]+)", text)
    seller = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Extract Shipping Address
    # Captures everything between 'Shipping ADDRESS' and the table start (Product)
    ship_match = re.search(r"Shipping ADDRESS\s*(.*?)\s*(?=Product|The following table)", text, re.DOTALL)
    shipping_address = ship_address = ship_match.group(1).replace('\n', ' ').strip() if ship_match else "Not Found"

    # 4. Extract Product SKU
    # Targeted logic: find text between the 2nd and 3rd '|' symbols
    sku = "Not Found"
    sku_match = re.search(r"\|\s*([^|]+)\s*\|\s*10 day", text)
    if sku_match:
        sku = sku_match.group(1).strip()

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
    
    # Display the result in a table
    df = pd.DataFrame(data_list)
    st.table(df)
    
    # Option to download results
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "extracted_invoices.csv", "text/csv")
