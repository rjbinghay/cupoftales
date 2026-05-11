# StorySip

A Django-based platform for publishing and discovering short stories. Writers can create accounts, publish stories with categories and tags, and customize their public profile with a pen name and donation links. Readers can browse, search, and filter by category, read time, and AI-authorship label.

Live at: `https://www.rhoderich.com/apps/cupoftales/`

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [URL Routes](#url-routes)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [Tailwind CSS](#tailwind-css)
- [Management Commands](#management-commands)

---

## Architecture

```
Browser
   │
   ▼
Nginx (reverse proxy)
   │  Passes /apps/cupoftales/* to localhost:8001
   ▼
Docker container (port 8001 → 8000)
   │
   ├── Gunicorn (2 workers, WSGI)
   │      │
   │      └── Django 6 application
   │             ├── WhiteNoise  ← serves static files directly
   │             ├── stories app ← story CRUD, categories, tags, search
   │             └── users app   ← auth, writer profiles
   │
   └── SQLite (./data/db.sqlite3, volume-mounted for persistence)
```

The app runs at the subpath `/apps/cupoftales/` — `FORCE_SCRIPT_NAME` in settings handles URL reversals, and Nginx forwards requests to the container on `127.0.0.1:8001`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 6.0.4 |
| Language | Python 3.12 |
| Database | SQLite 3 |
| WSGI server | Gunicorn 23.0.0 |
| Static files | WhiteNoise 6.9.0 |
| CSS framework | Tailwind CSS v4 + Typography plugin |
| CSS build | Node 20 / npm |
| Email | Brevo SMTP (password resets) |
| Containerization | Docker (multi-stage build) |
| Fonts | Source Serif 4 (prose), Inter (UI) via Google Fonts |

---

## Project Structure

```
storysip/
├── config/                  # Django project settings
│   ├── settings.py          # All configuration (env-driven)
│   ├── urls.py              # Root URL router
│   ├── wsgi.py
│   └── asgi.py
│
├── stories/                 # Core content app
│   ├── models.py            # Story, Category, Tag, WriterProfile
│   ├── views.py             # Home, detail, search, create/edit/delete
│   ├── forms.py             # StoryForm with tag parsing
│   ├── urls.py
│   ├── admin.py
│   ├── migrations/
│   ├── templates/stories/
│   └── management/commands/ # seed_stories, clear_fake_stories
│
├── users/                   # Auth + writer profile app
│   ├── views.py             # Login, signup, logout, dashboard, profile edit
│   ├── forms.py             # CustomUserCreationForm
│   ├── urls.py
│   ├── templates/users/
│   └── migrations/
│
├── static/
│   ├── css/
│   │   ├── input.css        # Tailwind source (design tokens + components)
│   │   └── main.css         # Generated — do not edit directly
│   └── images/              # Logo assets
│
├── data/                    # SQLite database (Docker volume target)
│   └── db.sqlite3
│
├── staticfiles/             # collectstatic output (Docker build artifact)
│
├── package.json             # npm build scripts
├── requirements.txt         # Python dependencies
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Single-service compose config
├── .env.example             # Environment variable template
└── manage.py
```

---

## Data Models

### Story
| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| content | TextField | |
| category | ForeignKey | → Category |
| tags | ManyToManyField | → Tag |
| author | ForeignKey | → User |
| ai_label | CharField | `human` / `assisted` / `ai` |
| read_time_minutes | IntegerField | Auto-calculated on save (words ÷ 200) |
| is_published | BooleanField | |
| view_count | IntegerField | |
| created_at / updated_at | DateTimeField | |

### Category
Slug-based, with `display_order` for custom ordering in the nav.

### Tag
Auto-slug from name. M2M with Story. Created on the fly from comma-separated form input.

### WriterProfile (extends User 1:1)
| Field | Notes |
|---|---|
| display_name | Optional pen name (unique, nullable) |
| bio | Short author bio |
| paypal_link | Donation link |
| kofi_link | Ko-fi link |
| other_donation_link | Any other link |
| is_verified | Verified writer flag |

`public_name` property returns: pen name → full name → @username (first non-empty).

---

## URL Routes

### Stories (`/`)

| URL | View | Auth |
|---|---|---|
| `/` | Home — filterable story list | Public |
| `/about/` | About page | Public |
| `/story/<id>/` | Story detail | Public |
| `/category/<slug>/` | Stories by category | Public |
| `/categories/` | All categories with counts | Public |
| `/tag/<slug>/` | Stories by tag | Public |
| `/search/` | Full-text search | Public |
| `/story/new/` | Create story | Login required |
| `/story/<id>/edit/` | Edit story | Owner only |
| `/story/<id>/delete/` | Delete story | Owner only |

### Users (`/users/`)

| URL | View | Auth |
|---|---|---|
| `/users/signup/` | Register | Public |
| `/users/login/` | Login | Public |
| `/users/logout/` | Logout | Login required |
| `/users/dashboard/` | Writer's story list | Login required |
| `/users/profile/edit/` | Edit profile | Login required |
| `/users/profile/<username>/` | Public writer profile | Public |
| `/users/password-reset/` | Password reset flow | Public |

> All routes are prefixed with `/apps/cupoftales/` in production.

---

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Steps

**1. Clone and enter the project**
```bash
git clone <repo-url>
cd storysip
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**4. Install Node dependencies (for Tailwind)**
```bash
npm install
```

**5. Set up environment variables**
```bash
cp .env.example .env
```
Edit `.env` and fill in the required values (see [Environment Variables](#environment-variables)).
For local development, set `DJANGO_DEBUG=1`.

**6. Run database migrations**
```bash
python manage.py migrate
```

**7. Create a superuser (optional)**
```bash
python manage.py createsuperuser
```

**8. Seed sample stories (optional)**
```bash
python manage.py seed_stories
```

**9. Start the Tailwind watcher and Django dev server**

In two separate terminals:

```bash
# Terminal 1 — CSS watcher
npm run dev

# Terminal 2 — Django dev server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

> Note: In local development, `FORCE_SCRIPT_NAME` is not set, so URLs resolve from `/` instead of `/apps/cupoftales/`.

---

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Steps

**1. Clone the repository on your server**
```bash
git clone <repo-url>
cd storysip
```

**2. Create the `.env` file**
```bash
cp .env.example .env
```
Fill in all values. For production, set `DJANGO_DEBUG=0` and use a strong `DJANGO_SECRET_KEY`.

**3. Create the data directory**
```bash
mkdir -p data
```

**4. Build and start the container**
```bash
docker compose up -d --build
```

The app will be available on `127.0.0.1:8001` (not exposed to the public internet directly).

**5. Run migrations**
```bash
docker compose exec web python manage.py migrate
```

**6. Create a superuser**
```bash
docker compose exec web python manage.py createsuperuser
```

### Nginx Configuration (Reverse Proxy)

Add a location block to your Nginx site config to forward requests to the container:

```nginx
location /apps/cupoftales/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Reload Nginx after updating:
```bash
sudo nginx -s reload
```

### Updating the App

```bash
git pull
docker compose up -d --build
docker compose exec web python manage.py migrate
```

### Useful Docker Commands

```bash
# View running containers
docker compose ps

# Tail application logs
docker compose logs -f web

# Open a shell inside the container
docker compose exec web bash

# Stop the app
docker compose down

# Stop and remove volumes (destructive — deletes database)
docker compose down -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and set the following:

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Long random string. Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | Yes | `1` for development, `0` for production |
| `DJANGO_ALLOWED_HOSTS` | Yes | Comma-separated hostnames, e.g. `www.rhoderich.com` |
| `BREVO_USER` | For email | Your Brevo SMTP login (email) |
| `BREVO_KEY` | For email | Your Brevo SMTP API key |

Email is only required for password reset functionality. If not configured, password resets will fail silently.

---

## Tailwind CSS

StorySip uses **Tailwind CSS v4** with a CSS-first configuration — there is no `tailwind.config.js`. All design tokens (colors, fonts, spacing) live in `static/css/input.css` inside the `@theme` block.

### Design Tokens

| Token | Value | Usage |
|---|---|---|
| `--color-paper` | `#FBFAF7` | Page background |
| `--color-ink` | `#1A1A1A` | Body text |
| `--color-accent` | warm brown | Links, buttons, highlights |
| `--font-prose` | Source Serif 4 | Story body text |
| `--font-ui` | Inter | Navigation, labels, UI chrome |

### Build Commands

```bash
npm run dev      # Watch mode — rebuilds main.css on every template or CSS save
npm run build    # Production minified build
```

### Where to Add Styles

| Goal | Where |
|---|---|
| Change a color, font, or spacing token | `@theme` block in `input.css` |
| Tweak default heading or body styles | `@layer base` in `input.css` |
| Add a reusable component (card, button) | `@layer components` in `input.css` |
| One-off style on a single element | Tailwind utility classes in the template |

If a class string repeats in 3+ places, promote it to a component in `input.css`.

### Story Body Rendering

Wrap rendered story content in `<div class="prose-story">…</div>`. The Tailwind Typography plugin handles paragraph spacing, blockquotes, lists, and links with reading-optimized defaults (65ch measure, 1.6 line-height).

---

## Management Commands

```bash
# Seed the database with fake stories (uses Faker)
python manage.py seed_stories

# Remove all seeded fake stories
python manage.py clear_fake_stories

# Standard Django commands
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```
