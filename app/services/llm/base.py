"""
Contratti astratti per i provider LLM.
 
Questo file definisce le *interfacce* — non contiene logica, non fa chiamate HTTP.
Chiunque importi questi ABC non sa e non deve sapere quale provider è dietro.
 
Pattern usato: Strategy (o Port in architettura esagonale).
  - EmbeddingProvider: dato un testo, dammi il vettore
  - ChatProvider:      data una lista di messaggi, streamami i token
  - ToolChatProvider:  come ChatProvider, ma supporta anche i tool (function calling)
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
 
class EmbeddingProvider(ABC):
    """
    Interfaccia per la generazione di embedding vettoriali.
 
    Perché è separata da ChatProvider?
    Perché spesso conviene usare provider diversi per le due operazioni:
    es. Ollama locale (gratuito) per gli embedding e OpenAI per la chat.
    Tenere i contratti separati permette questa combinazione senza problemi.
    """
 
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Converte un testo in un vettore numerico.
 
        Args:
            text: il testo da vettorizzare (chunk, query, ecc.)
 
        Returns:
            lista di float che rappresentano il vettore
            (la dimensione dipende dal modello — es. 768 per nomic-embed-text)
 
        Note:
            ⚠️  Cambiare provider di embedding invalida TUTTI i vettori esistenti
            in MongoDB. L'indice vettoriale è costruito per una dimensione specifica.
            Se si cambia provider occorre re-indicizzare tutto.
        """
        ...
 
  
# ---------------------------------------------------------------------------
# Chat / Completion
# ---------------------------------------------------------------------------

class ChatProvider(ABC):
    """
    Interfaccia per la generazione di testo in modalità chat (streaming).
 
    Usata da rag.py per la risposta RAG e dalla pipeline di chat base.
    Non supporta tool/function calling — per quello vedi ToolChatProvider.
    """
 
    @abstractmethod
    def stream_chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Invia una conversazione al modello e restituisce i token in streaming.
 
        Args:
            messages:      lista di dict {"role": "user"|"assistant", "content": "..."}
                           Formato OpenAI-compatibile — supportato da tutti i provider.
            system_prompt: prompt di sistema (separato per comodità — alcuni provider
                           lo gestiscono diversamente dai messaggi)
 
        Yields:
            token: stringa con un frammento di testo (uno o più caratteri)
 
        Note sul formato messages:
            Il formato {"role": ..., "content": ...} è diventato lo standard de-facto
            (iniziato da OpenAI, adottato da Ollama, Anthropic, Groq, ecc.).
            Questo è il motivo per cui funziona come denominatore comune tra provider.
        """
        ...

class ToolChatProvider(ChatProvider):
    """
    Estende ChatProvider con il supporto per tool/function calling.
 
    Usata da agent.py per il loop ReAct — il modello deve poter scegliere
    autonomamente quando chiamare un tool e con quali argomenti.
 
    Perché è una sottoclasse e non un'interfaccia separata?
    Perché un agente ha bisogno di ENTRAMBE le capacità:
    - stream_chat per la risposta finale (quando non ci sono più tool call)
    - stream_chat_with_tools per i passi intermedi del ReAct loop
 
    Ereditare da ChatProvider garantisce che qualunque ToolChatProvider possa
    essere usato anche dove basta un ChatProvider semplice.
    """
 
    @abstractmethod
    def stream_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Come stream_chat, ma il modello può emettere tool_calls invece di testo.
 
        Args:
            messages:      conversazione corrente (stessa struttura di stream_chat)
            tools:         lista di tool in formato JSON Schema OpenAI-compatibile
                           (es. [{"type": "function", "function": {"name": ..., "parameters": ...}}])
            system_prompt: prompt di sistema
 
        Yields:
            dict con uno di questi formati:
              {"type": "token",      "content": "..."}          → token di testo
              {"type": "tool_call",  "name": "...", "args": {}} → il modello vuole usare un tool
              {"type": "done"}                                   → stream completato
 
        Nota sul formato unificato:
            I provider differiscono su COME comunicano le tool_calls durante lo streaming
            (Ollama le mette in chunk intermedi, OpenAI le accumula, Anthropic usa input_json_delta).
            Questa interfaccia normalizza tutto in eventi dict uniformi così agent.py
            non deve sapere nulla di questi dettagli.
        """
        ...

    @abstractmethod
    def build_assistant_message(self, content: str, tool_calls: list[dict]) -> dict:
        """
        Ricostruisce l'assistant_message da appendere alla conversation history
        dopo che il modello ha emesso tool_calls.

        Perché è nel provider e non in agent.py?
        Perché il formato esatto che il modello si aspetta di rivedere nella history
        è specifico del provider:
          - Ollama richiede {"type": "function", "function": {...}} senza id obbligatorio
          - OpenAI richiede {"id": "call_xyz", "type": "function", "function": {...}} con id obbligatorio

        agent.py chiama questo metodo passando i tool_calls normalizzati e riceve
        un dict pronto da appendere a messages — senza sapere nulla del formato wire.

        Args:
            content:    testo di reasoning accumulato durante lo step (spesso "" con qwen2.5)
            tool_calls: lista di eventi {"type": "tool_call", "name": "...", "args": {}, "id": ...}
                        già normalizzati da stream_chat_with_tools

        Returns:
            dict pronto per messages.append()
        """
        ...

    @abstractmethod
    def build_tool_message(self, tool_call: dict, result) -> dict:
        """
        Costruisce il messaggio role="tool" da appendere alla conversation history
        dopo aver eseguito un tool.

        Perché è nel provider?
        Perché OpenAI richiede obbligatoriamente il campo "tool_call_id" che referenzia
        l'id dell'assistant_message precedente. Ollama non lo richiede e lo ignora.

        Args:
            tool_call: l'evento normalizzato {"type": "tool_call", "name": "...", "args": {}, "id": ...}
                       restituito da stream_chat_with_tools
            result:    il risultato della funzione Python eseguita (qualsiasi tipo serializzabile)

        Returns:
            dict pronto per messages.append()
        """
        ...