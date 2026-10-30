# PayDefteri Instagram otomasyonu

Her gün 3 post: **12:30 görsel, 18:30 görsel, 21:30 üç günde bir reel (diğer günler görsel)** (Türkiye'de Instagram'ın genel olarak en yoğun olduğu öğle ve akşam saatleri).
**Her post önce Telegram'a önizleme olarak gelir; "✅ Paylaş"a basılmadan hiçbir şey yayınlanmaz.** 1 saat içinde cevap gelmezse post kuyrukta kalır ve bir sonraki saatte tekrar sorulur.

WhatsApp onayı isteğe bağlıdır: `~/instagram-poster/.whatsapp` dosyası varsa önizleme WhatsApp'a da gider, hangisinde önce basılırsa o geçerlidir. WhatsApp bozulursa Telegram mesajında uyarı çıkar, onay Telegram'dan devam eder. Meta buton yanıtlarını yalnızca açık bir adrese gönderdiği için `whatsapp-relay/` içindeki Cloudflare Worker yanıtı tutar, `ig_post.py` oradan okur. Karuselin diğer görselleri ve reel videosu, son 24 saatte WhatsApp'tan yazmadıysan gelmez; tam önizleme Telegram'dadır.

## Nasıl çalışır
| Parça | Ne yapar | Nerede |
|---|---|---|
| Windows Görev Zamanlayıcısı `\PayDefteri\Instagram-1230/1830/2130` | `paylas.py` çalıştırır: kuyruktaki sıradaki postu `ig_post.py` ile Telegram onayına gönderir; son reel 3+ gün önceyse 21:30'da reel, değilse görsel | PC'yi uykudan uyandırır; oturum açık olmalı, PC **kapalıysa** çalışmaz |
| Windows görevi `\PayDefteri\Uretim-Uyandir-2305` | PC'yi uykudan uyandırıp 90 dk uyanık tutar ki Claude gece üretimini yapabilsin | Aynı |
| Claude zamanlanmış görevi "PayDefteri Instagram içerik üretimi" (her gece 23:15) | Kuyrukta 6'dan az hazır post varsa gerçek ekranlardan yeni postlar üretir. **Paylaşmaz.** | Claude masaüstü uygulaması açıkken çalışır |

## Klasörler
- `kuyruk/` paylaşılmayı bekleyen postlar (`post.json` + `01.jpg…` veya `video.mp4`). Bir postu istemiyorsan klasörünü sil.
- `paylasilanlar/`, `reddedilenler/` (Telegram'da İptal), `hatali/` (3 kez hata veren)
- `gunluk.txt` her çalışmanın kaydı
- `motor/` şablonlar (`post.html`, `reel.html`), gerçek ekranlar (`assets/`), kırpımlar (`kirpimlar.js`), üretici (`uret.js`)
- `ICERIK-KURALLARI.md` içerik üretiminin kuralları (doğrulanmış özellik listesi dahil)

## Elle kullanım
```
node motor/uret.js kuyruk/<klasör>            # post.json'dan görsel/video üret
python paylas.py photo                         # sıradaki görseli şimdi Telegram onayına gönder
```
Durdurmak için: Görev Zamanlayıcısı'nda `PayDefteri` klasöründeki görevleri devre dışı bırak, Claude'da "Scheduled" bölümünden içerik görevini kapat.
