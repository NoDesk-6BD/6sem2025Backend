from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# -------------------------
# Base + shared table args
# -------------------------
class Base(DeclarativeBase):
    pass


SCHEMA = "dbo"


class TicketTag(Base):
    __tablename__ = "TicketTags"
    __table_args__ = {"schema": SCHEMA}
    TicketId: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.Tickets.TicketId", name="FK_TT_Ticket"),
        primary_key=True,
    )
    TagId: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{SCHEMA}.Tags.TagId", name="FK_TT_Tag"),
        primary_key=True,
    )


# -------------------------
# Simple lookup entities
# -------------------------
class Category(Base):
    __tablename__ = "Categories"
    __table_args__ = {"schema": SCHEMA}

    category_id: Mapped[int] = mapped_column("CategoryId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(100), nullable=False)

    subcategories: Mapped[List["Subcategory"]] = relationship(back_populates="category")


class Subcategory(Base):
    __tablename__ = "Subcategories"
    __table_args__ = {"schema": SCHEMA}

    subcategory_id: Mapped[int] = mapped_column("SubcategoryId", Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        "CategoryId",
        Integer,
        ForeignKey(f"{SCHEMA}.Categories.CategoryId", name="FK_Subcategories_Category"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("Name", String(100), nullable=False)

    category: Mapped[Category] = relationship(back_populates="subcategories")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="subcategory")


class Department(Base):
    __tablename__ = "Departments"
    __table_args__ = {"schema": SCHEMA}

    department_id: Mapped[int] = mapped_column("DepartmentId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(100), nullable=False)

    agents: Mapped[List["Agent"]] = relationship(back_populates="department")


class Priority(Base):
    __tablename__ = "Priorities"
    __table_args__ = {"schema": SCHEMA}

    priority_id: Mapped[int] = mapped_column("PriorityId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(50), nullable=False)
    weight: Mapped[Optional[int]] = mapped_column("Weight")

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="priority")


class Product(Base):
    __tablename__ = "Products"
    __table_args__ = {"schema": SCHEMA}

    product_id: Mapped[int] = mapped_column("ProductId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(150), nullable=False)
    code: Mapped[Optional[str]] = mapped_column("Code", String(50))
    description: Mapped[Optional[str]] = mapped_column("Description", String(500))
    is_active: Mapped[Optional[bool]] = mapped_column("IsActive", Boolean)
    created_at: Mapped[Optional[datetime]] = mapped_column("CreatedAt", DATETIME2)

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="product")


class SLAPlan(Base):
    __tablename__ = "SLA_Plans"
    __table_args__ = {"schema": SCHEMA}

    sla_plan_id: Mapped[int] = mapped_column("SLAPlanId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(80), nullable=False)
    first_response_mins: Mapped[Optional[int]] = mapped_column("FirstResponseMins")
    resolution_mins: Mapped[Optional[int]] = mapped_column("ResolutionMins")

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="sla_plan")


class Status(Base):
    __tablename__ = "Statuses"
    __table_args__ = {"schema": SCHEMA}

    status_id: Mapped[int] = mapped_column("StatusId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(60), nullable=False)

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="current_status")
    from_history: Mapped[List["TicketStatusHistory"]] = relationship(
        back_populates="from_status",
        foreign_keys="TicketStatusHistory.from_status_id",
    )
    to_history: Mapped[List["TicketStatusHistory"]] = relationship(
        back_populates="to_status",
        foreign_keys="TicketStatusHistory.to_status_id",
    )


class Tag(Base):
    __tablename__ = "Tags"
    __table_args__ = {"schema": SCHEMA}

    tag_id: Mapped[int] = mapped_column("TagId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(60), nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(secondary=f"{SCHEMA}.TicketTags", back_populates="tags")


class Company(Base):
    __tablename__ = "Companies"
    __table_args__ = {"schema": SCHEMA}

    company_id: Mapped[int] = mapped_column("CompanyId", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("Name", String(120), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column("CNPJ", String(32))
    segmento: Mapped[Optional[str]] = mapped_column("Segmento", String(60))
    created_at: Mapped[Optional[datetime]] = mapped_column("CreatedAt", DATETIME2)

    users: Mapped[List["User"]] = relationship(back_populates="company")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="company")


# -------------------------
# People
# -------------------------
class Agent(Base):
    __tablename__ = "Agents"
    __table_args__ = {"schema": SCHEMA}

    agent_id: Mapped[int] = mapped_column("AgentId", Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column("FullName", String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column("Email", String(254))
    phone: Mapped[Optional[str]] = mapped_column("Phone", String(40))
    department_id: Mapped[Optional[int]] = mapped_column(
        "DepartmentId",
        Integer,
        ForeignKey(f"{SCHEMA}.Departments.DepartmentId", name="FK_Agents_Department"),
    )
    is_active: Mapped[Optional[bool]] = mapped_column("IsActive", Boolean)
    hired_at: Mapped[Optional[date]] = mapped_column("HiredAt", Date)

    department: Mapped[Optional[Department]] = relationship(back_populates="agents")
    assigned_tickets: Mapped[List["Ticket"]] = relationship(back_populates="assigned_agent")
    changed_status: Mapped[List["TicketStatusHistory"]] = relationship(back_populates="changed_by_agent")
    interactions: Mapped[List["TicketInteraction"]] = relationship(back_populates="author_agent")


class User(Base):
    __tablename__ = "Users"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[int] = mapped_column("UserId", Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        "CompanyId",
        Integer,
        ForeignKey(f"{SCHEMA}.Companies.CompanyId", name="FK_Users_Company"),
    )
    full_name: Mapped[str] = mapped_column("FullName", String(120), nullable=False)
    email: Mapped[Optional[str]] = mapped_column("Email", String(254))
    phone: Mapped[Optional[str]] = mapped_column("Phone", String(40))
    cpf: Mapped[Optional[str]] = mapped_column("CPF", String(32))
    created_at: Mapped[Optional[datetime]] = mapped_column("CreatedAt", DATETIME2)
    is_vip: Mapped[Optional[bool]] = mapped_column("IsVIP", Boolean)

    company: Mapped[Optional[Company]] = relationship(back_populates="users")
    created_tickets: Mapped[List["Ticket"]] = relationship(back_populates="created_by_user")
    interactions: Mapped[List["TicketInteraction"]] = relationship(back_populates="author_user")


# -------------------------
# Tickets & related
# -------------------------
class Ticket(Base):
    __tablename__ = "Tickets"
    __table_args__ = {"schema": SCHEMA}

    ticket_id: Mapped[int] = mapped_column("TicketId", BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        "CompanyId",
        Integer,
        ForeignKey(f"{SCHEMA}.Companies.CompanyId", name="FK_Tickets_Company"),
        nullable=False,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        "CreatedByUserId",
        Integer,
        ForeignKey(f"{SCHEMA}.Users.UserId", name="FK_Tickets_User"),
        nullable=False,
    )
    assigned_agent_id: Mapped[Optional[int]] = mapped_column(
        "AssignedAgentId",
        Integer,
        ForeignKey(f"{SCHEMA}.Agents.AgentId", name="FK_Tickets_Agent"),
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        "ProductId",
        Integer,
        ForeignKey(f"{SCHEMA}.Products.ProductId", name="FK_Tickets_Product"),
    )
    category_id: Mapped[int] = mapped_column(
        "CategoryId",
        Integer,
        ForeignKey(f"{SCHEMA}.Categories.CategoryId", name="FK_Tickets_Category"),
        nullable=False,
    )
    subcategory_id: Mapped[Optional[int]] = mapped_column(
        "SubcategoryId",
        Integer,
        ForeignKey(f"{SCHEMA}.Subcategories.SubcategoryId", name="FK_Tickets_Subcategory"),
    )
    priority_id: Mapped[int] = mapped_column(
        "PriorityId",
        Integer,
        ForeignKey(f"{SCHEMA}.Priorities.PriorityId", name="FK_Tickets_Priority"),
        nullable=False,
    )
    current_status_id: Mapped[int] = mapped_column(
        "CurrentStatusId",
        Integer,
        ForeignKey(f"{SCHEMA}.Statuses.StatusId", name="FK_Tickets_Status"),
        nullable=False,
    )
    sla_plan_id: Mapped[int] = mapped_column(
        "SLAPlanId",
        Integer,
        ForeignKey(f"{SCHEMA}.SLA_Plans.SLAPlanId", name="FK_Tickets_SLA"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column("Title", String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column("Description", Text)
    channel: Mapped[Optional[str]] = mapped_column("Channel", String(40))
    device: Mapped[Optional[str]] = mapped_column("Device", String(60))
    created_at: Mapped[Optional[datetime]] = mapped_column("CreatedAt", DATETIME2)
    first_response_at: Mapped[Optional[datetime]] = mapped_column("FirstResponseAt", DATETIME2)
    closed_at: Mapped[Optional[datetime]] = mapped_column("ClosedAt", DATETIME2)

    # Relationships
    company: Mapped[Company] = relationship(back_populates="tickets")
    created_by_user: Mapped[User] = relationship(back_populates="created_tickets", foreign_keys=[created_by_user_id])
    assigned_agent: Mapped[Optional[Agent]] = relationship(back_populates="assigned_tickets")
    product: Mapped[Optional[Product]] = relationship(back_populates="tickets")
    category: Mapped[Category] = relationship()
    subcategory: Mapped[Optional[Subcategory]] = relationship(back_populates="tickets")
    priority: Mapped[Priority] = relationship(back_populates="tickets")
    current_status: Mapped[Status] = relationship(back_populates="tickets")
    sla_plan: Mapped[SLAPlan] = relationship(back_populates="tickets")

    attachments: Mapped[List["Attachment"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    interactions: Mapped[List["TicketInteraction"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    status_history: Mapped[List["TicketStatusHistory"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    tags: Mapped[list[Tag]] = relationship(secondary=f"{SCHEMA}.TicketTags", back_populates="tickets")


class Attachment(Base):
    __tablename__ = "Attachments"
    __table_args__ = {"schema": SCHEMA}

    attachment_id: Mapped[int] = mapped_column("AttachmentId", BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        "TicketId",
        BigInteger,
        ForeignKey(f"{SCHEMA}.Tickets.TicketId", name="FK_Att_Ticket"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column("FileName", String(255), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column("MimeType", String(100))
    size_bytes: Mapped[Optional[int]] = mapped_column("SizeBytes", BigInteger)
    storage_path: Mapped[str] = mapped_column("StoragePath", String(400), nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column("UploadedAt", DATETIME2)

    ticket: Mapped[Ticket] = relationship(back_populates="attachments")


class TicketInteraction(Base):
    __tablename__ = "TicketInteractions"
    __table_args__ = {"schema": SCHEMA}

    interaction_id: Mapped[int] = mapped_column("InteractionId", BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        "TicketId",
        BigInteger,
        ForeignKey(f"{SCHEMA}.Tickets.TicketId", name="FK_TI_Ticket"),
        nullable=False,
    )
    author_type: Mapped[str] = mapped_column("AuthorType", CHAR(1), nullable=False)  # 'U' or 'A'
    author_user_id: Mapped[Optional[int]] = mapped_column(
        "AuthorUserId", Integer, ForeignKey(f"{SCHEMA}.Users.UserId", name="FK_TI_User")
    )
    author_agent_id: Mapped[Optional[int]] = mapped_column(
        "AuthorAgentId",
        Integer,
        ForeignKey(f"{SCHEMA}.Agents.AgentId", name="FK_TI_Agent"),
    )
    message: Mapped[str] = mapped_column("Message", Text, nullable=False)
    is_public: Mapped[Optional[bool]] = mapped_column("IsPublic", Boolean)
    created_at: Mapped[Optional[datetime]] = mapped_column("CreatedAt", DATETIME2)

    ticket: Mapped[Ticket] = relationship(back_populates="interactions")
    author_user: Mapped[Optional[User]] = relationship(back_populates="interactions")
    author_agent: Mapped[Optional[Agent]] = relationship(back_populates="interactions")


class TicketStatusHistory(Base):
    __tablename__ = "TicketStatusHistory"
    __table_args__ = {"schema": SCHEMA}

    history_id: Mapped[int] = mapped_column("HistoryId", BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        "TicketId",
        BigInteger,
        ForeignKey(f"{SCHEMA}.Tickets.TicketId", name="FK_TSH_Ticket"),
        nullable=False,
    )
    from_status_id: Mapped[Optional[int]] = mapped_column(
        "FromStatusId",
        Integer,
        ForeignKey(f"{SCHEMA}.Statuses.StatusId", name="FK_TSH_FromStatus"),
    )
    to_status_id: Mapped[int] = mapped_column(
        "ToStatusId",
        Integer,
        ForeignKey(f"{SCHEMA}.Statuses.StatusId", name="FK_TSH_ToStatus"),
        nullable=False,
    )
    changed_at: Mapped[Optional[datetime]] = mapped_column("ChangedAt", DATETIME2)
    changed_by_agent_id: Mapped[Optional[int]] = mapped_column(
        "ChangedByAgentId",
        Integer,
        ForeignKey(f"{SCHEMA}.Agents.AgentId", name="FK_TSH_Agent"),
    )

    ticket: Mapped[Ticket] = relationship(back_populates="status_history")
    from_status: Mapped[Optional[Status]] = relationship(back_populates="from_history", foreign_keys=[from_status_id])
    to_status: Mapped[Status] = relationship(back_populates="to_history", foreign_keys=[to_status_id])
    changed_by_agent: Mapped[Optional[Agent]] = relationship(back_populates="changed_status")


# -------------------------
# Audit
# -------------------------
class AuditLog(Base):
    __tablename__ = "AuditLogs"
    __table_args__ = {"schema": SCHEMA}

    audit_id: Mapped[int] = mapped_column("AuditId", BigInteger, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column("EntityType", String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column("EntityId", BigInteger, nullable=False)
    operation: Mapped[str] = mapped_column("Operation", String(20), nullable=False)
    performed_by: Mapped[Optional[str]] = mapped_column("PerformedBy", String(120))
    performed_at: Mapped[Optional[datetime]] = mapped_column("PerformedAt", DATETIME2)
    details_json: Mapped[Optional[str]] = mapped_column("DetailsJson", Text)
