# PayDefteri içerik kuralları (kuyruğu dolduran görev bunu okur)

## Kesin kurallar
1. **Telegram onayı:** Hiçbir post onaysız paylaşılmaz. Paylaşım yalnızca `paylas.py` → `ig_post.py` ile yapılır; bu betik önce Telegram'a önizleme gönderir ve sahibi "Paylaş"a basmadan yayınlamaz. Kuyruk görevi **asla** kendisi paylaşım yapmaz, `ig_post.py`'yi çağırmaz.
2. **Sadece gerçek ürün:** Görsellerde yalnızca `motor/assets/` içindeki gerçek uygulama ekranları ve `motor/kirpimlar.js` içindeki kırpımlar kullanılır. Sahte arayüz, uydurma ekran, uydurma rakam yok.
3. **Sadece doğrulanmış özellikler** (Google Play sayfası, paydefteri.com ve uygulama ekranlarından):
   - Ortak plan oluşturma, ortak davet etme, davetleri kabul etme, planlar arası geçiş, hazır şablonlar
   - Gider ekleme; tarih, kategori, ödeyen kişi ve kişi başı pay; düzenleme/silme
   - Gider arama, Filtre, "Ödenenler" / "Planlananlar"
   - Bakiyeler & Mahsuplaşma: net bakiye (pozitif = alacaklı, negatif = borçlu), "Açık bakiye var"
   - Transfer (mahsup): borçlunun alacaklıya gönderdiği tutarı kaydetme
   - Kredi kartı ekstresi içe aktarma (PDF), ekstre nabzı, toplam harcama, işlem sayısı, en büyük harcama, en yüksek kategori; yapay zekâ destekli harcama analizi
   - Fiş fotoğrafı ekleme (Play "Yenilikler" metninde geçiyor; ekran görüntüsü yok, yalnızca metinde anılabilir)
   - Ortak taksit / tasarruf finansmanı (FuzulEv, Eminevim, araç/konut kredileri): kalan pay, teslimat vadesi, kim ödedi işaretleme
   - Google ile giriş, e-posta ile kayıt, 256-bit SSL ile veri koruma
   - Android uygulaması Google Play'de: `com.paydefteri.app`; web: paydefteri.com
   Bunların dışında özellik, fiyat, kullanıcı sayısı, yorum, ödül veya iş birliği **uydurma**.
4. **Marka:** "PayDefteri" yazımı; renkler/fontlar şablonlarda hazır.
   **Sessiz video asla üretilmez.** Her reel'de Dilara seslendirmesi olur (ElevenLabs, voice_id `D2dHiTSPRx6l2bhKGmyJ`, model `eleven_v4`, generations_count 1). Kurallar:
   - Her sahnenin `metin` alanı o sahnede söylenecek cümledir (bir sahne = bir cümle; son sahne en çok iki kısa cümle). Seslendirmeye bu metinler aralarında boşlukla, aynen ve tek parça gönderilir. Kesip birleştirme yok, duygu etiketi ([excited] vb.) yok.
   - Seslendirme metninde marka her zaman küçük harfle "pay defteri" yazılır (yoksa İngilizce "pey" okunur) ve cümle "Pay" ile başlamaz. Ekrandaki yazı "PayDefteri" kalır.
   - Tonu samimi, konuşur gibi; reel toplam 15-22 sn (yaklaşık 45-60 kelime).
   - Üretilen sesi `creative_get_flow_run_status` ile alınan `content_url` adresinden `kuyruk/<klasör>/ses.mp3` olarak indir. `uret.js` sahne sürelerini bu sesin duraklarından kendisi hesaplar (`dur` yazma); `ses.mp3` yoksa reel üretmez.
5. **Dil:** Türkçe, samimi, kısa. Her açıklama: dikkat çekici ilk cümle → 2-4 maddelik fayda → CTA → 6-9 hashtag (#PayDefteri her zaman).
6. **Google Play'den her postta bahsetme.** "Android'de / Google Play'de yayında" mesajı en çok 3 posttan 1'inde olsun; diğerlerinde CTA etkileşim odaklı olsun (kaydet, etiketle, yorum sorusu) ya da yumuşak: `👉 PayDefteri'ni denemek için bağlantı profilde.`
   Google Play'den bahseden her postta açıklamaya linki yaz (arama ile bulunması henüz zor): `👉 Android'de ücretsiz indir: https://play.google.com/store/apps/details?id=com.paydefteri.app` ve görselde/reel sonunda `play: true`. "Google Play'de PayDefteri ara" ifadesini kullanma.
7. **Tekrar yok:** `paylasilanlar/`, `reddedilenler/` ve `kuyruk/` içindeki `post.json` dosyalarının `konu` alanlarına bak; aynı açıyı aynı hafta tekrar etme. Reddedilenlerden ders çıkar (o tarzı tekrarlama).

## Amaç ve marka kimliği
Amaç: sayfayı büyütmek (takipçi, kaydetme, paylaşım) ve uygulamaya indirme getirmek. İyi performans gösteren postlar ileride ücretli reklama dönüştürülecek, bu yüzden her post tek başına reklam kalitesinde olmalı.

**Marka kimliğinden çıkma:**
- Görsel dil yalnızca `motor/` şablonlarındaki gibi: koyu lacivert zemin (#090D16), mor gradyan (#7C3AED → #A78BFA), lila/indigo vurgular, nane yeşili (#34D399) yalnızca küçük vurgu; Outfit başlık, Inter metin; logo ve "PayDefteri" yazımı. Yeni renk, font, stok fotoğraf, emoji yağmuru, meme şablonu yok.
- Ton: samimi, sakin, güven veren, akıllı finans uygulaması. "Sen" diliyle konuş. Abartı, korkutma, "zengin ol" vaatleri, agresif satış dili, yanıltıcı clickbait yok.
- Her postun tek bir net mesajı olsun.

**Dikkat çekme ve büyüme:**
- İlk 1-2 saniye / ilk satır kazanır: reel `hook` sahnesi ve açıklamanın ilk cümlesi tanıdık bir derde dokunsun ("Faturayı yine kim ödedi?", "Ay sonu hesap kavgası mı?"). Başlık kısa, büyük, merak uyandıran.
- Hedef kitle senaryoları: ev arkadaşları, öğrenci evi, çiftler, kardeşler, aile bütçesi, arkadaşlarla tatil, ortak taksit (FuzulEv/Eminevim), kredi kartı kullanan çalışanlar. Kendini görsün.
- Kaydetme/paylaşma tetikleyicisi: işe yarayan mini rehber, ipucu, adım adım; "Kaydet", "ev arkadaşını etiketle", "bunu ona gönder" çağrıları (her postta değil, dönüşümlü).
- Yorum tetikleyicisi: zaman zaman basit bir soru ("Sizin evde faturayı kim öder? 👇").
- Carousel: kapak merak uyandırır, son slayt indirme çağrısı. Reel: hızlı tempo, her sahne tek fikir, sonda logo (Google Play rozeti yalnızca `play: true` ile).
- Görsellerin ana öğesi her zaman gerçek uygulama ekranı; ürünü göster, anlatma.
- Hashtag: #PayDefteri + konuya uygun 5-8 Türkçe etiket; her postta aynı seti kopyalama.

## Format karışımı (günde 3 post: 12:30 ve 18:30 görsel; 21:30 üç günde bir reel, diğer günler görsel)
- Kuyrukta en fazla 1 hazır reel bulunsun; geri kalan her şey görsel. Reel seyrek olduğu için her reel en güçlü konulardan biri olsun.
- Görsel türleri dönüşümlü: tek görsel (`kart`, `telefon`, `liste`) ve carousel (`kapak` + 2-4 slayt + `son`).
- Reel: 4-6 sahne, 14-20 sn, `hook` ile başlar, `son` ile biter.
- İçerik açıları: problem→çözüm, "biliyor muydun?" ipucu, adım adım kullanım, senaryo (ev arkadaşı, çift, kardeş, tatil, ortak taksit, öğrenci evi), mini rehber, kaydet/paylaş çağrısı.

## post.json biçimi
```json
{
  "type": "photo" | "reel",
  "konu": "kısa konu etiketi (tekrar kontrolü için)",
  "caption": "Instagram açıklaması",
  "slides": [ ... ],   // photo: 1-10 slayt
  "scenes": [ ... ]    // reel
}
```
Metin işaretleri: `\n` satır sonu, `*metin*` marka gradyanı, `**metin**` kalın.

**Slayt düzenleri** (`layout`):
- `telefon`: eyebrow, title, sub, `screen`, `crops` (en çok 2)
- `kart`: eyebrow, title, sub, `crop` (1), `note` (isteğe bağlı)
- `liste`: eyebrow, title, `items` (en çok 3; `t`, `d`, isteğe bağlı `crop`)
- `kapak`: carousel ilk slaytı; eyebrow, title, sub, `screen`, `hint`
- `son`: kapanış; isteğe bağlı title, sub, `play` (true: Google Play rozeti)
- Ortak: `cta` (true: altta Google Play rozetli çağrı çubuğu; varsayılan kapalı, yalnızca Play'den bahseden postlarda aç), `ctaTitle`, `tema` (0-2)

**Reel kapağı** (`kapak`, her reel'de zorunlu): profil ızgarasında görünen tek kare; dikkat çekici olmalı.
- `eyebrow`: kime hitap ettiği, 2-3 kelime büyük harf ("EV ARKADAŞLARI İÇİN", "ORTAK TAKSİT")
- `title`: en çok 2 satır, satır başına 2-3 kelime; soru, şaşırtan bir rakam ya da net bir vaat. İkinci satır `*gradyan*`. Rakam kullanırsan kırpımda görünen rakamla aynı olsun.
- `crop`: kapağın ana öğesi olan gerçek UI kartı; rakam, renk veya karşıtlık içeren bir kırpım seç (alacaklı/borçlu, toplam harcama, kalan pay)
- `screen`: arkadaki telefonun ekranı
**Reel sahneleri** (`kind`): `hook` (title, sub, metin), `ekran` (title, sub, `screen`, `crops` en çok 2, metin), `son` (sub, `play`, metin). Süreler sesten gelir.

Ekranlar: takip, bakiye, analiz, planlar, onboarding, giris. Kırpım adları `motor/kirpimlar.js` içinde.
Başlık en çok 2 satır, satır başına ~16 karakter (telefon/liste) veya ~20 karakter (kart/kapak).

## Üretim ve kontrol
1. Yeni klasör: `kuyruk/<sonraki 3 haneli numara>-<kisa-slug>/post.json`
2. Reel ise önce seslendirmeyi üret ve `ses.mp3` olarak indir. Sonra `node motor/uret.js kuyruk/<klasör>` (reel için önce `--onizleme` ile kareleri kontrol et, sonra tam üret). Reel videosunun ses akışı olduğunu kontrol et. Tam üretim `kapak.jpg` (profil ızgarasında görünen kapak) da yazar; kapağı aç ve kontrol et: ilk sahnenin başlığı kısa ve okunur olmalı, çünkü kapakta da o başlık kullanılır.
3. Üretilen her JPEG'e / önizleme karesine bak: taşma, üst üste binme, okunmayan metin varsa düzelt ve yeniden üret. `onizleme-*.jpg` dosyalarını sil.
