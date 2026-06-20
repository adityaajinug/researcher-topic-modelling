# Cara Menjalankan Pipeline TCI

## Prasyarat

- Python 3.10 atau lebih baru
- Koneksi internet (untuk fetch data OpenAlex & verifikasi DOI)

---

## 1. Install Dependensi

Buka terminal di folder project ini, lalu jalankan:

```bash
pip install -r requirements.txt
```

---

## 2. Isi File `.env`

Buka file `.env`, ganti isinya dengan API key dan email kamu:

```
OPENALEX_API_KEY=isi_api_key_kamu_di_sini
OPENALEX_MAILTO=email_kamu@domain.com
```

> **Cara dapat API key OpenAlex:** daftar gratis di https://openalex.org/settings/api
>
> **Kenapa perlu email?** OpenAlex kasih rate limit lebih longgar kalau kita kasih tahu email (disebut "polite pool").

---

## 3. Download Data Scimago

1. Buka https://www.scimagojr.com/journalrank.php
2. Klik tombol **Download** (pojok kanan bawah tabel)
3. Simpan file CSV yang didownload ke:

```
data/raw/scimagojr.csv
```

> File ini pakai separator titik koma (`;`), bukan koma — sudah ditangani otomatis oleh script.

---

## 4. Jalankan Pipeline

### Cara cepat — jalankan semua sekaligus:

```bash
python run_pipeline.py
```

Pipeline akan berjalan 8 langkah secara berurutan dan mencetak progress di terminal.

---

### Cara manual — jalankan per step (kalau mau debug):

```bash
# Step 1 — Ambil data works dari OpenAlex
python -m src.fetch_works

# Step 2 — Extract daftar author unik
python -m src.extract_authors

# Step 3 — Join dengan Scimago, filter Q1/Q2
python -m src.join_scimago

# Step 4 — Verifikasi DOI aktif
python -m src.verify_doi

# Step 5 — Rekonstruksi abstrak + bangun corpus
python -m src.reconstruct_abstract

# Step 6 — Preprocessing teks
python -m src.preprocess_text

# Step 7 — Training LDA topic model
python -m src.topic_model

# Step 8 — Hitung TCI per author
python -m src.compute_tci
```

> Kalau script crash di tengah jalan (misal Step 1), kamu bisa langsung run ulang dari step yang sama — script sudah dirancang **resumable** (tidak re-fetch data yang sudah ada).

---

## 5. Cek Hasil

| File output | Isi |
|---|---|
| `data/interim/works_filtered.csv` | Works setelah filter Q1/Q2 + DOI aktif |
| `data/interim/corpus_per_author.csv` | Teks lengkap per artikel per author |
| `data/processed/topic_distribution.csv` | Distribusi topik tiap artikel |
| `outputs/tci_ranking.csv` | **Ranking TCI per author (hasil akhir)** |

---

## Estimasi Waktu

| Step | Estimasi |
|---|---|
| Fetch works | 5–15 menit (tergantung jumlah data) |
| Verifikasi DOI | 10–30 menit (ada HTTP request per DOI) |
| Training LDA | 5–20 menit (tergantung jumlah dokumen & range k) |
| Lainnya | < 1 menit per step |

---

## Troubleshooting

**Error: `ModuleNotFoundError`**
```bash
pip install -r requirements.txt
```

**Error: `scimagojr.csv not found`**
→ Pastikan sudah download dan simpan di `data/raw/scimagojr.csv`

**Error: `OPENALEX_API_KEY`**
→ Pastikan file `.env` sudah diisi dan ada di folder root project

**Step fetch sangat lambat / sering 429**
→ Pastikan `OPENALEX_MAILTO` di `.env` sudah diisi email yang valid
