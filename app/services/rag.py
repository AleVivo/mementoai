from app.models.search import SearchResult
from app.services import ollama

async def return_chat_response(question: str, results: list[SearchResult]) -> dict:
    if not results:
        return {
            "response": "No relevant information found.",
            "sources": []
        }
    
    context_parts = []
    for i, entry in enumerate(results):
        context_parts.append(
            f"Source {i+1}:\n"
            f"Title: {entry.title}\n"
            f"Summary: {entry.summary}\n"
            f"Raw Text: {entry.content}\n"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Sei un assistente per team di sviluppo. Rispondi alla domanda usando SOLO le informazioni fornite nel contesto.
Se la risposta non è nel contesto, dillo esplicitamente.
Cita le fonti usando i numeri tra parentesi quadre, es. [1] o [2].

CONTESTO:
{context}

DOMANDA: {question}

RISPOSTA:"""
    
    answer = await ollama.generate_by_prompt(prompt)
    return {
        "answer": answer,
        "sources": [
            {
                "ref": i + 1,
                "id": entry.id,
                "title": entry.title,
                "type": entry.entry_type,
                "score": entry.score
            } for i, entry in enumerate(results)
        ]
    }