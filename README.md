# HotelBooking — Plateforme de réservation d'hôtels

API Django 6 + DRF (backend/) et frontend React 19 + Vite (frontend/).

## Fonctionnalités

- Authentification JWT avec rôles : client, gestionnaire d'hôtel, administrateur
- Hôtels et chambres avec recherche par ville, pays, dates, disponibilité et tri par prix
- Cycle de vie des réservations (pending → confirmed → completed / cancelled) avec protection anti-double-réservation (niveau application + contrainte d'exclusion GiST PostgreSQL)
- Paiements Stripe Checkout + webhook vérifié par signature HMAC, remboursements, gestion des expirations
- Avis clients (1–5) avec dénormalisation des notes moyennes et compteurs sur l'hôtel
- Notifications internes (info, réservation, paiement, annulation, rappel) avec API de lecture groupée
- Tâches asynchrones Celery + Redis : emails de confirmation, rappels J‑x, expiration des paiements en attente

## Architecture

- **backend/** : Django 6.1, DRF, SimpleJWT, PostgreSQL (prod) / SQLite (dev), Celery + Redis. API versionnée sous `/api/v1/`.
- **frontend/** : React 19, Vite, proxy `/api` vers `http://localhost:8000`.
- Documentation détaillée : `docs/ARCHITECTURE.md`.

## Démarrage rapide

### Backend

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Compléter SECRET_KEY, STRIPE_*, etc. dans .env
python manage.py migrate
python manage.py runserver          # API sur http://localhost:8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev                         # Dev server sur http://localhost:5173
```

### Tâches asynchrones (Celery)

Worker et beat (nécessitent Redis sur `redis://localhost:6379/0`) :

```powershell
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

Pour développer sans Redis, mettre `CELERY_TASK_ALWAYS_EAGER=true` dans `.env` (exécution synchrone immédiate).

### Webhooks Stripe (développement local)

```powershell
stripe listen --forward-to http://localhost:8000/api/v1/payments/webhook/
# Copier la valeur "whsec_…" dans STRIPE_WEBHOOK_SECRET du .env
stripe trigger payment_intent.succeeded   # Test du webhook
```

## Tests

Depuis `backend/` avec le venv racine activé :

```powershell
..\.venv\Scripts\python.exe -m pytest
```

## Variables d'environnement principales

| Variable | Description |
|---|---|
| `SECRET_KEY` | Clé secrète Django (générer avec `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DEBUG` | `True` en dev, `False` en prod |
| `ALLOWED_HOSTS` | Liste d'hôtes autorisés (ex: `localhost,127.0.0.1`) |
| `DATABASE_URL` | URL PostgreSQL (ex: `postgres://user:pass@host:5432/db`) — absent = SQLite `backend/db.sqlite3` |
| `CORS_ALLOWED_ORIGINS` | Origines CORS (ex: `http://localhost:5173`) |
| `EMAIL_BACKEND` | Backend email (console ou SMTP) + `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` |
| `REDIS_URL` | URL Redis pour Celery (ex: `redis://localhost:6379/0`) |
| `CELERY_TASK_ALWAYS_EAGER` | `true` pour exécution synchrone sans worker (dev/tests) |
| `SITE_NAME` | Nom du site utilisé dans les emails/notifications |
| `PAYMENT_PENDING_TIMEOUT_SECONDS` | Délai avant expiration d'un paiement en attente (défaut 3600) |
| `STRIPE_PUBLISHABLE_KEY` | Clé publique Stripe (dashboard) |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe (dashboard) |
| `STRIPE_WEBHOOK_SECRET` | Secret du webhook Stripe (obtenu via `stripe listen --forward-to …`) |
| `STRIPE_CURRENCY` | Devise (défaut `eur`) |
| `BOOKING_TAX_RATE` | Taux de taxe (défaut `0.10`) |
| `BOOKING_SERVICE_FEE` | Frais de service fixes (défaut `5.0`) |
| `BOOKING_CANCELLATION_DEADLINE_DAYS` | Jours avant l'arrivée pour annulation libre (défaut `2`) |
| `FRONTEND_URL` | URL du frontend pour les liens emails (défaut `http://localhost:5173`) |