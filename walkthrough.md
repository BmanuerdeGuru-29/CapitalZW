# CapitalZW MVP Implementation Walkthrough

The CapitalZW Receivables Platform MVP has been successfully implemented. This document provides a walkthrough of the architecture, features, and instructions on how to test the platform.

## 🏗 Architecture & Design Decisions

*   **Framework**: Django (Python) using a modular monolith architecture.
*   **Database**: SQLite for local development (configured via `.env`), prepared for PostgreSQL in production.
*   **Styling**: Tailwind CSS (via CDN for rapid MVP development) with custom components built on top of a clean, modern aesthetic (Inter font, glass-morphism cards, emerald/teal color scheme).
*   **Service Layer**: Business logic is decoupled from views into a `services/` package. State transitions (e.g., approving an invoice, accepting an offer) are handled within atomic transactions, ensuring data integrity while generating audit logs and notifications simultaneously.
*   **Security**: Role-based access control (RBAC) enforced via custom decorators (`@supplier_required`, `@admin_required`, etc.) and data-level isolation rules in the service layer.

## 📦 Implemented Modules

1.  **Accounts & Authentication (`accounts`)**: Custom email-based User model with role assignment.
2.  **Organisations & Profiles (`organisations`)**: KYC and profile management for Suppliers, Buyers, and Financiers.
3.  **Invoice Management (`invoices`)**: Core tracking of invoices, document attachments, and status history.
4.  **Financing Offers (`offers`)**: Management of financier bids, discount calculations, and acceptance workflows.
5.  **Settlements (`settlements`)**: Tracking of final disbursements and subsequent repayment schedules.
6.  **Approvals (`approvals`)**: Buyer validation and approval workflow for submitted invoices.
7.  **Audit Trail (`audit`)**: Immutable, append-only logging of all critical actions and data mutations.
8.  **Notifications (`notifications`)**: In-app alerts for state changes.
9.  **Reporting (`reports`)**: Filterable, role-restricted CSV exports of platform data.
10. **Dashboards (`dashboard`)**: Role-specific KPI overviews and queue management.
11. **Public Site (`public_site`)**: Landing pages and lead generation forms.

## 🔄 Core Workflow

The platform supports a comprehensive end-to-end receivables financing lifecycle:

1.  **Submission**: Supplier uploads an invoice and supporting documents.
2.  **Verification**: Buyer reviews and approves the invoice (or requests clarification/rejects).
3.  **Marketplace**: Approved invoices become visible to Financiers.
4.  **Bidding**: Financiers submit competing offers (advance %, discount rate).
5.  **Acceptance**: Supplier accepts the best offer (auto-rejecting others).
6.  **Settlement**: Platform admin records the disbursement of funds from Financier to Supplier.
7.  **Repayment**: Platform tracks the eventual repayment from Buyer to Financier on the due date.

## 🚀 Running the Demo

The system includes a pre-configured demo scenario. A command has been built to seed the database with representative data and users.

### 1. Start the Server
If it is not already running, start the Django development server:
```bash
python manage.py runserver 127.0.0.1:8000
```

### 2. Demo Credentials
The `seed_demo_data` command has generated the following accounts. All accounts use the password: `password123`

*   **Platform Admin**: `admin@capitalzw.co.zw` (Full system overview, settlement recording)
*   **Supplier**: `supplier@acme.co.zw` (Invoice submission, offer acceptance)
*   **Buyer**: `buyer@megacorp.co.zw` (Invoice approval)
*   **Financier**: `financier@cfbank.co.zw` (Marketplace browsing, offer submission)

### 3. Recommended Testing Flow
1.  **View Public Site**: Open `http://127.0.0.1:8000/` to see the landing page.
2.  **Admin Overview**: Log in as Admin to view the platform-wide KPIs and the prepopulated demo data (Invoices, Organisations).
3.  **Supplier Submission**: Log in as Supplier. Navigate to "Submit Invoice". Notice the pending and approved invoices already in the dashboard.
4.  **Buyer Approval**: Log in as Buyer. Navigate to "Pending Approvals" and approve an invoice.
5.  **Financier Offer**: Log in as Financier. Go to the "Marketplace", view the newly approved invoice, and submit a financing offer.
6.  **Supplier Acceptance**: Log back in as Supplier. Go to the invoice details and "Accept" the financier's offer.
7.  **Admin Settlement**: Log in as Admin. Go to "Offers" and record the settlement for the accepted offer.
8.  **Audit Review**: As Admin, view the "Audit Logs" to see the immutable trail of the entire transaction.

## 🎥 Demo Recording
A browser subagent was used to verify the UI. You can view the recording of this verification here:
![CapitalZW Demo Workflow](file:///C:/Users/HP/.gemini/antigravity/brain/160f7d96-c2c5-4df5-819a-c102930bcd12/capitalzw_demo_1778777379025.webp)

## Next Steps for Production (Implemented)
The following production-readiness steps have been implemented in the codebase:
1.  **PostgreSQL** configured in `config/settings/prod.py`.
2.  **Redis and Celery** configured for async tasks (e.g., email notifications). The `send_email_notification_task` handles async emails.
3.  **AWS S3 Storage** configured via `django-storages` for KYC and invoice documents.
4.  **Static Files** handled by Whitenoise in production settings.
5.  **Dockerization** complete with `Dockerfile` and `docker-compose.yml` including web, db, redis, and celery services.

