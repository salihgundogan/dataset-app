"""
ai_filter.py — Gemini 2.5 Flash ile görsel uygunluk filtreleme modülü.

İndirilen görsellerin, belirtilen anahtar kelimeye (yemeğe) ait
gerçek fotoğraflar olup olmadığını kontrol eder.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv(Path(__file__).parent / ".env")

# Gemini istemcisini oluştur
_client = None

FILTER_PROMPT = """Sen bir food dataset kalite kontrol asistanısın.

Görevin: Verilen görselin, belirtilen anahtar kelimeye ait GERÇEK bir fotoğraf olup olmadığını belirlemek.

Anahtar kelime: "{keyword}"

Aşağıdaki kriterlere göre değerlendir:
1. Görsel, GERÇEK bir "{keyword}" fotoğrafı mı? (çizim, logo, meme, infografik, kolaj DEĞİL)
2. Görselde "{keyword}" net ve belirgin şekilde görünüyor mu?
3. Görsel bir food/gıda veri setinde kullanılmaya uygun kalitede mi? (çok bulanık, çok küçük, aşırı watermark'lı DEĞİL)

SADECE ve SADECE "EVET" veya "HAYIR" yaz. Başka hiçbir şey yazma."""


def _get_client() -> genai.Client:
    """Gemini API istemcisini döndürür (lazy initialization)."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY bulunamadı.\n"
                ".env dosyasına GEMINI_API_KEY=your_key_here satırını ekleyin."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def is_relevant_food_image(image_path: str, keyword: str) -> bool:
    """
    Görselin belirtilen anahtar kelimeye uygun bir yemek fotoğrafı olup olmadığını kontrol eder.

    Args:
        image_path: Kontrol edilecek görselin dosya yolu.
        keyword: Aranacak yemek/gıda anahtar kelimesi (örn: "green olives").

    Returns:
        True → görsel uygun, False → görsel uygun değil.
        Hata durumunda True döner (görsel kaybetmemek için).
    """
    try:
        client = _get_client()

        # Görseli oku
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Dosya uzantısından MIME tipini belirle
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".gif": "image/gif",
            ".jfif": "image/jpeg",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        prompt = FILTER_PROMPT.format(keyword=keyword)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=image_data, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
        )

        answer = response.text.strip().upper()
        is_relevant = "EVET" in answer

        logger.info(
            "AI filtre: %s → %s (%s)",
            os.path.basename(image_path),
            "✓ UYGUN" if is_relevant else "✗ UYGUN DEĞİL",
            answer,
        )

        return is_relevant

    except ValueError:
        # API key hatası — yukarı fırlat
        raise

    except Exception as e:
        # Diğer hatalar — görseli kaybetmemek için True dön
        logger.warning(
            "AI filtre hatası, görsel kabul ediliyor: %s — %s",
            os.path.basename(image_path),
            e,
        )
        return True
