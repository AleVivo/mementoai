from app.models.entry import EntryResponse, EntryDocument

def doc_to_response(doc: EntryDocument) -> EntryResponse:
    return EntryResponse(
        id=str(doc.id),
        content=doc.content,
        entry_type=doc.entry_type,
        title=doc.title,
        project=doc.project,
        author=doc.author,
        tags=doc.tags or [],
        summary=doc.summary or "",
        created_at=doc.created_at,
        week=doc.week,
        vector_status=doc.vector_status,
    )

def list_docs_to_responses(docs: list[EntryDocument]) -> list[EntryResponse]:
    return [doc_to_response(doc) for doc in docs]