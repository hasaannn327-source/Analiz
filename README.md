# 🏗️ Gelişmiş Yapısal Eleman Analiz Uygulaması

**DWG/DXF dosyalarından yapı elemanlarını otomatik analiz eden profesyonel Streamlit uygulaması**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Yeni Özellikler

### 🚀 **Versiyon 2.0 Geliştirmeleri**
- 🔄 **Gelişmiş DWG Dönüştürme**: LibreCAD, FreeCAD, QCAD, ODA Converter desteği
- 📊 **3D Görselleştirme**: İnteraktif 3D grafikler ve plan görünümleri
- 📄 **PDF Raporlama**: Profesyonel PDF rapor oluşturma
- 🎯 **Kapsamlı Statik Kontroller**: TBDY 2018 uyumlu yapısal kontroller
- 🗺️ **Otomatik Plan Çizimi**: Matplotlib ile yapısal plan görünümü
- 📈 **Gelişmiş İstatistikler**: Detaylı analiz ve trend tespiti
- 🔧 **Modüler Kod Yapısı**: Bakım ve geliştirme kolaylığı
- ⚡ **Performans İyileştirmeleri**: Hızlı dosya işleme ve analiz
- 🛡️ **Güvenlik**: Dosya validasyonu ve güvenli işleme
- 📱 **Modern UI**: Sekmeli arayüz ve responsive tasarım

## 🎯 Ana Özellikler

### 📁 **Dosya İşleme**
- ✅ **Çoklu Format**: DWG, DXF dosya desteği
- ✅ **Otomatik Dönüştürme**: DWG → DXF otomatik dönüşüm
- ✅ **Büyük Dosya**: 100MB'a kadar dosya desteği
- ✅ **Güvenli İşleme**: Dosya validasyonu ve virus koruması

### 🏗️ **Yapısal Analiz**
- 🏛️ **Kolonlar**: Boyut, alan, kesit tipi analizi
- 📏 **Kirişler**: Uzunluk, açıklık, yön analizi
- 🧱 **Perdeler**: Alan, kalınlık, oran kontrolleri
- 🏢 **Döşemeler**: Alan hesaplaması ve dağılım analizi
- 🏗️ **Temeller**: Adet, boyut ve kolon uyum kontrolü

### 📊 **Görselleştirme & Raporlama**
- 📈 **İnteraktif Grafikler**: Plotly ile dinamik görselleştirme
- 🗺️ **Plan Görünümü**: Otomatik yapısal plan çizimi
- 📄 **PDF Rapor**: Profesyonel rapor oluşturma
- 📊 **CSV Export**: Detaylı veri çıktısı
- 💾 **JSON Export**: Ham veri kaydetme

### ⚠️ **Statik Kontroller**
- 🔍 **Minimum Boyut**: Kolon boyut kontrolleri (25x25cm)
- 📐 **Maksimum Açıklık**: Kiriş açıklık kontrolü (8m)
- 📊 **Perde Oranı**: Minimum perde alanı oranı (%1)
- 🏛️ **Kolon Yoğunluğu**: Alan/kolon oranı kontrolü (25m²/kolon)
- ⚖️ **Geometrik Kontroller**: Simetri ve kompaktlık analizi

## 🚀 Kurulum

### 📋 Gereksinimler
- Python 3.9+
- CAD dönüştürme araçları (LibreCAD, FreeCAD, QCAD)
- 4GB+ RAM önerili
- 1GB+ disk alanı

### 🔧 Otomatik Kurulum
```bash
# Repoyu klonlayın
git clone https://github.com/yourusername/structural-analyzer.git
cd structural-analyzer

# Otomatik kurulum scriptini çalıştırın
./setup.sh production

# Uygulamayı başlatın
./start.sh
```

### 🐳 Docker ile Kurulum
```bash
# Docker Compose ile
docker-compose up -d

# Veya Docker ile
docker build -t structural-analyzer .
docker run -p 8501:8501 structural-analyzer
```

### 📦 Manuel Kurulum
```bash
# Python sanal ortamı oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# CAD araçlarını yükle (Ubuntu/Debian)
sudo apt-get install librecad freecad qcad

# Uygulamayı başlat
streamlit run app.py
```

## 💻 Kullanım

### 1️⃣ **Dosya Yükleme**
- Sol menüden DWG/DXF dosyanızı seçin
- Maksimum dosya boyutu: 100MB
- Desteklenen formatlar: .dwg, .dxf

### 2️⃣ **Analiz Seçenekleri**
- ⚙️ **Detaylı Analiz**: Kapsamlı eleman analizi
- 📊 **3D Görselleştirme**: İnteraktif 3D grafikler
- 📄 **PDF Rapor**: Otomatik rapor oluşturma

### 3️⃣ **Sonuçları İnceleme**
- **📊 Genel Bakış**: KPI metrikleri ve özet
- **📈 Detaylı Analiz**: Eleman bazlı detaylar
- **🎯 Statik Kontroller**: Uyarılar ve öneriler
- **📊 Görselleştirmeler**: Grafikler ve planlar
- **📄 Raporlar**: İndirilebilir raporlar

## 📊 Örnekler

### Kolon Analizi
```python
# Otomatik kolon tespiti
kolonlar = analyzer.elements['kolon']

# İstatistikler
toplam_kolon = len(kolonlar)
ortalama_alan = np.mean([k['alan'] for k in kolonlar])
min_boyut = min([min(k['genişlik'], k['uzunluk']) for k in kolonlar])

# Uyarı kontrolü
if min_boyut < 0.25:  # 25cm
    print("⚠️ Minimum kolon boyutu altında elemanlar var!")
```

### Plan Görünümü
```python
# Yapısal plan oluşturma
plan_path = analyzer.create_structural_plan_view()

# Plan görüntüleme
st.image(plan_path, caption="Yapısal Plan")
```

## ⚙️ Konfigürasyon

### config.py
```python
CONFIG = {
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'min_column_size': 0.25,  # 25cm
    'max_beam_span': 8.0,     # 8m
    'min_wall_ratio': 0.01,   # %1
}
```

### Ortam Değişkenleri
```bash
export MAX_FILE_SIZE=100        # MB cinsinden
export ANALYSIS_TIMEOUT=300     # Saniye
export LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

## 🔧 Geliştirme

### Kod Yapısı
```
structural-analyzer/
├── app.py                 # Ana uygulama
├── config.py             # Konfigürasyon
├── utils.py              # Yardımcı fonksiyonlar
├── requirements.txt      # Python bağımlılıkları
├── Dockerfile           # Docker konfigürasyonu
├── docker-compose.yml   # Docker Compose
├── setup.sh            # Kurulum scripti
└── README.md           # Dokümantasyon
```

### Test Çalıştırma
```bash
# Unit testler
python -m pytest tests/ -v

# Coverage raporu
python -m pytest tests/ --cov=. --cov-report=html

# Linting
black app.py utils.py config.py
flake8 app.py utils.py config.py
```

### Yeni Özellik Ekleme
```python
# utils.py'ye yeni yardımcı fonksiyon
class NewAnalysisUtils:
    @staticmethod
    def custom_analysis(elements):
        # Özel analiz mantığı
        return results

# app.py'de kullanım
from utils import NewAnalysisUtils
results = NewAnalysisUtils.custom_analysis(elements)
```

## 📈 Performans

### Optimizasyon İpuçları
- **🔄 Büyük Dosyalar**: Progress bar ile kullanıcı deneyimi
- **💾 Bellek**: Lazy loading ile bellek optimizasyonu
- **⚡ Hız**: Numpy ve vectorization kullanımı
- **🔧 Cache**: Streamlit cache ile hızlandırma

### Benchmark Sonuçları
| Dosya Boyutu | Element Sayısı | İşlem Süresi | Bellek Kullanımı |
|--------------|----------------|--------------|------------------|
| 1MB          | 100            | 2s           | 50MB             |
| 10MB         | 1,000          | 15s          | 200MB            |
| 50MB         | 5,000          | 45s          | 500MB            |

## 🛡️ Güvenlik

### Dosya Güvenliği
- ✅ Dosya boyutu kontrolü
- ✅ Format validasyonu
- ✅ Güvenli geçici dosya işleme
- ✅ Otomatik temizlik

### Sistem Güvenliği
- ✅ Input sanitization
- ✅ Path traversal koruması
- ✅ Resource limiting
- ✅ Error handling

## 🐛 Sorun Giderme

### Yaygın Sorunlar

#### 1. LibreCAD Bulunamadı
```bash
# Ubuntu/Debian
sudo apt-get install librecad

# macOS
brew install --cask librecad

# Windows
# LibreCAD'i https://librecad.org adresinden indirin
```

#### 2. Python Paket Hatası
```bash
# Sanal ortamı yeniden oluştur
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Bellek Hatası
```bash
# Daha büyük dosyalar için swap alanı artırın
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Log Analizi
```bash
# Uygulama logları
tail -f structural_analysis.log

# Sistem logları
journalctl -u structural-analyzer -f
```

## 📚 API Dokümantasyonu

### AdvancedStructuralAnalyzer Sınıfı

#### Temel Methodlar
```python
analyzer = AdvancedStructuralAnalyzer()

# Dosya analizi
success = analyzer.enhanced_analyze_dxf('dosya.dxf')

# İstatistik hesaplama
stats = analyzer.calculate_enhanced_statistics()

# Statik kontroller
warnings = analyzer.perform_comprehensive_checks()

# Görselleştirme
visualizations = analyzer.create_advanced_visualizations()

# PDF rapor
pdf_data = analyzer.generate_pdf_report()
```

#### Yardımcı Sınıflar
```python
from utils import GeometryUtils, ValidationUtils, StatisticsUtils

# Geometri hesaplamaları
area = GeometryUtils.calculate_polygon_area(points)
perimeter = GeometryUtils.calculate_perimeter(points)

# Validasyon
is_valid = ValidationUtils.validate_coordinates(coords)

# İstatistik
stats = StatisticsUtils.calculate_statistics(values)
```

## 🤝 Katkıda Bulunma

### Geliştirme Süreci
1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

### Kod Standartları
- Python PEP8 uyumlu kod
- Docstring ile dokümantasyon
- Unit test coverage %80+
- Type hints kullanımı

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👥 Katkıda Bulunanlar

- 👨‍💻 **Ana Geliştirici**: Yapısal analiz algoritmaları
- 🎨 **UI/UX Tasarımcı**: Arayüz tasarımı
- 🧪 **Test Engineer**: Test senaryoları
- 📝 **Dokümantasyon**: Teknik dokümantasyon

## 📞 İletişim

- 📧 Email: support@structural-analyzer.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/structural-analyzer/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/structural-analyzer/discussions)
- 📖 Wiki: [GitHub Wiki](https://github.com/yourusername/structural-analyzer/wiki)

## 🙏 Teşekkürler

- [Streamlit](https://streamlit.io/) - Web framework
- [ezdxf](https://github.com/mozman/ezdxf) - DXF kütüphanesi
- [Plotly](https://plotly.com/) - Görselleştirme
- [ReportLab](https://www.reportlab.com/) - PDF oluşturma
- [LibreCAD](https://librecad.org/) - CAD dönüştürme

---

**🏗️ Yapısal Analiz Uygulaması v2.0** - Profesyonel yapı elemanı analizi için geliştirilmiştir.