from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative model."""


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inn: Mapped[str] = mapped_column(String(20), nullable=False)
    kpp: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    bank: Mapped[str] = mapped_column(String(255), nullable=False)
    account: Mapped[str] = mapped_column(String(34), nullable=False)
    bik: Mapped[str] = mapped_column(String(20), nullable=False)

    invoices: Mapped[list[Invoice]] = relationship(back_populates="organization")


class Contractor(Base):
    __tablename__ = "contractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    inn: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    kpp: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    invoices: Mapped[list[Invoice]] = relationship(back_populates="contractor")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(ForeignKey("contractors.id"), nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    template: Mapped[str] = mapped_column(String(100), nullable=False)
    docx_path: Mapped[str] = mapped_column(String(500), nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="invoices")
    contractor: Mapped[Contractor] = relationship(back_populates="invoices")
    items: Mapped[list[InvoiceItem]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        UniqueConstraint("invoice_id", "service_name", "description", name="uq_invoice_service_desc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[dict] = mapped_column(JSON, default=dict)

    invoice: Mapped[Invoice] = relationship(back_populates="items")
