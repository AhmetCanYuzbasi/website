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

# Eski load_data_from_sheets fonksiyonu kaldırıldı - Artık load_data() kullanılıyor

# Excel dosyasından veri yükleme fonksiyonu kaldırıldı - Artık Google Sheets kullanılıyor

# Ana veri yükleme fonksiyonu
def load_data():
    """Ana veri yükleme fonksiyonu - Google Sheets'ten yükler"""
    try:
        client = get_google_sheets_client()
        if not client:
            print("❌ Google Sheets bağlantısı kurulamadı!")
            return None
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        if not SHEET_ID:
            print("❌ GOOGLE_SHEET_ID environment variable'ı ayarlanmamış!")
            return None
        
        # Ana veri worksheet'ini bul (varsayılan olarak ilk worksheet)
        spreadsheet = client.open_by_key(SHEET_ID)
        worksheets = spreadsheet.worksheets()
        
        print(f"📊 Mevcut worksheet'ler: {[ws.title for ws in worksheets]}")
        print(f"📊 Toplam worksheet sayısı: {len(worksheets)}")
        
        # Ana veri worksheet'ini bul (genellikle ilk worksheet)
        main_worksheet = None
        for ws in worksheets:
            print(f"🔍 Worksheet kontrol ediliyor: '{ws.title}'")
            # Ana veri worksheet'ini tanımla
            if ws.title.lower() in ['üniversiteler', 'universiteler', 'ana veri', 'ana_veri', 'main', 'data']:
                main_worksheet = ws
                print(f"✅ Ana veri worksheet bulundu: '{ws.title}'")
                break
        
        # Eğer bulunamazsa ilk worksheet'i kullan
        if not main_worksheet and len(worksheets) > 0:
            main_worksheet = worksheets[0]  # İlk worksheet
            print(f"⚠️ Ana veri worksheet bulunamadı, '{main_worksheet.title}' kullanılıyor")
        
        if not main_worksheet:
            print("❌ Ana veri worksheet bulunamadı!")
            return None
        
        print(f"🎯 Seçilen ana veri worksheet: '{main_worksheet.title}'")
        
        # Ham veriyi al
        all_values = main_worksheet.get_all_values()
        
        print(f"📊 Worksheet'ten alınan satır sayısı: {len(all_values)}")
        
        if not all_values or len(all_values) < 2:
            print("❌ Ana veri worksheet'inde veri bulunamadı!")
            return None
        
        # Başlıkları al
        headers = all_values[0]
        print(f"📋 Başlıklar: {headers}")
        
        # Veri satırlarını al
        data_rows = all_values[1:]
        
        # DataFrame oluştur
        df = pd.DataFrame(data_rows, columns=headers)
        print(f'✅ Ana veri worksheet\'inden {len(df)} satır veri yüklendi')
        print('📊 Ana veri başlıkları:', list(df.columns))
        
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
        print(f'❌ Ana veri yükleme hatası: {e}')
        import traceback
        traceback.print_exc()
        return None


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

# Ders programı verilerini yükleme
def load_ders_programi_data():
    """Ders programı worksheet'inden veri yükler"""
    try:
        client = get_google_sheets_client()
        if not client:
            print("Google Sheets bağlantısı kurulamadı!")
            return None
        
        SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
        if not SHEET_ID:
            print("GOOGLE_SHEET_ID environment variable'ı ayarlanmamış!")
            return None
        
        # Ders programı worksheet'ini bul (varsayılan olarak ikinci worksheet)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Worksheet listesini al
        worksheets = spreadsheet.worksheets()
        
        # Debug: Mevcut worksheet'leri listele
        print(f"Mevcut worksheet'ler: {[ws.title for ws in worksheets]}")
        print(f"Toplam worksheet sayısı: {len(worksheets)}")
        
        # Ders programı worksheet'ini bul (genellikle ikinci worksheet)
        ders_worksheet = None
        for ws in worksheets:
            print(f"Worksheet kontrol ediliyor: '{ws.title}' (lower: '{ws.title.lower()}')")
            if ws.title.lower() in ['ders programı', 'ders_programi', 'ders programi', 'ders_programı']:
                ders_worksheet = ws
                print(f"✅ Ders programı worksheet bulundu: '{ws.title}'")
                break
        
        # Eğer bulunamazsa ikinci worksheet'i kullan
        if not ders_worksheet and len(worksheets) > 1:
            ders_worksheet = worksheets[1]  # İkinci worksheet
            print(f"⚠️ Ders programı worksheet bulunamadı, {ders_worksheet.title} kullanılıyor")
        
        if not ders_worksheet:
            print("❌ Ders programı worksheet bulunamadı!")
            return None
        
        print(f"🎯 Seçilen worksheet: '{ders_worksheet.title}'")
        
        # Ham veriyi al
        all_values = ders_worksheet.get_all_values()
        
        print(f"📊 Worksheet'ten alınan satır sayısı: {len(all_values)}")
        
        if not all_values or len(all_values) < 2:
            print("❌ Ders programı worksheet'inde veri bulunamadı!")
            return None
        
        # Başlıkları al
        headers = all_values[0]
        print(f"📋 Başlıklar: {headers}")
        
        # Veri satırlarını al
        data_rows = all_values[1:]
        
        # DataFrame oluştur
        df = pd.DataFrame(data_rows, columns=headers)
        print(f'✅ Ders programı worksheet\'inden {len(df)} satır veri yüklendi')
        print('📊 Ders programı başlıkları:', list(df.columns))
        
        return df
        
    except Exception as e:
        print(f'❌ Ders programı veri yükleme hatası: {e}')
        import traceback
        traceback.print_exc()
        return None

# Ders programı sayfası
@app.route('/ders-planlari')
def ders_planlari():
    """Ders planları sayfası"""
    return render_template('ders_planlari.html')

# Ders programı verilerini API olarak döndürme
@app.route('/api/ders-programi')
def get_ders_programi():
    """Ders programı verilerini JSON olarak döndürür"""
    try:
        df = load_ders_programi_data()
        
        if df is None:
            return jsonify({'error': 'Ders programı verisi yüklenemedi'}), 500
        
        # Veriyi JSON formatına çevir
        data = []
        for _, row in df.iterrows():
            row_dict = {}
            for col in df.columns:
                value = row[col]
                # NaN değerleri boş string olarak değiştir
                if pd.isna(value):
                    value = ""
                row_dict[col] = str(value)
            data.append(row_dict)
        
        return jsonify({
            'data': data,
            'total_count': len(data),
            'columns': list(df.columns)
        })
        
    except Exception as e:
        print(f'Ders programı API hatası: {e}')
        return jsonify({'error': 'Veri alınırken hata oluştu'}), 500

# Ders programı filtreleri
@app.route('/api/ders-programi-filtreler')
def get_ders_programi_filtreler():
    """Ders programı için filtre seçeneklerini döndürür"""
    try:
        df = load_ders_programi_data()
        
        if df is None:
            return jsonify({'error': 'Ders programı verisi yüklenemedi'}), 500
        
        # Filtre seçeneklerini hazırla
        filtreler = {}
        
        # Üniversite filtreleri
        if 'ÜNİVERSİTE' in df.columns:
            universite_list = sorted(df['ÜNİVERSİTE'].dropna().unique())
            filtreler['universite'] = [str(u) for u in universite_list if str(u).strip()]
        
        # Bölüm filtreleri
        if 'BÖLÜM' in df.columns:
            bolum_list = sorted(df['BÖLÜM'].dropna().unique())
            filtreler['bolum'] = [str(b) for b in bolum_list if str(b).strip()]
        
        # Dönem filtreleri
        if 'DÖNEM' in df.columns:
            donem_list = sorted(df['DÖNEM'].dropna().unique())
            filtreler['donem'] = [str(d) for d in donem_list if str(d).strip()]
        
        # Ders grubu filtreleri
        if 'DERS GRUBU' in df.columns:
            ders_grubu_list = sorted(df['DERS GRUBU'].dropna().unique())
            filtreler['ders_grubu'] = [str(dg) for dg in ders_grubu_list if str(dg).strip()]
        
        # Ders alt grubu filtreleri
        if 'DERS ALT GRUBU' in df.columns:
            ders_alt_grubu_list = sorted(df['DERS ALT GRUBU'].dropna().unique())
            filtreler['ders_alt_grubu'] = [str(dag) for dag in ders_alt_grubu_list if str(dag).strip()]
        
        return jsonify(filtreler)
        
    except Exception as e:
        print(f'Ders programı filtre hatası: {e}')
        return jsonify({'error': 'Filtreler alınırken hata oluştu'}), 500

# Filtrelenmiş ders programı verileri
@app.route('/api/ders-programi-filtrele', methods=['POST'])
def filter_ders_programi():
    """Ders programı verilerini filtreler"""
    try:
        df = load_ders_programi_data()
        
        if df is None:
            return jsonify({'error': 'Ders programı verisi yüklenemedi'}), 500
        
        # Filtre parametrelerini al
        data = request.get_json()
        universite = data.get('universite', '')
        bolum = data.get('bolum', '')
        donem = data.get('donem', '')
        ders_grubu = data.get('ders_grubu', '')
        ders_alt_grubu = data.get('ders_alt_grubu', '')
        
        # Debug: Log the received parameters
        print(f"🔍 Filtre parametreleri alındı:")
        print(f"   Üniversite: '{universite}'")
        print(f"   Bölüm: '{bolum}'")
        print(f"   Dönem: '{donem}'")
        print(f"   Ders Grubu: '{ders_grubu}'")
        print(f"   Ders Alt Grubu: '{ders_alt_grubu}'")
        
        # Debug: Log the data shape and sample
        print(f"🔍 DataFrame boyutu: {df.shape}")
        print(f"🔍 DataFrame sütunları: {list(df.columns)}")
        if not df.empty:
            print(f"🔍 İlk 3 satır örneği:")
            for i, row in df.head(3).iterrows():
                print(f"   Satır {i}: {dict(row)}")
        
        # Filtreleme yap
        filtered_df = df.copy()
        original_count = len(filtered_df)
        
        if universite:
            print(f"🔍 Üniversite filtresi uygulanıyor: '{universite}'")
            before_filter = len(filtered_df)
            
            # Üniversite filtresi için esnek mantık
            def universite_filter_logic(row_universite, filter_universite):
                """Üniversite filtresi için özel mantık"""
                if pd.isna(row_universite) or pd.isna(filter_universite):
                    return False
                
                row_str = str(row_universite).strip()
                filter_str = str(filter_universite).strip()
                
                if not row_str or not filter_str:
                    return False
                
                # 1. Tam eşleşme (büyük/küçük harf duyarsız)
                if row_str.lower() == filter_str.lower():
                    print(f"   ✅ Tam eşleşme bulundu: '{row_str}' == '{filter_str}'")
                    return True
                
                # 2. İçeriyor kontrolü (büyük/küçük harf duyarsız)
                if filter_str.lower() in row_str.lower():
                    print(f"   ✅ İçeriyor bulundu: '{filter_str}' in '{row_str}'")
                    return True
                
                # 3. Kısmi eşleşme kontrolü (kelime bazında)
                row_words = set(row_str.lower().split())
                filter_words = set(filter_str.lower().split())
                
                # Eğer filtredeki tüm kelimeler satırda varsa
                if filter_words.issubset(row_words):
                    print(f"   ✅ Kelime eşleşmesi bulundu: {filter_words} ⊆ {row_words}")
                    return True
                
                # 4. Özel durumlar için kontrol
                # "İstanbul Üniversitesi" gibi parantezli ifadeler
                if '(' in filter_str and ')' in filter_str:
                    # Parantez içindeki kısmı çıkar
                    base_filter = filter_str.split('(')[0].strip()
                    if base_filter.lower() in row_str.lower():
                        print(f"   ✅ Parantez öncesi eşleşme: '{base_filter}' in '{row_str}'")
                        return True
                
                return False
            
            # Filtreleme uygula
            universite_mask = filtered_df['ÜNİVERSİTE'].apply(
                lambda x: universite_filter_logic(x, universite)
            )
            
            filtered_df = filtered_df[universite_mask]
            after_filter = len(filtered_df)
            print(f"   Üniversite filtresi öncesi: {before_filter}, sonrası: {after_filter}")
            
            # Debug: Show what was found
            if after_filter > 0:
                found_universities = filtered_df['ÜNİVERSİTE'].unique()
                print(f"   ✅ Bulunan üniversiteler ({len(found_universities)} adet):")
                for i, uni in enumerate(found_universities, 1):
                    print(f"      {i}. {uni}")
            else:
                print(f"   ❌ Hiç üniversite bulunamadı!")
                
                # Mevcut üniversiteleri kontrol et
                if len(filtered_df) > 0:
                    all_universities = filtered_df['ÜNİVERSİTE'].astype(str).unique()
                    print(f"   🔍 Mevcut üniversiteler ({len(all_universities)} adet):")
                    for i, uni in enumerate(all_universities[:10], 1):  # İlk 10'unu göster
                        print(f"      {i}. {uni}")
                    if len(all_universities) > 10:
                        print(f"      ... ve {len(all_universities) - 10} tane daha")
                else:
                    print(f"   ⚠️ Filtrelenecek veri kalmadı (önceki filtreler çok kısıtlayıcı)")
        
        if bolum:
            print(f"🔍 Bölüm filtresi uygulanıyor: '{bolum}'")
            before_filter = len(filtered_df)
            
            # Bölüm filtresi için yeni mantık
            def bolum_filter_logic(row_bolum, filter_bolum):
                """Bölüm filtresi için özel mantık"""
                if pd.isna(row_bolum) or pd.isna(filter_bolum):
                    return False
                
                row_str = str(row_bolum).strip()
                filter_str = str(filter_bolum).strip()
                
                if not row_str or not filter_str:
                    return False
                
                # 1. Tam eşleşme (büyük/küçük harf duyarsız)
                if row_str.lower() == filter_str.lower():
                    print(f"   ✅ Tam eşleşme bulundu: '{row_str}' == '{filter_str}'")
                    return True
                
                # 2. İçeriyor kontrolü (büyük/küçük harf duyarsız)
                if filter_str.lower() in row_str.lower():
                    print(f"   ✅ İçeriyor bulundu: '{filter_str}' in '{row_str}'")
                    return True
                
                # 3. Kısmi eşleşme kontrolü (kelime bazında)
                row_words = set(row_str.lower().split())
                filter_words = set(filter_str.lower().split())
                
                # Eğer filtredeki tüm kelimeler satırda varsa
                if filter_words.issubset(row_words):
                    print(f"   ✅ Kelime eşleşmesi bulundu: {filter_words} ⊆ {row_words}")
                    return True
                
                # 4. Özel durumlar için kontrol
                # "Bilgisayar Mühendisliği (İngilizce)" gibi parantezli ifadeler
                if '(' in filter_str and ')' in filter_str:
                    # Parantez içindeki kısmı çıkar
                    base_filter = filter_str.split('(')[0].strip()
                    if base_filter.lower() in row_str.lower():
                        print(f"   ✅ Parantez öncesi eşleşme: '{base_filter}' in '{row_str}'")
                        return True
                
                return False
            
            # Filtreleme uygula
            bolum_mask = filtered_df['BÖLÜM'].apply(
                lambda x: bolum_filter_logic(x, bolum)
            )
            
            filtered_df = filtered_df[bolum_mask]
            after_filter = len(filtered_df)
            
            print(f"   Bölüm filtresi öncesi: {before_filter}, sonrası: {after_filter}")
            
            # Debug: Show what was found
            if after_filter > 0:
                found_bolums = filtered_df['BÖLÜM'].unique()
                print(f"   ✅ Bulunan bölümler ({len(found_bolums)} adet):")
                for i, bol in enumerate(found_bolums, 1):
                    print(f"      {i}. {bol}")
            else:
                print(f"   ❌ Hiç bölüm bulunamadı!")
                
                # Mevcut bölümleri kontrol et
                if len(filtered_df) > 0:
                    all_bolums = filtered_df['BÖLÜM'].astype(str).unique()
                    print(f"   🔍 Mevcut bölümler ({len(all_bolums)} adet):")
                    for i, bol in enumerate(all_bolums[:10], 1):  # İlk 10'unu göster
                        print(f"      {i}. {bol}")
                    if len(all_bolums) > 10:
                        print(f"      ... ve {len(all_bolums) - 10} tane daha")
                else:
                    print(f"   ⚠️ Filtrelenecek veri kalmadı (önceki filtreler çok kısıtlayıcı)")
        
        if donem:
            print(f"🔍 Dönem filtresi uygulanıyor: '{donem}'")
            before_filter = len(filtered_df)
            
            # Dönem filtresi için esnek mantık
            def donem_filter_logic(row_donem, filter_donem):
                """Dönem filtresi için özel mantık"""
                if pd.isna(row_donem) or pd.isna(filter_donem):
                    return False
                
                row_str = str(row_donem).strip()
                filter_str = str(filter_donem).strip()
                
                if not row_str or not filter_str:
                    return False
                
                # 1. Tam eşleşme (büyük/küçük harf duyarsız)
                if row_str.lower() == filter_str.lower():
                    print(f"   ✅ Tam eşleşme bulundu: '{row_str}' == '{filter_str}'")
                    return True
                
                # 2. İçeriyor kontrolü (büyük/küçük harf duyarsız)
                if filter_str.lower() in row_str.lower():
                    print(f"   ✅ İçeriyor bulundu: '{filter_str}' in '{row_str}'")
                    return True
                
                # 3. Sayısal eşleşme kontrolü (1, 2, 3 vs.)
                try:
                    if row_str.isdigit() and filter_str.isdigit():
                        if int(row_str) == int(filter_str):
                            print(f"   ✅ Sayısal eşleşme bulundu: {row_str} == {filter_str}")
                            return True
                except:
                    pass
                
                return False
            
            # Filtreleme uygula
            donem_mask = filtered_df['DÖNEM'].apply(
                lambda x: donem_filter_logic(x, donem)
            )
            
            filtered_df = filtered_df[donem_mask]
            after_filter = len(filtered_df)
            print(f"   Dönem filtresi öncesi: {before_filter}, sonrası: {after_filter}")
            
            # Debug: Show what was found
            if after_filter > 0:
                found_donems = filtered_df['DÖNEM'].unique()
                print(f"   ✅ Bulunan dönemler ({len(found_donems)} adet):")
                for i, don in enumerate(found_donems, 1):
                    print(f"      {i}. {don}")
            else:
                print(f"   ❌ Hiç dönem bulunamadı!")
                
                # Mevcut dönemleri kontrol et
                if len(filtered_df) > 0:
                    all_donems = filtered_df['DÖNEM'].astype(str).unique()
                    print(f"   🔍 Mevcut dönemler ({len(all_donems)} adet):")
                    for i, don in enumerate(all_donems[:10], 1):  # İlk 10'unu göster
                        print(f"      {i}. {don}")
                    if len(all_donems) > 10:
                        print(f"      ... ve {len(all_donems) - 10} tane daha")
                else:
                    print(f"   ⚠️ Filtrelenecek veri kalmadı (önceki filtreler çok kısıtlayıcı)")
        
        if ders_grubu:
            print(f"🔍 Ders Grubu filtresi uygulanıyor: '{ders_grubu}'")
            before_filter = len(filtered_df)
            
            # Ders Grubu filtresi için esnek mantık
            def ders_grubu_filter_logic(row_ders_grubu, filter_ders_grubu):
                """Ders Grubu filtresi için özel mantık"""
                if pd.isna(row_ders_grubu) or pd.isna(filter_ders_grubu):
                    return False
                
                row_str = str(row_ders_grubu).strip()
                filter_str = str(filter_ders_grubu).strip()
                
                if not row_str or not filter_str:
                    return False
                
                # 1. Tam eşleşme (büyük/küçük harf duyarsız)
                if row_str.lower() == filter_str.lower():
                    print(f"   ✅ Tam eşleşme bulundu: '{row_str}' == '{filter_str}'")
                    return True
                
                # 2. İçeriyor kontrolü (büyük/küçük harf duyarsız)
                if filter_str.lower() in row_str.lower():
                    print(f"   ✅ İçeriyor bulundu: '{filter_str}' in '{row_str}'")
                    return True
                
                # 3. Kısmi eşleşme kontrolü (kelime bazında)
                row_words = set(row_str.lower().split())
                filter_words = set(filter_str.lower().split())
                
                # Eğer filtredeki tüm kelimeler satırda varsa
                if filter_words.issubset(row_words):
                    print(f"   ✅ Kelime eşleşmesi bulundu: {filter_words} ⊆ {row_words}")
                    return True
                
                # 4. Kısaltma kontrolü (MATEMATİK -> MAT)
                if len(filter_str) >= 3:
                    if filter_str.lower() in row_str.lower()[:len(filter_str)]:
                        print(f"   ✅ Kısaltma eşleşmesi bulundu: '{filter_str}' in '{row_str}'")
                        return True
                
                return False
            
            # Filtreleme uygula
            ders_grubu_mask = filtered_df['DERS GRUBU'].apply(
                lambda x: ders_grubu_filter_logic(x, ders_grubu)
            )
            
            filtered_df = filtered_df[ders_grubu_mask]
            after_filter = len(filtered_df)
            print(f"   Ders Grubu filtresi öncesi: {before_filter}, sonrası: {after_filter}")
            
            # Debug: Show what was found
            if after_filter > 0:
                found_ders_gruplari = filtered_df['DERS GRUBU'].unique()
                print(f"   ✅ Bulunan ders grupları ({len(found_ders_gruplari)} adet):")
                for i, dg in enumerate(found_ders_gruplari, 1):
                    print(f"      {i}. {dg}")
            else:
                print(f"   ❌ Hiç ders grubu bulunamadı!")
                
                # Mevcut ders gruplarını kontrol et
                if len(filtered_df) > 0:
                    all_ders_gruplari = filtered_df['DERS GRUBU'].astype(str).unique()
                    print(f"   🔍 Mevcut ders grupları ({len(all_ders_gruplari)} adet):")
                    for i, dg in enumerate(all_ders_gruplari[:10], 1):  # İlk 10'unu göster
                        print(f"      {i}. {dg}")
                    if len(all_ders_gruplari) > 10:
                        print(f"      ... ve {len(all_ders_gruplari) - 10} tane daha")
                else:
                    print(f"   ⚠️ Filtrelenecek veri kalmadı (önceki filtreler çok kısıtlayıcı)")
        
        if ders_alt_grubu:
            print(f"🔍 Ders Alt Grubu filtresi uygulanıyor: '{ders_alt_grubu}'")
            before_filter = len(filtered_df)
            
            # Ders Alt Grubu filtresi için esnek mantık
            def ders_alt_grubu_filter_logic(row_ders_alt_grubu, filter_ders_alt_grubu):
                """Ders Alt Grubu filtresi için özel mantık"""
                if pd.isna(row_ders_alt_grubu) or pd.isna(filter_ders_alt_grubu):
                    return False
                
                row_str = str(row_ders_alt_grubu).strip()
                filter_str = str(filter_ders_alt_grubu).strip()
                
                if not row_str or not filter_str:
                    return False
                
                # 1. Tam eşleşme (büyük/küçük harf duyarsız)
                if row_str.lower() == filter_str.lower():
                    print(f"   ✅ Tam eşleşme bulundu: '{row_str}' == '{filter_str}'")
                    return True
                
                # 2. İçeriyor kontrolü (büyük/küçük harf duyarsız)
                if filter_str.lower() in row_str.lower():
                    print(f"   ✅ İçeriyor bulundu: '{filter_str}' in '{row_str}'")
                    return True
                
                # 3. Kısmi eşleşme kontrolü (kelime bazında)
                row_words = set(row_str.lower().split())
                filter_words = set(filter_str.lower().split())
                
                # Eğer filtredeki tüm kelimeler satırda varsa
                if filter_words.issubset(row_words):
                    print(f"   ✅ Kelime eşleşmesi bulundu: {filter_words} ⊆ {row_words}")
                    return True
                
                # 4. Kısaltma kontrolü (WebProgramlama -> Web)
                if len(filter_str) >= 3:
                    if filter_str.lower() in row_str.lower()[:len(filter_str)]:
                        print(f"   ✅ Kısaltma eşleşmesi bulundu: '{filter_str}' in '{row_str}'")
                        return True
                
                # 5. Boş değer kontrolü (eğer filtre boşsa, boş olanları da kabul et)
                if not filter_str and not row_str:
                    print(f"   ✅ Boş değer eşleşmesi bulundu")
                    return True
                
                return False
            
            # Filtreleme uygula
            ders_alt_grubu_mask = filtered_df['DERS ALT GRUBU'].apply(
                lambda x: ders_alt_grubu_filter_logic(x, ders_alt_grubu)
            )
            
            filtered_df = filtered_df[ders_alt_grubu_mask]
            after_filter = len(filtered_df)
            print(f"   Ders Alt Grubu filtresi öncesi: {before_filter}, sonrası: {after_filter}")
            
            # Debug: Show what was found
            if after_filter > 0:
                found_ders_alt_gruplari = filtered_df['DERS ALT GRUBU'].unique()
                print(f"   ✅ Bulunan ders alt grupları ({len(found_ders_alt_gruplari)} adet):")
                for i, dag in enumerate(found_ders_alt_gruplari, 1):
                    print(f"      {i}. {dag}")
            else:
                print(f"   ❌ Hiç ders alt grubu bulunamadı!")
                
                # Mevcut ders alt gruplarını kontrol et
                if len(filtered_df) > 0:
                    all_ders_alt_gruplari = filtered_df['DERS ALT GRUBU'].astype(str).unique()
                    print(f"   🔍 Mevcut ders alt grupları ({len(all_ders_alt_gruplari)} adet):")
                    for i, dag in enumerate(all_ders_alt_gruplari[:10], 1):  # İlk 10'unu göster
                        print(f"      {i}. {dag}")
                    if len(all_ders_alt_gruplari) > 10:
                        print(f"      ... ve {len(all_ders_alt_gruplari) - 10} tane daha")
                else:
                    print(f"   ⚠️ Filtrelenecek veri kalmadı (önceki filtreler çok kısıtlayıcı)")
        
        print(f"🔍 Filtreleme tamamlandı. Orijinal: {original_count}, Filtrelenmiş: {len(filtered_df)}")
        
        # Veriyi JSON formatına çevir
        data = []
        for _, row in filtered_df.iterrows():
            row_dict = {}
            for col in filtered_df.columns:
                value = row[col]
                if pd.isna(value):
                    value = ""
                row_dict[col] = str(value)
            data.append(row_dict)
        
        return jsonify({
            'data': data,
            'total_count': len(data),
            'filtered_count': len(filtered_df),
            'columns': list(filtered_df.columns)
        })
        
    except Exception as e:
        print(f'❌ Ders programı filtreleme hatası: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Filtreleme yapılırken hata oluştu'}), 500



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

    
    