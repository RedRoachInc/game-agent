
def chunk_text(
    text: str,
    chunk_size: int = 100,
    overlap: int = 20,
) -> list[dict]:
    """Split text into overlapping line-based chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid overlap")

    lines = text.splitlines()

    if not lines:
        return []

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(lines), step):
        end = min(start + chunk_size, len(lines))

        content = "\n".join(lines[start:end])

        if content.strip():
            chunks.append({
                "text": content,
                "start_line": start + 1,
                "end_line": end,
            })

        if end == len(lines):
            break

    return chunks
