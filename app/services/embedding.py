from app.services import ollama

async def generate_embedding(text: str) -> list[float]:
    return await ollama.generate_embedding(text)