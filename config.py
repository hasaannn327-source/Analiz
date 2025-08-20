# Konfigürasyon dosyası
import os
from pathlib import Path

# Temel konfigürasyon
CONFIG = {
    # Dosya işleme
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'supported_formats': ['.dwg', '.dxf'],
    'timeout_seconds': 300,
    
    # Yapısal kriterler
    'min_column_size': 0.25,  # 25cm
    'max_beam_span': 8.0,     # 8m
    'min_wall_ratio': 0.01,   # %1
    'max_area_per_column': 25.0,  # 25m²
    
    # Analiz parametreleri
    'grid_resolution': 20,
    'min_element_area': 0.01,  # 1cm²
    'precision_digits': 2,
    
    # Görselleştirme
    'plot_colors': {
        'kolon': '#FF6B6B',
        'kiriş': '#4ECDC4', 
        'perde': '#45B7D1',
        'döşeme': '#96CEB4',
        'temel': '#FFEAA7'
    },
    
    # Rapor ayarları
    'report_formats': ['csv', 'pdf', 'json'],
    'pdf_page_size': 'A4',
    'chart_dpi': 300,
    
    # CAD dönüştürücü yolları
    'cad_converters': {
        'librecad': [
            '/usr/bin/librecad',
            '/opt/librecad/bin/librecad',
            'librecad'
        ],
        'freecad': [
            '/usr/bin/freecad',
            '/opt/freecad/bin/freecad',
            'freecad'
        ],
        'qcad': [
            '/usr/bin/qcad',
            '/opt/qcad/bin/qcad',
            'qcad'
        ],
        'oda_converter': [
            '/opt/ODAFileConverter/ODAFileConverter',
            '/usr/bin/ODAFileConverter',
            'ODAFileConverter'
        ]
    },
    
    # Logging
    'log_level': 'INFO',
    'log_file': 'structural_analysis.log',
    'log_format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Ortam değişkenlerinden ayarları güncelle
def update_config_from_env():
    """Ortam değişkenlerinden konfigürasyonu güncelle"""
    
    # Dosya boyutu limiti
    if 'MAX_FILE_SIZE' in os.environ:
        try:
            CONFIG['max_file_size'] = int(os.environ['MAX_FILE_SIZE']) * 1024 * 1024
        except ValueError:
            pass
    
    # Timeout değeri
    if 'ANALYSIS_TIMEOUT' in os.environ:
        try:
            CONFIG['timeout_seconds'] = int(os.environ['ANALYSIS_TIMEOUT'])
        except ValueError:
            pass
    
    # Log seviyesi
    if 'LOG_LEVEL' in os.environ:
        CONFIG['log_level'] = os.environ['LOG_LEVEL'].upper()

# Geliştirme/Üretim ortamı ayarları
def get_config(environment='production'):
    """Ortama göre konfigürasyon döndür"""
    
    config = CONFIG.copy()
    
    if environment == 'development':
        config.update({
            'log_level': 'DEBUG',
            'timeout_seconds': 60,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
        })
    elif environment == 'testing':
        config.update({
            'log_level': 'WARNING',
            'timeout_seconds': 30,
            'max_file_size': 5 * 1024 * 1024,   # 5MB
        })
    
    return config

# Konfigürasyonu başlat
update_config_from_env()