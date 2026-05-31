"""
MCP Tools - Thin wrappers around authenticRAG.py functions
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def search_documentation(rag_client, query: str, limit: int = 5) -> str:
    """
    Search using existing hybrid search with Contextual Retrieval
    
    Wrapper around authenticRAG.search_documents()
    """
    try:
        logger.info(f"Searching: '{query}' (limit={limit})")
        
        # Call existing function
        results = rag_client.search_documents(query, top_k=limit)
        
        if not results or len(results) == 0:
            return "No results found for your query."
        
        # Format results for MCP response
        formatted = []
        for i, result in enumerate(results, 1):
            score = result.get('score', 0.0)
            content = result.get('content', '')
            source = result.get('source', 'Unknown')
            title = result.get('title', source)
            
            formatted.append(
                f"[{i}] {title} (Score: {score:.3f})\n"
                f"Source: {source}\n\n"
                f"{content}\n"
            )
        
        return "\n---\n".join(formatted)
    
    except Exception as e:
        error_msg = f"Error searching: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


async def add_documents(rag_client, path: str) -> str:
    """
    Index documents with Contextual Retrieval
    
    Wrapper around authenticRAG.load_documents() and add_documents_with_context()
    """
    try:
        import os
        from pathlib import Path
        
        logger.info(f"Indexing documents from: {path}")
        
        # Check if path exists
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        # Get all markdown files
        md_files = []
        if os.path.isfile(path):
            if path.endswith('.md'):
                md_files = [path]
        elif os.path.isdir(path):
            md_files = list(Path(path).glob('*.md'))
            md_files = [str(f) for f in md_files]
        
        if not md_files:
            return f"No markdown files found in: {path}"
        
        logger.info(f"Found {len(md_files)} markdown files")
        
        # Load and chunk documents
        docs = rag_client.load_documents(md_files)
        
        if not docs:
            return "No documents could be loaded"
        
        logger.info(f"Loaded {len(docs)} chunks")
        
        # Index with context generation
        indexed_count = rag_client.add_documents_with_context(docs)
        
        # Format response
        return f"""✅ Successfully indexed documents with Contextual Retrieval:
- Files processed: {len(md_files)}
- Chunks created: {len(docs)}
- Contexts generated: {indexed_count}
- Indexed to OpenSearch: {indexed_count}
- Vector index: anthropic-vector-index
- BM25 index: anthropic-bm25-index

Files: {', '.join([os.path.basename(f) for f in md_files])}"""
    
    except Exception as e:
        error_msg = f"Error indexing documents: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


async def generate_answer(rag_client, query: str, use_context: bool = True) -> str:
    """
    Generate answer using RAG pipeline
    
    Wrapper around authenticRAG functions
    """
    try:
        logger.info(f"Generating answer for: '{query}' (use_context={use_context})")
        
        if use_context:
            # Search first, then generate answer
            search_results = rag_client.search_documents(query, top_k=5)
            
            if not search_results:
                return "No relevant context found. Please try a different query."
            
            # Generate answer with context
            answer = rag_client.generate_answer(query, search_results)
        else:
            # Direct answer without context
            answer = rag_client.generate_answer(query, [])
        
        return answer
    
    except Exception as e:
        error_msg = f"Error generating answer: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
