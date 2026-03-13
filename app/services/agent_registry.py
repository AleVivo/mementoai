"""
Unica fonte di verità per i tool dell'agente.

Ogni tool è definito in un unico posto come ToolDefinition — un oggetto
che tiene insieme la definizione JSON (per Qwen) e il callable Python
(per il dispatcher).

Per aggiungere un tool:
1. Scrivi la funzione in agent_tools.py
2. Aggiungi un ToolDefinition in REGISTERED_TOOLS qui sotto
Nient'altro.

TOOLS e TOOL_FUNCTIONS vengono derivati automaticamente da REGISTERED_TOOLS
— non vanno mai modificati a mano.
"""

from dataclasses import dataclass
from typing import Callable, Any
from app.services.agent_tools import (
    search_semantic,
    filter_entries,
    get_entry,
    count_entries,
)


# ---------------------------------------------------------------------------
# Struttura dati di un tool
#
# Concetto generale Python — dataclass:
# @dataclass è un decoratore che genera automaticamente __init__, __repr__
# e altri metodi boilerplate per una classe che è essenzialmente un
# contenitore di dati. È l'equivalente di un'interface TypeScript con
# costruttore automatico.
#
# frozen=True significa che l'istanza è immutabile dopo la creazione —
# un tool registrato non deve poter essere modificato a runtime.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolDefinition:
    """
    Contenitore per tutto ciò che definisce un tool.

    schema:   il dict JSON che descrive il tool a Qwen (formato OpenAI/Ollama)
    fn:       la funzione Python async da chiamare quando Qwen invoca il tool
    """
    schema: dict        # definizione JSON per Ollama
    fn: Callable[..., Any]  # funzione Python corrispondente


# ---------------------------------------------------------------------------
# Registry — unica lista da modificare quando si aggiunge un tool
# ---------------------------------------------------------------------------

REGISTERED_TOOLS: list[ToolDefinition] = [

    ToolDefinition(
        fn=search_semantic,
        schema={
            "type": "function",
            "function": {
                "name": "search_semantic",
                "description": (
                    "Cerca nella knowledge base per significato semantico. "
                    "Restituisce CHUNK di testo — frammenti di entry, non entry complete. "
                    "Usa questo tool per domande aperte su decisioni tecniche, "
                    "problemi passati, o qualsiasi contenuto dove non conosci "
                    "le parole esatte usate. "
                    "Se la risposta richiede il contenuto completo di una entry, "
                    "usa l'entry_id restituito per chiamare get_entry. "
                    "Non usarlo per conteggi o filtri esatti."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "La domanda o il concetto da cercare",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Numero massimo di risultati (default 5)",
                        },
                        "project": {
                            "type": "string",
                            "description": (
                                "Filtra la ricerca per progetto. "
                                "Se nel contesto attivo è indicato un progetto, "
                                "usalo qui. Ometti solo se la domanda riguarda "
                                "esplicitamente tutti i progetti."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    ),

    ToolDefinition(
        fn=filter_entries,
        schema={
            "type": "function",
            "function": {
                "name": "filter_entries",
                "description": (
                    "Filtra entry per campi esatti: progetto, tipo, settimana. "
                    "Restituisce entry COMPLETE con tutto il contenuto già incluso — "
                    "NON serve chiamare get_entry dopo questo tool. "
                    "Usa questo tool quando la domanda specifica criteri precisi come "
                    "'tutti gli ADR', 'entry di questa settimana', 'l'ultimo aggiornamento'. "
                    "I risultati sono ordinati dalla più recente alla più vecchia: "
                    "usa limit=1 per ottenere l'ultima entry di un tipo. "
                    "Il formato della settimana è YYYY-Www (es. 2026-W10)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": (
                                "Nome del progetto. "
                                "Se nel contesto attivo è indicato un progetto, "
                                "usalo qui. Ometti solo se la domanda riguarda "
                                "esplicitamente tutti i progetti."
                            ),
                        },
                        "entry_type": {
                            "type": "string",
                            "enum": ["adr", "postmortem", "update"],
                            "description": "Tipo di entry",
                        },
                        "week": {
                            "type": "string",
                            "description": "Settimana in formato YYYY-Www",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Numero massimo di risultati (default 20)",
                        },
                    },
                    "required": [],
                },
            },
        },
    ),

    ToolDefinition(
        fn=get_entry,
        schema={
            "type": "function",
            "function": {
                "name": "get_entry",
                "description": (
                    "Recupera una singola entry completa tramite il suo ID MongoDB. "
                    "Usa questo tool SOLO dopo search_semantic, quando il chunk "
                    "restituito non contiene abbastanza contesto e vuoi leggere "
                    "il contenuto completo dell'entry originale. "
                    "NON usarlo dopo filter_entries — quelle entry sono già complete. "
                    "IMPORTANTE: usa SOLO ID reali ottenuti dal campo entry_id "
                    "di search_semantic — non inventare mai un ID."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "L'ID MongoDB dell'entry",
                        },
                    },
                    "required": ["id"],
                },
            },
        },
    ),

    ToolDefinition(
        fn=count_entries,
        schema={
            "type": "function",
            "function": {
                "name": "count_entries",
                "description": (
                    "Conta le entry che corrispondono ai filtri e restituisce "
                    "un breakdown per tipo e per progetto. "
                    "Usa questo tool per domande quantitative: 'quanti post-mortem', "
                    "'qual è il progetto più attivo', 'quanto spesso scriviamo ADR'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Filtra per progetto",
                        },
                        "entry_type": {
                            "type": "string",
                            "enum": ["adr", "postmortem", "update"],
                            "description": "Filtra per tipo",
                        },
                        "week": {
                            "type": "string",
                            "description": "Filtra per settimana YYYY-Www",
                        },
                    },
                    "required": [],
                },
            },
        },
    ),

]


# ---------------------------------------------------------------------------
# Viste derivate — calcolate una volta al momento dell'import
#
# Concetto generale Python — list/dict comprehension:
# Sono sintassi compatte per costruire liste o dizionari trasformando
# o filtrando una sequenza esistente. Equivalente a .map() e .reduce()
# in JavaScript/TypeScript.
#
# [item.schema for item in REGISTERED_TOOLS]
#   → equivalente a REGISTERED_TOOLS.map(t => t.schema)
#
# {item.schema["function"]["name"]: item.fn for item in REGISTERED_TOOLS}
#   → equivalente a REGISTERED_TOOLS.reduce((acc, t) => ({...acc, [t.schema.function.name]: t.fn}), {})
# ---------------------------------------------------------------------------

# Lista di schema JSON da passare ad Ollama nel parametro "tools"
TOOLS: list[dict] = [tool.schema for tool in REGISTERED_TOOLS]

# Dict nome → funzione per il dispatcher in agent.py
TOOL_FUNCTIONS: dict[str, Callable] = {
    tool.schema["function"]["name"]: tool.fn
    for tool in REGISTERED_TOOLS
}