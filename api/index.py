"""Pintu masuk Vercel: membungkus aplikasi Flask di app.py.

Jika aplikasi gagal dimuat, halaman menampilkan penyebabnya (untuk debugging).
Setelah situs berjalan normal, blok `except` boleh dihapus.
"""
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from app import app  # Vercel mencari variabel `app`
except Exception:  # pragma: no cover
    _err = traceback.format_exc()
    _files = sorted(os.listdir(ROOT))

    def app(environ, start_response):
        body = ("Gagal memuat aplikasi Flask.\n\n" + _err +
                "\nIsi folder root fungsi: " + ", ".join(_files) +
                "\nPython: " + sys.version).encode("utf-8")
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [body]
