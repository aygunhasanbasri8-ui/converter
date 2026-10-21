import re


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class QuietLogger:
    """yt-dlp'nin kendi çıktısını yutar; hatalar zaten istisna olarak geliyor."""

    def debug(self, message: str) -> None:
        return None

    def info(self, message: str) -> None:
        return None

    def warning(self, message: str) -> None:
        return None

    def error(self, message: str) -> None:
        return None


def readable_error(error: Exception) -> str:
    raw_message = ANSI_ESCAPE.sub("", str(error)).strip()
    message = raw_message.lower()

    # Sıra önemli, ilk eşleşen kazanır.
    messages = (
        (("ffmpeg", "ffprobe"), "ffmpeg bulunamadi. Kurup PATH'e ekledikten sonra tekrar dene."),
        (("unsupported url", "is not a valid url"), "Bu bağlantı desteklenmiyor. Adresi kontrol et."),
        (("private video", "members-only"), "Video özel ya da üyelere kapalı, indirilemiyor."),
        (("video unavailable", "removed"), "Video yayından kalkmış görünüyor."),
        (("sign in", "confirm your age", "cookies"), "Bu içerik oturum açmayı gerektiriyor, indirilemiyor."),
        (("requested format is not available",), "Seçtiğin biçim bu içerik için mevcut değil. Diğer biçimi dene."),
        (("unable to download", "timed out", "connection"), "Bağlantı kurulamadı. İnternetini kontrol edip tekrar dene."),
    )
    for indicators, user_message in messages:
        if any(indicator in message for indicator in indicators):
            return user_message

    last_line = raw_message.splitlines()[-1] if raw_message else "Bilinmeyen hata"
    return last_line.replace("ERROR:", "").strip()[:200] or "İndirme tamamlanamadı."
