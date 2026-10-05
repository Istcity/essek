# 🏇 TJK AI - Yapay Zeka Destekli At Yarışı Tahmin ve Analiz Platformu

> **TJK günlük yarış bültenlerini, koşu mesafelerini, pist uyumunu ve galop istatistiklerini en ileri uluslararası yarış modellemeleriyle (Beyer Speed Figures, Timeform, Outlier Filtering) analiz eden web tabanlı ve iOS uyumlu profesyonel tahmin uygulaması.**

---

## 🌟 Öne Çıkan Özellikler

### 1. 🎯 Birebir Mesafe ve Pist Karşılaştırma Motoru
- **Hedef Pist & Mesafe Eşleştirmesi**: Koşulacak yarışın (örn. *1400m Çim*) şartlarında koşan tüm atların bu pist ve mesafedeki resmi en iyi derecelerini öncelikli olarak kıyaslar.
- **Dinamik Mesafe Uyarlaması**: Eğer atın hedef mesafede kaydı yoksa, en yakın koşularından yorgunluk ve tempo katsayıları (**fatigue decay curve**) kullanılarak projeksiyon derece hesaplanır.
- **Pist Geçiş Katsayıları**: Çim, Kum ve Sentetik pistler arasındaki hız farkları (örn. Kum pistin Çim piste göre 100m başına ~0.195s sürtünme farkı) hesaba katılır.
- **Sıklet (Kilo) Toleransı**: Dünya standartlarında her **+1 kg sıklet farkı**, 1400 metrede yaklaşık **+0.22 saniye** handikap cezası olarak dereceye yansıtılır.

### 2. 🔬 Galop ve İdman Laboratuvarı (Aşırı Dalgalanma / Outlier Filtresi)
- **Standart Sprint Kriterleri**: 400m (~25.4s), 600m (~38.2s), 800m (~51.8s) ve 1000m (~65.0s) standart idman skalası baz alınır.
- **Akıllı Outlier (Sapma) Ayıklama**: Bir atın idmanında anormal dalgalanma varsa (örneğin 400m galopunda **40 saniye kenter/gezinti** yapmışsa veya normal temposundan %25'ten fazla sapmışsa), bu derece **otomatik olarak ayıklanır** ve ortalamaya katılmaz.
- Sadece gerçek ve tutarlı sprint temposu yansıtan galoplar üzerinden **Galop Sprint Skoru (0-100)** hesaplanır.

### 3. 🧠 Şeffaf ve Açıklanabilir Yapay Zeka (Explainable AI)
- Her koşu için atlar **1., 2., 3., 4., 5., 6...** şeklinde kesin olarak sıralanır.
- Sıralamadaki her at için **"Neden Bu Sırada?"** gerekçesi Türkçe yarış jargonuyla şeffafça açıklanır:
  - *Düzeltilmiş derece avantajı*
  - *Pist ve yüzey uyum yüzdesi*
  - *Galop idman istikrarı ve filtrelenen aykırı çalışmalar*
  - *Sıklet ve jokey katkısı*
  - *KGS (Koşmadığı Gün Sayısı) ve form momentumu*

### 4. 📊 Piyasa (AGF) vs. Gerçek Model Değeri (Value Bet Tespiti)
- Altılı Ganyan Favorisi (AGF) oranları gösterilir ancak karar mekanizması tamamen mekanik derece ve hız endekslerine dayanır.
- Modelin 1. veya 2. sırada gördüğü ancak kamuoyunun (AGF) gözden kaçırdığı atlar **"Cazip Oran / Bomba Potansiyeli"** olarak etiketlenir.

### 5. 🎮 2D İnteraktif Canlı Koşu Simülatörü
- HTML5 Canvas üzerinde atların start boxlarından çıkışını, öncü/kaçak ve sprinter taktiklerini, son viraj atağını ve fotofinişi gerçek zamanlı simüle eder.
- Spiker anlatım şeridi, hız kontrolleri (1x, 2x, 4x) ve canlı lider tablosu içerir.

### 6. 🎫 Akıllı Altılı Ganyan Kupon Sihirbazı
- **Ekonomik, İdeal ve Bomba/Sürpriz** olmak üzere 3 farklı otomatik şablon stratejisi sunar.
- TJK birim fiyatına göre toplam kombinasyon ve kupon tutarını anlık hesaplar. Tek tıkla kupon kodunu panoya kopyalama imkanı verir.

### 7. 📱 iOS & Mobil PWA Desteği
- iPhone ve iPad için tam ekran **Standalone Web Clip / PWA** desteği.
- Safari üzerinden *"Ana Ekrana Ekle"* ile yerel iOS uygulaması gibi çalışır.

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.9+ (veya modern bir Python sürümü)
- Tarayıcı (Chrome, Safari, Edge, Firefox)

### 1. Depoyu İndirin / Klonlayın
```bash
git clone https://github.com/Istcity/essek.git
cd essek
```

### 2. Gerekli Paketleri Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
**Windows:**
Çift tıklayarak `start.bat` dosyasını çalıştırabilir veya terminalden:
```bash
python backend/app.py 8080
```

Tarayıcınızdan **`http://localhost:8080`** adresine gidin.

---

## 📁 Proje Dizin Yapısı

```
essek/
├── backend/
│   ├── app.py                # Çok kanallı REST API ve statik sunucu
│   ├── tjk_scraper.py        # Canlı TJK CDN & bülten ayrıştırıcı
│   ├── prediction_engine.py  # Beyer Hız, Derece Projeksiyonu ve XAI motoru
│   └── gallop_engine.py      # Galop analizörü & Outlier (Aykırı Değer) filtresi
├── frontend/
│   ├── index.html            # Lüks Dark Mode SPA Ana Sayfası
│   ├── manifest.json         # PWA / iOS manifest
│   ├── sw.js                 # Service Worker (Çevrimdışı önbellekleme)
│   ├── css/
│   │   ├── style.css         # Glassmorphism, renk tokenları, mikro-animasyonlar
│   │   └── mobile.css        # iOS & mobil dokunmatik ekran optimizasyonları
│   ├── js/
│   │   ├── app.js            # Ana frontend kontrolcüsü ve durum yönetimi
│   │   ├── race-simulator.js # 2D Canvas canlı yarış simülatörü
│   │   ├── coupon-builder.js # Altılı Ganyan kupon optimizasyon sihirbazı
│   │   └── h2h-compare.js    # Kafa Kafaya (H2H) karşılaştırma modalı
│   └── icons/                # iOS & PWA uygulama ikonları
├── requirements.txt
├── start.bat
└── README.md
```

---

## 📡 REST API Uç Noktaları

| Metot | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/cities?date=DD.MM.YYYY` | Günün aktif TJK hipodrom ve şehir listesi |
| `GET` | `/api/program?city=Bursa&date=DD.MM.YYYY` | Seçili şehrin tüm koşuları, yapay zeka sıralamaları ve analizleri |
| `GET` | `/api/gallops?horse=AT_ADI&rating=40` | Atın detaylı idman logları ve outlier durumu |
| `GET` | `/api/status` | Sistem sağlık ve sürüm kontrolü |

---

## 📱 iOS Kurulum Kılavuzu (iPhone / iPad)

1. iPhone Safari tarayıcınızda uygulamanın adresini açın (`http://localhost:8080` veya canlı sunucu adresiniz).
2. Safari'nin alt ortasındaki **Paylaş (Share)** butonuna dokunun.
3. Menüyü aşağı kaydırıp **"Ana Ekrana Ekle" (Add to Home Screen)** seçeneğini seçin.
4. Sağ üstteki **"Ekle"** butonuna basın. Uygulama ana ekranınızda bir App Store uygulaması gibi açılacaktır.

---

## ⚖️ Lisans
Bu proje eğitim, analiz ve istatistiki araştırma amaçlı geliştirilmiştir. TJK resmi bülten verilerini analiz eder.
