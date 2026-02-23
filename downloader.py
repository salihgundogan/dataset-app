"""
downloader.py — icrawler ile Bing Görseller'den toplu görsel indirme modülü.

Not: GoogleImageCrawler, Google'ın sayfa yapısını sık değiştirmesi nedeniyle
     güvenilir çalışmamaktadır. BingImageCrawler çok daha kararlıdır.
"""

import os
import logging
from icrawler.builtin import BingImageCrawler

logger = logging.getLogger(__name__)


def download_images(keyword: str, max_num: int, save_dir: str) -> str:
    """
    Belirtilen anahtar kelime ile Bing Görseller'den görsel indirir.

    Args:
        keyword: Aranacak anahtar kelime (örn: "green olives").
        max_num: İndirilecek maksimum görsel sayısı.
        save_dir: Görsellerin kaydedileceği dizin yolu.

    Returns:
        Görsellerin kaydedildiği dizin yolunu döndürür.

    Raises:
        ValueError: Geçersiz parametre verildiğinde.
        OSError: Dizin oluşturulamadığında.
        Exception: İndirme sırasında beklenmeyen bir hata oluştuğunda.
    """
    if not keyword or not keyword.strip():
        raise ValueError("Anahtar kelime boş olamaz.")

    if max_num <= 0:
        raise ValueError("Görsel sayısı 0'dan büyük olmalıdır.")

    if not save_dir or not save_dir.strip():
        raise ValueError("Kayıt dizini belirtilmelidir.")

    # Dizin yoksa oluştur
    try:
        os.makedirs(save_dir, exist_ok=True)
    except OSError as e:
        raise OSError(f"Dizin oluşturulamadı: {save_dir}\n{e}")

    try:
        crawler = BingImageCrawler(
            downloader_threads=4,
            storage={"root_dir": save_dir},
            log_level=logging.WARNING,
        )
        # 403/404 hatalarına karşı timeout ayarları
        crawler.crawl(
            keyword=keyword.strip(),
            max_num=max_num,
            file_idx_offset=0,
        )
    except Exception as e:
        logger.error("İndirme sırasında hata: %s", e)
        raise RuntimeError(f"Görseller indirilirken bir hata oluştu:\n{e}")

    return save_dir

