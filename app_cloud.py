import streamlit as st
import ezdxf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import tempfile
import os
import io
import logging
import json
import time
from typing import Dict, List, Tuple, Optional
import math
from pathlib import Path
import base64

# Streamlit Cloud için basitleştirilmiş imports
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    st.warning("⚠️ Matplotlib kurulu değil, plan görünümü devre dışı")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    st.warning("⚠️ ReportLab kurulu değil, PDF rapor devre dışı")

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="DWG/DXF Yapı Elemanı Analizi",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Konfigürasyon
CONFIG = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB (Streamlit Cloud limiti)
    'supported_formats': ['.dwg', '.dxf'],
    'timeout_seconds': 120,
    'min_column_size': 0.25,  # 25cm
    'max_beam_span': 8.0,     # 8m
    'min_wall_ratio': 0.01,   # %1
    'max_area_per_column': 25.0  # 25m²
}

class CloudStructuralAnalyzer:
    def __init__(self):
        self.elements = {
            'kolon': [],
            'kiriş': [],
            'perde': [],
            'döşeme': [],
            'temel': []
        }
        self.layer_keywords = {
            'kolon': ['kolon', 'column', 'col', 'pillar', 'c-', 'c_', 'sütun'],
            'kiriş': ['kiriş', 'beam', 'b-', 'b_', 'kirish'],
            'perde': ['perde', 'wall', 'shear', 'w-', 'w_', 'duvar'],
            'döşeme': ['döşeme', 'slab', 'floor', 'f-', 'f_', 'doseme'],
            'temel': ['temel', 'foundation', 'found', 'foot', 'fd-', 'fd_']
        }
        self.analysis_results = {}
        self.warnings = []
    
    def validate_file(self, file) -> bool:
        """Dosya validasyonu"""
        try:
            if file.size > CONFIG['max_file_size']:
                st.error(f"Dosya boyutu çok büyük! Maksimum {CONFIG['max_file_size']//1024//1024}MB")
                return False
            
            file_extension = Path(file.name).suffix.lower()
            if file_extension not in CONFIG['supported_formats']:
                st.error(f"Desteklenmeyen dosya formatı: {file_extension}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Dosya validasyon hatası: {e}")
            return False
    
    def create_demo_dxf(self):
        """Demo DXF oluştur"""
        try:
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Demo katmanlar
            doc.layers.new(name='KOLON', dxfattribs={'color': 1})
            doc.layers.new(name='KIRIŞ', dxfattribs={'color': 2})
            doc.layers.new(name='PERDE', dxfattribs={'color': 3})
            doc.layers.new(name='DÖŞEME', dxfattribs={'color': 4})
            doc.layers.new(name='TEMEL', dxfattribs={'color': 5})
            
            # Demo elemanlar - 4x4 grid
            for i in range(4):
                for j in range(4):
                    x, y = i * 5, j * 5
                    size = 0.5
                    # Kolonlar
                    msp.add_lwpolyline([
                        (x, y), (x + size, y), (x + size, y + size), (x, y + size)
                    ], close=True, dxfattribs={'layer': 'KOLON'})
                    
                    # Temeller
                    foundation_size = 1.2
                    offset = (foundation_size - size) / 2
                    msp.add_lwpolyline([
                        (x - offset, y - offset), 
                        (x + foundation_size - offset, y - offset),
                        (x + foundation_size - offset, y + foundation_size - offset), 
                        (x - offset, y + foundation_size - offset)
                    ], close=True, dxfattribs={'layer': 'TEMEL'})
            
            # Kirişler - Grid bağlantıları
            for i in range(3):
                for j in range(4):
                    x1, x2 = i * 5 + 0.5, (i + 1) * 5
                    msp.add_line((x1, j * 5 + 0.25), (x2, j * 5 + 0.25), 
                                dxfattribs={'layer': 'KIRIŞ'})
            
            for i in range(4):
                for j in range(3):
                    y1, y2 = j * 5 + 0.5, (j + 1) * 5
                    msp.add_line((i * 5 + 0.25, y1), (i * 5 + 0.25, y2), 
                                dxfattribs={'layer': 'KIRIŞ'})
            
            # Perdeler - Çevre duvarlar
            msp.add_lwpolyline([
                (0, 0), (15, 0), (15, 0.3), (0, 0.3)
            ], close=True, dxfattribs={'layer': 'PERDE'})
            
            msp.add_lwpolyline([
                (0, 15), (15, 15), (15, 15.3), (0, 15.3)
            ], close=True, dxfattribs={'layer': 'PERDE'})
            
            # Döşeme
            msp.add_lwpolyline([
                (0.3, 0.3), (14.7, 0.3), (14.7, 14.7), (0.3, 14.7)
            ], close=True, dxfattribs={'layer': 'DÖŞEME'})
            
            # Geçici dosyaya kaydet
            temp_path = tempfile.mktemp(suffix='.dxf')
            doc.saveas(temp_path)
            return temp_path
            
        except Exception as e:
            logger.error(f"Demo DXF oluşturma hatası: {e}")
            return None
    
    def analyze_dxf(self, dxf_path: str) -> bool:
        """DXF analizi"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📖 DXF dosyası okunuyor...")
            progress_bar.progress(0.2)
            
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            # Elemanları sıfırla
            for key in self.elements:
                self.elements[key] = []
            
            status_text.text("🔍 Elemanlar analiz ediliyor...")
            progress_bar.progress(0.5)
            
            # Her entity için analiz
            for entity in msp:
                try:
                    layer_name = entity.dxf.layer.lower()
                    element_type = self.classify_element(layer_name)
                    
                    if element_type:
                        element_data = self.extract_element_data(entity, element_type)
                        if element_data:
                            self.elements[element_type].append(element_data)
                except:
                    continue  # Hatalı entity'leri atla
            
            status_text.text("📊 İstatistikler hesaplanıyor...")
            progress_bar.progress(0.8)
            
            self.analysis_results = self.get_statistics()
            self.warnings = self.perform_checks()
            
            progress_bar.progress(1.0)
            status_text.text("✅ Analiz tamamlandı!")
            
            return True
            
        except Exception as e:
            st.error(f"DXF analiz hatası: {str(e)}")
            return False
    
    def classify_element(self, layer_name: str) -> Optional[str]:
        """Eleman sınıflandırması"""
        layer_name = layer_name.lower().strip()
        
        for element_type, keywords in self.layer_keywords.items():
            if any(keyword in layer_name for keyword in keywords):
                return element_type
        return None
    
    def extract_element_data(self, entity, element_type: str) -> Optional[Dict]:
        """Eleman veri çıkarımı"""
        try:
            if entity.dxftype() == 'LWPOLYLINE':
                return self.analyze_polyline(entity, element_type)
            elif entity.dxftype() == 'LINE':
                return self.analyze_line(entity, element_type)
            elif entity.dxftype() == 'CIRCLE':
                return self.analyze_circle(entity, element_type)
        except:
            pass
        return None
    
    def analyze_polyline(self, polyline, element_type):
        """Polyline analizi"""
        try:
            points = list(polyline.vertices())
            if len(points) < 3:
                return None
            
            # Alan hesapla (Shoelace formula)
            area = self.calculate_polygon_area(points)
            perimeter = self.calculate_perimeter(points)
            
            # Bounding box
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            width = max_x - min_x
            height = max_y - min_y
            
            return {
                'tip': element_type,
                'alan': abs(area),
                'çevre': perimeter,
                'genişlik': width,
                'uzunluk': height,
                'koordinat': ((min_x + max_x) / 2, (min_y + max_y) / 2)
            }
        except:
            return None
    
    def analyze_line(self, line, element_type):
        """Çizgi analizi"""
        try:
            start = line.dxf.start
            end = line.dxf.end
            length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            
            return {
                'tip': element_type,
                'uzunluk': length,
                'alan': 0,
                'genişlik': 0,
                'koordinat': ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            }
        except:
            return None
    
    def analyze_circle(self, circle, element_type):
        """Daire analizi"""
        try:
            radius = circle.dxf.radius
            area = math.pi * radius ** 2
            
            return {
                'tip': element_type,
                'alan': area,
                'çap': radius * 2,
                'koordinat': (circle.dxf.center[0], circle.dxf.center[1])
            }
        except:
            return None
    
    def calculate_polygon_area(self, points):
        """Polygon alanı"""
        n = len(points)
        if n < 3:
            return 0
        
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return area / 2
    
    def calculate_perimeter(self, points):
        """Çevre hesapla"""
        if len(points) < 2:
            return 0
        
        perimeter = 0
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            dx = points[next_i][0] - points[i][0]
            dy = points[next_i][1] - points[i][1]
            perimeter += math.sqrt(dx**2 + dy**2)
        
        return perimeter
    
    def get_statistics(self):
        """İstatistikler"""
        stats = {}
        
        for element_type, elements in self.elements.items():
            if elements:
                areas = [e.get('alan', 0) for e in elements]
                lengths = [e.get('uzunluk', 0) for e in elements]
                
                stats[element_type] = {
                    'adet': len(elements),
                    'toplam_alan': sum(areas),
                    'ortalama_alan': np.mean(areas) if areas else 0,
                    'toplam_uzunluk': sum(lengths)
                }
            else:
                stats[element_type] = {
                    'adet': 0,
                    'toplam_alan': 0,
                    'ortalama_alan': 0,
                    'toplam_uzunluk': 0
                }
        
        return stats
    
    def perform_checks(self):
        """Statik kontroller"""
        warnings = []
        stats = self.analysis_results
        
        # Perde oranı kontrolü
        total_floor_area = stats.get('döşeme', {}).get('toplam_alan', 0)
        total_wall_area = stats.get('perde', {}).get('toplam_alan', 0)
        
        if total_floor_area > 0:
            wall_ratio = (total_wall_area / total_floor_area) * 100
            if wall_ratio < CONFIG['min_wall_ratio'] * 100:
                warnings.append(f"🚨 Perde alanı oranı düşük: %{wall_ratio:.1f}")
        
        # Kolon kontrolleri
        column_elements = self.elements.get('kolon', [])
        small_columns = 0
        for col in column_elements:
            width = col.get('genişlik', 0)
            height = col.get('uzunluk', 0)
            if min(width, height) < CONFIG['min_column_size']:
                small_columns += 1
        
        if small_columns > 0:
            warnings.append(f"🚨 {small_columns} adet kolon minimum boyutun altında")
        
        # Kiriş kontrolleri
        beam_elements = self.elements.get('kiriş', [])
        long_beams = [b for b in beam_elements if b.get('uzunluk', 0) > CONFIG['max_beam_span']]
        if long_beams:
            warnings.append(f"⚠️ {len(long_beams)} adet kiriş çok uzun")
        
        # Temel kontrolü
        column_count = stats.get('kolon', {}).get('adet', 0)
        foundation_count = stats.get('temel', {}).get('adet', 0)
        if foundation_count < column_count:
            warnings.append(f"🚨 Temel eksikliği: {foundation_count}/{column_count}")
        
        return warnings
    
    def create_visualizations(self):
        """Görselleştirmeler"""
        visualizations = {}
        
        # Eleman dağılımı
        element_counts = [len(self.elements[key]) for key in self.elements.keys() if len(self.elements[key]) > 0]
        element_names = [key.capitalize() for key in self.elements.keys() if len(self.elements[key]) > 0]
        
        if element_counts:
            fig_pie = px.pie(
                values=element_counts, 
                names=element_names,
                title="Eleman Dağılımı"
            )
            visualizations['pie_chart'] = fig_pie
            
            # Bar chart
            fig_bar = px.bar(
                x=element_names,
                y=element_counts,
                title="Eleman Sayıları"
            )
            visualizations['bar_chart'] = fig_bar
        
        # Kolon konumları
        if self.elements['kolon']:
            col_x = [col['koordinat'][0] for col in self.elements['kolon']]
            col_y = [col['koordinat'][1] for col in self.elements['kolon']]
            col_areas = [col.get('alan', 0) for col in self.elements['kolon']]
            
            fig_scatter = go.Figure(data=go.Scatter(
                x=col_x, y=col_y,
                mode='markers',
                marker=dict(
                    size=[max(10, area * 100) for area in col_areas],
                    color=col_areas,
                    colorscale='Reds',
                    showscale=True
                ),
                text=[f"Alan: {area:.2f} m²" for area in col_areas]
            ))
            fig_scatter.update_layout(title="Kolon Konumları")
            visualizations['scatter_plot'] = fig_scatter
        
        return visualizations

def main():
    st.title("🏗️ DWG/DXF Yapı Elemanı Analizi")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("📁 Dosya Yükleme")
    uploaded_file = st.sidebar.file_uploader(
        "DWG veya DXF dosyası seçin",
        type=['dwg', 'dxf'],
        help="Maksimum dosya boyutu: 50MB"
    )
    
    # Demo modu
    use_demo = st.sidebar.checkbox("📝 Demo Modu", value=not uploaded_file)
    
    if st.sidebar.button("🚀 Analizi Başlat") or uploaded_file or use_demo:
        # Analyzer oluştur
        analyzer = CloudStructuralAnalyzer()
        
        with st.spinner('🔄 Analiz yapılıyor...'):
            if use_demo or not uploaded_file:
                # Demo analizi
                st.info("📝 Demo verileri kullanılıyor")
                dxf_path = analyzer.create_demo_dxf()
                success = analyzer.analyze_dxf(dxf_path) if dxf_path else False
            else:
                # Gerçek dosya analizi
                if analyzer.validate_file(uploaded_file):
                    if uploaded_file.name.lower().endswith('.dwg'):
                        st.warning("⚠️ DWG dosyaları için DXF'ye dönüştürme gerekli. Demo modu kullanılıyor.")
                        dxf_path = analyzer.create_demo_dxf()
                        success = analyzer.analyze_dxf(dxf_path) if dxf_path else False
                    else:
                        # DXF dosyasını geçici olarak kaydet
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as temp_file:
                            temp_file.write(uploaded_file.read())
                            dxf_path = temp_file.name
                        success = analyzer.analyze_dxf(dxf_path)
                else:
                    success = False
        
        if success:
            # Sekmeli arayüz
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Genel Bakış", 
                "📈 Detaylar", 
                "⚠️ Kontroller",
                "📊 Grafikler"
            ])
            
            with tab1:
                st.header("📊 Genel Bakış")
                
                stats = analyzer.analysis_results
                
                # KPI metrikleri
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
                    summary_data.append({
                        'Eleman Tipi': element_type.capitalize(),
                        'Adet': stat['adet'],
                        'Toplam Alan (m²)': round(stat['toplam_alan'], 2),
                        'Ortalama Alan (m²)': round(stat['ortalama_alan'], 2),
                        'Toplam Uzunluk (m)': round(stat['toplam_uzunluk'], 2)
                    })
                
                df_summary = pd.DataFrame(summary_data)
                st.dataframe(df_summary, use_container_width=True)
            
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
                            st.metric("Toplam Alan", f"{stat['toplam_alan']:.2f} m²")
                        with col3:
                            st.metric("Ortalama Alan", f"{stat['ortalama_alan']:.2f} m²")
                        
                        # İlk 10 elemanı göster
                        if len(elements) > 0:
                            element_details = []
                            for i, element in enumerate(elements[:10]):
                                detail = {
                                    'ID': i + 1,
                                    'Alan (m²)': round(element.get('alan', 0), 2),
                                    'Genişlik (m)': round(element.get('genişlik', 0), 2),
                                    'Uzunluk (m)': round(element.get('uzunluk', 0), 2),
                                    'X': round(element.get('koordinat', (0, 0))[0], 2),
                                    'Y': round(element.get('koordinat', (0, 0))[1], 2)
                                }
                                element_details.append(detail)
                            
                            df_details = pd.DataFrame(element_details)
                            st.dataframe(df_details, use_container_width=True)
                        
                        st.markdown("---")
            
            with tab3:
                st.header("⚠️ Statik Kontroller")
                
                if analyzer.warnings:
                    st.subheader("🚨 Tespit Edilen Sorunlar")
                    for warning in analyzer.warnings:
                        if '🚨' in warning:
                            st.error(warning)
                        else:
                            st.warning(warning)
                else:
                    st.success("✅ Statik kontrollerde sorun tespit edilmedi!")
                
                # Kontrol kriterleri
                st.subheader("📋 Kontrol Kriterleri")
                
                criteria_data = [
                    ['Minimum Kolon Boyutu', '25 cm', '✅' if not any('kolon minimum' in w for w in analyzer.warnings) else '❌'],
                    ['Maksimum Kiriş Açıklığı', '8 m', '✅' if not any('çok uzun' in w for w in analyzer.warnings) else '❌'],
                    ['Minimum Perde Oranı', '%1', '✅' if not any('Perde alanı' in w for w in analyzer.warnings) else '❌'],
                    ['Temel-Kolon Uyumu', '1:1', '✅' if not any('Temel eksikliği' in w for w in analyzer.warnings) else '❌']
                ]
                
                df_criteria = pd.DataFrame(criteria_data, columns=['Kriter', 'Değer', 'Durum'])
                st.dataframe(df_criteria, use_container_width=True)
            
            with tab4:
                st.header("📊 Görselleştirmeler")
                
                visualizations = analyzer.create_visualizations()
                
                for viz_name, fig in visualizations.items():
                    st.plotly_chart(fig, use_container_width=True)
            
            # Rapor indirme
            st.sidebar.markdown("---")
            st.sidebar.subheader("📄 Rapor")
            
            if st.sidebar.button("📊 JSON Raporu İndir"):
                report_data = {
                    'istatistikler': stats,
                    'uyarilar': analyzer.warnings,
                    'tarih': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
                
                st.sidebar.download_button(
                    label="📁 JSON Raporu İndir",
                    data=json_str,
                    file_name=f"yapi_analiz_raporu_{int(time.time())}.json",
                    mime="application/json"
                )
        
        else:
            st.error("❌ Dosya analiz edilemedi!")
        
        # Geçici dosyaları temizle
        try:
            if 'dxf_path' in locals() and dxf_path and os.path.exists(dxf_path):
                os.unlink(dxf_path)
        except:
            pass
    
    else:
        # Başlangıç sayfası
        st.markdown("""
        ## 🏗️ Yapı Elemanı Analiz Uygulaması
        
        Bu uygulama DWG/DXF dosyalarınızdan yapı elemanlarını otomatik olarak analiz eder.
        
        ### ✨ Özellikler:
        - ✅ **DXF Dosya Desteği**: Otomatik eleman tanıma
        - ✅ **Demo Modu**: Örnek analiz sonuçları
        - ✅ **İnteraktif Grafikler**: Plotly ile görselleştirme
        - ✅ **Statik Kontroller**: TBDY 2018 uyumlu
        - ✅ **JSON Rapor**: Detaylı analiz çıktısı
        
        ### 📋 Analiz Edilen Elemanlar:
        - **🏛️ Kolonlar**: Boyut ve alan analizi
        - **📏 Kirişler**: Uzunluk ve açıklık kontrolü
        - **🧱 Perdeler**: Alan ve oran hesaplamaları
        - **🏢 Döşemeler**: Alan dağılımı
        - **🏗️ Temeller**: Adet ve kolon uyumu
        
        ### 🚀 Kullanım:
        1. Sol menüden dosya yükleyin veya demo modunu seçin
        2. "Analizi Başlat" butonuna tıklayın
        3. Sonuçları sekmelerde inceleyin
        4. İhtiyaç duyduğunuzda raporu indirin
        
        ---
        **Streamlit Cloud Optimized Version**
        """)

if __name__ == "__main__":
    main()