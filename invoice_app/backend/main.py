from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db, init_db
from models import Contractor, Invoice, InvoiceItem, Organization
from services.invoice_generator import (
    build_service_description,
    convert_docx_to_pdf,
    flatten_notes,
    replace_docx_variables,
)
from services.numbering import get_next_invoice_number
from services.templates_mapper import SERVICE_DEFINITIONS, get_services_catalog, resolve_template_for_services

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = BASE_DIR / "backend" / "templates"
INVOICES_DIR = BASE_DIR / "invoices"

app = FastAPI(title="Invoice Creator RU", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContractorPayload(BaseModel):
    name: str = Field(min_length=2)
    inn: str = Field(min_length=10, max_length=12)
    kpp: str = ""
    address: str = Field(min_length=3)


class InvoiceItemPayload(BaseModel):
    service_name: str
    description: str = ""
    qty: float = Field(gt=0)
    price: float = Field(gt=0)
    notes: dict[str, str] = Field(default_factory=dict)


class InvoiceCreatePayload(BaseModel):
    organization_id: int
    contractor: ContractorPayload
    items: list[InvoiceItemPayload]


@app.on_event("startup")
def on_startup() -> None:
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


@app.get("/api/organizations")
def list_organizations(db: Session = Depends(get_db)):
    organizations = db.scalars(select(Organization).order_by(Organization.name)).all()
    return [
        {
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "kpp": org.kpp,
            "address": org.address,
            "bank": org.bank,
            "account": org.account,
            "bik": org.bik,
        }
        for org in organizations
    ]


@app.get("/api/services")
def list_services():
    return get_services_catalog()


@app.get("/api/contractors/search")
def search_contractor(inn: str = Query(..., min_length=10, max_length=12), db: Session = Depends(get_db)):
    contractor = db.scalar(select(Contractor).where(Contractor.inn == inn))
    if not contractor:
        raise HTTPException(status_code=404, detail="Контрагент не найден")
    return {
        "id": contractor.id,
        "name": contractor.name,
        "inn": contractor.inn,
        "kpp": contractor.kpp,
        "address": contractor.address,
    }


@app.get("/api/invoices")
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.scalars(
        select(Invoice)
        .options(joinedload(Invoice.organization), joinedload(Invoice.contractor))
        .order_by(Invoice.id.desc())
    ).unique().all()
    return [
        {
            "id": inv.id,
            "number": inv.number,
            "date": inv.date.strftime("%d.%m.%Y"),
            "organization": inv.organization.name,
            "contractor": inv.contractor.name,
            "total": inv.total,
            "template": inv.template,
            "docx_url": f"/api/invoices/{inv.id}/docx",
            "pdf_url": f"/api/invoices/{inv.id}/pdf",
        }
        for inv in invoices
    ]


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.scalar(
        select(Invoice)
        .options(
            joinedload(Invoice.organization),
            joinedload(Invoice.contractor),
            joinedload(Invoice.items),
        )
        .where(Invoice.id == invoice_id)
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return {
        "id": invoice.id,
        "number": invoice.number,
        "date": invoice.date.strftime("%d.%m.%Y"),
        "organization": invoice.organization.name,
        "contractor": invoice.contractor.name,
        "items": [
            {
                "service_name": item.service_name,
                "description": item.description,
                "qty": item.qty,
                "price": item.price,
                "notes": item.notes,
            }
            for item in invoice.items
        ],
        "total": invoice.total,
    }


@app.get("/api/invoices/{invoice_id}/docx")
def download_docx(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return FileResponse(path=invoice.docx_path, filename=Path(invoice.docx_path).name)


@app.get("/api/invoices/{invoice_id}/pdf")
def download_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.scalar(select(Invoice).where(Invoice.id == invoice_id))
    if not invoice:
        raise HTTPException(status_code=404, detail="Счет не найден")
    return FileResponse(path=invoice.pdf_path, filename=Path(invoice.pdf_path).name)


@app.post("/api/invoices")
def create_invoice(payload: InvoiceCreatePayload, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы одну услугу")

    unknown_services = [item.service_name for item in payload.items if item.service_name not in SERVICE_DEFINITIONS]
    if unknown_services:
        raise HTTPException(status_code=400, detail=f"Неизвестные услуги: {', '.join(unknown_services)}")

    org = db.scalar(select(Organization).where(Organization.id == payload.organization_id))
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    template = resolve_template_for_services([item.service_name for item in payload.items])

    contractor = db.scalar(select(Contractor).where(Contractor.inn == payload.contractor.inn))
    if contractor:
        contractor.name = payload.contractor.name
        contractor.kpp = payload.contractor.kpp
        contractor.address = payload.contractor.address
    else:
        contractor = Contractor(**payload.contractor.model_dump())
        db.add(contractor)

    number = get_next_invoice_number(db)
    issue_date = date.today()
    items_data = [item.model_dump() for item in payload.items]
    total = round(sum(item["qty"] * item["price"] for item in items_data), 2)

    docx_name = f"invoice_{number}_{issue_date:%Y%m%d}.docx"
    pdf_name = f"invoice_{number}_{issue_date:%Y%m%d}.pdf"
    docx_path = INVOICES_DIR / docx_name
    pdf_path = INVOICES_DIR / pdf_name

    notes_flat = flatten_notes(items_data)
    context = {
        "invoice_number": number,
        "date": issue_date.strftime("%d.%m.%Y"),
        "org_name": org.name,
        "org_inn": org.inn,
        "org_kpp": org.kpp,
        "org_address": org.address,
        "org_bank": org.bank,
        "org_account": org.account,
        "org_bik": org.bik,
        "client_name": payload.contractor.name,
        "client_inn": payload.contractor.inn,
        "client_kpp": payload.contractor.kpp,
        "client_address": payload.contractor.address,
        "service_description": build_service_description(items_data),
        "total": f"{total:.2f}",
    }
    context.update(notes_flat)

    template_path = TEMPLATES_DIR / template
    replace_docx_variables(template_path, docx_path, context)
    convert_docx_to_pdf(docx_path, pdf_path)

    invoice = Invoice(
        number=number,
        date=issue_date,
        organization_id=org.id,
        contractor=contractor,
        total=total,
        template=template,
        docx_path=str(docx_path),
        pdf_path=str(pdf_path),
    )
    db.add(invoice)
    db.flush()

    for item in items_data:
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                service_name=item["service_name"],
                description=item.get("description") or item["service_name"],
                qty=item["qty"],
                price=item["price"],
                notes=item.get("notes") or {},
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения счета: {exc.orig}")

    return {
        "id": invoice.id,
        "number": invoice.number,
        "date": invoice.date.strftime("%d.%m.%Y"),
        "docx_url": f"/api/invoices/{invoice.id}/docx",
        "pdf_url": f"/api/invoices/{invoice.id}/pdf",
    }


app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def root_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/create")
def create_page():
    return FileResponse(FRONTEND_DIR / "create_invoice.html")
