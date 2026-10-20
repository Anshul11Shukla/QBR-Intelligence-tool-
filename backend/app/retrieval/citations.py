
def build_citation(
    document_id: int,
    filename: str,
    location: str,
    chunk_id: int,
) -> str:
    return (
        f"[Document {document_id} | {filename} | "
        f"{location} | Chunk {chunk_id}]"
    )


def build_excerpt(text: str, max_chars: int = 450) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars].rsplit(" ", 1)[0] + "..."
