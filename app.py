from flask import Flask, render_template, request, jsonify, make_response
import pandas as pd
import os
import unicodedata
import numpy as np
import locale
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

import locale

try:
    locale.setlocale(locale.LC_COLLATE, 'tr_TR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_COLLATE, '')  # Sistem varsayılanına geç

app = Flask(__name__)

# Google Sheets API ayarları
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Google Sheets bağlantısı
def get_google_sheets_client():
    try:
        # Önce environment variable'dan credentials'ı kontrol et (Render için)
        google_credentials = os.environ.get('GOOGLE_CREDENTIALS')
        
        if google_credentials:
            # Environment variable'dan credentials oluştur
            import json
            creds_dict = json.loads(google_credentials)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            print("✅ Environment variable'dan credentials yüklendi")
        elif os.path.exists('credentials.json'):
            # Dosyadan credentials yükle (local development için)
            creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            print("✅ credentials.json dosyasından yüklendi")
        else:
            # Credentials bulunamadı
            print("❌ Google Sheets credentials bulunamadı!")
            print("💡 Render'da GOOGLE_CREDENTIALS environment variable'ını ayarlayın")
            print("💡 Local'de credentials.json dosyasını oluşturun")
            return None
        
        if creds:
            client = gspread.authorize(creds)
            return client
        else:
            return None
    except Exception as e:
        print(f"Google Sheets bağlantı hatası: {e}")
        return None

# Google Sheets'ten veri yükleme
def load_data_from_sheets():
    try:
        client = get_google_sheets_client()
        if not client:
            print("Google Sheets bağlantısı kurulamadı, Excel dosyası kullanılıyor...")
            return load_data_from_excel()
        
        # Google Sheets ID'sini buraya ekleyin
        # Sheets URL'sinden alabilirsiniz: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')  # Environment variable'dan al
        
        if not SHEET_ID:
            print("GOOGLE_SHEET_ID environment variable'ı ayarlanmamış, Excel dosyası kullanılıyor...")
            return load_data_from_excel()
        
        # Sheet'i aç
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Ham veriyi al (formatlanmamış)
        all_values = sheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            print("Google Sheets'te veri bulunamadı, Excel dosyası kullanılıyor...")
            return load_data_from_excel()
        
        # Başlıkları al
        headers = all_values[0]
        
        # Veri satırlarını al
        data_rows = all_values[1:]
        
        # DataFrame oluştur
        df = pd.DataFrame(data_rows, columns=headers)
        print(f'Google Sheets\'ten {len(df)} satır veri yüklendi')
        print('Google Sheets başlıkları:', list(df.columns))
        
        # Sütun yapısını kontrol et ve gerekirse düzenle
        expected_columns = ['Üniversite Adı', 'Program Kodu', 'Fakülte Adı', 'Ülke', 'Şehir', 'Grup', 'Program Adı', 'Kontenjan', '2024 Başarı Sırası', '2024 YKS En Küçük Puanı', 'Kuruluş Tarihi', 'Adres', 'Telefon', 'E-posta', 'Rektör', 'Üni Alan Adı', 'Fakülte Alan adı', 'Bölüm Alan Adı']
        
        # Eksik sütunları kontrol et
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            print(f'Eksik sütunlar: {missing_columns}')
            print('Excel dosyası kullanılıyor...')
            return load_data_from_excel()
        
        # Sayısal sütunları düzelt
        numeric_columns = ['Kontenjan', '2024 Başarı Sırası', '2024 YKS En Küçük Puanı']
        
        for col in numeric_columns:
            if col in df.columns:
                if col == '2024 YKS En Küçük Puanı':
                    # YKS puanı için virgülü nokta ile değiştir (ondalık sayı)
                    df[col] = df[col].astype(str).str.replace(',', '.').str.replace(' ', '')
                else:
                    # Diğer sayılar için virgülü kaldır (tam sayı)
                    df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                
                # Sayısal değerlere çevir
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                print(f'✅ {col} sütunu düzeltildi')
                print(f'   Örnek değerler: {df[col].head().tolist()}')
        
        return df
        
    except Exception as e:
        print(f'Google Sheets okuma hatası: {e}')
        print("Excel dosyası kullanılıyor...")
        return load_data_from_excel()

# Excel dosyasından veri yükleme (fallback)
def load_data_from_excel():
    try:
        # Excel dosyasını yükle (dosya adını kendi dosyanızla değiştirin)
        df = pd.read_excel('toplantı tablo 1.xlsx')
        print('Excel başlıkları:', list(df.columns))
        print('İlk satır:', df.iloc[0].to_dict() if not df.empty else 'Tablo boş')
        return df
    except Exception as e:
        print('Excel okuma hatası:', e)
        # Örnek veri oluştur (gerçek verilerinizi yükleyene kadar)
        data = {
            'Üniversite Adı': ['İstanbul Üniversitesi', 'Ankara Üniversitesi', 'İzmir Üniversitesi'],
            'Program Kodu': ['101110001', '101110002', '101110003'],
            'Fakülte Adı': ['Tıp Fakültesi', 'Hukuk Fakültesi', 'Mühendislik Fakültesi'],
            'Şehir': ['İstanbul', 'Ankara', 'İzmir'],
            'Grup': ['MF-3', 'TM-2', 'MF-4'],
            'Kontenjan': [100, 80, 120],
            '2024 Başarı Sırası': [1500, 2500, 3000],
            '2024 YKS En Küçük Puanı': [450.5, 420.3, 380.7]
        }
        return pd.DataFrame(data)

# Ana veri yükleme fonksiyonu
def load_data():
    return load_data_from_sheets()


# Türkçe sıralama anahtarı
TURKISH_ALPHABET = 'a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü v y z'.split()
TURKISH_ORDER = {char: idx for idx, char in enumerate(TURKISH_ALPHABET)}
def turkish_key(s):
    s = str(s).lower()
    return [TURKISH_ORDER.get(char, ord(char)) for char in s]

@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response



@app.route('/api/universiteler')
def get_universiteler():
    df = load_data()
    print('Toplam üniversite:', len(df))
    print(df[['Üniversite Adı', 'Şehir', 'Grup']].head(10))
    
    # Filtreleme parametreleri
    search = request.args.get('search', '').lower()
    ulke = request.args.get('ulke', '')
    sehir = request.args.get('sehir', '')
    grup = request.args.get('grup', '')
    tur = request.args.get('tur', '')
    sort_by = request.args.get('sort_by', 'Üniversite Adı')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Sıralama öncesi: sayısal sütunları dönüştür
    for col in ['2024 YKS En Küçük Puanı', '2024 Başarı Sırası', 'Kontenjan']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Arama filtresi (normalize)
    def normalize(s):
        if pd.isna(s):
            return ''
        s = str(s).strip().lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join([c for c in s if not unicodedata.combining(c)])
        return s

    if search:
        search_norm = normalize(search)
        df = df[df['Üniversite Adı'].apply(normalize).str.contains(search_norm)]
    
    # Ülke filtresi
    if ulke:
        df = df[df['Ülke'] == ulke]
    
    # Şehir filtresi
    if sehir:
        df = df[df['Şehir'] == sehir]
    
    # Grup filtresi
    if grup:
        df = df[df['Grup'] == grup]
    
    # Tür filtresi
    if tur and 'Tür' in df.columns:
        df = df[df['Tür'] == tur]
    
    # Sıralama
    if sort_by in df.columns:
        if sort_by == 'Üniversite Adı':
            df = df.sort_values(by=sort_by, key=lambda col: col.map(turkish_key), ascending=(sort_order != 'desc'))
        else:
            df = df.sort_values(by=sort_by, ascending=(sort_order != 'desc'))
    else:
        df = df.sort_values(by='Üniversite Adı', key=lambda col: col.map(turkish_key))

    df = df.replace({np.nan: None})  # Tüm NaN'leri None yap
    return jsonify(df.to_dict('records'))

@app.route('/api/filtreler')
def get_filtreler():
    df = load_data()
    
    ulkeler = sorted(df['Ülke'].unique().tolist())
    sehirler = sorted(df['Şehir'].unique().tolist())
    gruplar = sorted(df['Grup'].unique().tolist())
    
    # Tür sütunu varsa ekle
    turler = []
    if 'Tür' in df.columns:
        turler = sorted(df['Tür'].unique().tolist())
    
    return jsonify({
        'ulkeler': ulkeler,
        'sehirler': sehirler,
        'gruplar': gruplar,
        'turler': turler
    })

@app.route('/api/sehirler')
def get_sehirler():
    df = load_data()
    ulke = request.args.get('ulke', '')
    
    if ulke:
        # Belirli ülkeye göre şehirler
        filtered_df = df[df['Ülke'] == ulke]
        sehirler = sorted(filtered_df['Şehir'].unique().tolist())
    else:
        # Tüm şehirler
        sehirler = sorted(df['Şehir'].unique().tolist())
    
    return jsonify({
        'sehirler': sehirler
    })

@app.route('/api/dinamik-filtreler')
def get_dinamik_filtreler():
    df = load_data()
    
    # Mevcut filtreleri al
    ulke = request.args.get('ulke', '')
    sehir = request.args.get('sehir', '')
    grup = request.args.get('grup', '')
    tur = request.args.get('tur', '')
    
    # DataFrame'i mevcut filtrelere göre filtrele
    filtered_df = df.copy()
    
    if ulke:
        filtered_df = filtered_df[filtered_df['Ülke'] == ulke]
    if sehir:
        filtered_df = filtered_df[filtered_df['Şehir'] == sehir]
    if grup:
        filtered_df = filtered_df[filtered_df['Grup'] == grup]
    if tur and 'Tür' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Tür'] == tur]
    
    # Filtrelenmiş veriye göre seçenekleri döndür
    result = {
        'ulkeler': sorted(df['Ülke'].unique().tolist()),  # Ülkeler her zaman tam liste
        'sehirler': sorted(filtered_df['Şehir'].unique().tolist()),
        'gruplar': sorted(filtered_df['Grup'].unique().tolist()),
    }
    
    # Tür sütunu varsa ekle
    if 'Tür' in filtered_df.columns:
        result['turler'] = sorted(filtered_df['Tür'].unique().tolist())
    else:
        result['turler'] = []
    
    return jsonify(result)

@app.route('/api/universite/<program_kodu>')
def get_universite_detay(program_kodu):
    df = load_data()
    # Program Kodu'nu string olarak karşılaştır, boşlukları kırp
    universite = df[df['Program Kodu'].astype(str).str.strip() == str(program_kodu).strip()]

    if universite.empty:
        return jsonify({'error': 'Üniversite bulunamadı'}), 404

    universite = universite.where(pd.notnull(universite), None)
    return jsonify(universite.iloc[0].to_dict())

@app.route('/detay/<program_kodu>')
def detay_sayfasi(program_kodu):
    response = make_response(render_template('detay.html', program_kodu=program_kodu))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Google Sheets'e veri ekleme
@app.route('/api/universite', methods=['POST'])
def add_universite():
    try:
        data = request.get_json()
        
        # Gerekli alanları kontrol et
        required_fields = ['Üniversite Adı', 'Program Kodu', 'Fakülte Adı', 'Şehir', 'Grup']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} alanı zorunludur'}), 400
        
        client = get_google_sheets_client()
        if not client:
            return jsonify({'error': 'Google Sheets bağlantısı kurulamadı'}), 500
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        if not SHEET_ID:
            return jsonify({'error': 'GOOGLE_SHEET_ID ayarlanmamış'}), 500
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Yeni satır olarak ekle (tüm sütunlar dahil)
        row_data = [
            data.get('Üniversite Adı', ''),
            data.get('Program Kodu', ''),
            data.get('Fakülte Adı', ''),
            data.get('Ülke', ''),
            data.get('Şehir', ''),
            data.get('Grup', ''),
            data.get('Program Adı', ''),
            data.get('Kontenjan', ''),
            data.get('2024 Başarı Sırası', ''),
            data.get('2024 YKS En Küçük Puanı', ''),
            data.get('Kuruluş Tarihi', ''),
            data.get('Adres', ''),
            data.get('Telefon', ''),
            data.get('E-posta', ''),
            data.get('Rektör', ''),
            data.get('Üni Alan Adı', ''),
            data.get('Fakülte Alan adı', ''),
            data.get('Bölüm Alan Adı', '')
        ]
        
        sheet.append_row(row_data)
        
        return jsonify({'message': 'Üniversite başarıyla eklendi', 'data': data}), 201
        
    except Exception as e:
        print(f'Veri ekleme hatası: {e}')
        return jsonify({'error': 'Veri eklenirken hata oluştu'}), 500

# Google Sheets'te veri güncelleme
@app.route('/api/universite/<program_kodu>', methods=['PUT'])
def update_universite(program_kodu):
    try:
        data = request.get_json()
        
        client = get_google_sheets_client()
        if not client:
            return jsonify({'error': 'Google Sheets bağlantısı kurulamadı'}), 500
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        if not SHEET_ID:
            return jsonify({'error': 'GOOGLE_SHEET_ID ayarlanmamış'}), 500
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Program koduna göre satırı bul
        all_records = sheet.get_all_records()
        row_index = None
        
        for i, record in enumerate(all_records, start=2):  # 2'den başla çünkü 1. satır başlık
            if str(record.get('Program Kodu', '')).strip() == str(program_kodu).strip():
                row_index = i
                break
        
        if row_index is None:
            return jsonify({'error': 'Üniversite bulunamadı'}), 404
        
        # Güncellenecek alanları belirle
        update_data = []
        for field in ['Üniversite Adı', 'Program Kodu', 'Fakülte Adı', 'Ülke', 'Şehir', 'Grup', 'Program Adı', 'Kontenjan', '2024 Başarı Sırası', '2024 YKS En Küçük Puanı', 'Kuruluş Tarihi', 'Adres', 'Telefon', 'E-posta', 'Rektör', 'Üni Alan Adı', 'Fakülte Alan adı', 'Bölüm Alan Adı']:
            if field in data:
                update_data.append(data[field])
            else:
                # Mevcut değeri koru
                cell_value = sheet.cell(row_index, all_records[0].keys().index(field) + 1).value
                update_data.append(cell_value)
        
        # Satırı güncelle (19 sütun için A-S aralığı)
        sheet.update(f'A{row_index}:S{row_index}', [update_data])
        
        return jsonify({'message': 'Üniversite başarıyla güncellendi', 'data': data}), 200
        
    except Exception as e:
        print(f'Veri güncelleme hatası: {e}')
        return jsonify({'error': 'Veri güncellenirken hata oluştu'}), 500

# Google Sheets'ten veri silme
@app.route('/api/universite/<program_kodu>', methods=['DELETE'])
def delete_universite(program_kodu):
    try:
        client = get_google_sheets_client()
        if not client:
            return jsonify({'error': 'Google Sheets bağlantısı kurulamadı'}), 500
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        if not SHEET_ID:
            return jsonify({'error': 'GOOGLE_SHEET_ID ayarlanmamış'}), 500
        
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Program koduna göre satırı bul
        all_records = sheet.get_all_records()
        row_index = None
        
        for i, record in enumerate(all_records, start=2):
            if str(record.get('Program Kodu', '')).strip() == str(program_kodu).strip():
                row_index = i
                break
        
        if row_index is None:
            return jsonify({'error': 'Üniversite bulunamadı'}), 404
        
        # Satırı sil
        sheet.delete_rows(row_index)
        
        return jsonify({'message': 'Üniversite başarıyla silindi'}), 200
        
    except Exception as e:
        print(f'Veri silme hatası: {e}')
        return jsonify({'error': 'Veri silinirken hata oluştu'}), 500

# Veri kaynağı durumu kontrolü
@app.route('/api/status')
def get_status():
    try:
        client = get_google_sheets_client()
        sheets_connected = client is not None
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        sheet_configured = bool(SHEET_ID)
        
        df = load_data()
        data_count = len(df) if df is not None else 0
        
        return jsonify({
            'sheets_connected': sheets_connected,
            'sheet_configured': sheet_configured,
            'data_source': 'Google Sheets' if sheets_connected and sheet_configured else 'Excel File',
            'data_count': data_count,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'sheets_connected': False,
            'sheet_configured': False,
            'data_source': 'Error'
        }), 500

#if __name__ == '__main__':
#    app.run(debug=True) 

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

    
    