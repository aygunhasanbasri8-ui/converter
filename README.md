# Video İndirici

Yapıştırdığın bağlantıdaki videoyu **MP4** (video + ses) veya **MP3** (192 kbps ses)
olarak indiren, tamamen kendi makinende çalışan küçük bir uygulama.

## Kurulum

Önce `ffmpeg` kur:

| Sistem | Komut |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Ubuntu | `sudo apt install ffmpeg` |

Ardından Python paketlerini kurup uygulamayı başlat:

```bash
pip install -r requirements.txt
python main.py
```

Tarayıcıda `http://127.0.0.1:8000` adresini aç.

## Yapı

- `main.py`: Uvicorn başlatıcısı.
- `app/main.py`: FastAPI uygulaması ve HTTP uçları.
- `app/downloader.py`: yt-dlp işlemleri ve çıktı seçimi.
- `app/jobs.py`: İş durumu, sınırlı worker havuzu ve dosya temizliği.
- `app/models.py`: API istek modelleri ve URL doğrulaması.
- `app/errors.py`: Kullanıcıya gösterilecek hata mesajları.
- `app/config.py`: Dizin, süre ve worker ayarları.
- `static/index.html`: Tek arayüz kaynağı.

Her indirme `downloads/<job_id>/` altında tutulur ve bir saat sonra otomatik silinir.
İş sayısı aynı anda `MAX_WORKERS` ile sınırlandırılır.

## Akış

1. Bağlantı girildiğinde `POST /api/info` başlık, süre ve kapak görselini getirir.
2. `POST /api/download` bir iş kaydı oluşturur ve indirmeyi worker havuzuna verir.
3. Arayüz `GET /api/progress/{job_id}` ucunu 600 ms'de bir yoklar.
4. İş hazır olduğunda dosya `GET /api/file/{job_id}` üzerinden kaydedilir.

## Ayarlar

| Ayar | Dosya |
|---|---|
| MP3 bit hızı | `app/downloader.py` |
| MP4 kalite seçimi | `app/downloader.py` |
| Dosya saklama süresi | `app/config.py` |
| Worker sayısı | `app/config.py` |
| Port | `main.py` |

Sunucu yalnızca `127.0.0.1` üzerinde dinler. Uygulamayı ağa açmadan önce kimlik
doğrulama, erişim kontrolü ve daha sıkı kaynak sınırları eklenmelidir.

Araç yalnızca sana ait olan ya da indirmesine izin verilen içerikler için tasarlanmıştır.
Platformların kullanım şartları ve telif kuralları senin sorumluluğundadır.
