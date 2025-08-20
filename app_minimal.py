#!/usr/bin/env python3
"""
Minimal Yapısal Analiz Uygulaması
Sistem paketleri ile çalışacak basit versiyon
"""

import sys
import os
import tempfile
import math
import json
from typing import Dict, List, Tuple, Optional

# Streamlit import kontrolü
try:
    import streamlit as st
except ImportError:
    print("❌ Streamlit kurulu değil!")
    print("Kurulum için: pip3 install --user streamlit")
    sys.exit(1)

# Diğer paketler için kontrol
missing_packages = []

try:
    import pandas as pd
except ImportError:
    missing_packages.append("pandas")

try:
    import numpy as np
except ImportError:
    missing_packages.append("numpy")

try:
    import ezdxf
except ImportError:
    missing_packages.append("ezdxf")

# Eksik paketler varsa uyarı ver ama devam et
if missing_packages:
    st.warning(f"⚠️ Eksik paketler: {', '.join(missing_packages)}")
    st.info("Kurulum için: pip3 install --user " + " ".join(missing_packages))

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Basit DWG/DXF Analizi",
    page_icon="🏗️",
    layout="wide"
)

class SimpleStructuralAnalyzer:
    def __init__(self):
        self.elements = {
            'kolon': [],
            'kiriş': [],
            'perde': [],
            'döşeme': [],
            'temel': []
        }
        
        self.layer_keywords = {
            'kolon': ['kolon', 'column', 'col', 'c-'],
            'kiriş': ['kiriş', 'beam', 'b-'],
            'perde': ['perde', 'wall', 'w-'],
            'döşeme': ['döşeme', 'slab', 'f-'],
            'temel': ['temel', 'foundation', 'fd-']
        }
    
    def create_demo_dxf(self):
        """Demo DXF oluştur - ezdxf olmadan basit versiyon"""
        demo_elements = {
            'kolon': [
                {'alan': 0.25, 'genişlik': 0.5, 'uzunluk': 0.5, 'koordinat': (0, 0)},
                {'alan': 0.36, 'genişlik': 0.6, 'uzunluk': 0.6, 'koordinat': (5, 0)},
                {'alan': 0.25, 'genişlik': 0.5, 'uzunluk': 0.5, 'koordinat': (10, 0)},
                {'alan': 0.36, 'genişlik': 0.6, 'uzunluk': 0.6, 'koordinat': (0, 5)},
                {'alan': 0.25, 'genişlik': 0.5, 'uzunluk': 0.5, 'koordinat': (5, 5)},
                {'alan': 0.36, 'genişlik': 0.6, 'uzunluk': 0.6, 'koordinat': (10, 5)},
            ],
            'kiriş': [
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (2.5, 0)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (7.5, 0)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (2.5, 5)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (7.5, 5)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (0, 2.5)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (5, 2.5)},
                {'uzunluk': 5.0, 'alan': 0, 'koordinat': (10, 2.5)},
            ],
            'perde': [
                {'alan': 15.0, 'genişlik': 0.3, 'uzunluk': 10, 'koordinat': (-0.15, 2.5)},
                {'alan': 7.5, 'genişlik': 0.3, 'uzunluk': 5, 'koordinat': (5, -0.15)},
            ],
            'döşeme': [
                {'alan': 125.0, 'genişlik': 10, 'uzunluk': 12.5, 'koordinat': (5, 2.5)},
            ],
            'temel': [
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (0, 0)},
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (5, 0)},
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (10, 0)},
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (0, 5)},
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (5, 5)},
                {'alan': 1.44, 'genişlik': 1.2, 'uzunluk': 1.2, 'koordinat': (10, 5)},
            ]
        }
        
        self.elements = demo_elements
        return True
    
    def analyze_file(self, uploaded_file):
        """Dosya analizi - şimdilik demo veri kullan"""
        if uploaded_file:
            st.info("📝 Demo verileri kullanılıyor (DXF parser kurulu değil)")
        
        return self.create_demo_dxf()
    
    def get_statistics(self):
        """Basit istatistikler"""
        stats = {}
        
        for element_type, elements in self.elements.items():
            if elements:
                areas = [e.get('alan', 0) for e in elements]
                lengths = [e.get('uzunluk', 0) for e in elements]
                
                stats[element_type] = {
                    'adet': len(elements),
                    'toplam_alan': sum(areas),
                    'ortalama_alan': sum(areas) / len(areas) if areas else 0,
                    'toplam_uzunluk': sum(lengths),
                    'min_alan': min(areas) if areas else 0,
                    'max_alan': max(areas) if areas else 0
                }
            else:
                stats[element_type] = {
                    'adet': 0,
                    'toplam_alan': 0,
                    'ortalama_alan': 0,
                    'toplam_uzunluk': 0,
                    'min_alan': 0,
                    'max_alan': 0
                }
        
        return stats
    
    def perform_checks(self):
        """Basit statik kontroller"""
        warnings = []
        stats = self.get_statistics()
        
        # Kolon boyut kontrolü
        column_elements = self.elements.get('kolon', [])
        small_columns = 0
        for col in column_elements:
            width = col.get('genişlik', 0)
            height = col.get('uzunluk', 0)
            if min(width, height) < 0.25:  # 25cm
                small_columns += 1
        
        if small_columns > 0:
            warnings.append(f"🚨 {small_columns} adet kolon minimum boyutun altında (25cm)")
        
        # Kiriş açıklık kontrolü
        beam_elements = self.elements.get('kiriş', [])
        long_beams = [b for b in beam_elements if b.get('uzunluk', 0) > 8]
        if long_beams:
            warnings.append(f"⚠️ {len(long_beams)} adet kiriş 8m'den uzun")
        
        # Perde oranı kontrolü
        total_floor_area = stats.get('döşeme', {}).get('toplam_alan', 0)
        total_wall_area = stats.get('perde', {}).get('toplam_alan', 0)
        
        if total_floor_area > 0:
            wall_ratio = (total_wall_area / total_floor_area) * 100
            if wall_ratio < 1.0:
                warnings.append(f"⚠️ Perde alanı oranı düşük: %{wall_ratio:.1f}")
        
        # Temel kontrolü
        column_count = stats.get('kolon', {}).get('adet', 0)
        foundation_count = stats.get('temel', {}).get('adet', 0)
        if foundation_count < column_count:
            warnings.append(f"🚨 Temel eksikliği: {foundation_count} temel / {column_count} kolon")
        
        return warnings

def main():
    st.title("🏗️ Basit DWG/DXF Yapı Elemanı Analizi")
    st.markdown("---")
    
    # Paket durumu kontrolü
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            import pandas
            st.success("✅ Pandas")
        except ImportError:
            st.error("❌ Pandas")
    
    with col2:
        try:
            import numpy
            st.success("✅ NumPy")
        except ImportError:
            st.error("❌ NumPy")
    
    with col3:
        try:
            import ezdxf
            st.success("✅ ezdxf")
        except ImportError:
            st.error("❌ ezdxf")
    
    # Sidebar
    st.sidebar.header("📁 Dosya Yükleme")
    uploaded_file = st.sidebar.file_uploader(
        "DWG veya DXF dosyası seçin",
        type=['dwg', 'dxf'],
        help="Demo modu - gerçek dosya analizi için ezdxf gerekli"
    )
    
    # Analyzer oluştur
    analyzer = SimpleStructuralAnalyzer()
    
    # Analiz yap
    if st.sidebar.button("📊 Analizi Başlat") or uploaded_file:
        with st.spinner('Analiz yapılıyor...'):
            success = analyzer.analyze_file(uploaded_file)
        
        if success:
            # Ana içerik
            tab1, tab2, tab3 = st.tabs(["📊 Genel Bakış", "📈 Detaylar", "⚠️ Kontroller"])
            
            with tab1:
                st.header("📊 Genel Bakış")
                
                stats = analyzer.get_statistics()
                
                # Metrикler
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_elements = sum(stats[key]['adet'] for key in stats)
                    st.metric("🏗️ Toplam Eleman", total_elements)
                
                with col2:
                    total_area = sum(stats[key]['toplam_alan'] for key in stats)
                    st.metric("📐 Toplam Alan", f"{total_area:.1f} m²")
                
                with col3:
                    column_count = stats['kolon']['adet']
                    st.metric("🏛️ Kolon Sayısı", column_count)
                
                with col4:
                    beam_length = stats['kiriş']['toplam_uzunluk']
                    st.metric("📏 Kiriş Uzunluğu", f"{beam_length:.1f} m")
                
                # Özet tablo
                st.subheader("📋 Eleman Özeti")
                
                summary_data = []
                for element_type, stat in stats.items():
                    summary_data.append([
                        element_type.capitalize(),
                        stat['adet'],
                        f"{stat['toplam_alan']:.2f}",
                        f"{stat['ortalama_alan']:.2f}",
                        f"{stat['toplam_uzunluk']:.2f}"
                    ])
                
                # Pandas varsa DataFrame kullan, yoksa basit tablo
                try:
                    import pandas as pd
                    df = pd.DataFrame(summary_data, columns=[
                        'Eleman Tipi', 'Adet', 'Toplam Alan (m²)', 
                        'Ortalama Alan (m²)', 'Toplam Uzunluk (m)'
                    ])
                    st.dataframe(df, use_container_width=True)
                except ImportError:
                    # Basit tablo
                    st.markdown("| Eleman Tipi | Adet | Toplam Alan (m²) | Ortalama Alan (m²) | Toplam Uzunluk (m) |")
                    st.markdown("|-------------|------|------------------|--------------------|--------------------|")
                    for row in summary_data:
                        st.markdown(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |")
            
            with tab2:
                st.header("📈 Detaylı Analiz")
                
                for element_type, elements in analyzer.elements.items():
                    if elements:
                        st.subheader(f"🔍 {element_type.capitalize()} Detayları")
                        
                        col1, col2, col3 = st.columns(3)
                        stat = stats[element_type]
                        
                        with col1:
                            st.metric("Adet", stat['adet'])
                        with col2:
                            st.metric("Min Alan", f"{stat['min_alan']:.2f} m²")
                        with col3:
                            st.metric("Max Alan", f"{stat['max_alan']:.2f} m²")
                        
                        # İlk 5 elemanı göster
                        st.write("**İlk 5 Eleman:**")
                        for i, element in enumerate(elements[:5]):
                            coord = element.get('koordinat', (0, 0))
                            alan = element.get('alan', 0)
                            st.write(f"{i+1}. Alan: {alan:.2f} m², Konum: ({coord[0]:.1f}, {coord[1]:.1f})")
                        
                        st.markdown("---")
            
            with tab3:
                st.header("⚠️ Statik Kontroller")
                
                warnings = analyzer.perform_checks()
                
                if warnings:
                    st.subheader("🚨 Tespit Edilen Sorunlar")
                    for warning in warnings:
                        if '🚨' in warning:
                            st.error(warning)
                        else:
                            st.warning(warning)
                else:
                    st.success("✅ Statik kontrollerde sorun tespit edilmedi!")
                
                # Kontrol kriterleri
                st.subheader("📋 Kontrol Kriterleri")
                
                criteria = [
                    ["Minimum Kolon Boyutu", "25 cm", "✅" if not any('kolon minimum' in w for w in warnings) else "❌"],
                    ["Maksimum Kiriş Açıklığı", "8 m", "✅" if not any('8m' in w for w in warnings) else "❌"],
                    ["Minimum Perde Oranı", "%1", "✅" if not any('Perde alanı' in w for w in warnings) else "❌"],
                    ["Temel-Kolon Uyumu", "1:1", "✅" if not any('Temel eksikliği' in w for w in warnings) else "❌"]
                ]
                
                st.markdown("| Kriter | Değer | Durum |")
                st.markdown("|--------|-------|-------|")
                for row in criteria:
                    st.markdown(f"| {row[0]} | {row[1]} | {row[2]} |")
            
            # CSV Export
            st.sidebar.markdown("---")
            st.sidebar.subheader("📄 Rapor")
            
            if st.sidebar.button("📊 CSV Raporu İndir"):
                # JSON formatında basit rapor
                report_data = {
                    'istatistikler': stats,
                    'uyarilar': warnings,
                    'tarih': str(pd.Timestamp.now()) if 'pd' in globals() else "N/A"
                }
                
                json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
                
                st.sidebar.download_button(
                    label="📁 JSON Raporu İndir",
                    data=json_str,
                    file_name="yapi_analiz_raporu.json",
                    mime="application/json"
                )
        
        else:
            st.error("❌ Dosya analiz edilemedi!")
    
    else:
        # Başlangıç sayfası
        st.markdown("""
        ## 🏗️ Basit Yapı Elemanı Analiz Uygulaması
        
        Bu, sistem paketleri ile çalışacak şekilde basitleştirilmiş versiyondur.
        
        ### 📋 Mevcut Durum:
        - ✅ **Streamlit**: Çalışıyor
        - ⚠️ **Demo Modu**: Gerçek DXF analizi için ek paketler gerekli
        
        ### 🔧 Tam Özellikler İçin Kurulum:
        ```bash
        pip3 install --user pandas numpy ezdxf plotly matplotlib reportlab
        ```
        
        ### 🎯 Bu Versiyonda:
        - ✅ Demo yapı elemanı verileri
        - ✅ Temel istatistik hesaplamaları
        - ✅ Statik kontroller
        - ✅ Basit raporlama
        
        Sol menüden "Analizi Başlat" butonuna tıklayarak demo analizi görebilirsiniz.
        """)

if __name__ == "__main__":
    main()