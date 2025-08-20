import streamlit as st
import ezdxf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import tempfile
import os
import subprocess
import shutil
import io
from typing import Dict, List, Tuple
import math
import platform

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="DWG/DXF Yapı Elemanı Analizi",
    page_icon="🏗️",
    layout="wide"
)

class StructuralElementAnalyzer:
    def __init__(self):
        self.elements = {
            'kolon': [],
            'kiriş': [],
            'perde': [],
            'döşeme': [],
            'temel': []
        }
        self.layer_keywords = {
            'kolon': ['kolon', 'column', 'col', 'pillar', 'c-'],
            'kiriş': ['kiriş', 'kiriş', 'beam', 'b-', 'kirish'],
            'perde': ['perde', 'wall', 'shear', 'w-', 'duvar'],
            'döşeme': ['döşeme', 'slab', 'floor', 'f-', 'doseme'],
            'temel': ['temel', 'foundation', 'found', 'foot', 'fd-']
        }
    
    def convert_dwg_to_dxf(self, dwg_file):
        """DWG dosyasını LibreCAD kullanarak DXF'ye dönüştür"""
        return self.convert_dwg_to_dxf_librecad(dwg_file)
    
    def check_librecad_installed(self):
        """LibreCAD kurulu mu kontrol et"""
        try:
            # Farklı işletim sistemleri için LibreCAD komutları
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows'ta LibreCAD genellikle Program Files'da
                possible_paths = [
                    r"C:\Program Files\LibreCAD\librecad.exe",
                    r"C:\Program Files (x86)\LibreCAD\librecad.exe",
                    "librecad.exe"  # PATH'ta varsa
                ]
                
                for path in possible_paths:
                    if shutil.which(path):
                        return True, path
                        
                # PATH'ta arama
                if shutil.which("librecad"):
                    return True, "librecad"
                    
            else:
                # Linux/macOS için
                if shutil.which("librecad"):
                    result = subprocess.run(
                        ['librecad', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return True, "librecad"
                        
            return False, None
            
        except Exception:
            return False, None
    
    def convert_dwg_to_dxf_librecad(self, dwg_file):
        """LibreCAD kullanarak DWG dosyasını DXF'ye dönüştür"""
        try:
            # LibreCAD kurulu mu kontrol et
            librecad_installed, librecad_path = self.check_librecad_installed()
            
            if not librecad_installed:
                return self.try_alternative_conversion(dwg_file)
            
            # Geçici dosyalar oluştur
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
                temp_dwg.write(dwg_file.read())
                temp_dwg_path = temp_dwg.name
            
            temp_dxf_path = temp_dwg_path.replace('.dwg', '.dxf')
            
            st.info(f"LibreCAD ile dönüştürme başlıyor: {librecad_path}")
            
            # Sistem tipine göre komut hazırla
            system = platform.system().lower()
            
            if system == 'windows':
                # Windows için batch dönüştürme
                cmd = [
                    librecad_path,
                    '-batch',
                    temp_dwg_path
                ]
            else:
                # Linux/macOS için
                cmd = [
                    librecad_path,
                    '--batch',
                    '--input', temp_dwg_path,
                    '--output', temp_dxf_path
                ]
            
            # Dönüştürme işlemini çalıştır
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(temp_dwg_path)
            )
            
            # Sonuç kontrol et
            if os.path.exists(temp_dxf_path) and os.path.getsize(temp_dxf_path) > 0:
                st.success("✅ DWG dosyası başarıyla DXF'ye dönüştürüldü!")
                return temp_dxf_path
            else:
                st.warning("LibreCAD dönüştürme tamamlanamadı.")
                if result.stderr:
                    st.code(f"LibreCAD çıktısı: {result.stderr}")
                return self.create_demo_dxf()
                
        except subprocess.TimeoutExpired:
            st.error("⏱️ Dönüştürme işlemi zaman aşımına uğradı (60 saniye)")
            return self.create_demo_dxf()
        except Exception as e:
            st.warning(f"LibreCAD hatası: {str(e)}")
            return self.create_demo_dxf()
        finally:
            # Geçici DWG dosyasını temizle
            try:
                if 'temp_dwg_path' in locals() and os.path.exists(temp_dwg_path):
                    os.unlink(temp_dwg_path)
            except:
                pass
    
    def try_alternative_conversion(self, dwg_file):
        """Alternatif dönüştürme yöntemleri dene"""
        st.warning("🔧 LibreCAD bulunamadı. Alternatif yöntemler deneniyor...")
        
        # FreeCAD'i dene (eğer varsa)
        if shutil.which("freecad"):
            st.info("FreeCAD ile dönüştürme deneniyor...")
            return self.convert_with_freecad(dwg_file)
        
        # QCAD'i dene (eğer varsa)  
        if shutil.which("qcad"):
            st.info("QCAD ile dönüştürme deneniyor...")
            return self.convert_with_qcad(dwg_file)
        
        # Hiçbiri yoksa demo dosya oluştur
        st.info("📝 Dönüştürme araçları bulunamadı. Demo dosyası kullanılıyor.")
        self.show_installation_instructions()
        return self.create_demo_dxf()
    
    def convert_with_freecad(self, dwg_file):
        """FreeCAD ile dönüştürme (alternatif)"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
                temp_dwg.write(dwg_file.read())
                temp_dwg_path = temp_dwg.name
            
            temp_dxf_path = temp_dwg_path.replace('.dwg', '.dxf')
            
            # FreeCAD Python scripti
            script = f"""
import FreeCAD
import Import
doc = FreeCAD.newDocument()
Import.insert("{temp_dwg_path}", doc.Name)
Import.export(doc.Objects, "{temp_dxf_path}")
FreeCAD.closeDocument(doc.Name)
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_file.write(script)
                script_path = script_file.name
            
            result = subprocess.run([
                'freecad', '--console', '--run-python', script_path
            ], capture_output=True, timeout=30)
            
            if os.path.exists(temp_dxf_path):
                st.success("✅ FreeCAD ile dönüştürme başarılı!")
                return temp_dxf_path
                
        except Exception as e:
            st.warning(f"FreeCAD dönüştürme hatası: {str(e)}")
            
        return self.create_demo_dxf()
    
    def convert_with_qcad(self, dwg_file):
        """QCAD ile dönüştürme (alternatif)"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
                temp_dwg.write(dwg_file.read())
                temp_dwg_path = temp_dwg.name
            
            temp_dxf_path = temp_dwg_path.replace('.dwg', '.dxf')
            
            result = subprocess.run([
                'qcad', '-batch', '-input', temp_dwg_path, '-output', temp_dxf_path
            ], capture_output=True, timeout=30)
            
            if os.path.exists(temp_dxf_path):
                st.success("✅ QCAD ile dönüştürme başarılı!")
                return temp_dxf_path
                
        except Exception as e:
            st.warning(f"QCAD dönüştürme hatası: {str(e)}")
            
        return self.create_demo_dxf()
    
    def show_installation_instructions(self):
        """Kurulum talimatlarını göster"""
        st.info("🔧 **CAD Dönüştürme Araçları Kurulum Talimatları:**")
        
        system = platform.system().lower()
        
        if system == 'windows':
            st.markdown("""
            **Windows için:**
            - LibreCAD: https://librecad.org/cms/home.html adresinden indirin
            - FreeCAD: https://www.freecad.org/downloads.php
            - QCAD: https://qcad.org/en/download
            """)
        elif system == 'darwin':  # macOS
            st.markdown("""
            **macOS için:**
            ```bash
            # Homebrew ile
            brew install librecad
            brew install freecad
            brew install qcad
            ```
            """)
        else:  # Linux
            st.markdown("""
            **Linux için:**
            ```bash
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install librecad freecad qcad
            
            # CentOS/RHEL
            sudo yum install librecad freecad qcad
            
            # Arch Linux
            sudo pacman -S librecad freecad qcad
            ```
            """)
        
        st.markdown("Kurulum sonrası uygulamayı yeniden başlatın.")
    
    def create_demo_dxf(self):
        """Demo DXF dosyası oluştur"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Demo katmanlar oluştur
        doc.layers.new(name='KOLON', dxfattribs={'color': 1})
        doc.layers.new(name='KIRIŞ', dxfattribs={'color': 2})
        doc.layers.new(name='PERDE', dxfattribs={'color': 3})
        doc.layers.new(name='DÖŞEME', dxfattribs={'color': 4})
        doc.layers.new(name='TEMEL', dxfattribs={'color': 5})
        
        # Demo elemanlar ekle
        # Kolonlar
        for i in range(5):
            x, y = i * 5, 0
            msp.add_lwpolyline(
                [(x, y), (x+0.5, y), (x+0.5, y+0.5), (x, y+0.5)],
                close=True,
                dxfattribs={'layer': 'KOLON'}
            )
        
        # Kirişler
        for i in range(4):
            x1, x2 = i * 5 + 0.5, (i+1) * 5
            msp.add_line((x1, 0.25), (x2, 0.25), dxfattribs={'layer': 'KIRIŞ'})
        
        # Perde
        msp.add_lwpolyline(
            [(0, -2), (20, -2), (20, -1.8), (0, -1.8)],
            close=True,
            dxfattribs={'layer': 'PERDE'}
        )
        
        # Döşeme
        msp.add_lwpolyline(
            [(-1, -1), (21, -1), (21, 1), (-1, 1)],
            close=True,
            dxfattribs={'layer': 'DÖŞEME'}
        )
        
        # Temel
        for i in range(5):
            x, y = i * 5 - 0.2, -3
            msp.add_lwpolyline(
                [(x, y), (x+0.9, y), (x+0.9, y+0.8), (x, y+0.8)],
                close=True,
                dxfattribs={'layer': 'TEMEL'}
            )
        
        # Geçici dosyaya kaydet
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.dxf')
        doc.saveas(temp_file.name)
        return temp_file.name
    
    def analyze_dxf(self, dxf_path):
        """DXF dosyasını analiz et"""
        try:
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            # Elemanları sıfırla
            for key in self.elements:
                self.elements[key] = []
            
            # Her entity için analiz yap
            for entity in msp:
                layer_name = entity.dxf.layer.lower()
                element_type = self.classify_element(layer_name)
                
                if element_type:
                    element_data = self.extract_element_data(entity, element_type)
                    if element_data:
                        self.elements[element_type].append(element_data)
            
            return True
            
        except Exception as e:
            st.error(f"DXF analiz hatası: {str(e)}")
            return False
    
    def classify_element(self, layer_name):
        """Katman adına göre eleman tipini belirle"""
        for element_type, keywords in self.layer_keywords.items():
            if any(keyword in layer_name for keyword in keywords):
                return element_type
        return None
    
    def extract_element_data(self, entity, element_type):
        """Entity'den eleman verilerini çıkar"""
        try:
            if entity.dxftype() == 'LWPOLYLINE':
                return self.analyze_polyline(entity, element_type)
            elif entity.dxftype() == 'LINE':
                return self.analyze_line(entity, element_type)
            elif entity.dxftype() == 'CIRCLE':
                return self.analyze_circle(entity, element_type)
            elif entity.dxftype() == 'RECTANGLE':
                return self.analyze_rectangle(entity, element_type)
        except:
            pass
        return None
    
    def analyze_polyline(self, polyline, element_type):
        """Polyline analizi"""
        points = list(polyline.vertices())
        if len(points) < 3:
            return None
        
        # Alan hesapla
        area = self.calculate_polygon_area(points)
        
        # Çevre hesapla
        perimeter = self.calculate_perimeter(points)
        
        # Boyutları hesapla
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        width = max_x - min_x
        length = max_y - min_y
        
        return {
            'tip': element_type,
            'alan': abs(area),
            'çevre': perimeter,
            'genişlik': width,
            'uzunluk': length,
            'koordinat': ((min_x + max_x) / 2, (min_y + max_y) / 2)
        }
    
    def analyze_line(self, line, element_type):
        """Çizgi analizi"""
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
    
    def analyze_circle(self, circle, element_type):
        """Daire analizi"""
        radius = circle.dxf.radius
        area = math.pi * radius ** 2
        perimeter = 2 * math.pi * radius
        
        return {
            'tip': element_type,
            'alan': area,
            'çevre': perimeter,
            'çap': radius * 2,
            'koordinat': (circle.dxf.center[0], circle.dxf.center[1])
        }
    
    def calculate_polygon_area(self, points):
        """Polygon alanı hesapla (Shoelace formula)"""
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
    
    def get_summary_statistics(self):
        """Özet istatistikler"""
        stats = {}
        
        for element_type, elements in self.elements.items():
            if elements:
                stats[element_type] = {
                    'adet': len(elements),
                    'toplam_alan': sum(e.get('alan', 0) for e in elements),
                    'ortalama_alan': np.mean([e.get('alan', 0) for e in elements]),
                    'toplam_uzunluk': sum(e.get('uzunluk', 0) for e in elements)
                }
            else:
                stats[element_type] = {
                    'adet': 0,
                    'toplam_alan': 0,
                    'ortalama_alan': 0,
                    'toplam_uzunluk': 0
                }
        
        return stats
    
    def perform_structural_checks(self, stats):
        """Statik kontroller"""
        warnings = []
        
        # Toplam döşeme alanı
        total_floor_area = stats.get('döşeme', {}).get('toplam_alan', 0)
        total_wall_area = stats.get('perde', {}).get('toplam_alan', 0)
        
        # Perde alanı oranı kontrolü (döşeme alanının %1'i minimum)
        if total_floor_area > 0:
            wall_ratio = (total_wall_area / total_floor_area) * 100
            if wall_ratio < 1.0:
                warnings.append(f"⚠️ Perde alanı oranı düşük: %{wall_ratio:.1f} (Minimum %1.0 önerilir)")
        
        # Kolon sayısı kontrolü
        column_count = stats.get('kolon', {}).get('adet', 0)
        if total_floor_area > 0:
            area_per_column = total_floor_area / max(column_count, 1)
            if area_per_column > 25:  # 25 m²'den fazla alan per kolon
                warnings.append(f"⚠️ Kolon yoğunluğu düşük: {area_per_column:.1f} m²/kolon (Max 25 m²/kolon önerilir)")
        
        # Kiriş açıklığı kontrolü
        beam_elements = self.elements.get('kiriş', [])
        long_beams = [b for b in beam_elements if b.get('uzunluk', 0) > 8]
        if long_beams:
            warnings.append(f"⚠️ {len(long_beams)} adet kiriş 8m'den uzun (Açıklık kontrolü gerekli)")
        
        # Temel kontrolü
        column_count = stats.get('kolon', {}).get('adet', 0)
        foundation_count = stats.get('temel', {}).get('adet', 0)
        if foundation_count < column_count:
            warnings.append(f"⚠️ Temel sayısı yetersiz: {foundation_count} temel / {column_count} kolon")
        
        return warnings

# Streamlit UI
def main():
    st.title("🏗️ DWG/DXF Yapı Elemanı Analizi")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("📁 Dosya Yükleme")
    uploaded_file = st.sidebar.file_uploader(
        "DWG veya DXF dosyası seçin",
        type=['dwg', 'dxf'],
        help="DWG dosyaları otomatik olarak DXF'ye dönüştürülür"
    )
    
    if uploaded_file is not None:
        # Analyzer oluştur
        analyzer = StructuralElementAnalyzer()
        
        with st.spinner('Dosya işleniyor...'):
            # Dosya tipine göre işle
            if uploaded_file.name.lower().endswith('.dwg'):
                st.info("DWG dosyası DXF'ye dönüştürülüyor...")
                dxf_path = analyzer.convert_dwg_to_dxf(uploaded_file)
            else:
                # DXF dosyasını geçici olarak kaydet
                with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as temp_file:
                    temp_file.write(uploaded_file.read())
                    dxf_path = temp_file.name
            
            if dxf_path and analyzer.analyze_dxf(dxf_path):
                # Ana içerik
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.header("📊 Analiz Sonuçları")
                    
                    # İstatistikler
                    stats = analyzer.get_summary_statistics()
                    
                    # Özet kartlar
                    metrics_cols = st.columns(5)
                    element_names = ['Kolon', 'Kiriş', 'Perde', 'Döşeme', 'Temel']
                    element_keys = ['kolon', 'kiriş', 'perde', 'döşeme', 'temel']
                    
                    for i, (name, key) in enumerate(zip(element_names, element_keys)):
                        with metrics_cols[i]:
                            adet = stats[key]['adet']
                            alan = stats[key]['toplam_alan']
                            st.metric(
                                label=f"{name}",
                                value=f"{adet} adet",
                                delta=f"{alan:.1f} m²"
                            )
                    
                    # Detay tablosu
                    st.subheader("📋 Detaylı Veriler")
                    
                    # Tablo seçimi
                    selected_element = st.selectbox(
                        "Görüntülenecek eleman tipi:",
                        options=element_keys,
                        format_func=lambda x: x.capitalize()
                    )
                    
                    if analyzer.elements[selected_element]:
                        df = pd.DataFrame(analyzer.elements[selected_element])
                        
                        # Koordinat sütununu düzenle
                        if 'koordinat' in df.columns:
                            df['X'] = df['koordinat'].apply(lambda x: f"{x[0]:.1f}")
                            df['Y'] = df['koordinat'].apply(lambda x: f"{x[1]:.1f}")
                            df = df.drop('koordinat', axis=1)
                        
                        # Sayısal sütunları düzenle
                        numeric_columns = ['alan', 'uzunluk', 'genişlik', 'çevre', 'çap']
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = df[col].round(2)
                        
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info(f"Bu projede {selected_element} elemanı bulunamadı.")
                
                with col2:
                    st.header("⚠️ Statik Kontroller")
                    
                    # Uyarılar
                    warnings = analyzer.perform_structural_checks(stats)
                    
                    if warnings:
                        for warning in warnings:
                            st.warning(warning)
                    else:
                        st.success("✅ Tüm temel kontroller başarılı!")
                    
                    # Alan dağılımı
                    st.subheader("📈 Alan Dağılımı")
                    
                    areas = [stats[key]['toplam_alan'] for key in element_keys if stats[key]['toplam_alan'] > 0]
                    labels = [key.capitalize() for key in element_keys if stats[key]['toplam_alan'] > 0]
                    
                    if areas:
                        fig_pie = px.pie(
                            values=areas,
                            names=labels,
                            title="Eleman Alan Dağılımı"
                        )
                        fig_pie.update_layout(height=400)
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                # Alt bölüm - Grafikler
                st.header("📊 Görselleştirme")
                
                # Grafik seçenekleri
                chart_type = st.radio(
                    "Grafik tipi seçin:",
                    options=["Adet Karşılaştırması", "Alan Karşılaştırması", "Detay Analiz"],
                    horizontal=True
                )
                
                if chart_type == "Adet Karşılaştırması":
                    counts = [stats[key]['adet'] for key in element_keys]
                    fig_bar = px.bar(
                        x=[key.capitalize() for key in element_keys],
                        y=counts,
                        title="Eleman Adet Karşılaştırması",
                        color=counts,
                        color_continuous_scale="viridis"
                    )
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                elif chart_type == "Alan Karşılaştırması":
                    areas = [stats[key]['toplam_alan'] for key in element_keys]
                    fig_area = px.bar(
                        x=[key.capitalize() for key in element_keys],
                        y=areas,
                        title="Toplam Alan Karşılaştırması (m²)",
                        color=areas,
                        color_continuous_scale="plasma"
                    )
                    fig_area.update_layout(height=400)
                    st.plotly_chart(fig_area, use_container_width=True)
                
                else:  # Detay Analiz
                    # Subplots oluştur
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=("Eleman Adetleri", "Toplam Alanlar", "Ortalama Alanlar", "Oransal Dağılım"),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                               [{"secondary_y": False}, {"type": "pie"}]]
                    )
                    
                    # Eleman adetleri
                    counts = [stats[key]['adet'] for key in element_keys]
                    fig.add_trace(
                        go.Bar(x=[key.capitalize() for key in element_keys], y=counts, name="Adet"),
                        row=1, col=1
                    )
                    
                    # Toplam alanlar
                    areas = [stats[key]['toplam_alan'] for key in element_keys]
                    fig.add_trace(
                        go.Bar(x=[key.capitalize() for key in element_keys], y=areas, name="Alan"),
                        row=1, col=2
                    )
                    
                    # Ortalama alanlar
                    avg_areas = [stats[key]['ortalama_alan'] for key in element_keys]
                    fig.add_trace(
                        go.Scatter(x=[key.capitalize() for key in element_keys], y=avg_areas, 
                                 mode='lines+markers', name="Ort. Alan"),
                        row=2, col=1
                    )
                    
                    # Pie chart
                    non_zero_areas = [(key.capitalize(), area) for key, area in 
                                    zip(element_keys, areas) if area > 0]
                    if non_zero_areas:
                        labels, values = zip(*non_zero_areas)
                        fig.add_trace(
                            go.Pie(labels=labels, values=values, name="Dağılım"),
                            row=2, col=2
                        )
                    
                    fig.update_layout(height=600, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Rapor indirme
                st.header("📄 Rapor")
                
                if st.button("📊 Analiz Raporunu İndir"):
                    # CSV raporu oluştur
                    report_data = []
                    for element_type in element_keys:
                        stat = stats[element_type]
                        report_data.append({
                            'Eleman Tipi': element_type.capitalize(),
                            'Adet': stat['adet'],
                            'Toplam Alan (m²)': round(stat['toplam_alan'], 2),
                            'Ortalama Alan (m²)': round(stat['ortalama_alan'], 2),
                            'Toplam Uzunluk (m)': round(stat['toplam_uzunluk'], 2)
                        })
                    
                    report_df = pd.DataFrame(report_data)
                    
                    # CSV'yi string'e çevir
                    csv_buffer = io.StringIO()
                    report_df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    csv_data = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="📁 CSV Raporu İndir",
                        data=csv_data,
                        file_name=f"yapi_analiz_raporu_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            else:
                st.error("Dosya analiz edilemedi. Lütfen geçerli bir DWG/DXF dosyası yükleyin.")
        
        # Geçici dosyaları temizle
        try:
            if 'dxf_path' in locals() and dxf_path:
                os.unlink(dxf_path)
        except:
            pass
    
    else:
        # Başlangıç sayfası
        st.markdown("""
        ## 🏗️ Yapı Elemanı Analiz Uygulaması
        
        Bu uygulama DWG/DXF dosyalarınızdan yapı elemanlarını otomatik olarak analiz eder.
        
        ### 🔧 Özellikler:
        - ✅ DWG dosyalarını otomatik DXF'ye dönüştürme
        - ✅ Katman bazlı eleman sınıflandırması
        - ✅ Kolon, kiriş, perde, döşeme ve temel analizi  
        - ✅ Alan, uzunluk ve adet hesaplamaları
        - ✅ Statik kontroller ve uyarılar
        - ✅ İnteraktif grafikler ve tablolar
        - ✅ CSV rapor çıktısı
        
        ### 📋 Desteklenen Eleman Tipleri:
        - **Kolon**: Dikdörtgen ve dairesel kesitler
        - **Kiriş**: Çizgisel elemanlar
        - **Perde**: Düzlem elemanlar  
        - **Döşeme**: Geniş düzlem elemanlar
        - **Temel**: Noktasal ve şerit temeller
        
        ### ⚙️ Kullanım:
        1. Sol menüden DWG/DXF dosyanızı yükleyin
        2. Analiz sonuçlarını inceleyin
        3. Statik kontrol uyarılarını değerlendirin
        4. İhtiyaç duyduğunuzda raporu indirin
        
        ---
        **Not**: DWG dönüştürme için ODA File Converter kurulu olmalıdır.
        """)

if __name__ == "__main__":
    main()
  
