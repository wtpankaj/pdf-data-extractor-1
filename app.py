import streamlit as st
import pdfplumber
import re
import pandas as pd

def extract_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        # Extract text from the first page
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # 1. Extract Order ID
    order_id_match = re.search(r"Order Id:\s*(\S+)", full_text)
    order_id = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Extract Seller Registered Address (Specific Name)
    # Looking for the line starting with 'Seller Registered Address:'
    seller_match = re.search(r"Seller Registered Address:\s*([^.]+)", full_text)
    seller_name = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Extract Shipping Address
    # Matches text between 'Shipping ADDRESS' and the next section (Product table)
    ship_pattern = r"Shipping ADDRESS\s+(.*?)(?=\nProduct|\nQty|\nHSN:)"
    ship_match = re.search(ship_pattern, full_text, re.DOTALL)
    shipping_address = ship_match.group(1).replace('\n', ' ').strip() if ship_match else "Not Found"

    # 4. Extract Product SKU (Strictly between two '|')
    # This looks for the IMEI/SrNo section or similar and grabs the value between | |
    sku_match = re.search(r"\|\s*([^|]+?)\s*\|", full_text)
    product_sku = sku_match.group(1).strip() if sku_match else "Not Found"

    return {
        "Seller Name": seller_name,
        "Order ID": order_id,
        "Shipping Address": shipping_address,
        "Product SKU": product_sku
    }

# Streamlit UI
st.title("Invoice Data Extractor")
st.write("Upload your PDF invoices to extract key details automatically.")

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    extracted_results = []
    
    for uploaded_file in uploaded_files:
        data = extract_data(uploaded_file)
        extracted_results.append(data)
    
    # Display results in a table
    df = pd.DataFrame(extracted_results)
    st.table(df)
    
    # Download as CSV option
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data as CSV", csv, "extracted_invoices.csv", "text/csv")
