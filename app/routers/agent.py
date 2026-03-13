from fastapi import APIRouter, HTTPException
from app.models.agent import AgentResponse, AgentStep, AgentRequest
from app.services.agent import run_agent
import httpx

router = APIRouter()

@router.post(
    "",
    response_model=AgentResponse,
    summary="Domanda all'agente con tool use",
    description=(
        "Invia una domanda in linguaggio naturale. L'agente decide autonomamente "
        "quali tool usare (ricerca semantica, filtri, conteggi) per costruire "
        "la risposta. Restituisce la risposta finale e la lista degli step eseguiti."
    ),
)
async def ask_agent(request: AgentRequest) -> AgentResponse:
    """
    Concetto generale — async def in FastAPI:
    FastAPI è un framework ASGI (Asynchronous Server Gateway Interface).
    Quando definisci un endpoint con "async def", FastAPI lo esegue
    in modo non bloccante — può gestire altre richieste mentre aspetta
    che Ollama risponda. È fondamentale per endpoint che fanno I/O lento
    come chiamate a LLM o query database.
    """
    try:
        result = await run_agent(
            question=request.question,
            project=request.project,
            max_steps=request.max_steps,
        )
        return AgentResponse(**result)

    except httpx.TimeoutException:
        # Ollama può essere lento su hardware limitato.
        # 504 Gateway Timeout è il codice HTTP semanticamente corretto.
        raise HTTPException(
            status_code=504,
            detail="Timeout: Ollama non ha risposto in tempo. Riprova o riduci max_steps.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno dell'agente: {str(e)}",
        )