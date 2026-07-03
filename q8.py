from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re

app = FastAPI()


class InvoiceRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(pattern="^[A-Z]{3}$")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


def extract_vendor(text: str):
    m = re.search(r"(?:Invoice from|Vendor|Billed to)\s*[:\-]?\s*(.+?)(?:\||Amount|Total|Due|Deadline|$)", text, re.I)
    return m.group(1).strip() if m else "Unknown"


def extract_amount(text: str):
    m = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)\s*(USD|EUR|GBP)", text, re.I)
    if m:
        return float(m.group(1))

    m = re.search(r"(?:amount due|total|amount)\s*[:=]?\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.I)
    return float(m.group(1)) if m else 0.0


def extract_currency(text: str):
    m = re.search(r"\b(USD|EUR|GBP)\b", text)
    return m.group(1) if m else "USD"


def extract_date(text: str):
    m = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return m.group(0) if m else "2026-01-01"


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):
    text = req.text

    # ONLY reject truly empty input
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    vendor = extract_vendor(text)
    amount = extract_amount(text)
    currency = extract_currency(text)
    date = extract_date(text)

    # IMPORTANT: never 422 for valid invoice
    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date
    )