# API Autenticazione

**Ultimo aggiornamento**: 2025-11-06

Documentazione completa degli endpoint per registrazione e login utenti.

## 🔐 Panoramica

L'autenticazione usa **JWT (JSON Web Tokens)** con il flusso OAuth2 Password Bearer.

### Flusso Base
1. **Registrazione**: `POST /auth/register` → crea nuovo utente
2. **Login**: `POST /auth/login` → ottieni JWT token
3. **Uso Token**: Includi token in header `Authorization: Bearer <token>`

## 📋 Endpoint

### POST /auth/register

Registra un nuovo utente nel sistema.

**Request**:
```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{
  "name_user": "mario_rossi",
  "password": "SecurePassword123!"
}
```

**Response Success (201)**:
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Error (400)**:
```json
{
  "detail": "Username already exists. Please choose a different username."
}
```

**Validazioni**:
- `name_user`: 3-50 caratteri, univoco
- `password`: 6-100 caratteri

**Esempio cURL**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name_user": "mario_rossi",
    "password": "SecurePassword123!"
  }'
```

---

### POST /auth/login

Esegue login e restituisce JWT token.

**Request**:
```http
POST /auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=mario_rossi&password=SecurePassword123!
```

**Response Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXJpb19yb3NzaSIsImV4cCI6MTYzOTU4NzYwMH0.signature",
  "token_type": "bearer"
}
```

**Response Error (401)**:
```json
{
  "detail": "Incorrect username or password"
}
```

**Note**:
- Usa `application/x-www-form-urlencoded` (standard OAuth2)
- Errore generico per username/password errati (security best practice)

**Esempio cURL**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=mario_rossi&password=SecurePassword123!"
```

**Esempio Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    data={
        "username": "mario_rossi",
        "password": "SecurePassword123!"
    }
)

token = response.json()["access_token"]
```

---

## 🔑 Uso del Token JWT

### Struttura Token

Il JWT contiene:
- **Header**: `{"alg": "HS256", "typ": "JWT"}`
- **Payload**: `{"sub": "mario_rossi", "exp": 1639587600}`
  - `sub`: Username (usato per RLS)
  - `exp`: Timestamp di scadenza
- **Signature**: HMAC-SHA256(header + payload + SECRET_KEY)

### Inclusione nelle Richieste

Tutti gli endpoint protetti richiedono il token nell'header `Authorization`:

```http
GET /tasks HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Esempio cURL**:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"
```

**Esempio JavaScript (Frontend)**:
```javascript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/tasks', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(response => response.json())
.then(tasks => console.log(tasks));
```

### Scadenza Token

- **Durata**: 30 minuti (configurabile in `app/core/config.py`)
- **Rinnovo**: Client deve rifare login quando token scade
- **Errore**: `401 Unauthorized` se token scaduto/invalido

---

## 🔒 Sicurezza

### Password Hashing
- **Algoritmo**: bcrypt
- **Salt**: Generato automaticamente per ogni password
- **Rounds**: Default bcrypt (configurabile)
- **Storage**: Solo hash salvato, mai password in chiaro

### JWT Signing
- **Algoritmo**: HS256 (HMAC-SHA256)
- **Secret Key**: Configurata tramite env var `SECRET_KEY`
- **Validazione**: Signature verificata ad ogni richiesta

### Best Practices Implementate
✅ Password mai loggata o esposta  
✅ Hash bcrypt con salt automatico  
✅ JWT con scadenza  
✅ Errori generici per login (non rivela se username esiste)  
✅ HTTPS obbligatorio in produzione  
✅ CORS configurato per origini specifiche  

---

## 🧪 Testing

### Test Registrazione
```bash
# Successo
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name_user": "test_user", "password": "Test123!"}'

# Username già esistente
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name_user": "test_user", "password": "Test123!"}'
# → 400 Bad Request
```

### Test Login
```bash
# Successo
curl -X POST http://localhost:8000/auth/login \
  -d "username=test_user&password=Test123!"

# Password errata
curl -X POST http://localhost:8000/auth/login \
  -d "username=test_user&password=WrongPassword"
# → 401 Unauthorized
```

### Test Token Uso
```bash
# Login e salva token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -d "username=test_user&password=Test123!" \
  | jq -r '.access_token')

# Usa token
curl -X GET http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚠️ Errori Comuni

### 422 Validation Error
**Causa**: Dati input non validi (es. password troppo corta)  
**Soluzione**: Verifica validazioni schema

### 400 Bad Request
**Causa**: Username già esistente (registrazione)  
**Soluzione**: Scegli username diverso

### 401 Unauthorized
**Causa**: Credenziali errate o token invalido/scaduto  
**Soluzione**: Verifica username/password o rifare login

### 415 Unsupported Media Type
**Causa**: Content-Type errato per login  
**Soluzione**: Usa `application/x-www-form-urlencoded` per login

---

## 📊 Rate Limiting

**Stato**: Non implementato (futuro)

**Pianificato**:
- Max 10 tentativi login/minuto per IP
- Max 5 registrazioni/ora per IP
- Backoff esponenziale dopo fallimenti

---

## 🔗 Link Correlati

- [Task Management API](tasks.md)
- [Implementazione RLS](../architecture/rls_implementation.md)
- [Security Best Practices](../development/security.md)

---

**OpenAPI/Swagger**: http://localhost:8000/docs#/Authentication

