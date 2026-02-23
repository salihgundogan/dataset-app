# 📸 Görsel Veri Seti İndirme ve İşleme Aracı

Anahtar kelimeye göre internetten görsel indirip, Gemini AI ile filtreleyerek veri seti oluşturan araç.

## 🚀 Kurulum

### 1. Repoyu klonla
```bash
git clone https://github.com/salihgundogan/dataset-app.git
cd dataset-app
```

### 2. Sanal ortam oluştur ve aktif et
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate          # Windows
```

### 3. Bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

### 4. API Key'i ayarla
`.env.example` dosyasını kopyalayıp `.env` olarak kaydet ve kendi API key'ini yaz:
```bash
cp .env.example .env
```
Sonra `.env` dosyasını aç ve `GEMINI_API_KEY` değerini kendi key'inle değiştir:
```
GEMINI_API_KEY=senin_api_keyin
```

> 💡 API key almak için: [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Çalıştır
```bash
python main.py
```
