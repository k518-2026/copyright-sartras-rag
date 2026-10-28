# -*- coding: utf-8 -*-
"""
LLM Client Module
Supports Google Gemini API and OpenAI API with streaming responses.
"""

import os
from typing import Generator, List, Dict
from dotenv import load_dotenv

load_dotenv()

def get_secret(key_name: str, default: str = "") -> str:
    """Helper to fetch config from st.secrets, then os.getenv."""
    try:
        import streamlit as st
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, default)

def generate_streaming_response(
    messages: List[Dict[str, str]],
    provider: str = None,
    api_key: str = None,
    model_name: str = None
) -> Generator[str, None, None]:
    """Generates streaming text from the selected LLM provider."""
    provider = (provider or get_secret("LLM_PROVIDER", "gemini")).lower()
    
    if provider == "gemini":
        from google import genai
        from google.genai import types
        from src.embedded_key import get_embedded_gemini_key
        
        gemini_key = api_key or get_secret("GEMINI_API_KEY") or get_embedded_gemini_key()
        if not gemini_key:
            yield "【システム通知】AIサーバーの初期化準備中です（GitHub Secrets の GEMINI_API_KEY 同期待ちです）。少々お待ちください。"
            return
            
        client = genai.Client(api_key=gemini_key)
        target_model = model_name or get_secret("LLM_MODEL", "gemini-3.8-flash")
        
        # Extract system prompt and user conversation
        system_content = ""
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg["content"])]))
            elif msg["role"] == "assistant":
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg["content"])]))
                
        config = types.GenerateContentConfig(
            system_instruction=system_content if system_content else None,
            temperature=0.1
        )
        
        # Multi-model fallback list in case of 503 / 429 high-demand spikes
        candidate_models = [
            target_model,
            "gemini-2.5-flash",
            "gemini-1.5-flash"
        ]
        # Remove duplicates while preserving order
        unique_models = []
        for m in candidate_models:
            if m not in unique_models:
                unique_models.append(m)

        success = False
        last_error = ""
        for model_to_try in unique_models:
            try:
                response = client.models.generate_content_stream(
                    model=model_to_try,
                    contents=contents,
                    config=config
                )
                first_chunk = True
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                        first_chunk = False
                success = True
                break  # Completed successfully
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                # If 503 (high demand) or 429 (rate limit) or 404, try the next fallback model
                if any(code in err_str for code in ["503", "429", "404", "UNAVAILABLE", "NOT_FOUND"]):
                    continue
                else:
                    # Non-recoverable error (e.g. auth error)
                    yield f"\n【Gemini API エラー】: {err_str}"
                    return

        if not success:
            yield f"\n【Gemini API エラー（全モデル一時混雑中）】: Google側のサーバー混雑（503）が発生しています。数秒後に再度送信してください。\n詳細: {last_error}"

    elif provider == "openai":
        from openai import OpenAI
        
        openai_key = api_key or get_secret("OPENAI_API_KEY")
        if not openai_key:
            yield "【エラー】OPENAI_API_KEY が設定されていません。Streamlit Secrets またはサイドバーで設定してください。"
            return
            
        client = OpenAI(api_key=openai_key)
        target_model = model_name or get_secret("LLM_MODEL", "gpt-4o-mini")
        
        try:
            stream = client.chat.completions.create(
                model=target_model,
                messages=messages,
                stream=True,
                temperature=0.1
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except Exception as e:
            yield f"\n【OpenAI API エラー】: {str(e)}"
    else:
        yield f"【エラー】未知のプロバイダーです: {provider}"
