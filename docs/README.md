# Documentazione MyPlanner Backend

Benvenuto nella documentazione del backend MyPlanner!

## 📚 Indice

### Architettura
- [Panoramica Architettura](architecture/overview.md) - Visione generale del sistema
- [Layer Pattern](architecture/layers.md) - Spiegazione dei vari layer
- [Implementazione RLS](architecture/rls_implementation.md) - Come funziona Row-Level Security

### API
- [Autenticazione](api/authentication.md) - Endpoint di registrazione e login
- [Task Management](api/tasks.md) - Endpoint CRUD per le task

### Sviluppo
- [Setup Ambiente](development/setup.md) - Come configurare l'ambiente di sviluppo
- [Testing](development/testing.md) - Come eseguire i test
- [Contributing](development/contributing.md) - Linee guida per contribuire

### Deployment
- [Docker](deployment/docker.md) - Guida deployment con Docker
- [Render](deployment/render.md) - Guida deployment su Render

### Architecture Decision Records (ADR)
- [001 - Architettura a Layer](adr/001-layered-architecture.md)
- [002 - Implementazione RLS](adr/002-rls-implementation.md)
- [003 - Organizzazione Domini](adr/003-domain-organization.md)

## 🚀 Quick Start

1. **Setup**:
   ```bash
   cd MyPlanner_BackEnd
   pip install -r requirements.txt
   ```

2. **Configurazione**:
   - Copia `.env.example` in `.env`
   - Configura `DATABASE_URL` e `SECRET_KEY`

3. **Avvio**:
   ```bash
   uvicorn main:app --reload
   ```

4. **Documentazione API**:
   - Apri http://localhost:8000/docs

## 📝 Manutenzione Documentazione

**IMPORTANTE**: Questa documentazione deve essere aggiornata ad ogni modifica significativa del codice!

### Quando Aggiornare
- ✅ Aggiunta di nuovi endpoint
- ✅ Modifiche alle API esistenti
- ✅ Cambiamenti architetturali
- ✅ Nuove dipendenze o configurazioni
- ✅ Modifiche alle procedure di deployment

### Come Aggiornare
1. Modifica i file markdown corrispondenti in `docs/`
2. Aggiungi la data di aggiornamento in alto al documento
3. Committa insieme al codice: `git add docs/ && git commit -m "docs: update API documentation"`

## 🔗 Link Utili

- **Codebase**: `/app` - Codice sorgente organizzato per layer
- **Tests**: `/tests` - Suite di test
- **API Docs**: http://localhost:8000/docs (quando il server è attivo)

## 📧 Contatti

Per domande o suggerimenti sulla documentazione, apri una issue nel repository.

---

**Ultimo aggiornamento**: 2025-11-06

