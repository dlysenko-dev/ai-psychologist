"""Knowledge Loader — loads markdown files into pgvector for RAG"""
import os
from pathlib import Path

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models.knowledge import KnowledgeDocument

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent / "knowledge_base"

# Chunk size for splitting large documents
MAX_CHUNK_SIZE = 1500  # chars
CHUNK_OVERLAP = 200


def chunk_text(content: str, max_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by paragraphs."""
    paragraphs = content.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > max_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap from end of previous chunk
            words = current_chunk.split()
            overlap_text = " ".join(words[-30:]) if len(words) > 30 else ""
            current_chunk = overlap_text + "\n\n" + para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def detect_category(filepath: Path) -> str:
    """Detect category from file path."""
    parts = filepath.relative_to(KNOWLEDGE_BASE_DIR).parts
    if len(parts) >= 2:
        return parts[0]  # neurobiology, cognitive_biases, etc.
    return "general"


async def load_knowledge_base(
    embed_fn=None,
    force_reload: bool = False,
):
    """Load all markdown files from knowledge_base/ into the database.

    Args:
        embed_fn: Optional function(text) -> list[float] for generating embeddings.
                  If None, embeddings are skipped (can be added later).
        force_reload: If True, delete existing documents and reload all.
    """
    if not KNOWLEDGE_BASE_DIR.exists():
        logger.error(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return {"loaded": 0, "error": "Directory not found"}

    async with AsyncSessionLocal() as db:
        if force_reload:
            await db.execute(text("DELETE FROM psych_knowledge_documents"))
            await db.commit()
            logger.info("Cleared existing knowledge documents")

        # Check existing count
        result = await db.execute(
            select(KnowledgeDocument.id).limit(1)
        )
        if result.scalar_one_or_none() and not force_reload:
            logger.info("Knowledge base already loaded. Use force_reload=True to reload.")
            return {"loaded": 0, "skipped": True}

        loaded = 0
        errors = 0

        for md_file in sorted(KNOWLEDGE_BASE_DIR.rglob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                category = detect_category(md_file)
                source = str(md_file.relative_to(KNOWLEDGE_BASE_DIR))

                chunks = chunk_text(content)

                for i, chunk in enumerate(chunks):
                    embedding = None
                    if embed_fn:
                        try:
                            embedding = embed_fn(chunk)
                        except Exception as e:
                            logger.warning(f"Embedding failed for {source} chunk {i}: {e}")

                    doc = KnowledgeDocument(
                        content=chunk,
                        source=f"{source}#chunk_{i}",
                        category=category,
                    )
                    if embedding is not None and doc.embedding is not None:
                        doc.embedding = embedding

                    db.add(doc)
                    loaded += 1

                logger.debug(f"Loaded {len(chunks)} chunks from {source}")

            except Exception as e:
                logger.error(f"Failed to load {md_file}: {e}")
                errors += 1

        await db.commit()
        logger.info(f"Knowledge base loaded: {loaded} chunks, {errors} errors")
        return {"loaded": loaded, "errors": errors}


async def search_knowledge(
    query: str,
    category: str | None = None,
    limit: int = 5,
    embed_fn=None,
) -> list[dict]:
    """Search knowledge base. Falls back to keyword search if no embeddings."""
    async with AsyncSessionLocal() as db:
        if embed_fn:
            # Vector similarity search
            try:
                query_embedding = embed_fn(query)
                sql = text("""
                    SELECT id, content, source, category,
                           embedding <=> :embedding AS distance
                    FROM psych_knowledge_documents
                    WHERE embedding IS NOT NULL
                    {}
                    ORDER BY embedding <=> :embedding
                    LIMIT :limit
                """.format("AND category = :category" if category else ""))

                params = {"embedding": str(query_embedding), "limit": limit}
                if category:
                    params["category"] = category

                result = await db.execute(sql, params)
                rows = result.fetchall()
                return [
                    {"id": r.id, "content": r.content, "source": r.source, "category": r.category, "distance": r.distance}
                    for r in rows
                ]
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to keyword: {e}")

        # Keyword fallback: simple ILIKE search
        keywords = query.lower().split()[:5]  # Top 5 words
        query_obj = select(KnowledgeDocument)
        if category:
            query_obj = query_obj.where(KnowledgeDocument.category == category)

        # Search for any keyword match
        conditions = []
        for kw in keywords:
            if len(kw) > 3:  # Skip short words
                conditions.append(KnowledgeDocument.content.ilike(f"%{kw}%"))

        if conditions:
            from sqlalchemy import or_
            query_obj = query_obj.where(or_(*conditions))

        query_obj = query_obj.limit(limit)
        result = await db.execute(query_obj)
        docs = result.scalars().all()

        return [
            {"id": d.id, "content": d.content, "source": d.source, "category": d.category}
            for d in docs
        ]
