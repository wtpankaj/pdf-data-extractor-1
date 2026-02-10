import pdfplumber
import re

def extract_invoice_details(pdf_path):
    """
    Extracts Sold By, Order Id, Shipping Address, and SKU from the invoice PDF.
    """
    data = {
        "Sold By": None,
        "Order Id": None,
        "Shipping Address": None,
        "Product SKU": None
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        # Assuming the invoice is on the first page
        page = pdf.pages[0] 
        text = page.extract_text()
        
        # 1. Extract 'Sold By'
        # Strategy: Look for "Sold By" and capture the next line which contains the seller name.
        # 
        sold_by_match = re.search(r"Sold By\s*\n\s*(.*?)(?:,|\n)", text, re.IGNORECASE)
        if sold_by_match:
            data["Sold By"] = sold_by_match.group(1).strip()
        else:
            # Fallback: iterate lines if regex misses
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if "Sold By" in line and i + 1 < len(lines):
                    data["Sold By"] = lines[i+1].strip().rstrip(',')
                    break

        # 2. Extract 'Order Id'
        # Strategy: Look for "Order Id:" followed by the alphanumeric ID.
        # 
        order_match = re.search(r"Order Id:\s*([A-Za-z0-9]+)", text)
        if order_match:
            data["Order Id"] = order_match.group(1).strip()

        # 3. Extract 'Shipping Address'
        # Strategy: Capture text starting after "Shipping ADDRESS" until a new section starts (e.g., "Product" or "Description").
        # 
        shipping_match = re.search(r"Shipping ADDRESS(.*?)(?=\nProduct|\nDescription|Qty|\Z)", text, re.DOTALL | re.IGNORECASE)
        if shipping_match:
            # Clean up the address by removing empty lines and leading/trailing whitespace
            raw_address = shipping_match.group(1).strip()
            # Remove any potential headers trapped in the block (like 'Quarter no' repetitions if any)
            cleaned_address = "\n".join([line.strip() for line in raw_address.split('\n') if line.strip()])
            data["Shipping Address"] = cleaned_address

        # 4. Extract 'Product SKU' (Strictly data between two '|')
        # Strategy: Find content between pipes. 
        # Note: In your sample, "AFDT-42-W" is immediately before a pipe. 
        # If the format strictly has it between pipes (e.g., "| AFDT-42-W |"), this regex works:
        # 
        sku_match = re.search(r"\|\s*([A-Za-z0-9-]+)\s*\|", text)
        
        if sku_match:
             data["Product SKU"] = sku_match.group(1).strip()
        else:
            # Fallback based on your sample where SKU is before the pipe for "10 day"
            # Matches "AFDT-42-W" in "Particle Board AFDT-42-W | 10 day"
            sku_fallback = re.search(r"([A-Za-z0-9-]+)\s*\|\s*10 day", text)
            if sku_fallback:
                data["Product SKU"] = sku_fallback.group(1).strip()

    return data

# --- Usage Example ---
# file_path = 'Pilla Uma.pdf'
# result = extract_invoice_details(file_path)
# print(result)
