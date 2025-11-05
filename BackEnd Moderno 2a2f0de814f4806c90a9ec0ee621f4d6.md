# BackEnd Moderno

Total votes: 0
Created by: Franco De Giorgio
Category: Code

## 🧱 STRUTTURA DI UN BACKEND MODERNO

Un backend moderno è tipicamente organizzato secondo **architetture a layer (multilayered)** o **architetture esagonali (hexagonal architecture)**.

L’obiettivo è **separare le responsabilità**, migliorare **la manutenibilità** e permettere una **scalabilità orizzontale** (più istanze, microservizi, ecc.).

---

### 1. **API Layer (Presentation Layer)**

📍 **Ruolo:**

Gestisce la **comunicazione con il mondo esterno**, ossia le richieste HTTP/REST (o GraphQL/gRPC).

Riceve la richiesta, la valida, la passa ai servizi e restituisce una risposta standardizzata (JSON, XML, ecc.).

📦 **Contenuti tipici:**

- Controller o router (`userController`, `productRouter` ecc.)
- Middleware (autenticazione, logging, rate-limiting, ecc.)
- Serializzazione e deserializzazione dei dati
- Gestione degli errori (exception handling)

💡 **Best practice:**

- Mantenere le API **stateless**
- Usare **HTTP status code coerenti**
- Validare i dati in ingresso (es. tramite `pydantic`, `Joi`, `class-validator`)
- Restituire errori strutturati (`{ "error": "InvalidEmail", "message": "Email not valid" }`)
- Separare **DTO (Data Transfer Object)** dal modello interno

---

### 2. **Service Layer (Business Logic Layer)**

📍 **Ruolo:**

Contiene la **logica di business**, ossia le regole che definiscono come i dati vengono manipolati e le operazioni vengono eseguite.

Non conosce *come* i dati vengono salvati (delegato al repository).

📦 **Contenuti tipici:**

- Funzioni che implementano operazioni complesse (es. “crea ordine e invia email”)
- Coordinamento tra repository, validazioni, e chiamate esterne
- Gestione delle transazioni e delle policy aziendali

💡 **Best practice:**

- Ogni service deve avere **un solo scopo ben definito**
- Nessuna logica di accesso ai dati qui
- Test unitari su ogni metodo di servizio
- Esporre metodi coerenti (es. `create_user()`, `calculate_invoice()`, `process_payment()`)

---

### 3. **Repository Layer (Data Access Layer)**

📍 **Ruolo:**

Responsabile del **dialogo con il database** o altri data store.

Nasconde la complessità dell’ORM o delle query SQL/NoSQL.

📦 **Contenuti tipici:**

- Query al DB (SQLAlchemy, Prisma, Sequelize, Mongoose…)
- Funzioni CRUD (`get_user_by_id()`, `save_order()`, `delete_post()`)
- Connessione e pooling del database

💡 **Best practice:**

- Il service non deve mai eseguire query dirette
- Repository “puliti”, che restituiscono entità o DTO
- Gestire errori di connessione e time-out
- Supportare transazioni e rollback

---

### 4. **Model Layer (Domain Model / Entities)**

📍 **Ruolo:**

Rappresenta le **entità centrali del dominio** (User, Order, Product…).

Qui si definisce la struttura e il comportamento interno degli oggetti.

📦 **Contenuti tipici:**

- Classi con attributi (`User`, `Invoice`, `Order`)
- Eventuale logica di dominio (metodi di validazione, calcoli)
- Mapping con il DB (ORM) o strutture pure (se separato dal database)

💡 **Best practice:**

- Definire **entità ricche**, non solo “contenitori di dati”
- Tenere separato il modello di dominio da quello di persistenza (quando possibile)
- Usare **tipi forti** e validazioni interne (es. `pydantic.BaseModel` o dataclass)

---

### 5. **Schema Layer (Validation / DTO Layer)**

📍 **Ruolo:**

Si occupa della **validazione e trasformazione dei dati** in ingresso e uscita dalle API.

Serve per garantire che il backend riceva e restituisca solo dati coerenti con le specifiche.

📦 **Contenuti tipici:**

- Input schema (`UserCreateSchema`, `LoginSchema`)
- Output schema (`UserResponseSchema`)
- Validatori e normalizzatori (es. `email: EmailStr`)

💡 **Best practice:**

- Non usare direttamente i model del database nelle API
- Mantenere i DTO/schema **immutabili**
- Versionare gli schema se l’API evolve (`v1`, `v2`, ecc.)

---

### 6. **Config Layer (Configuration & Environment)**

📍 **Ruolo:**

Gestione della **configurazione dell’app**, come variabili d’ambiente, connessioni, segreti, chiavi API.

📦 **Contenuti tipici:**

- File `.env` o `config.yaml`
- Moduli Python/Node per leggere le variabili d’ambiente
- Impostazioni diverse per dev/staging/prod

💡 **Best practice:**

- Mai includere credenziali nel codice
- Caricare tutto da variabili d’ambiente (es. con `dotenv`)
- Definire una classe `Settings` per centralizzare la configurazione

---

### 7. **Utility / Helpers Layer**

📍 **Ruolo:**

Funzioni trasversali non appartenenti a un dominio specifico, come logging, formattazione, caching, o invio email.

📦 **Contenuti tipici:**

- Logger, formatter, serializer
- Funzioni per hashing password
- Wrapper per API esterne
- Gestione cache (Redis)

💡 **Best practice:**

- Moduli indipendenti e riutilizzabili
- Evitare dipendenze circolari
- Tenere i side effects sotto controllo (es. retry policy)

---

### 8. **Tests**

📍 **Ruolo:**

Validare il corretto funzionamento di ogni componente.

📦 **Contenuti tipici:**

- Unit test (per service, repository)
- Integration test (API + DB)
- Mock di dipendenze esterne

💡 **Best practice:**

- Usare **test coverage**
- Automatizzare con pipeline CI/CD
- Evitare test che dipendono dallo stato locale

---

## 🔁 STRUTTURA TIPICA DEL PROGETTO

Esempio (Python FastAPI o Node.js):

```
/app
 ├── api/
 │    ├── routes/
 │    ├── controllers/
 │    └── middleware/
 ├── services/
 │    ├── user_service.py
 │    └── order_service.py
 ├── repositories/
 │    ├── user_repository.py
 │    └── order_repository.py
 ├── models/
 │    ├── user.py
 │    └── order.py
 ├── schemas/
 │    ├── user_schema.py
 │    └── order_schema.py
 ├── core/
 │    ├── config.py
 │    ├── database.py
 │    └── security.py
 ├── utils/
 │    ├── logger.py
 │    └── email.py
 └── tests/
      ├── test_api.py
      ├── test_services.py
      └── test_repository.py

```

---

## ⚙️ ALTRE COMPONENTI MODERNE (per backend evoluti)

| Componente | Descrizione | Esempi |
| --- | --- | --- |
| **Cache Layer** | Migliora le performance riducendo query ripetute | Redis, Memcached |
| **Message Queue** | Gestisce processi asincroni (email, notifiche, job) | RabbitMQ, Kafka |
| **Auth Layer** | Gestione token JWT, OAuth2, ruoli | Keycloak, Auth0 |
| **Observability** | Log, metrics, tracing distribuito | Prometheus, Grafana, OpenTelemetry |
| **CI/CD Pipeline** | Deploy automatico e test continuo | GitHub Actions, GitLab CI |
| **Containerization** | Esecuzione in ambienti isolati | Docker, Kubernetes |

---

## 🧭 RIASSUNTO VISIVO

```
[API Layer] → [Schema/DTO] → [Service Layer] → [Repository Layer] → [Database]
        ↓                           ↓
   [Auth, Cache, MQ]          [Model/Entities]

```