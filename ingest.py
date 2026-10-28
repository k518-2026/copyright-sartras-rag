# -*- coding: utf-8 -*-
"""
Manual data ingestion script to build/refresh the Chroma vector store.
"""

import os
import shutil
from src.db import DB_DIR, get_chroma_collection

def main():
    print(f"Clearing old database at {DB_DIR}...")
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)
        
    print("Initializing ChromaDB and building vector embeddings...")
    collection = get_chroma_collection()
    print(f"Success! {collection.count()} legal documents indexed.")

if __name__ == "__main__":
    main()
