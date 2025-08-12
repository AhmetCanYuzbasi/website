# 🎓 Üniversite API

Python Flask ile geliştirilmiş üniversite bilgi ve ders programı API'si.

## 🚀 Özellikler

- **Üniversite Listesi**: Tüm üniversiteleri listeleme ve filtreleme
- **Ders Programları**: Bölüm bazında ders programı görüntüleme
- **Google Sheets Entegrasyonu**: Veri kaynağı olarak Google Sheets kullanımı
- **RESTful API**: JSON formatında veri sunumu
- **Filtreleme**: Ülke, şehir, grup, tür bazında filtreleme

## 📋 Gereksinimler

- Python 3.9+
- Flask
- pandas
- gspread
- google-auth

## 🔧 Kurulum

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/yourusername/universite-api.git
cd universite-api
```

### 2. Virtual Environment Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Environment Variables Ayarlayın
```bash
export GOOGLE_CREDENTIALS="your_google_credentials_json"
export GOOGLE_SHEET_ID="your_google_sheet_id"
```

### 5. Uygulamayı Çalıştırın
```bash
python app.py
```

## 🌐 API Endpoints

### Üniversite Listesi
```
GET /api/universiteler
GET /api/universiteler?search=İstanbul&ulke=Türkiye
```

### Filtreler
```
GET /api/filtreler
GET /api/sehirler?ulke=Türkiye
```

### Ders Programı
```
GET /api/ders-programi
GET /api/ders-programi-filtreler
```

### Üniversite Detayı
```
GET /api/universite/{program_kodu}
```

## 📊 Veri Yapısı

### Üniversite Verileri
- Üniversite Adı
- Program Kodu
- Fakülte Adı
- Şehir
- Ülke
- Grup
- YKS Puanı
- Kontenjan

### Ders Programı Verileri
- Üniversite
- Bölüm
- Dönem
- Ders Grubu
- Ders Alt Grubu

## 🔒 Güvenlik

- Google Sheets API anahtarları environment variables olarak saklanır
- API rate limiting uygulanır
- Input validation ve sanitization yapılır

## 🚀 Deployment

### Render.com
1. Repository'yi Render.com'a bağlayın
2. Environment variables'ları ayarlayın
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`

### Heroku
```bash
heroku create your-app-name
git push heroku main
heroku config:set GOOGLE_CREDENTIALS="your_credentials"
heroku config:set GOOGLE_SHEET_ID="your_sheet_id"
```

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## 📞 İletişim

- **Proje Sahibi**: [Your Name]
- **Email**: your.email@example.com
- **GitHub**: [@yourusername](https://github.com/yourusername)

## 🙏 Teşekkürler

- Flask framework
- Google Sheets API
- Pandas kütüphanesi
- Açık kaynak topluluğu 