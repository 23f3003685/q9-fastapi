from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re

app = FastAPI()


# ---------------- Request ----------------
class InvoiceRequest(BaseModel):
    text: str


# ---------------- Response ----------------
class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(pattern="^[A-Z]{3}$")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


# ---------------- Vendor extraction ----------------
def extract_vendor(text: str):
    patterns = [
        r"Invoice from\s*[:\-]?\s*(.+?)(?:\||Amount|Total|Due|Deadline|$)",
        r"Vendor\s*[:\-]?\s*(.+?)(?:\||Amount|Total|Due|Deadline|$)",
        r"Billed to\s*[:\-]?\s*(.+?)(?:\||Amount|Total|Due|Deadline|$)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            vendor = match.group(1).strip()
            # safety cleanup (avoid capturing empty/word like "Invoice")
            if len(vendor) > 1 and "invoice" not in vendor.lower():
                return vendor

    return None


# ---------------- Amount extraction ----------------
def extract_amount(text: str):
    patterns = [
        r"(?:amount due|total|amount)\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)\s*(USD|EUR|GBP)",
        r"(USD|EUR|GBP)\s*([0-9]+(?:\.[0-9]{1,2})?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            for g in match.groups():
                if g and re.match(r"^[0-9]+(\.[0-9]{1,2})?$", g):
                    return float(g)

    return None


# ---------------- Currency extraction ----------------
def extract_currency(text: str):
    match = re.search(r"\b(USD|EUR|GBP)\b", text)
    return match.group(1) if match else None


# ---------------- Date extraction ----------------
def extract_date(text: str):
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else None


# ---------------- Endpoint ----------------
@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):
    text = req.text

    # Only reject truly invalid input
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    vendor = extract_vendor(text)
    amount = extract_amount(text)
    currency = extract_currency(text)
    date = extract_date(text)

    # IMPORTANT: no fake defaults, but also avoid over-rejecting
    if not vendor or not amount or not currency or not date:
        raise HTTPException(status_code=422, detail="Could not extract invoice fields")

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date
    )