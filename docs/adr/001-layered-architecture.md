# ADR 001: Adozione Architettura a Layer

**Data**: 2025-11-06  
**Status**: ✅ Accettata  
**Autore**: Team MyPlanner

## Contesto

Il progetto MyPlanner inizialmente utilizzava un'architettura organizzata per domini (`domains/auth/`, `domains/tasks/`), dove ogni dominio conteneva tutti i layer (router, service, repository, models, schemas) in una struttura piatta.

Con la crescita del progetto, sono emersi alcuni problemi:

1. **Difficoltà di navigazione**: Trovare un tipo specifico di componente (es. tutti i repository) richiedeva di navigare in directory multiple
2. **Duplicazione logica**: Codice comune tra domini era difficile da condividere
3. **Testing complesso**: Testare layer specifici richiedeva mock di interi domini
4. **Scalabilità limitata**: Aggiungere nuovi domini richiedeva duplicazione di boilerplate
5. **Manutenzione difficile**: Modifiche trasversali (es. logging) richiedevano aggiornamenti in molti file

## Decisione

Abbiamo deciso di ristrutturare il progetto usando un'**architettura a layer** (layered architecture), organizzando il codice per responsabilità tecnica piuttosto che per dominio funzionale.

### Nuova Struttura

```
app/
├── api/              # Presentation Layer
├── services/         # Business Logic Layer
├── repositories/     # Data Access Layer
├── models/           # Domain Models
├── schemas/          # DTO Layer
├── core/             # Infrastructure
└── utils/            # Shared Utilities
```

### Motivazioni Principali

1. **Separation of Concerns Chiara**
   - Ogni layer ha responsabilità ben definite
   - Facile identificare dove va una nuova funzionalità

2. **Riusabilità**
   - Utilities condivise in `utils/`
   - Repository base per CRUD comuni
   - Middleware riusabili

3. **Testabilità**
   - Test unitari per layer isolati
   - Mock semplificati
   - Coverage migliorata

4. **Manutenibilità**
   - Modifiche localizzate
   - Refactoring più sicuro
   - Code review focalizzate

5. **Scalabilità**
   - Facile aggiungere nuovi service/repository
   - Pattern chiari da seguire
   - Onboarding più rapido

## Alternative Considerate

### 1. Mantenere Struttura a Domini
**Pro**:
- Nessuna migrazione necessaria
- Cohesion alta per dominio
- Bounded contexts chiari

**Contro**:
- ❌ Difficoltà trovare componenti per tipo
- ❌ Duplicazione codice tra domini
- ❌ Testing più complesso
- ❌ **Motivazione rifiuto**: Non scala bene con crescita progetto

### 2. Hexagonal Architecture (Ports & Adapters)
**Pro**:
- Isolamento dominio ancora maggiore
- Facile sostituire adapter
- Testing molto pulito

**Contro**:
- ❌ Overhead per progetto di questa dimensione
- ❌ Curva apprendimento più ripida
- ❌ **Motivazione rifiuto**: Over-engineering per le esigenze attuali

### 3. Clean Architecture (Onion)
**Pro**:
- Dipendenze sempre verso interno
- Dominio completamente isolato
- Testabilità massima

**Contro**:
- ❌ Troppi layer per progetto piccolo
- ❌ Complessità eccessiva
- ❌ **Motivazione rifiuto**: Troppo complesso per il team size e scope

## Conseguenze

### Positive ✅

1. **Developer Experience Migliorata**
   - Navigazione codice più intuitiva
   - Import path chiari: `from app.services.auth_service import AuthService`
   - Pattern consistenti

2. **Codice Più Pulito**
   - Separazione responsabilità netta
   - Meno duplicazione
   - Più riusabilità

3. **Testing Semplificato**
   - Mock layer-specific
   - Test isolati
   - Coverage incrementale

4. **Manutenibilità Aumentata**
   - Modifiche localizzate
   - Impatto cambiamenti chiaro
   - Refactoring più sicuro

5. **Scalabilità Migliorata**
   - Facile aggiungere feature
   - Pattern replicabili
   - Microservices-ready

### Negative ⚠️

1. **Migrazione Iniziale**
   - Sforzo one-time significativo
   - Rischio breaking changes
   - Testing completo necessario
   - **Mitigazione**: Migrazione graduale con test estensivi

2. **Perdita Cohesion Dominio**
   - Componenti di un dominio sparsi in layer diversi
   - **Mitigazione**: Naming convention chiare (es. `AuthService`, `auth.py`)

3. **Possibili Over-Layering**
   - Rischio di creare troppi layer
   - **Mitigazione**: Linee guida chiare su quando creare nuovo layer

## Implementazione

### Fase 1: Setup Struttura ✅
- Creazione cartelle `app/` con sottodirectory
- Creazione file `__init__.py`

### Fase 2: Migrazione Core ✅
- Spostamento `config.py`, `security.py`, `database.py` → `app/core/`
- Creazione `app/core/exceptions.py`

### Fase 3: Migrazione Utils ✅
- Spostamento decorator RLS → `app/utils/decorators.py`
- Creazione `app/utils/logger.py`, `validators.py`

### Fase 4: Migrazione Models & Schemas ✅
- Spostamento domain models → `app/models/`
- Spostamento Pydantic schemas → `app/schemas/`

### Fase 5: Migrazione Repositories ✅
- Creazione `app/repositories/base_repository.py`
- Spostamento repository specifici con import aggiornati

### Fase 6: Migrazione Services ✅
- Spostamento service con import aggiornati

### Fase 7: Migrazione API ✅
- Spostamento router → `app/api/routes/`
- Creazione middleware → `app/api/middleware/`
- Aggiornamento dependencies

### Fase 8: Aggiornamento Main ✅
- Update import
- Configurazione middleware centralizzata

### Fase 9: Documentazione ✅
- Creazione `docs/` completa
- ADR, guide, API docs

### Fase 10: Testing & Cleanup
- Test suite completa
- Rimozione file obsoleti

## Metriche di Successo

### Obiettivi Raggiunti
- ✅ Tutti i file migrati senza breaking changes
- ✅ Import path consistenti (`app.*`)
- ✅ Documentazione completa (100% docstring)
- ✅ Separazione layer rispettata
- ✅ Zero dipendenze circolari

### Da Monitorare
- ⏳ Test coverage (target: >80%)
- ⏳ Build time
- ⏳ Feedback team su DX
- ⏳ Tempo onboarding nuovi developer

## Riferimenti

- [Layered Architecture Pattern](https://martinfowler.com/bliki/PresentationDomainDataLayering.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Docs interne: [Layer Pattern](../architecture/layers.md)

## Revisioni

- **2025-11-06**: Decisione iniziale e implementazione
- **TBD**: Revisione dopo 3 mesi di uso

---

**Next ADR**: [002 - Implementazione RLS](002-rls-implementation.md)

