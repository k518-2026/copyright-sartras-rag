# -*- coding: utf-8 -*-
"""
Database & Vector Store Module
Supports ChromaDB with multilingual embeddings.
"""

import os
import json
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

def load_json_data() -> List[Dict[str, Any]]:
    """Loads all knowledge JSON files from the data directory."""
    all_data = []
    for filename in ["copyright_law.json", "sartras_guidelines.json", "precedents.json"]:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                items = json.load(f)
                all_data.extend(items)
    return all_data

def get_chroma_collection():
    """Initializes and returns the Chroma collection with persistent storage."""
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Multilingual embedding model (lightweight, runs in cloud container memory easily)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-base"
    )
    
    collection = client.get_or_create_collection(
        name="legal_knowledge",
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Auto-populate if empty
    if collection.count() == 0:
        data = load_json_data()
        if data:
            ids = [item["id"] for item in data]
            docs = [f"passage: {item['content']}" for item in data]
            metas = [
                {
                    "title": item["title"],
                    "category": item["category"],
                    "source_url": item["source_url"],
                    "raw_content": item["content"]
                }
                for item in data
            ]
            collection.add(ids=ids, documents=docs, metadatas=metas)
            
    return collection

def search_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Searches relevant laws, guidelines, and precedents."""
    collection = get_chroma_collection()
    formatted_query = f"query: {query}"
    
    results = collection.query(query_texts=[formatted_query], n_results=top_k)
    
    hits = []
    if results and results.get("metadatas") and results["metadatas"][0]:
        for meta in results["metadatas"][0]:
            hits.append({
                "title": meta["title"],
                "category": meta["category"],
                "url": meta["source_url"],
                "content": meta["raw_content"]
            })
    return hits
