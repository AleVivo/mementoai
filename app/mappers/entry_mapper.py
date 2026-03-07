from app.models.entry import EntryResponse, EntryDocument

def doc_to_response(doc: EntryDocument) -> EntryResponse:
    return EntryResponse(
        id=str(doc.id),
        raw_text=doc.raw_text,
        type=doc.type,
        title=doc.title,
        project=doc.project,
        author=doc.author,
        tags=doc.tags or [],
        summary=doc.summary or "",
        created_at=doc.created_at,
        week=doc.week,
    )

def list_docs_to_responses(docs: list[EntryDocument]) -> list[EntryResponse]:
    return [doc_to_response(doc) for doc in docs]