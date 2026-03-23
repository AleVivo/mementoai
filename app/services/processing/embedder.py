from langfuse import observe
from app.services.llm.factory import get_embedding_provider

@observe(as_type="generation", name="generate_embedding", capture_output=False)
async def generate_embedding(text: str) -> list[float]:
    provider = get_embedding_provider()
    return await provider.embed(text)