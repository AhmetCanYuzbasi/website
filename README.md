# Üniversite Tercih Chatbot

Bu proje, üniversite tercih sürecinde öğrencilere yardımcı olmak için geliştirilmiş bir web uygulamasıdır. Google Sheets'ten üniversite verilerini çekerek kullanıcılara arama, filtreleme ve sıralama imkanı sunar.

## 🚀 Özellikler

- **Google Sheets Entegrasyonu**: Veriler Google Sheets'ten gerçek zamanlı olarak çekilir
- **Gelişmiş Arama**: Üniversite adına göre arama yapabilme
- **Filtreleme**: Şehir ve bölüm grubuna göre filtreleme
- **Sıralama**: Çeşitli kriterlere göre sıralama
- **Responsive Tasarım**: Mobil ve masaüstü uyumlu arayüz
- **Türkçe Desteği**: Türkçe karakterler ve sıralama desteği

## 🛠️ Teknolojiler

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Veri Kaynağı**: Google Sheets API
- **Veri İşleme**: Pandas
- **Deployment**: Render

## 📋 Gereksinimler

- Python 3.8+
- Google Cloud Console hesabı
- Google Sheets API erişimi

## 🔧 Kurulum

### 1. Projeyi Klonlayın
```bash
git clone <repository-url>
cd chatbotDeneme
```

### 2. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Google Sheets API Kurulumu

#### a) Google Cloud Console'da Proje Oluşturun
1. [Google Cloud Console](https://console.cloud.google.com/) adresine gidin
2. Yeni proje oluşturun veya mevcut projeyi seçin
3. Google Sheets API'yi etkinleştirin

#### b) Service Account Oluşturun
1. "APIs & Services" > "Credentials" bölümüne gidin
2. "Create Credentials" > "Service Account" seçin
3. Service account adı: `chatbot-sheets`
4. Role: "Editor" seçin
5. "Keys" sekmesine gidin
6. "Add Key" > "Create new key" > "JSON" seçin
7. İndirilen dosyayı `credentials.json` olarak kaydedin

#### c) Google Sheets'i Hazırlayın
1. Google Sheets'te yeni bir sheet oluşturun
2. Aşağıdaki sütunları ekleyin:
   - Üniversite Adı
   - Program Kodu
   - Fakülte Adı
   - Şehir
   - Grup
   - Program Adı
   - Kontenjan
   - 2024 Başarı Sırası
   - 2024 YKS En Küçük Puanı
3. Service account'u paylaşın: `chatbot-sheets@your-project.iam.gserviceaccount.com`
4. Role: "Editor" verin

### 4. Environment Variables Ayarlayın

#### Windows PowerShell:
```powershell
$env:GOOGLE_SHEET_ID = "your-sheet-id-here"
```

#### Windows CMD:
```cmd
set GOOGLE_SHEET_ID=your-sheet-id-here
```

#### Linux/Mac:
```bash
export GOOGLE_SHEET_ID="your-sheet-id-here"
```

### 5. Uygulamayı Çalıştırın
```bash
python app.py
```

Uygulama `http://localhost:10000` adresinde çalışacaktır.

## 🌐 Render'da Deployment

### 1. GitHub'a Push Edin
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Render'da Yeni Web Service Oluşturun
1. [Render Dashboard](https://dashboard.render.com/) adresine gidin
2. "New" > "Web Service" seçin
3. GitHub repository'nizi bağlayın
4. Aşağıdaki ayarları yapın:
   - **Name**: `universite-chatbot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 3. Environment Variables Ayarlayın
Render dashboard'da "Environment" sekmesine gidin ve şu değişkenleri ekleyin:
- `GOOGLE_SHEET_ID`: Google Sheets ID'niz
- `PYTHON_VERSION`: `3.12.0`

### 4. Google Sheets Credentials
Render'da environment variables'a credentials.json içeriğini ekleyin:
- `GOOGLE_CREDENTIALS`: credentials.json dosyasının tüm içeriği

### 5. Deploy Edin
"Create Web Service" butonuna tıklayın. Render otomatik olarak deploy edecektir.

## 📊 Veri Formatı

Google Sheets'teki veriler şu formatta olmalıdır:

| Üniversite Adı | Program Kodu | Fakülte Adı | Şehir | Grup | Program Adı | Kontenjan | 2024 Başarı Sırası | 2024 YKS En Küçük Puanı |
|----------------|--------------|-------------|-------|------|-------------|-----------|-------------------|------------------------|
| İstanbul Üniversitesi | 101110001 | Tıp Fakültesi | İstanbul | MF-3 | Tıp | 100 | 1500 | 450,5 |

## 🔍 API Endpoints

- `GET /` - Ana sayfa
- `GET /api/universiteler` - Üniversite listesi
- `GET /api/filtreler` - Filtre seçenekleri
- `GET /api/universite/<program_kodu>` - Üniversite detayı
- `GET /api/status` - Sistem durumu

## 🐛 Sorun Giderme

### Google Sheets Bağlantı Sorunu
1. `credentials.json` dosyasının doğru konumda olduğunu kontrol edin
2. Service account'un Google Sheets'e erişim izni olduğunu kontrol edin
3. `GOOGLE_SHEET_ID` environment variable'ının doğru ayarlandığını kontrol edin

### Sayı Formatı Sorunu
- YKS puanları virgüllü olarak girilmelidir (örn: 439,03)
- Sistem otomatik olarak virgülü nokta ile değiştirir

### Render Deployment Sorunu
1. Build loglarını kontrol edin
2. Environment variables'ın doğru ayarlandığından emin olun
3. `requirements.txt` dosyasının güncel olduğunu kontrol edin

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add some amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📞 İletişim

Sorularınız için issue açabilir veya iletişime geçebilirsiniz. 