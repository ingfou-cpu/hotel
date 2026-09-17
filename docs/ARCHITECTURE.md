# HotelBooking — Architecture technique

Plateforme de réservation hôtelière : backend **Django 6 / DRF / PostgreSQL** et
frontend **React / Vite** (prévu aux étapes suivantes).

---

## 1. Structure du dépôt

```
Hotel_IA/
├── backend/                  # Backend Django 6.1
│   ├── manage.py
│   ├── config/               # Projet Django (settings, urls, celery)
│   ├── apps/                 # Applications métier (dossier apps.*)
│   │   ├── core/             # TimeStampedModel (base commune)
│   │   ├── accounts/         # Utilisateur personnalisé (email + rôles)
│   │   ├── hotels/           # Hôtels, chambres, équipements, images, favoris
│   │   ├── bookings/         # Réservations + anti double-réservation
│   │   ├── payments/         # Paiements Stripe
│   │   ├── reviews/          # Avis + note moyenne des hôtels
│   │   └── notifications/    # Notifications internes
│   ├── requirements.txt
│   ├── .env / .env.example   # Configuration par environnement
│   └── db.sqlite3            # Dev uniquement (PostgreSQL en prod)
├── docs/
│   └── ARCHITECTURE.md       # Ce document
└── .gitignore
```

## 2. Modèle de données

### Utilisateurs (`accounts`)
- **User** (`AbstractBaseUser` + `PermissionsMixin`) : authentification par
  **email** (`USERNAME_FIELD="email"`), rôles **client / hotel_manager / admin**,
  téléphone, avatar, `full_name`. Gestionnaire (`UserManager`) et admin Django
  personnalisés (remplacent le couple username/password).

### Hôtels (`hotels`)
- **Amenity** : équipement (Wi-Fi, piscine…) partagé entre hôtels et chambres.
- **Hotel** : nom, description, adresse, ville/pays indexés, latitude/longitude,
  étoiles (1-5), équipements (M2M), gestionnaire (`hotel_manager`),
  **`average_rating` / `reviews_count`** dénormalisés (mis à jour par signal à
  chaque ajout/suppression d'avis). Propriétés : `room_count`, `starting_price`.
- **HotelImage / RoomImage** : galeries, une image principale par objet.
- **Room** : numéro unique par hôtel (contrainte), type (simple/double/suite/
  familiale), prix/nuit indexé, capacité, lits, équipements, disponibilité.
  Méthode `is_available_for(check_in, check_out)` (délègue à Booking).
- **Favorite** : favori unique par (utilisateur, hôtel).

### Réservations (`bookings`)
- **Booking** : code unique auto-généré (10 caractères), client/hôtel/chambre
  en `PROTECT`, dates `check_in`/`check_out`, adultes/enfants, **snapshot du prix
  par nuit**, `nights`, taxes + frais de service + total recalculés à la volée
  (`calculate_totals`), cycle de vie **pending → confirmed → completed**
  (ou **cancelled**).
  - **Anti double-réservation** à deux niveaux :
    1. *Application* : `Booking.clean()` + `overlapping(room, in, out)` sur les
       statuts actifs (`pending`, `confirmed`), intervalle demi-ouvert `[in, out)`.
    2. *Base de données* : contrainte d'**exclusion GiST PostgreSQL**
       (`bookings/0002_…`) sur `room_id` + `daterange(check_in, check_out, '[)')`,
       condition `status IN ('pending','confirmed')`. No-op sur SQLite.
  - Annulation libre-service autorisée jusqu'à `BOOKING_CANCELLATION_DEADLINE_DAYS`
    jours avant l'arrivée.
  - Les chambres/périodes qui se touchent (**départ = arrivée**) restent réservables.

### Paiements (`payments`)
- **Payment** (`OneToOne` → Booking) : montant/ devise, statuts
  (pending / paid / failed / refunded / partially_refunded), identifiants sessions
  et PaymentIntent Stripe, moyen de paiement. `mark_paid()` confirme la réservation.
  Aucune donnée bancaire stockée (Stripe Checkout).

### Avis (`reviews`)
- **Review** : note 1-5 + commentaire, **une seule par (client, hôtel)**,
  réservation associée optionnelle et validée (terminée + même client).
  Le signal `reviews/signals.py` maintient `Hotel.average_rating` et
  `Hotel.reviews_count` (recalcul à chaque création/suppression).

### Notifications (`notifications`)
- **Notification** : type (info / réservation / paiement / annulation / rappel),
  titre/message/lien, lue/non-lue. QuerySet dédié (`unread()`, `mark_all_read`).

## 3. Choix techniques

| Sujet | Choix | Justification |
|---|---|---|
| Base de données | PostgreSQL (prod), SQLite (dev) | Exclusion GiST anti double-réservation |
| Authentification | JWT (SimpleJWT, access 60 min / refresh 7 j, rotation + blacklist) | API sans état, compatible React |
| Tarification | Snapshot du prix à la réservation | Le prix affiché reste celui du moment de la réservation |
| Règles métier | Variables d'environnement (`BOOKING_*`) | Ajustable sans redéploiement |
| Emails | `MAILERS` Django 6 (console dev / SMTP prod) | `EMAIL_BACKEND` déprécié |
| Célérity | Tâches asynchrones via Celery + Redis | Emails de confirmation, rappels |
| Paiement | Stripe Checkout (côté serveur) | Sécurité PCI, webhooks |
| API | DRF + drf-spectacular (Swagger/OpenAPI) | Documentation auto |
| Sécurité | Splits prod (HTTPS, HSTS, cookies Secure) activés si `DEBUG=False` | Bonnes pratiques |

## 4. Plan d'API (état implémenté)

Préfixe : `/api/v1/`

- `POST /api/v1/auth/register/` · `POST /auth/login/` (JWT) · `POST /auth/refresh/` ·
  `POST /auth/verify/` · `POST /auth/logout/` (blacklist) · `GET/PATCH /auth/me/`
- `GET /hotels/` (filtres ville, pays, étoiles, dates, voyageurs ; tri `sort=price`) ·
  `GET/PUT/PATCH/DELETE /hotels/{id}/` · `GET /hotels/mine/` (gestionnaire)
- `GET /rooms/?hotel=&check_in=&check_out=` · `POST /rooms/` ; `GET /amenities/`
- `POST/GET/DELETE /favorites/`
- `POST /bookings/` (vérifie la disponibilité) · `GET /bookings/` · 
  `POST /bookings/{id}/cancel|confirm|complete/`
- `POST /auth/change-password/` (étape 4) · `DELETE /auth/me/` (étape 4)
- `POST /payments/` (montant = total de la réservation) · `GET /payments/` ·
  `POST /payments/{id}/checkout/` (session Checkout → `checkout_url`) ·
  `POST /payments/{id}/refund/` (manager/staff) ·
  `POST /payments/webhook/` (Stripe, signature vérifiée)
- `GET/POST /reviews/?hotel=` · `PATCH/DELETE /reviews/{id}/` (auteur)
- `GET /notifications/` · `POST /notifications/mark_all_read/` · `POST /notifications/{id}/read/`
- Documentation (OpenAPI 3) : `GET /api/schema/` (YAML, `?format=json` for JSON) ·
  `GET /api/docs/` (Swagger UI) · `GET /api/redoc/` (ReDoc)

## 5. Variables d'environnement

Voir `backend/.env.example`. Blocs : Django (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`),
BD (`DATABASE_URL`), CORS, emails, Redis/Celery (`REDIS_URL`,
`CELERY_TASK_ALWAYS_EAGER`, `SITE_NAME`, `PAYMENT_PENDING_TIMEOUT_SECONDS`),
Stripe, règles réservation (`BOOKING_*`), frontend (`FRONTEND_URL`).

## 6. Feuille de route

1. ✅ **Étape 1 — Architecture + modèles** : projet, apps, modèles, contraintes,
   migration d'exclusion, administrables, vérification.
2. ✅ **Étape 2 — Serializers** : serializers DRF pour `accounts`, `hotels`,
   `bookings`, `payments`, `reviews`, `notifications` — validation métier
   exposée par l'API (disponibilité des chambres, séjours terminés pour les
   avis, montant des paiements déduit de la réservation). Vérifié par smoke
   test (création + chevauchement refusé + double avis refusé).
3. ✅ **Étape 3 — Views/URLs** : ViewSets + routeurs montés sous `/api/v1/`
   (accounts : register/login/refresh/verify/logout/me ; hotels/rooms/amenities/
   favorites ; bookings + actions cancel/confirm/complete ; payments ; reviews ;
   notifications + mark_all_read). Permissions métier (`apps/core/permissions.py` :
   rôles client/gestionnaire, propriété objet), visibilité des réservations par
   rôle, recherche publique avec disponibilité et tri prix, throttling activé,
   blacklist JWT au logout. Vérifié par smoke test de bout en bout (JWT → hôtel →
   chambre → réservation → cycle de vie → avis → paiement → notifications).
4. ✅ **Étape 4 — Authentification JWT avancée** : changement de mot de passe
   (`POST /auth/change-password/`, validations Django + vérification de l'ancien,
   révocation du refresh), suppression de compte (`DELETE /auth/me/` : refus si
   réservation en cours, désactivation + révocation de tous les refresh tokens),
   rotation des refresh tokens vérifiée (l'ancien est blacklisté). Le socle JWT
   (register/login/refresh/verify/logout/me + permissions par rôle) a été livré
   avec l'étape 3. Vérifié par smoke test (mdp refusé/accepté, rotation,
   suppression → 401).
5. ✅ **Étape 5 — Paiement Stripe** : `POST /payments/{pk}/checkout/` crée la
   session Checkout (montant = total de la réservation, devise `STRIPE_CURRENCY`,
   réutilisation idempotente de la session active) ; webhook `POST
   /payments/webhook/` vérifié par signature HMAC (`STRIPE_WEBHOOK_SECRET`) et
   idempotent (completed/async_payment_succeeded → paiement payé + réservation
   confirmée + notifications client/manager ; expired/async_payment_failed →
   paiement échoué, retry possible ; réservation annulée entre-temps →
   remboursement automatique) ; `POST /payments/{pk}/refund/` (manager/staff
   uniquement, uniquement sur paiement payé) ; **l'annulation d'une réservation
   payée rembourse automatiquement** (refusée si le remboursement échoue).
   Vérifié avec les vraies clés Stripe de test : session réelle, rejeu webhook
   ignoré, signature invalide rejetée, remboursements (403/400/erreur Stripe
   proprement remontée).
6. ✅ **Étape 6 — Tâches asynchrones (Celery + Redis)** : `config/celery.py`
   (app `hotelbooking`, config via namespace `CELERY`) ; tâches dans
   `apps/bookings/tasks.py` (email de confirmation `send_booking_confirmation`,
   rappel J-x `send_upcoming_reminder` avec drapeau anti-doublon
   `reminder_sent_at`, scan périodique `scan_upcoming_reminders`) et
   `apps/payments/tasks.py` (`expire_stale_payments` : paiements en attente
   au-delà de `PAYMENT_PENDING_TIMEOUT_SECONDS` → statut échoué + notification).
   Emails envoyés avec `send_mail()` (Django 6, backend MAILERS), multi-langues
   non requis (contenu factuel). **Branchements** : confirmation (action API ou
   webhook Stripe) → notification BOOKING/PAYMENT + email de confirmation async ;
   annulation → notification CANCELLATION ; rappels planifiés par beat toutes les
   30 min (séjours sous 2 jours), expiration des paiements chaque nuit à 03h00.
   `CELERY_TASK_ALWAYS_EAGER=true` pour exécuter sans worker en dev/tests
   (par défaut false en prod ; worker `celery -A config worker` + beat
   `celery -A config beat`). Vérifié par smoke test : broker Redis joignable,
   email + notification de confirmation, tâche idempotente (non confirmée →
   aucun envoi), rappel unique (2ᵉ scan sans doublon, drapeau posé), expiration
   d'un paiement périmé (2 h) → échoué + notification (récent intact), annulation
   → notification.
7. ✅ **Étape 7 — Documentation API** : OpenAPI/Swagger via drf-spectacular
   (déjà présent dans `INSTALLED_APPS` + `DEFAULT_SCHEMA_CLASS`). Ajout de
   `SPECTACULAR_SETTINGS` (titre « HotelBooking API », version 1.0.0,
   `SERVE_INCLUDE_SCHEMA=False`), des URLs `/api/schema/` (schéma YAML/JSON),
   `/api/docs/` (Swagger UI) et `/api/redoc/` (ReDoc), et des `@extend_schema`
   sur les actions custom : bookings `cancel`/`confirm`/`complete`, payments
   `checkout`/`refund` + webhook (corps brut `OpenApiTypes.OBJECT`), notifications
   `mark_all_read`/`read`, hotels `mine`, accounts `register`/`delete`/
   `change-password`/`logout`. Vérifié par smoke test : 3 vues doc répondent 200,
   13/13 chemins article documentés dans le schéma, `check` 0 issue.
8. **Étape 8 — Frontend React/Vite** : connexion à l'API, UI booking.

## 7. Commandes utiles

```powershell
# Depuis le dossier backend/, avec le venv actif
python manage.py runserver            # API sur :8000
python manage.py makemigrations       # après modification des modèles
python manage.py migrate
python manage.py createsuperuser
python manage.py check                # vérification système
python manage.py spectacular --file schema.yml --validate   # génération/vérif schéma OpenAPI
celery -A config worker -l info      # worker (prod : toujours actif)
celery -A config beat -l info        # planificateur périodique
```