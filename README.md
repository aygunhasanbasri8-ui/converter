# Video İndirici

Bağlantısını verdiğin videoyu **MP4** (video + ses) ya da **MP3** (192 kbps ses)
olarak indiren, tamamen kendi makinende çalışan küçük bir uygulama. İndirmeyi
yt-dlp, dönüştürmeyi ffmpeg yapıyor.

## Kurulum

ffmpeg şart; MP3 dönüşümü ve MP4'te ses ile görüntünün birleştirilmesi onunla
yapılıyor.

| Sistem | Komut |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Ubuntu | `sudo apt install ffmpeg` |

Sonra Python paketlerini kurup uygulamayı başlat:

```bash
pip install -r requirements.txt
python main.py
```

Tarayıcıda `http://127.0.0.1:8000` adresini aç.

Testler için:

```bash
python -m unittest discover -s tests
```

## Yapı

- `main.py`: Uvicorn'u başlatır.
- `app/main.py`: FastAPI uygulaması ve HTTP uçları.
- `app/downloader.py`: yt-dlp ayarları, indirme ve çıktı dosyasının bulunması.
- `app/jobs.py`: İş kayıtları, worker havuzu ve eski dosyaların temizliği.
- `app/models.py`: İstek modelleri ve URL doğrulaması.
- `app/errors.py`: yt-dlp hatalarını kullanıcının anlayacağı mesajlara çevirir.
- `app/config.py`: Dizinler, süreler ve worker sayısı.
- `static/index.html`: Arayüz.

Her indirme `downloads/<job_id>/` altına iner ve bir saat sonra silinir. Aynı
anda en fazla `MAX_WORKERS` kadar indirme çalışır, fazlası sırada bekler.

## Akış

1. Bağlantı yapıştırılınca `POST /api/info` başlık, süre ve kapak görselini getirir.
2. `POST /api/download` bir iş kaydı açar ve indirmeyi worker havuzuna verir.
3. Arayüz `GET /api/progress/{job_id}` ucunu 600 ms'de bir yoklar.
4. İş bitince dosya `GET /api/file/{job_id}` üzerinden kaydedilir.

MP4 seçiliyken kaynakta MP4 yoksa yt-dlp eldeki en iyi biçimi indirir; dosya
uzantısı o yüzden farklı olabilir.

## Ayarlar

| Ayar | Dosya |
|---|---|
| MP3 bit hızı, MP4 kalite seçimi | `app/downloader.py` |
| Dosya saklama süresi, worker sayısı | `app/config.py` |
| Port | `main.py` |

Sunucu bilerek yalnızca `127.0.0.1` üzerinde dinliyor. Ağa açacaksan önce kimlik
doğrulama, erişim kontrolü ve daha sıkı kaynak sınırları eklemen gerekir; yoksa
ağdaki herkes senin makinen üzerinden istediği adrese istek attırabilir.

## Not

Sadece sana ait ya da indirilmesine izin verilen içerikler için kullan.
Platformların kullanım şartlarına ve telif kurallarına uymak senin sorumluluğunda.

## Lisans

[MIT](LICENSE)
