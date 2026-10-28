# -*- coding: utf-8 -*-
"""
Database & Legal Search Module
Supports full text search and exact article lookup across:
- 著作権法 (全文)
- 著作権法施行令 (全文)
- 著作権法施行規則 (全文)
- SARTRAS運用指針
- 重要判例
"""

import os
import json
import re
import unicodedata
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

_KNOWLEDGE_CACHE = None

def load_all_knowledge() -> List[Dict[str, Any]]:
    """Loads all laws, guidelines, and precedents into memory."""
    global _KNOWLEDGE_CACHE
    if _KNOWLEDGE_CACHE is not None:
        return _KNOWLEDGE_CACHE
        
    all_data = []
    
    # 1. Full Laws (著作権法、施行令、施行規則 全621条)
    full_laws_path = os.path.join(DATA_DIR, "all_copyright_laws.json")
    if os.path.exists(full_laws_path):
        with open(full_laws_path, "r", encoding="utf-8") as f:
            all_data.extend(json.load(f))
            
    # 2. SARTRAS Guidelines
    sartras_path = os.path.join(DATA_DIR, "sartras_guidelines.json")
    if os.path.exists(sartras_path):
        with open(sartras_path, "r", encoding="utf-8") as f:
            all_data.extend(json.load(f))
            
    # 3. Precedents
    precedents_path = os.path.join(DATA_DIR, "precedents.json")
    if os.path.exists(precedents_path):
        with open(precedents_path, "r", encoding="utf-8") as f:
            all_data.extend(json.load(f))
            
    _KNOWLEDGE_CACHE = all_data
    return all_data

def normalize_text(text: str) -> str:
    """Normalize full-width numbers/alphabets to half-width."""
    return unicodedata.normalize("NFKC", text).lower()

def extract_article_numbers(query: str) -> List[str]:
    """Extracts article numbers like '第41条', '41条', '第35条第2項' from query."""
    normalized = normalize_text(query)
    # Match patterns like 第41条, 41条
    matches = re.findall(r"(?:第)?(\d+)(?:条)", normalized)
    return list(set(matches))

def search_knowledge(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Hybrid search:
    1. Exact Article Number matching (e.g. 第41条, 35条)
    2. Law type matching (著作権法, 施行令, 施行規則, SARTRAS, 判例)
    3. Keyword / BM25 term overlap matching
    """
    items = load_all_knowledge()
    norm_query = normalize_text(query)
    target_articles = extract_article_numbers(query)
    
    # Determine target law filter if specified
    law_filter = None
    if "施行規則" in query or "規則" in query:
        law_filter = "著作権法施行規則"
    elif "施行令" in query or "政令" in query:
        law_filter = "著作権法施行令"
    elif "民法" in query:
        law_filter = "民法"
    elif "不正競争" in query or "不競法" in query:
        law_filter = "不正競争防止法"
    elif "プロバイダ" in query or "プロ責" in query or "発信者情報" in query:
        law_filter = "プロバイダ責任制限法"
    elif "刑法" in query:
        law_filter = "刑法"
    elif "独占禁止" in query or "独禁法" in query:
        law_filter = "独占禁止法"
    elif "sartras" in norm_query or "補償金" in query or "授業目的公衆送信" in query:
        law_filter = "SARTRAS"
    elif "判例" in query or "裁判" in query:
        law_filter = "裁判例"
    elif "著作権法" in query:
        law_filter = "著作権法"

    scored_items = []
    
    # Simple tokenization by words/characters
    query_tokens = [t for t in re.findall(r"[\w]+", norm_query) if len(t) > 1]
    
    for item in items:
        score = 0.0
        law_name = item.get("law_name", "")
        title = item.get("title", "")
        content = item.get("content", "")
        art_num = item.get("article_num", "")
        norm_content = normalize_text(content)
        norm_title = normalize_text(title)
        
        # 1. Exact Article match (Highest Priority)
        if target_articles and art_num in target_articles:
            if law_filter and law_filter in law_name:
                score += 150.0  # Perfect match on law + article
            elif not law_filter and (law_name == "著作権法" or not law_name):
                score += 100.0  # Default to 著作権法 if unspecified
            else:
                score += 50.0   # Matches article in another law
                
        # 2. Law filter boost
        if law_filter and (law_filter in item.get("category", "") or law_filter in law_name):
            score += 15.0
            
        # 3. Keyword matching
        for token in query_tokens:
            if token in norm_title:
                score += 10.0
            if token in norm_content:
                score += 2.0
                
        if score > 0:
            scored_items.append((score, item))
            
    # Sort by score descending
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    hits = []
    seen_ids = set()
    for score, item in scored_items:
        item_id = item.get("id")
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        hits.append({
            "title": item.get("title", ""),
            "category": item.get("category", "法令"),
            "url": item.get("source_url", ""),
            "content": item.get("content", "")
        })
        if len(hits) >= top_k:
            break
            
    return hits
