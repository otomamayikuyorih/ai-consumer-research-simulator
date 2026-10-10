import os
import json
import time
import logging
from typing import Any, Optional, Tuple
from google import genai
from google.genai import types

from .config import settings

logger = logging.getLogger(__name__)

def get_gemini_client(prefer_model: Optional[str] = None) -> Tuple[Optional[genai.Client], str, str, Optional[str]]:
    """
    Geminiクライアントを取得する。
    優先順位:
    1. settings.GEMINI_API_KEY が設定されている場合は Google AI Studio (Gemini Developer API)
    2. Cloud Run環境またはGCP環境の場合は Vertex AI (Application Default Credentials / ADC)
    3. いずれも利用できない場合は None と理由を返却

    戻り値: (client, provider, resolved_model, error_message)
    provider: 'gemini_developer_api' | 'vertex_ai' | 'none'
    """
    target_model = prefer_model or settings.DEFAULT_GEMINI_MODEL

    # 1. APIキーが存在する場合
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
            return client, "gemini_developer_api", target_model, None
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini Developer API client with key: {e}")
            return None, "none", target_model, f"Gemini APIキー初期化失敗: {str(e)}"

    # 2. Cloud Run / GCP Vertex AI 環境
    if settings.IS_CLOUD_RUN or settings.USE_VERTEX_AI or os.getenv("K_SERVICE"):
        try:
            project_id = settings.GOOGLE_CLOUD_PROJECT or "stable-century-479407-m7"
            location = settings.GOOGLE_CLOUD_LOCATION or "asia-northeast1"
            client = genai.Client(vertexai=True, project=project_id, location=location)

            # Vertex AI asia-northeast1 では gemini-3.5-flash が実稼働・利用可能
            resolved_model = target_model
            return client, "vertex_ai", resolved_model, None
        except Exception as e:
            logger.warning(f"Failed to initialize Vertex AI client: {e}")
            return None, "none", target_model, f"Vertex AI初期化失敗: {str(e)}"

    return None, "none", target_model, "GEMINI_API_KEY が設定されておらず、Google Cloud ADC認証情報も未検出です。"

def is_gemini_available() -> Tuple[bool, str, str]:
    """Gemini APIまたはVertex AIが利用可能かを判定し (available, provider, model_name) を返却"""
    client, provider, model, err = get_gemini_client()
    if client is not None:
        return True, provider, model
    return False, "none", model

async def call_gemini_json_with_tracking(
    prompt: str,
    system_instruction: Optional[str] = None,
    prefer_model: Optional[str] = None,
    temperature: float = 0.7
) -> Tuple[Any, dict[str, Any]]:
    """
    Gemini APIをJSONモードで呼び出し、結果と詳細なメタデータ（所要時間、トークン数、使用モデル、プロバイダ）を返却する。
    失敗時は例外を発生させ、呼び出し元でフォールバックと理由を記録可能にする。
    """
    t_start = time.time()
    client, provider, model, err = get_gemini_client(prefer_model)

    if not client:
        raise RuntimeError(err or "Gemini APIクライアントを初期化できませんでした。")

    config_kwargs: dict[str, Any] = {
        "response_mime_type": "application/json",
        "temperature": temperature
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
    except Exception as api_err:
        logger.error(f"Gemini API JSON call failed for model {model}: {api_err}")
        raise api_err


    duration_ms = int((time.time() - t_start) * 1000)

    # トークン数の抽出
    tokens = {
        "prompt_tokens": 0,
        "candidates_tokens": 0,
        "total_tokens": 0
    }
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        tokens["prompt_tokens"] = getattr(um, "prompt_token_count", 0) or 0
        tokens["candidates_tokens"] = getattr(um, "candidates_token_count", 0) or 0
        tokens["total_tokens"] = getattr(um, "total_token_count", 0) or (tokens["prompt_tokens"] + tokens["candidates_tokens"])

    text = response.text.strip() if response.text else "{}"
    parsed_json = json.loads(text)

    meta = {
        "provider": provider,
        "model_used": model,
        "duration_ms": duration_ms,
        "tokens": tokens,
        "api_calls": 1
    }

    return parsed_json, meta

async def call_gemini_text_with_tracking(
    prompt: str,
    system_instruction: Optional[str] = None,
    prefer_model: Optional[str] = None,
    temperature: float = 0.7
) -> Tuple[str, dict[str, Any]]:
    """Gemini APIをテキストモードで呼び出し、結果と詳細なメタデータを返却する。"""
    t_start = time.time()
    client, provider, model, err = get_gemini_client(prefer_model)

    if not client:
        raise RuntimeError(err or "Gemini APIクライアントを初期化できませんでした。")

    config_kwargs: dict[str, Any] = {
        "temperature": temperature
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
    except Exception as api_err:
        logger.error(f"Gemini API text call failed for model {model}: {api_err}")
        raise api_err


    duration_ms = int((time.time() - t_start) * 1000)

    tokens = {
        "prompt_tokens": 0,
        "candidates_tokens": 0,
        "total_tokens": 0
    }
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        tokens["prompt_tokens"] = getattr(um, "prompt_token_count", 0) or 0
        tokens["candidates_tokens"] = getattr(um, "candidates_token_count", 0) or 0
        tokens["total_tokens"] = getattr(um, "total_token_count", 0) or (tokens["prompt_tokens"] + tokens["candidates_tokens"])

    meta = {
        "provider": provider,
        "model_used": model,
        "duration_ms": duration_ms,
        "tokens": tokens,
        "api_calls": 1
    }

    return response.text.strip() if response.text else "", meta
