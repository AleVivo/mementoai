from app.services.llm.factory import get_embedding_provider

async def generate_embedding(text: str) -> list[float]:
    provider = get_embedding_provider()
    return await provider.embed(text)