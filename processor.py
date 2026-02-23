"""
processor.py — İndirilen görselleri JPG formatına dönüştürme ve sıralı isimlendirme modülü.
"""

import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Desteklenen görsel uzantıları
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    ".gif", ".tiff", ".tif", ".jfif", ".ico",
}


def _is_image_file(filename: str) -> bool:
    """Dosyanın desteklenen bir görsel uzantısına sahip olup olmadığını kontrol eder."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in SUPPORTED_EXTENSIONS


def _convert_to_rgb(image: Image.Image) -> Image.Image:
    """Görseli RGB moduna dönüştürür (RGBA, P, LA gibi modları destekler)."""
    if image.mode in ("RGBA", "LA", "PA"):
        # Alfa kanalı varsa beyaz arka plan üzerine yapıştır
        background = Image.new("RGB", image.size, (255, 255, 255))
        # Alfa kanalını maske olarak kullan
        if image.mode == "RGBA":
            background.paste(image, mask=image.split()[3])
        else:
            background.paste(image, mask=image.split()[-1])
        return background
    elif image.mode == "P":
        # Palette modunu önce RGBA'ya çevir (transparan olabilir)
        rgba_image = image.convert("RGBA")
        background = Image.new("RGB", rgba_image.size, (255, 255, 255))
        background.paste(rgba_image, mask=rgba_image.split()[3])
        return background
    elif image.mode != "RGB":
        return image.convert("RGB")
    return image


def process_images(
    directory: str,
    start_index: int = 1,
    ai_filter_enabled: bool = False,
    keyword: str = "",
    progress_callback=None,
    status_callback=None,
) -> int:
    """
    Belirtilen dizindeki tüm görselleri JPG formatına dönüştürür ve sıralı isimlendirir.

    İşlem adımları:
        1. Dizindeki tüm desteklenen görsel dosyalarını bulur.
        2. (AI aktifse) Her görseli Gemini 2.5 Flash ile kontrol eder.
        3. Uygun görselleri RGB'ye dönüştürür ve start_index.jpg, ... olarak kaydeder.
        4. Orijinal dosyaları siler.

    Args:
        directory: Görsellerin bulunduğu dizin yolu.
        start_index: İlk görselin numarası (varsayılan: 1).
        ai_filter_enabled: AI filtreleme aktif mi.
        keyword: AI filtreleme için anahtar kelime.
        progress_callback: İlerleme bildirmek için opsiyonel callback (current, total).
        status_callback: Durum mesajı bildirmek için opsiyonel callback (message).

    Returns:
        Başarıyla işlenen görsel sayısını döndürür.

    Raises:
        ValueError: Geçersiz dizin yolu verildiğinde.
        FileNotFoundError: Dizin bulunamadığında.
    """
    if not directory or not directory.strip():
        raise ValueError("Dizin yolu boş olamaz.")

    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Dizin bulunamadı: {directory}")

    # Dizindeki tüm görsel dosyalarını bul
    image_files = sorted(
        [f for f in os.listdir(directory) if _is_image_file(f)]
    )

    if not image_files:
        logger.warning("Dizinde işlenecek görsel bulunamadı: %s", directory)
        return 0

    # AI filtre modülünü gerektiğinde import et
    ai_filter_func = None
    if ai_filter_enabled:
        try:
            from ai_filter import is_relevant_food_image
            ai_filter_func = is_relevant_food_image
        except ImportError as e:
            logger.error("AI filtre modülü yüklenemedi: %s", e)
            ai_filter_func = None

    total = len(image_files)
    processed_count = 0
    filtered_count = 0
    current_number = start_index
    temp_outputs = []  # (geçici_dosya_adı, orijinal_dosya_yolu, nihai_numara) listesi

    # 1. Adım: Tüm görselleri geçici adlarla JPG olarak kaydet
    for i, filename in enumerate(image_files):
        filepath = os.path.join(directory, filename)

        # AI filtreleme kontrolü
        if ai_filter_func:
            if status_callback:
                status_callback(f"🤖 AI kontrol: {i + 1}/{total}")
            try:
                if not ai_filter_func(filepath, keyword):
                    filtered_count += 1
                    logger.info("AI filtre: elendi → %s", filename)
                    # İlerleme bildirimi
                    if progress_callback:
                        progress_callback(i + 1, total)
                    continue
            except ValueError:
                # API key hatası — yukarı fırlat
                raise
            except Exception as e:
                logger.warning("AI filtre hatası, görsel kabul ediliyor: %s — %s", filename, e)

        temp_name = f"_temp_{current_number}.jpg"
        temp_path = os.path.join(directory, temp_name)

        try:
            with Image.open(filepath) as img:
                rgb_image = _convert_to_rgb(img)
                rgb_image.save(temp_path, format="JPEG", quality=95)
                temp_outputs.append((temp_name, filepath, current_number))
                processed_count += 1
                current_number += 1
                logger.info("Dönüştürüldü: %s → %s", filename, temp_name)
        except Exception as e:
            logger.warning("Görsel işlenemedi, atlanıyor: %s — Hata: %s", filename, e)

        # İlerleme bildirimi
        if progress_callback:
            progress_callback(i + 1, total)

    if filtered_count > 0:
        logger.info("AI filtre: %d görsel elendi, %d görsel kaldı", filtered_count, processed_count)

    # 2. Adım: Orijinal dosyaları sil
    for _, original_path, _ in temp_outputs:
        try:
            if os.path.exists(original_path):
                os.remove(original_path)
        except OSError as e:
            logger.warning("Orijinal dosya silinemedi: %s — %s", original_path, e)

    # Orijinallerden kalan (dönüştürülemeyen) orijinal dosyaları da temizle
    # Sadece temp_ ile başlamayanları sil
    remaining_originals = [
        f for f in os.listdir(directory)
        if _is_image_file(f) and not f.startswith("_temp_")
    ]
    for f in remaining_originals:
        try:
            os.remove(os.path.join(directory, f))
        except OSError:
            pass

    # 3. Adım: Geçici dosyaları nihai isimlere taşı
    for temp_name, _, file_number in temp_outputs:
        temp_path = os.path.join(directory, temp_name)
        final_name = f"{file_number}.jpg"
        final_path = os.path.join(directory, final_name)

        try:
            os.rename(temp_path, final_path)
            logger.info("Yeniden adlandırıldı: %s → %s", temp_name, final_name)
        except OSError as e:
            logger.warning("Dosya yeniden adlandırılamadı: %s — %s", temp_name, e)

    return processed_count
