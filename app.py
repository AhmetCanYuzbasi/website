from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import unicodedata
import numpy as np
import locale
#locale.setlocale(locale.LC_COLLATE, 'tr_TR.UTF-8')  # Türkçe sıralama
try:
    locale.setlocale(locale.LC_COLLATE, 'tr_TR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_COLLATE, '')  # Sistem varsayılanına geç

app = Flask(__name__)


# Türkçe sıralama anahtarı
TURKISH_ALPHABET = 'a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü v y z'.split()
TURKISH_ORDER = {char: idx for idx, char in enumerate(TURKISH_ALPHABET)}
def turkish_key(s):
    s = str(s).lower()
    return [TURKISH_ORDER.get(char, ord(char)) for char in s]

# Excel dosyasını yükle
def load_data():
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/universiteler')
def get_universiteler():
    df = load_data()
    print('Toplam üniversite:', len(df))
    print(df[['Üniversite Adı', 'Şehir', 'Grup']].head(10))
    
    # Filtreleme parametreleri
    search = request.args.get('search', '').lower()
    sehir = request.args.get('sehir', '')
    grup = request.args.get('grup', '')
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
    
    # Şehir filtresi
    if sehir:
        df = df[df['Şehir'] == sehir]
    
    # Grup filtresi
    if grup:
        df = df[df['Grup'] == grup]
    
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
    
    sehirler = sorted(df['Şehir'].unique().tolist())
    gruplar = sorted(df['Grup'].unique().tolist())
    
    return jsonify({
        'sehirler': sehirler,
        'gruplar': gruplar
    })

@app.route('/api/universite/<program_kodu>')
def get_universite_detay(program_kodu):
    df = load_data()
    # Program Kodu'nu string olarak karşılaştır, boşlukları kırp
    universite = df[df['Program Kodu'].astype(str).str.strip() == str(program_kodu).strip()]

    if universite.empty:
        return jsonify({'error': 'Üniversite bulunamadı'}), 404

    universite = universite.where(pd.notnull(universite), None)
    return jsonify(universite.iloc[0].to_dict())

#if __name__ == '__main__':
#    app.run(debug=True) 

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)


    

    

