# AGENTS.md — HotelBooking

Plateforme de réservation hôtelière : backend **Django 6.1 + DRF** (`backend/`) et
frontend **React 19 + Vite + Tailwind 4** (`frontend/`). La référence
architecturale est `docs/ARCHITECTURE.md` (lecture avant de toucher au backend) ;
`README.md` contient le démarrage rapide et les variables d'environnement.

## Repo map (facile à se tromper)
- **`backend/`** — Django. `manage.py` vit *ici*, pas à la racine : tout se lance
  depuis `backend/`. Le venv est à la **racine** : `.venv\Scripts\python.exe`
  (pas `env/`). Fichiers `.env`/`.env.example` dans `backend/` (le `.env` est
  nécessaire pour tourner ; ne jamais le lire/commiter).
- **`backend/apps/`** — apps métier sous namespace `apps.*` :
  `core` (TimeStampedModel), `accounts` (User email + rôles client /
  hotel_manager / admin), `hotels`, `bookings`, `payments` (Stripe),
  `reviews`, `notifications`. `config/` = projet Django (settings, urls, celery).
- **`frontend/`** — React 19, source en **`.jsx`** (pas TS malgré tsconfig +
  script `typecheck`), alias `@` → `./src`, Tailwind 4 via plugin
  `@tailwindcss/vite`, animations avec `motion`. `npm run dev` sert :5173
  (`strictPort`) et proxifie `/api` + `/media` → Django :8000 : ouvrir l'app via
  **:5173**, jamais :8000.
- **`docs/ARCHITECTURE.md`** — modèles de données, choix techniques, état de la
  route des étapes (reflète "qu'est-ce qui est implémenté").

## Backend — points chauds
- API versionnée `/api/v1/` (DRF ViewSets + routeurs), JWT SimpleJWT avec
  rotation + blacklist, permissions métier dans `apps/core/permissions.py`.
- **Réservations** : cycle de vie `pending → confirmed → completed` (ou
  `cancelled`), snapshot du prix, anti double-réservation à deux niveaux
  (logique `Booking.clean()`/`overlapping()` + contrainte d'exclusion GiST
  PostgreSQL — no-op sur SQLite dev).
- **Paiements** : Stripe Checkout côté serveur, webhook vérifié par signature
  HMAC + idempotence ; payer/réservation se confirment mutuellement.
- **Avis** : 1 par (client, hôtel), signaux qui tiennent à jour
  `Hotel.average_rating` / `reviews_count`.
- **Async** : Celery + Redis (`config/celery.py`) ; tâches dans
  `apps/bookings/tasks.py` et `apps/payments/tasks.py`. En dev/tests sans
  worker : `CELERY_TASK_ALWAYS_EAGER=true` dans `.env`.
- Nouvelles chaînes/évolutions API : `@extend_schema` attendu sur toute action
  custom (drf-spectacular, docs `/api/docs/`).

## Frontend — conventions
- Pages dans `src/pages/` (`*.jsx`), composants partagés dans `src/components/`
  (`ui/` pour les primitives), `lib/api.js` (axios) + `lib/auth.jsx`,
  styles dans `src/styles/` (Tailwind, `global.css`).
- Routage react-router-dom v7 ; `PrivateRoute` / `ManagerRoute` pour
  restreindre les pages ; jetons JWT gérés via `lib/auth`.

## Vérification (il y a de vrais tests)
- Backend : `pytest` avec pytest-django. Depuis `backend/` :
  `..\.venv\Scripts\python.exe -m pytest` (`pytest.ini` configure le settings
  module ; `apps/factories.py` + `conftest.py` fournissent factories et
  fixtures). Un `tests.py` par app métier.
- Backend système : `..\.venv\Scripts\python.exe manage.py check` (depuis
  `backend/`).
- Frontend : `npm run build` (depuis `frontend/`) ; `npm run typecheck` existe
  (tsc --noEmit) même si la source est en `.jsx` — à utiliser avec prudence.
- Dev local : `./start-dev.ps1` lance Django :8000 + Vite :5173 en parallèle.
  Smoke-test des pages dans un vrai navigateur (via :5173) — ne pas sonder avec
  curl (défauts CSS/JS invisibles autrement).

## Ne pas commiter
`.env`, `db.sqlite3`, `media/`, `staticfiles/`, `.venv/`, `node_modules/`,
`dist/`, `*.log`, artefacts d'exécution (`_server*.log`, `_server.err`,
`_vite.log`, `_vite.err`, `_pytest_hbp.log`, `_startdev-test.log`). Le dépôt
n'est pas encore initialisé en git (voir note racine `.gitignore`).