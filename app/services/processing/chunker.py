import re
from bs4 import BeautifulSoup, Tag
import tiktoken
from app.models.chunk import ChunkDocument
from bson import ObjectId
from datetime import datetime

# cl100k_base è il tokenizer di GPT-4 — buona approssimazione anche per Qwen2.5
# Lo inizializziamo una volta sola a livello di modulo (è costoso da caricare)
_tokenizer = tiktoken.get_encoding("cl100k_base")

# Soglia oltre la quale un chunk viene ulteriormente diviso per paragrafi
# 300 token ≈ 220 parole — lascia spazio per 4-5 chunk nel budget RAG di Qwen2.5
CHUNK_TOKEN_LIMIT = 300

# Dimensione minima sotto la quale un chunk viene fuso con il successivo
# Evita chunk da 2 righe che inquinano il retrieval
CHUNK_MIN_TOKENS = 30

HEADING_TAGS = {"h1","h2", "h3"}

def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text))

def extract_text(element) -> str:
    """
    Estrae il testo pulito da un elemento BeautifulSoup.
    
    Caso generale Python: get_text() di BeautifulSoup percorre tutti i nodi
    figli di un elemento e concatena il loro testo. Il parametro separator
    aggiunge un separatore tra elementi inline (es. testo dentro <strong>).
    strip=True rimuove spazi e newline iniziali e finali.
    """
    return element.get_text(separator=" ", strip=True)

def split_paragraphs_by_tokens(
    paragraphs: list[str],
    max_tokens: int,
    heading_prefix: str | None
) -> list[str]:
    """
    Accorpa paragrafi in chunk rispettando il limite token.
    Se è presente un heading, viene preposto a ogni chunk risultante.
    
    Questo è il fallback che scatta quando una sezione ha troppi paragrafi
    per stare in un singolo chunk.
    """
    chunks = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > max_tokens and current_parts:
            # Chiudi il chunk corrente
            body = "\n\n".join(current_parts)
            full = f"{heading_prefix}\n\n{body}" if heading_prefix else body
            chunks.append(full)
            current_parts = [para]
            current_tokens = para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    if current_parts:
        body = "\n\n".join(current_parts)
        full = f"{heading_prefix}\n\n{body}" if heading_prefix else body
        chunks.append(full)

    return chunks

def chunk_html(
    content: str,
    entry_id: ObjectId,
    entry_title: str,
    project_id: str,
    entry_type: str,
    created_at: datetime,
) -> list[ChunkDocument]:
    """
    Divide il contenuto HTML prodotto da TipTap in chunk pronti per l'embedding.

    Strategia:
    1. Parsa l'HTML con BeautifulSoup
    2. Scorre i tag di primo livello in ordine
    3. Ogni <h2> o <h3> apre una nuova sezione
    4. I <p> vengono accumulati nella sezione corrente
    5. Se una sezione supera CHUNK_TOKEN_LIMIT, viene divisa per paragrafi
    6. Se non ci sono headings, tutta l'entry diventa un chunk unico

    Caso generale Python: BeautifulSoup costruisce un albero di oggetti
    navigabili. soup.children restituisce i figli diretti del nodo radice —
    nel nostro caso i tag di primo livello dell'HTML di TipTap.
    """
    soup = BeautifulSoup(content, "html.parser")

    # Struttura dati per accumulare le sezioni durante il parsing
    # Ogni sezione ha un heading opzionale e una lista di paragrafi
    sections: list[dict] = []
    current_heading: str | None = None
    current_paragraphs: list[str] = []

    for element in soup.children:
        # Ignora nodi di testo puri (spazi, newline tra tag)
        # Caso generale: in BeautifulSoup non tutti i children sono Tag —
        # alcuni sono NavigableString (testo grezzo). Controlliamo il tipo.
        if not isinstance(element, Tag):
            continue

        if element.name in HEADING_TAGS:
            # Nuovo heading — salva la sezione precedente se non è vuota
            if current_paragraphs or current_heading:
                sections.append({
                    "heading": current_heading,
                    "paragraphs": current_paragraphs
                })
            current_heading = extract_text(element)
            current_paragraphs = []

        elif element.name == "p":
            text = extract_text(element)
            if text:
                current_paragraphs.append(text)

        # Gestione liste — <ul> e <ol> come blocco unico
        elif element.name in {"ul", "ol"}:
            items = [
                f"- {extract_text(li)}"
                for li in element.find_all("li", recursive=False)
                if extract_text(li)
            ]
            if items:
                current_paragraphs.append("\n".join(items))

        # Gestione blocchi di codice — <pre><code>
        elif element.name == "pre":
            code = extract_text(element)
            if code:
                current_paragraphs.append(f"```\n{code}\n```")

    # Chiudi l'ultima sezione rimasta aperta dopo il loop
    if current_paragraphs or current_heading:
        sections.append({
            "heading": current_heading,
            "paragraphs": current_paragraphs
        })

    # Nessuna sezione trovata — entry senza struttura, chunk unico
    if not sections:
        plain_text = BeautifulSoup(content, "html.parser").get_text(
            separator="\n", strip=True
        )
        if plain_text:
            sections = [{"heading": None, "paragraphs": [plain_text]}]

    # Costruisci i ChunkDocument finali
    chunks: list[ChunkDocument] = []
    chunk_index = 0

    for section in sections:
        heading: str | None = section["heading"]
        paragraphs: list[str] = section["paragraphs"]

        if not paragraphs and not heading:
            continue

        # Testo completo della sezione per misurare i token
        body = "\n\n".join(paragraphs)
        full_text = f"{heading}\n\n{body}" if heading and body else heading or body

        if not full_text.strip():
            continue

        token_count = count_tokens(full_text)

        if token_count > CHUNK_TOKEN_LIMIT:
            # La sezione è troppo lunga — dividila per paragrafi
            sub_texts = split_paragraphs_by_tokens(
                paragraphs, CHUNK_TOKEN_LIMIT, heading
            )
            for sub_text in sub_texts:
                sub_tokens = count_tokens(sub_text)
                if sub_tokens < CHUNK_MIN_TOKENS:
                    continue

                chunks.append(ChunkDocument(
                    entry_id=entry_id,
                    chunk_index=chunk_index,
                    heading=heading,
                    text=sub_text,
                    token_count=sub_tokens,
                    entry_title=entry_title,
                    project_id=project_id,
                    entry_type=entry_type,
                    created_at=created_at,
                ))
                chunk_index += 1
        else:
            if token_count < CHUNK_MIN_TOKENS:
                continue

            chunks.append(ChunkDocument(
                entry_id=entry_id,
                chunk_index=chunk_index,
                heading=heading,
                text=full_text,
                token_count=token_count,
                entry_title=entry_title,
                project_id=project_id,
                entry_type=entry_type,
                created_at=created_at,
            ))
            chunk_index += 1

    return chunks