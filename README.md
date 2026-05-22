# pysearch

Kod tabanlarında arama yapmak için yazdığım bir CLI tool. ripgrep'e alternatif olarak başladım ama semantic search ve AI özellikleri ekleyince çok daha farklı bir şeye dönüştü.

## Ne yapıyor?

Temel olarak üç farklı arama modu var:

**1. Normal arama** — klasik kelime eşleşmesi, ripgrep gibi çalışır ama Python'da.

**2. Semantic arama** — kelime yazmak zorunda değilsin. "Dosya okuyan fonksiyon" yazarsın, tool ilgili kodu bulur. Bunun için önce dizini indexlemen gerekiyor.

**3. AI analizi** — seçtiğin kod bloğunu açıklatabilir ya da refactor önerisi alabilirsin. Tamamen local çalışıyor, internet gerekmez.

## Kurulum

```bash
git clone https://github.com/KULLANICI_ADIN/pysearch.git
cd pysearch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

AI özellikleri için [Ollama](https://ollama.com) kurulup `ollama pull llama3.2` çalıştırılması gerekiyor.

## Kullanım

```bash
python cli.py search "kelime" .
python cli.py index .
python cli.py semantic "aradığın şeyin anlamı"
python cli.py explain dosya.py --start 1 --end 30
python cli.py refactor dosya.py
```

## Kullanılan teknolojiler

- sentence-transformers, chromadb (semantic search)
- litellm + Ollama (AI özellikleri)
- typer, rich (CLI)