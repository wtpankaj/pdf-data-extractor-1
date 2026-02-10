import streamlit as st
import pdfplumber
import re
import pandas as pd

def extract_invoice_data(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        # Extract text from the first page
        page = pdf.pages[0]
        text = page.extract_text()
        
    data = {}

    # 1. Extract Order ID
    # Patterns: OD followed by digits [cite: 2, 29]
    order_id_match = re.search(r"Order Id:\s*(OD\d+)", text)
    data['Order ID'] = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Extract Seller Registered Address (Name Only)
    # Extracts specifically "R K Enterprises" [cite: 27, 32]
    seller_match = re.search(r"Seller Registered Address:\s*([^.]+)", text)
    data['Seller'] = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Extract Shipping Address
    # Captures everything between 'Shipping ADDRESS' and the start of the product table [cite: 17-23]
    shipping_pattern = re.compile(r"Shipping ADDRESS\s*(.*?)(?=Product|Description)", re.DOTALL)
    shipping_match = shipping_pattern.search(text)
    if shipping_match:
        address = shipping_match.group(1).replace('\n', ' ').strip()
        data['Shipping Address'] = address
    else:
        data['Shipping Address'] = "Not Found"

    # 4. Extract Product SKU (Data between two '|')
    # Specifically looking for the pattern | SKU | 
    sku_match = re.search(r"\|\s*([^|]+)\s*\|", text)
    data['Product SKU'] = sku_match.group(1).strip() if sku_match else "Not Found"

    return data

# Streamlit UI
st.title("Invoice Data Extractor")
st.write("Upload your formatted PDFs to extract specific details.")

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    for uploaded_file in uploaded_files:
        extracted = extract_invoice_data(uploaded_file)
        results.append(extracted)
    
    # Display results in a table without the filename column
    df = pd.DataFrame(results)
    st.table(df)

    # Option to download the results as CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Data as CSV", csv, "extracted_invoices.csv", "text/csv")
