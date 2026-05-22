# pysearch

Kod tabanlarında arama yaparken ripgrep veya grep gibi araçlar sadece kelime eşleşmesi yapar. Yani aradığın şeyin tam adını bilmen gerekir. Bu projede amacım, kelime yazmak zorunda kalmadan **anlam bazlı arama** yapabilen, üstüne bir de **yerel AI ile kod analizi** sunan bir CLI aracı geliştirmekti.

Örneğin ripgrep ile "dosyayı kapatan fonksiyon" diye arayamazsın. pysearch ile arayabilirsin.

Üç temel özellik üzerine kurulu:

- **Normal arama** — ripgrep gibi kelime eşleşmesi, renkli terminal çıktısı
- **Semantic arama** — doğal dil ile arama, kelimeyi bilmene gerek yok
- **AI analizi** — seçilen kod bloğunu Türkçe açıklar veya refactor önerisi sunar, tamamen yerel çalışır

---

## Kurulum

### Gereksinimler

- Python 3.10+
- [Ollama](https://ollama.com) (AI özellikleri için)

### Adımlar

**1. Repoyu klonla**
```bash
git clone https://github.com/enesss2463/pysearch.git
cd pysearch
```

**2. Sanal ortam oluştur ve aktif et**
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

**3. Gerekli kütüphaneleri kur**
```bash
pip install -r requirements.txt
```

**4. Ollama ile AI modelini indir (AI özellikleri için)**
```bash
ollama pull llama3.2
```

---

## Kullanım

### 1. Normal Arama

Klasik kelime araması yapar. Eşleşen kelimeler kırmızı ile vurgulanır.

```bash
python cli.py search "import" .
```

Belirli uzantılarda ara:
```bash
python cli.py search "def " . --ext .py
```

Regex kullan:
```bash
python cli.py search "def \w+" . --regex
```

---

### 2. Semantic Arama

Önce dizini indexle (ilk seferinde model yüklenir):
```bash
python cli.py index .
```

Sonra doğal dil ile ara:
```bash
python cli.py semantic "dosya okuyan fonksiyon"
python cli.py semantic "hata fırlatan kod"
python cli.py semantic "binary dosya kontrolü"
```

Dizin değiştiğinde tekrar indexlemeye gerek yok, sadece değişen dosyalar otomatik güncellenir (incremental indexing).

---

### 3. AI Kod Açıklama

Seçilen satır aralığını Türkçe olarak açıklar:
```bash
python cli.py explain pysearch\scanner.py --start 1 --end 30
```

---

### 4. AI Refactor Önerisi

Seçilen kod bloğu için iyileştirme önerisi sunar:
```bash
python cli.py refactor pysearch\engine.py --start 1 --end 40
```

---

## Kullanılan Teknolojiler

| Kütüphane | Amaç |
|-----------|------|
| sentence-transformers | Semantic search için embedding modeli |
| chromadb | Yerel vektör veritabanı |
| litellm | AI model entegrasyonu |
| Ollama + llama3.2 | Yerel AI modeli (internet gerekmez) |
| typer | CLI arayüzü |
| rich | Renkli terminal çıktısı |
| aiofiles | Async dosya okuma |
| pathspec | .gitignore desteği |
| chardet | Dosya encoding tespiti |