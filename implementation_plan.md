# CapitalZW MVP Implementation Plan

## Workspace Status
- **Path**: `c:\Users\HP\Documents\2047 Tech Projects\Antigravity\CapitalZw`
- **State**: Empty directory — fresh project
- **Action**: Build from scratch

## Overview

CapitalZW is a secure digital receivables finance platform for invoice discounting. The MVP implements the core loop:

> Supplier submits invoice → Buyer approves → Financier offers → Supplier accepts → Admin settles → Reports & audit update

## Build Strategy

Given the massive scope (22 phases, 16+ apps, 30+ templates, REST API, public site, Docker), I'll implement in **4 macro-phases** to deliver a working system incrementally:

### Macro-Phase A: Foundation (Phases 1-3)
- Django project scaffold with split settings
- Custom User model with email auth
- Organisation + profile models
- Registration, login, logout, password reset
- Role-based redirect
- Base templates with Tailwind CSS (CDN for MVP speed)
- Docker files

### Macro-Phase B: Core Workflow (Phases 4-8)
- KYC/Document models
- Invoice model + submission workflow
- Buyer approval workflow
- Financier offer workflow
- Offer acceptance + settlement + repayment
- Service layer for all workflow actions
- Audit logging + notifications

### Macro-Phase C: UI & Features (Phases 9-15)
- Dashboard views for all roles
- Portal pages (supplier, buyer, financier, admin, compliance, auditor)
- Public website pages
- Reporting with CSV export
- Permissions enforcement
- Empty states + form UX

### Macro-Phase D: Polish & Delivery (Phases 16-22)
- REST API endpoints
- Demo data seeding command
- Tests
- Security hardening
- Deployment files
- README

## Proposed Changes

### Project Structure

```
capitalzw/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/        # Custom User, auth views
│   ├── organisations/   # Org + profiles
│   ├── documents/       # KYC + invoice docs
│   ├── invoices/        # Invoice CRUD + status
│   ├── approvals/       # Buyer approval
│   ├── offers/          # Financier offers
│   ├── settlements/     # Settlement + repayment
│   ├── notifications/   # In-app notifications
│   ├── audit/           # Audit log
│   ├── reports/         # Reporting + CSV
│   ├── dashboard/       # Role dashboards
│   └── public_site/     # Public pages + contact
├── services/            # Business logic service layer
├── templates/
├── static/
├── media/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CSS Framework | Tailwind CDN | Fast MVP; no build step needed |
| DB | SQLite (dev), PostgreSQL (Docker) | Simplest local dev experience |
| Auth | Custom User with email login | Requirement spec |
| File uploads | Django FileField + protected views | Secure, no external deps |
| Notifications | In-app DB model | Email/SMS are future phases |
| Charts | Chart.js CDN | Lightweight, no build step |
| API | DRF with versioned routes | Requirement spec |
| Env vars | python-decouple | Simple, well-supported |

### Models Summary

| App | Models |
|-----|--------|
| accounts | User |
| organisations | Organisation, SupplierProfile, BuyerProfile, FinancierProfile |
| documents | KYCDocument |
| invoices | Invoice, InvoiceDocument, InvoiceStatusHistory |
| approvals | BuyerApproval |
| offers | FinancingOffer |
| settlements | Settlement, Repayment |
| notifications | Notification |
| audit | AuditLog |
| public_site | ContactEnquiry |
| reports | (no models — query-based views) |
| dashboard | (no models — aggregate views) |

## Verification Plan

### Automated Tests
- `python manage.py test` — Django TestCase covering 16 critical workflow tests
- Migration check: `python manage.py migrate --check`
- System check: `python manage.py check --deploy` (prod settings)

### Manual Verification
- Run `python manage.py runserver` and verify all key URLs
- Load demo data with `python manage.py seed_demo_data`
- Walk through the 20-step demo scenario
- Verify role-based access isolation

## Open Questions

> [!IMPORTANT]
> **Tailwind CSS approach**: I'll use the Tailwind CDN (Play CDN) for MVP speed. This avoids Node.js build tooling but means slightly larger page loads. Is this acceptable, or do you want a compiled Tailwind setup with Node?

> [!NOTE]
> **Scope pragmatism**: This is an enormous specification. I'll prioritize the core workflow loop and essential pages, with clean stubs for lower-priority pages. All models, services, and permissions will be fully implemented.
