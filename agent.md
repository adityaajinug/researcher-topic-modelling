# AGENT.md — Topic Consistency Index (TCI) Research Pipeline

## Project Overview

Penelitian ini mengukur **konsistensi topik riset** seorang dosen/peneliti menggunakan topic modelling (LDA) terhadap publikasi jurnal ber-DOI aktif. Studi kasus: dosen bidang Computer Science di **Universitas Dian Nuswantoro (UDINUS)**.

**Output akhir:** Topic Consistency Index (TCI) per author — skor 0–1 berbasis Shannon entropy dari distribusi topik publikasi.

```
TCI = 1 - (H / H_max)
```
di mana H = entropy distribusi topik, H_max = log2(jumlah topik).

---

## Research Scope

| Parameter | Value |
|---|---|
| Institusi | Universitas Dian Nuswantoro — OpenAlex ID `I4210127958` |
| Bidang | Computer Science (cross-check dengan ACM CCS 2012) |
| Tipe publikasi | `journal-article` only (exclude proceedings, book-chapter) |
| DOI | Wajib ada (`has_doi:true`) dan aktif (verified) |
| Tier jurnal | Filter Q1 & Q2 (Scimago SJR) |
| Minimum artikel | ≥5 artikel per author untuk masuk analisis |

---

## Data Sources

### 1. OpenAlex API
- Base URL: `https://api.openalex.org`
- **Wajib pakai API key** — daftar gratis di https://openalex.org/settings/api
- Tambahkan `&api_key=YOUR_KEY` di setiap request, atau set di header
- Free tier: $1 credit/hari, cukup untuk seluruh kebutuhan riset ini (estimasi total < $0.10)
- Pricing: List+Filter endpoint = $0.10/1000 calls; Get-by-ID = gratis selamanya

**PENTING — pelajaran dari eksplorasi awal:**
- Filter `last_known_institutions.id` di endpoint `/authors` **noisy/tidak reliable** (banyak salah assign institusi)
- **Strategi yang benar:** filter dari endpoint `/works` dengan `institutions.id`, baru extract author dari hasil works. Affiliation di level paper jauh lebih akurat.

Endpoint utama yang dipakai:
```
GET /works?filter=institutions.id:I4210127958,type:journal-article,has_doi:true
GET /works/{id}          # detail satu work jika perlu
GET /authors/{id}        # detail satu author jika perlu enrich data
```

### 2. Scimago Journal Rank (SJR)
- Download manual (gratis, tidak ada API resmi): https://www.scimagojr.com/journalrank.php → tombol Download
- Format: CSV dengan separator `;`
- Kolom kunci: `Issn`, `Title`, `SJR Best Quartile`
- Disimpan lokal di `data/raw/scimagojr.csv`, di-update manual per tahun jika perlu

### 3. CrossRef API (verifikasi DOI aktif — opsional/extra validation)
- Base URL: `https://api.crossref.org/works/{doi}`
- Tidak perlu API key, gratis
- Dipakai sebagai lapisan validasi tambahan di luar `has_doi:true` dari OpenAlex
- Alternatif lebih ringan: HEAD request langsung ke `https://doi.org/{doi}`

---

## Project Structure

Bangun struktur folder berikut:

```
tci-research/
├── AGENT.md
├── .env                          # API_KEY_OPENALEX, MAILTO (untuk polite pool)
├── .gitignore                    # jangan commit .env dan data mentah besar
├── requirements.txt
├── config.py                     # constants: institution ID, concept IDs, paths
│
├── data/
│   ├── raw/
│   │   ├── scimagojr.csv         # download manual
│   │   ├── works_raw.jsonl       # hasil pull OpenAlex, 1 JSON per line
│   │   └── authors_raw.jsonl
│   ├── interim/
│   │   ├── works_filtered.csv    # setelah filter Q1/Q2 + DOI aktif
│   │   └── corpus_per_author.csv # title+abstract gabungan per author
│   └── processed/
│       ├── topic_distribution.csv
│       └── tci_scores.csv
│
├── src/
│   ├── __init__.py
│   ├── fetch_works.py            # pull data works dari OpenAlex (paginated)
│   ├── extract_authors.py        # extract unique authors dari works
│   ├── join_scimago.py           # join ISSN -> tier jurnal
│   ├── verify_doi.py             # cek DOI aktif (CrossRef/HEAD request)
│   ├── reconstruct_abstract.py   # decode abstract_inverted_index -> teks
│   ├── preprocess_text.py        # cleaning, stopwords (EN + ID/Sastrawi)
│   ├── topic_model.py            # LDA training (gensim) + coherence eval
│   ├── compute_tci.py            # hitung Shannon entropy -> TCI per author
│   └── utils.py                  # helper: rate limiting, retry, logging
│
├── notebooks/
│   └── 01_explore_raw_data.ipynb # eksplorasi cepat sebelum dijadikan script
│
├── outputs/
│   ├── figures/
│   └── tci_ranking.csv
│
└── run_pipeline.py               # orchestrator, jalankan semua step berurutan
```

---

## Implementation Notes per Module

### `src/fetch_works.py`
- Gunakan `requests` dengan session + retry (exponential backoff untuk 429)
- Paginate pakai cursor: `&cursor=*` lalu ambil `meta.next_cursor` dari response, looping sampai `next_cursor` null
- Simpan tiap halaman langsung ke `.jsonl` (append mode) — supaya kalau script crash di tengah, tidak perlu pull ulang dari awal
- Selalu sertakan `mailto=email@domain.com` di parameter (bukan hanya api_key) — masuk ke "polite pool" OpenAlex, rate limit lebih baik
- Filter fields yang diambil pakai `select=` param untuk hemat bandwidth & cost:
  ```
  select=id,doi,title,publication_year,type,primary_location,authorships,abstract_inverted_index,cited_by_count
  ```

### `src/reconstruct_abstract.py`
- `abstract_inverted_index` adalah dict `{word: [posisi, ...]}` — perlu di-reverse jadi urutan kalimat
- Logic: bikin array kosong sepanjang max posisi + 1, isi tiap index dengan kata sesuai, join dengan spasi

### `src/join_scimago.py`
- Scimago CSV pakai `;` sebagai separator (bukan koma) — set `sep=";"` di `pd.read_csv`
- ISSN di OpenAlex field `primary_location.source.issn_l`, kadang null — fallback ke `issn` (list, ambil elemen pertama)
- Normalisasi format ISSN sebelum join (kadang ada dash kadang tidak): `XXXX-XXXX`

### `src/preprocess_text.py`
- Mixed language corpus (paper Indonesia + internasional) — deteksi bahasa dulu (pakai `langdetect`), baru pilih stopword set yang sesuai:
  - English → NLTK stopwords
  - Indonesian → Sastrawi (`pip install Sastrawi`)

### `src/topic_model.py`
- Pakai `gensim` untuk LDA
- Train pakai SELURUH corpus gabungan (semua author), bukan per-author — supaya topik konsisten dan bisa dibandingkan antar author
- Coherence score (`c_v`) untuk menentukan jumlah topik optimal — coba range k=5 sampai k=20, plot coherence vs k

### `src/compute_tci.py`
- Aggregate distribusi topik semua artikel per author (rata-rata atau jumlah, lalu normalisasi jadi distribusi probabilitas)
- Shannon entropy: `H = -sum(p * log2(p) for p in dist if p > 0)`
- `TCI = 1 - (H / log2(jumlah_topik))`

---

## Environment Setup

```bash
# requirements.txt minimal
requests
pandas
python-dotenv
gensim
nltk
Sastrawi
langdetect
tqdm
```

`.env` template:
```
OPENALEX_API_KEY=your_key_here
OPENALEX_MAILTO=your_email@domain.com
```

---

## Execution Order (run_pipeline.py orchestrates this)

1. `fetch_works.py` → `data/raw/works_raw.jsonl`
2. `extract_authors.py` → daftar unique author_id dari works
3. `join_scimago.py` → tambah kolom tier jurnal, filter Q1/Q2 → `data/interim/works_filtered.csv`
4. `verify_doi.py` → tambah kolom `doi_active`, drop yang false
5. Filter author dengan ≥5 artikel (lakukan di sini, setelah semua filter di atas)
6. `reconstruct_abstract.py` → tambah kolom `full_text` (title + abstract)
7. `preprocess_text.py` → tambah kolom `clean_tokens`
8. `topic_model.py` → train LDA, simpan model + `data/processed/topic_distribution.csv`
9. `compute_tci.py` → `outputs/tci_ranking.csv`

---

## Constraints & Reminders

- **Jangan hardcode API key** di script — selalu load dari `.env`
- **Rate limit awareness** — OpenAlex polite pool cukup longgar tapi tetap beri delay kecil (0.1–0.2s) antar request saat looping banyak author
- **Idempotency** — script fetch harus bisa di-resume, jangan re-fetch data yang sudah ada di `.jsonl`
- **Logging** — setiap step cetak progress (jumlah record diproses, jumlah yang di-drop dan kenapa) supaya mudah debug
- Scope BUKAN untuk improve metode LDA — pakai implementasi standar (gensim), fokus riset ada di **penerapan pipeline end-to-end** dan **interpretasi hasil TCI**, bukan di novelty algoritma
