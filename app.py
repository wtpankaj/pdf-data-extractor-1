import fitz  # PyMuPDF
import re

def extract_invoice_data(pdf_path):
    # Open the PDF and extract text
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    # 1. Extract Order ID
    order_id_match = re.search(r"Order Id:\s*(\w+)", full_text)
    order_id = order_id_match.group(1) if order_id_match else "Not Found"

    # 2. Extract Seller Registered Address
    # Looks for text after 'Seller Registered Address:' up until the first period
    seller_match = re.search(r"Seller Registered Address:\s*([^.]+)", full_text)
    seller_address = seller_match.group(1).strip() if seller_match else "Not Found"

    # 3. Extract Shipping Address
    # Captures everything between 'Shipping ADDRESS' and the start of the product table
    shipping_match = re.search(r"Shipping ADDRESS\s+(.*?)(?=\nProduct|\nDescription)", full_text, re.DOTALL)
    shipping_address = shipping_match.group(1).replace('\n', ' ').strip() if shipping_match else "Not Found"

    # 4. Extract Product SKU (Strictly between two '|')
    # Regex looks for the second occurrence of | SKU | usually found in the description
    sku_match = re.search(r"\|\s*([^|]+?)\s*\|", full_text)
    product_sku = sku_match.group(1).strip() if sku_match else "Not Found"

    return {
        "Seller Registered Address": seller_address,
        "Order Id": order_id,
        "Shipping Address": shipping_address,
        "Product SKU": product_sku
    }

# Example Usage
if __name__ == "__main__":
    file_path = "Pilla Uma.pdf"  # Ensure your file is in the same folder
    data = extract_invoice_data(file_path)
    
    for key, value in data.items():
        print(f"{key}: {value}")
