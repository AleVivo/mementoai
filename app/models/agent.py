from typing import Optional
from pydantic import BaseModel, Field

class AgentRequest(BaseModel):
    question: str = Field(
        ...,  # ... significa "obbligatorio" in Pydantic
        min_length=3,
        description="La domanda in linguaggio naturale",
        examples=["Quanti ADR abbiamo scritto sul progetto Memento?"],
    )
    project_id: Optional[str] = None
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID per tracciare la conversazione. Se non fornito, ne viene generato uno nuovo.",
    )


class AgentStep(BaseModel):
    """Rappresenta un singolo step del ReAct loop — tool chiamato + risultato."""
    tool: str
    args: dict
    result: object  # può essere lista, dict, int a seconda del tool


class AgentResponse(BaseModel):
    answer: str = Field(description="La risposta finale dell'agente")
    steps: list[AgentStep] = Field(description="Gli step eseguiti (tool calls + risultati)")
    model: str = Field(description="Il modello LLM usato")

