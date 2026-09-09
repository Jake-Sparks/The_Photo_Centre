# Flask Photo Store

A full-stack photography marketplace built with Flask and SQLite, where users can browse and purchase photo licenses or physical prints, and bid on limited-edition releases. Includes a full admin back-end for managing inventory and reviewing activity.

## Demo

<img width="3024" height="1644" alt="image" src="https://github.com/user-attachments/assets/4a0f8557-89f2-4245-b04a-7a40917140a0" />
<img width="1950" height="1614" alt="image" src="https://github.com/user-attachments/assets/c90ddc14-40e7-4b38-9dd1-a5107287c443" />


## Features

**Customer-facing**
- Account signup/login with hashed passwords (Werkzeug security)
- Browsable photo gallery, filterable by theme, price range, and purchase type (license, print, or both) — filters persist across visits via session
- Photo detail pages supporting two purchase types per photo: digital license and/or physical print (with quantity and live inventory checks)
- Session-based shopping cart — add, remove, and review items before checkout
- Checkout flow collecting shipping details and payment method, with automatic inventory deduction and purchase logging
- User profile page showing full purchase history
- Limited-edition section: time-boxed listings (7-day window) with a live bidding system — tracks the current highest bid and enforces minimum-increment rules

**Admin**
- Role-gated control panel (`admin_required` decorator checks a DB flag, layered under `login_required`)
- Upload new photos (standard or limited-edition) with theme, pricing, and inventory
- Edit or delete existing listings, with file cleanup on delete
- Audit log of every admin action (upload/update/delete) with timestamp and user
- Payment log viewer for completed transactions and settled auctions

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, Flask |
| Session handling | Flask-Session (filesystem-backed) |
| Forms & validation | Flask-WTF / WTForms (CSRF protection included by default) |
| Auth | Werkzeug password hashing |
| Database | SQLite, raw SQL via a custom `database.py` connection helper |
| Frontend | Jinja2 templates, HTML/CSS, JavaScript |

## Getting Started

### Prerequisites
- Python 3.12 (avoid 3.14 — some session/serialization dependencies have build issues on it)

### Installation

```bash
git clone [your-repo-url]
cd [project-folder]

python3.12 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Running the app

```bash
flask run
```

Then open `http://127.0.0.1:5000`.

## Key Routes

| Route | Purpose |
|---|---|
| `/` | Home page with featured limited-edition item |
| `/signup`, `/login`, `/logout` | Authentication |
| `/gallery` | Filterable photo listing |
| `/photo/<id>` | Photo detail + add to cart |
| `/cart`, `/checkout`, `/order_confirmation` | Purchase flow |
| `/profile` | Purchase history |
| `/limited_edition`, `/bid/<id>` | Auction browsing and bidding |
| `/admin`, `/admin/upload`, `/admin/photos`, `/admin/logs`, `/admin/payment-logs` | Admin panel |

## What I'd improve next

- Move `SECRET_KEY` and other config to environment variables
- Replace the manual `/process_bid` trigger with a scheduled job to close auctions automatically
- Add automated tests around cart/checkout logic and inventory edge cases
- Pagination for the gallery as the catalog grows

## Author

Jake Sparks
