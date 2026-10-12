"""Pintu masuk Vercel: membungkus aplikasi Flask di app.py.

vercel.json mengalihkan semua alamat ke /api/index?__p=<alamat asli>. Middleware di
bawah memulihkan alamat asli supaya rute Flask (/, /destinasi, ...) cocok.
Jika aplikasi gagal dimuat, halaman menampilkan penyebabnya (untuk debugging).
"""
import os
import sys
import traceback
from urllib.parse import parse_qsl, urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def restore_path(wsgi):
    def middleware(environ, start_response):
        if environ.get("PATH_INFO", "").startswith("/api/index"):
            qs = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
            orig = next((v for k, v in qs if k == "__p"), "")
            environ["PATH_INFO"] = "/" + orig.lstrip("/")
            environ["QUERY_STRING"] = urlencode([(k, v) for k, v in qs if k != "__p"])
        return wsgi(environ, start_response)
    return middleware


try:
    from app import app  # Vercel mencari variabel `app`
    app.wsgi_app = restore_path(app.wsgi_app)
except Exception:  # pragma: no cover
    _err = traceback.format_exc()
    _files = sorted(os.listdir(ROOT))

    def app(environ, start_response):
        body = ("Gagal memuat aplikasi Flask.\n\n" + _err +
                "\nIsi folder root fungsi: " + ", ".join(_files) +
                "\nPython: " + sys.version).encode("utf-8")
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [body]
