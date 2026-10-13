"""Jelajah Jabodetabek - direktori wisata Jakarta, Bogor, Depok, Tangerang, Bekasi.

Data ada di DESTINATIONS dan diakses lewat fungsi repository (all_destinations,
find_destination, search_destinations). Untuk pindah ke SQLite, cukup ganti isi
tiga fungsi itu dengan query; route dan template tidak perlu diubah.
"""
from urllib.parse import quote_plus
from flask import Flask, abort, jsonify, render_template, request, url_for

app = Flask(__name__, static_folder="public/static", static_url_path="/static")  # public/ dilayani CDN Vercel

REGIONS = ["Jakarta", "Bogor", "Depok", "Tangerang", "Bekasi"]
CATEGORIES = ["Alam", "Sejarah & Budaya", "Keluarga & Rekreasi", "Belanja & Kuliner"]
CAT_CLASS = {"Alam": "c-alam", "Sejarah & Budaya": "c-sejarah",
             "Keluarga & Rekreasi": "c-keluarga", "Belanja & Kuliner": "c-belanja"}
CAT_BLURB = {"Alam": "Hutan, danau, curug, dan mangrove",
             "Sejarah & Budaya": "Monumen, kota lama, dan museum",
             "Keluarga & Rekreasi": "Taman bermain dan wisata akhir pekan",
             "Belanja & Kuliner": "Pusat belanja dan tempat makan"}


def _d(slug, name, region, category, area, address, short, about, hours, price, tip, featured=False):
    # verified=False: alamat, jam, dan harga ditulis dari pengetahuan umum dan WAJIB dicek ulang.
    return dict(slug=slug, name=name, region=region, category=category, area=area,
                address=address, short=short, about=about, hours=hours, price=price,
                tip=tip, featured=featured, verified=False)


DESTINATIONS = [
    _d("taman-mini-indonesia-indah", "Taman Mini Indonesia Indah", "Jakarta", "Keluarga & Rekreasi",
       "Cipayung", "Jl. Raya Taman Mini, Ceger, Cipayung, Jakarta Timur",
       "Miniatur budaya Nusantara lengkap dengan anjungan daerah dan museum.",
       "Kompleks luas berisi anjungan rumah adat dari berbagai provinsi, museum, taman, dan wahana keluarga. Cocok untuk sehari penuh.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Tiket masuk dan wahana terpisah; cek situs resmi",
       "Sewa sepeda atau naik kereta gantung untuk menghemat tenaga.", True),
    _d("monumen-nasional", "Monumen Nasional (Monas)", "Jakarta", "Sejarah & Budaya",
       "Gambir", "Jl. Medan Merdeka, Gambir, Jakarta Pusat",
       "Tugu ikonik Jakarta dengan taman kota dan museum sejarah di dasarnya.",
       "Monas dikelilingi taman luas untuk jalan santai. Pengunjung bisa masuk ke area museum dan naik ke pelataran puncak.",
       "Umumnya buka pagi hingga malam; jadwal tiap area bisa berbeda (perkiraan)", "Area taman biasanya gratis; naik tugu berbayar",
       "Datang pagi hari agar antrean ke puncak lebih pendek.", True),
    _d("kota-tua-jakarta", "Kota Tua Jakarta", "Jakarta", "Sejarah & Budaya",
       "Pinangsia", "Taman Fatahillah, Pinangsia, Taman Sari, Jakarta Barat",
       "Kawasan bangunan kolonial, museum, dan kafe di sekitar Taman Fatahillah.",
       "Berjalan kaki dari Museum Sejarah Jakarta ke museum lain, lalu berhenti di kafe. Akhir pekan ramai pengamen dan penyewaan sepeda.",
       "Kawasan terbuka; jam museum berbeda-beda", "Kawasan gratis; museum berbayar",
       "Pilih hari kerja jika ingin suasana lebih tenang.", True),
    _d("mangrove-angke-kapuk", "Taman Wisata Alam Mangrove Angke Kapuk", "Jakarta", "Alam",
       "Penjaringan", "Kamal Muara, Penjaringan, Jakarta Utara",
       "Jalur kayu di tengah hutan mangrove di pesisir utara Jakarta.",
       "Susuri jembatan kayu di antara pohon bakau, lalu lanjut dengan perahu atau titik pandang ke arah laut.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Tiket masuk berbayar; cek loket",
       "Bawa topi dan air minum; area ini terbuka dan panas.", True),
    _d("taman-impian-jaya-ancol", "Taman Impian Jaya Ancol", "Jakarta", "Keluarga & Rekreasi",
       "Pademangan", "Jl. Lodan Timur No.7, Ancol, Pademangan, Jakarta Utara",
       "Kawasan pantai dengan taman bermain, akuarium, dan jalur sepeda.",
       "Ancol menggabungkan area pantai, wahana, dan tempat makan di satu kompleks tepi laut.",
       "Umumnya buka sepanjang hari; wahana punya jadwal sendiri (perkiraan)", "Tiket gerbang dan wahana terpisah; cek situs resmi",
       "Beli tiket daring lebih dulu jika tersedia."),
    _d("kebun-raya-bogor", "Kebun Raya Bogor", "Bogor", "Alam",
       "Paledang", "Jl. Ir. H. Juanda No.13, Paledang, Bogor Tengah, Kota Bogor",
       "Kebun botani tua dengan pohon-pohon besar, danau, dan taman tematik.",
       "Salah satu kebun botani tertua di Asia Tenggara. Cocok untuk piknik, jalan santai, dan fotografi.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Tiket masuk berbayar; cek loket",
       "Datang sebelum siang; hujan sore sering turun di Bogor.", True),
    _d("taman-safari-indonesia", "Taman Safari Indonesia", "Bogor", "Keluarga & Rekreasi",
       "Cisarua", "Jl. Raya Puncak No.601, Cibeureum, Cisarua, Kabupaten Bogor",
       "Safari berkendara dan taman satwa di kawasan Puncak.",
       "Lihat satwa dari dalam kendaraan, lalu lanjut ke area pertunjukan dan kebun binatang mini.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Tiket berbayar; cek situs resmi",
       "Hindari akhir pekan panjang agar tidak terjebak macet Puncak.", True),
    _d("curug-cilember", "Curug Cilember", "Bogor", "Alam",
       "Cisarua", "Kp. Bojong Murni, Cisarua, Kabupaten Bogor",
       "Rangkaian air terjun di lereng Puncak dengan jalur trekking ringan.",
       "Jalur menanjak melewati beberapa curug. Sebagian jalur licin saat hujan.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Tiket masuk berbayar; cek di lokasi",
       "Pakai sepatu dengan grip yang baik."),
    _d("gunung-pancar", "Gunung Pancar", "Bogor", "Alam",
       "Babakan Madang", "Karang Tengah, Babakan Madang, Kabupaten Bogor",
       "Hutan pinus untuk berkemah, bersepeda, dan bersantai.",
       "Area perbukitan dekat Sentul dengan hutan pinus dan pemandangan terbuka.",
       "Umumnya buka pagi hingga sore; kemah punya aturan sendiri (perkiraan)", "Tiket masuk dan kemah berbayar",
       "Tanyakan kondisi jalan sebelum membawa mobil rendah."),
    _d("danau-kenanga-ui", "Danau Kenanga Universitas Indonesia", "Depok", "Alam",
       "Beji", "Kampus UI, Pondok Cina, Beji, Kota Depok",
       "Danau di kampus UI yang cocok untuk joging dan piknik.",
       "Danau dikelilingi pepohonan dan jalur jalan kaki. Sering dipakai untuk berolahraga sore hari.",
       "Aturan akses kampus dapat berubah (perkiraan)", "Aturan masuk kampus bisa berbeda; cek lebih dulu",
       "Cek aturan kendaraan masuk kampus sebelum datang."),
    _d("depok-lama-gereja-immanuel", "Kawasan Depok Lama dan Gereja Immanuel", "Depok", "Sejarah & Budaya",
       "Pancoran Mas", "Jl. Pemuda, Pancoran Mas, Kota Depok",
       "Jejak sejarah kota Depok lewat bangunan lama dan gereja tua.",
       "Jalan kaki di kawasan Depok Lama untuk melihat bangunan peninggalan masa kolonial. Hormati aktivitas ibadah.",
       "Jam kunjungan gereja menyesuaikan kegiatan (perkiraan)", "Umumnya tidak ada tiket; cek di lokasi",
       "Hubungi pengelola jika ingin masuk ke dalam gereja."),
    _d("pantai-tanjung-pasir", "Pantai Tanjung Pasir", "Tangerang", "Alam",
       "Teluknaga", "Tanjung Pasir, Teluknaga, Kabupaten Tangerang",
       "Pantai sederhana di pesisir utara Tangerang dengan warung seafood.",
       "Suasana khas kampung nelayan. Fasilitas apa adanya, cocok untuk yang suka suasana lokal.",
       "Umumnya buka siang hari (perkiraan)", "Retribusi kecil; cek di lokasi",
       "Bawa uang tunai untuk warung dan parkir."),
    _d("museum-benteng-heritage", "Museum Benteng Heritage", "Tangerang", "Sejarah & Budaya",
       "Pasar Lama", "Jl. Cilame No.17, Pasar Lama, Kota Tangerang",
       "Museum budaya Cina Benteng di kawasan Pasar Lama.",
       "Bangunan tua yang menyimpan koleksi tentang sejarah dan budaya komunitas Tionghoa Benteng.",
       "Jam buka bisa berubah (perkiraan)", "Tiket masuk berbayar; cek di lokasi",
       "Gabungkan dengan jajan di Pasar Lama."),
    _d("situ-gintung", "Situ Gintung", "Tangerang", "Alam",
       "Ciputat", "Cireundeu, Ciputat Timur, Tangerang Selatan",
       "Danau di Tangerang Selatan untuk bersantai dan memancing.",
       "Area tepi danau dengan pepohonan, jalur jalan kaki, dan warung.",
       "Umumnya buka pagi hingga sore (perkiraan)", "Retribusi kecil; cek di lokasi",
       "Sore hari lebih sejuk."),
    _d("pantai-bahagia-muara-gembong", "Pantai Bahagia dan Mangrove Muara Gembong", "Bekasi", "Alam",
       "Muara Gembong", "Muara Gembong, Kabupaten Bekasi",
       "Kawasan pesisir dan mangrove di ujung utara Bekasi.",
       "Perjalanan ke sini sendiri sudah petualangan: jalan darat dan perahu menuju area mangrove dan pantai.",
       "Umumnya siang hari; cek kondisi akses (perkiraan)", "Biaya perahu dan retribusi bervariasi",
       "Berangkat pagi dan tanyakan akses jalan lebih dulu."),
    _d("summarecon-mall-bekasi", "Summarecon Mall Bekasi", "Bekasi", "Belanja & Kuliner",
       "Bekasi Utara", "Jl. Bulevar Ahmad Yani, Harapan Indah, Bekasi Utara, Kota Bekasi",
       "Pusat belanja dan kuliner di kawasan Summarecon Bekasi.",
       "Pilihan toko, bioskop, dan restoran, cocok untuk jalan sore.",
       "Umumnya buka siang hingga malam (perkiraan)", "Masuk gratis; parkir berbayar",
       "Ramai di akhir pekan sore."),
]


# ---------- Repository (ganti isi fungsi ini saat pindah ke SQLite) ----------
def all_destinations():
    return DESTINATIONS


def find_destination(slug):
    return next((d for d in all_destinations() if d["slug"] == slug), None)


def search_destinations(q="", region="", category="", featured=False):
    q = q.strip().lower()
    out = []
    for d in all_destinations():
        if q and q not in d["name"].lower():
            continue
        if region and d["region"] != region:
            continue
        if category and d["category"] != category:
            continue
        if featured and not d["featured"]:
            continue
        out.append(d)
    return out


def public(d):
    q = quote_plus(f'{d["name"]} {d["region"]}')
    return {**d, "cat_class": CAT_CLASS[d["category"]],
            "image": url_for("static", filename=f'images/{d["slug"]}.jpg'),
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={q}"}


@app.context_processor
def inject():
    return dict(REGIONS=REGIONS, CATEGORIES=CATEGORIES, CAT_BLURB=CAT_BLURB, CAT_CLASS=CAT_CLASS)


@app.route("/")
def index():
    counts = {r: sum(1 for d in all_destinations() if d["region"] == r) for r in REGIONS}
    return render_template("index.html", counts=counts, total=len(all_destinations()))


@app.route("/destinasi")
def destinations():
    return render_template("destinations.html")


@app.route("/destinasi/<slug>")
def detail(slug):
    d = find_destination(slug)
    if d is None:
        abort(404)
    return render_template("detail.html", d=public(d))


@app.route("/favorit")
def favorites():
    return render_template("favorites.html")


@app.route("/rencana")
def itinerary():
    return render_template("itinerary.html")


@app.route("/api/destinations")
def api_destinations():
    items = search_destinations(request.args.get("q", ""), request.args.get("region", ""),
                                request.args.get("category", ""), request.args.get("featured") == "1")
    return jsonify(count=len(items), items=[public(d) for d in items])


@app.errorhandler(404)
def not_found(_):
    # Info diagnostik sementara; hapus `dbg` setelah deploy normal.
    dbg = {
        "request.path": request.path,
        "PATH_INFO": request.environ.get("PATH_INFO"),
        "QUERY_STRING": request.environ.get("QUERY_STRING"),
        "SCRIPT_NAME": request.environ.get("SCRIPT_NAME"),
        **{k: v for k, v in request.headers.items() if k.lower().startswith(("x-vercel", "x-matched", "x-forwarded-uri"))},
    }
    return render_template("404.html", dbg=dbg), 404


if __name__ == "__main__":
    app.run(debug=True)
