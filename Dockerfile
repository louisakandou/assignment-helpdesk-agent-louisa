
FROM python:3.11-slim
# Mulai dari "truk dasar": Linux mini yang sudah berisi Python 3.11.
# "slim" = versi ramping, ukurannya kecil.

WORKDIR /app
# Di dalam truk, buat dan masuk ke folder kerja bernama /app.
# Semua perintah berikutnya dijalankan dari folder ini.

COPY requirements.txt .
# Salin daftar belanja (requirements.txt) dari laptopmu ke /app di dalam image.

RUN pip install --no-cache-dir -r requirements.txt
# Belanja dan pasang semua library di DALAM image.
# --no-cache-dir = jangan simpan file sisa download, supaya image lebih kecil.

COPY app/ ./app/
COPY data/ ./data/
# Baru salin kode aplikasi dan data CSV ke dalam image.
# Sengaja HANYA dua folder ini: venv/ dan .env TIDAK ikut masuk.

EXPOSE 8000
# Catatan: aplikasi di dalam container memakai port 8000.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Perintah yang otomatis dijalankan saat container dinyalakan: nyalakan server API.