"""
Router FastAPI per distribuire rapidamente collezione e ambiente Postman.

Espone:
- GET /postman              -> Pagina HTML con istruzioni e link download
- GET /postman/collection   -> Download collezione Postman (JSON)
- GET /postman/environment  -> Download ambiente Postman (JSON)
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse


router = APIRouter(
    prefix="/postman",
    tags=["Postman"]
)


POSTMAN_DIR = Path(__file__).resolve().parent.parent.parent.parent / "postman"
COLLECTION_PATH = POSTMAN_DIR / "postman_collection.json"
ENVIRONMENT_PATH = POSTMAN_DIR / "postman_environment.json"


def _ensure_file_exists(path: Path) -> Path:
    """
    Verifica che il file esista su disco; solleva un 500 se mancante.

    Args:
        path: Percorso del file da verificare.

    Returns:
        Path: Il percorso se esiste.

    Raises:
        HTTPException: Se il file non è presente.
    """
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File Postman non trovato: {path.name}"
        )
    return path


@router.get(
    "",
    response_class=HTMLResponse,
    summary="Pagina di onboarding Postman"
)
def get_postman_page() -> str:
    """
    Restituisce una semplice pagina HTML con i link per scaricare
    la collezione e l'ambiente Postman preconfigurati.
    """
    return """
<!DOCTYPE html>
<html lang="it">
  <head>
    <meta charset="utf-8" />
    <title>MyPlanner · Postman bootstrap</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem auto; max-width: 720px; line-height: 1.5; color: #1f2933; }
      h1 { color: #2563eb; }
      code { background: #f1f5f9; padding: 0.2rem 0.3rem; border-radius: 4px; }
      a.button { display: inline-block; margin: 0.5rem 0; padding: 0.6rem 1rem; background: #2563eb; color: #fff; text-decoration: none; border-radius: 6px; }
      a.button:hover { background: #1d4ed8; }
      section { margin-bottom: 2rem; }
      footer { font-size: 0.8rem; color: #64748b; margin-top: 3rem; }
    </style>
  </head>
  <body>
    <h1>Importa MyPlanner in Postman</h1>
    <section>
      <p>1. Scarica la collezione e l'ambiente già configurati:</p>
      <p>
        <a class="button" href="/postman/collection" download>Scarica collezione</a>
        <a class="button" href="/postman/environment" download>Scarica ambiente</a>
      </p>
    </section>
    <section>
      <p>2. Apri Postman e usa <strong>Import &gt; File</strong> per caricare i due file.</p>
      <p>3. Seleziona l'ambiente <code>MyPlanner Local</code> e invia la richiesta <code>Auth - Login</code> per popolare il token.</p>
    </section>
    <section>
      <p>4. Personalizza le variabili (utente demo, data di test, UUID task) direttamente in Postman.</p>
    </section>
    <footer>
      Generato automaticamente da MyPlanner Backend.
    </footer>
  </body>
</html>
    """


@router.get(
    "/collection",
    response_class=FileResponse,
    summary="Download collezione Postman"
)
def download_collection() -> FileResponse:
    """
    Restituisce la collezione Postman in formato JSON.
    """
    path = _ensure_file_exists(COLLECTION_PATH)
    return FileResponse(path, media_type="application/json", filename=path.name)


@router.get(
    "/environment",
    response_class=FileResponse,
    summary="Download ambiente Postman"
)
def download_environment() -> FileResponse:
    """
    Restituisce l'ambiente Postman in formato JSON.
    """
    path = _ensure_file_exists(ENVIRONMENT_PATH)
    return FileResponse(path, media_type="application/json", filename=path.name)

