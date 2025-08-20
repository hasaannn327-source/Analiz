import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ezdxf
import numpy as np
import io
import tempfile
import os
from typing import Dict, List, Tuple
import re
from dataclasses import dataclass
import math

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="CAD Dosya Analiz Uygulaması",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class StructuralElement:
    """Yapısal eleman veri sınıfı"""
    element_type: str
    layer: str
    length: float = 0.0
    area: float = 0.0
    width: float = 0.0
    height: float = 0.0
    coordinates: List[Tuple[float, float]] = None
    
    def __post_init__(self):
        if self.coordinates is None:
            self.coordinates = []

class CADAnalyzer:
    """CAD dosya analiz sınıfı"""
    
    def __init__(self):
        self.elements = []
        self.layer_mapping = {
            'kolon': ['kolon', 'column', 'col', 'pillar', 'sütun'],
            'kiriş': ['kiriş', 'beam', 'kirish', 'träger'],
            'perde': ['perde', 'wall', 'shear_wall', 'duvar'],
            'döşeme': ['döşeme', 'slab', 'doseme', 'floor', 'platte'],
            'temel': ['temel', 'foundation', 'fundament', 'footing']
        }
    
    def identify_element_type(self, layer_name: str) -> str:
        """Katman adından eleman tipini belirler"""
        layer_lower = layer_name.lower()
        
        for element_type, keywords in self.layer_mapping.items():
            for keyword in keywords:
                if keyword in layer_lower:
                    return element_type
        
        return 'diğer'
    
    def calculate_line_length(self, entity) -> float:
        """Çizgi uzunluğunu hesaplar"""
        if hasattr(entity, 'start') and hasattr(entity, 'end'):
            start = entity.start
            end = entity.end
            return math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
        return 0.0
    
    def calculate_polyline_length(self, entity) -> float:
        """Polyline uzunluğunu hesaplar"""
        total_length = 0.0
        if hasattr(entity, 'vertices'):
            vertices = list(entity.vertices)
            for i in range(len(vertices) - 1):
                v1, v2 = vertices[i], vertices[i + 1]
                length = math.sqrt((v2[0] - v1[0])**2 + (v2[1] - v1[1])**2)
                total_length += length
            
            # Kapalı polyline ise son ve ilk nokta arası mesafe
            if entity.is_closed and len(vertices) > 2:
                v_last, v_first = vertices[-1], vertices[0]
                length = math.sqrt((v_first[0] - v_last[0])**2 + (v_first[1] - v_last[1])**2)
                total_length += length
                
        return total_length
    
    def calculate_rectangle_area(self, entity) -> Tuple[float, float, float]:
        """Dikdörtgen alan, genişlik ve yükseklik hesaplar"""
        if hasattr(entity, 'vertices'):
            vertices = list(entity.vertices)
            if len(vertices) >= 4:
                # İlk iki kenar uzunluğunu hesapla
                width = abs(vertices[1][0] - vertices[0][0])
                height = abs(vertices[2][1] - vertices[1][1])
                area = width * height
                return area, width, height
        return 0.0, 0.0, 0.0
    
    def extract_dimensions_from_text(self, text: str) -> Tuple[float, float]:
        """Metin içinden boyut bilgilerini çıkarır"""
        # 30x50, 30X50, 30*50 formatlarını tanır
        pattern = r'(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)'
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)), float(match.group(2))
        return 0.0, 0.0
    
    def analyze_dxf_file(self, file_content: bytes) -> Dict:
        """DXF dosyasını analiz eder"""
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # DXF dosyasını oku
            doc = ezdxf.readfile(temp_file_path)
            msp = doc.modelspace()
            
            self.elements = []
            layer_stats = {}
            
            # Katman bilgilerini topla
            for entity in msp:
                layer_name = entity.dxf.layer
                element_type = self.identify_element_type(layer_name)
                
                if layer_name not in layer_stats:
                    layer_stats[layer_name] = {'count': 0, 'type': element_type}
                layer_stats[layer_name]['count'] += 1
                
                # Eleman analizi
                element = StructuralElement(
                    element_type=element_type,
                    layer=layer_name
                )
                
                # Entity tipine göre hesaplamalar
                if entity.dxftype() == 'LINE':
                    element.length = self.calculate_line_length(entity)
                    
                elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    element.length = self.calculate_polyline_length(entity)
                    if entity.is_closed:
                        area, width, height = self.calculate_rectangle_area(entity)
                        element.area = area
                        element.width = width
                        element.height = height
                
                elif entity.dxftype() == 'CIRCLE':
                    if hasattr(entity.dxf, 'radius'):
                        radius = entity.dxf.radius
                        element.area = math.pi * radius**2
                        element.width = element.height = 2 * radius
                
                elif entity.dxftype() == 'TEXT':
                    if hasattr(entity.dxf, 'text'):
                        width, height = self.extract_dimensions_from_text(entity.dxf.text)
                        if width > 0 and height > 0:
                            element.width = width
                            element.height = height
                            element.area = width * height
                
                if element.length > 0 or element.area > 0:
                    self.elements.append(element)
            
            # Geçici dosyayı temizle
            os.unlink(temp_file_path)
            
            return {
                'success': True,
                'layer_stats': layer_stats,
                'total_elements': len(self.elements)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_element_summary(self) -> pd.DataFrame:
        """Eleman özetini DataFrame olarak döndürür"""
        summary_data = []
        
        # Element türlerine göre gruplama
        element_groups = {}
        for element in self.elements:
            if element.element_type not in element_groups:
                element_groups[element.element_type] = []
            element_groups[element.element_type].append(element)
        
        for element_type, elements in element_groups.items():
            total_count = len(elements)
            total_length = sum(e.length for e in elements)
            total_area = sum(e.area for e in elements)
            avg_width = np.mean([e.width for e in elements if e.width > 0]) if any(e.width > 0 for e in elements) else 0
            avg_height = np.mean([e.height for e in elements if e.height > 0]) if any(e.height > 0 for e in elements) else 0
            
            summary_data.append({
                'Eleman Tipi': element_type.title(),
                'Adet': total_count,
                'Toplam Uzunluk (m)': round(total_length, 2),
                'Toplam Alan (m²)': round(total_area, 2),
                'Ortalama Genişlik (cm)': round(avg_width, 1) if avg_width > 0 else '-',
                'Ortalama Yükseklik (cm)': round(avg_height, 1) if avg_height > 0 else '-'
            })
        
        return pd.DataFrame(summary_data)
    
    def get_detailed_analysis(self) -> Dict:
        """Detaylı analiz sonuçları"""
        analysis = {
            'kolon_analysis': self._analyze_columns(),
            'beam_analysis': self._analyze_beams(),
            'wall_analysis': self._analyze_walls(),
            'slab_analysis': self._analyze_slabs(),
            'foundation_analysis': self._analyze_foundations()
        }
        return analysis
    
    def _analyze_columns(self) -> Dict:
        """Kolon analizi"""
        columns = [e for e in self.elements if e.element_type == 'kolon']
        if not columns:
            return {'count': 0, 'warnings': []}
        
        warnings = []
        total_area = sum(c.area for c in columns)
        
        # Boyut kontrolü
        small_columns = [c for c in columns if c.width > 0 and c.height > 0 and (c.width < 25 or c.height < 25)]
        if small_columns:
            warnings.append(f"⚠️ {len(small_columns)} adet kolon boyutu 25cm'den küçük!")
        
        return {
            'count': len(columns),
            'total_area': total_area,
            'warnings': warnings,
            'avg_dimensions': {
                'width': np.mean([c.width for c in columns if c.width > 0]),
                'height': np.mean([c.height for c in columns if c.height > 0])
            }
        }
    
    def _analyze_beams(self) -> Dict:
        """Kiriş analizi"""
        beams = [e for e in self.elements if e.element_type == 'kiriş']
        if not beams:
            return {'count': 0, 'warnings': []}
        
        warnings = []
        lengths = [b.length for b in beams if b.length > 0]
        
        # Uzun açıklık kontrolü
        long_beams = [l for l in lengths if l > 800]  # 8m üzeri
        if long_beams:
            warnings.append(f"⚠️ {len(long_beams)} adet kiriş 8m'den uzun açıklıkta!")
        
        return {
            'count': len(beams),
            'total_length': sum(lengths),
            'max_span': max(lengths) if lengths else 0,
            'avg_span': np.mean(lengths) if lengths else 0,
            'warnings': warnings
        }
    
    def _analyze_walls(self) -> Dict:
        """Perde analizi"""
        walls = [e for e in self.elements if e.element_type == 'perde']
        if not walls:
            return {'count': 0, 'warnings': []}
        
        warnings = []
        total_area = sum(w.area for w in walls)
        
        # Perde oranı kontrolü (toplam kat alanının %0.2'si minimum)
        slab_area = sum(s.area for s in self.elements if s.element_type == 'döşeme')
        if slab_area > 0:
            wall_ratio = (total_area / slab_area) * 100
            if wall_ratio < 0.2:
                warnings.append(f"⚠️ Perde alanı oranı düşük: %{wall_ratio:.1f} (Min: %0.2)")
        
        return {
            'count': len(walls),
            'total_area': total_area,
            'wall_ratio': wall_ratio if 'wall_ratio' in locals() else 0,
            'warnings': warnings
        }
    
    def _analyze_slabs(self) -> Dict:
        """Döşeme analizi"""
        slabs = [e for e in self.elements if e.element_type == 'döşeme']
        return {
            'count': len(slabs),
            'total_area': sum(s.area for s in slabs),
            'warnings': []
        }
    
    def _analyze_foundations(self) -> Dict:
        """Temel analizi"""
        foundations = [e for e in self.elements if e.element_type == 'temel']
        return {
            'count': len(foundations),
            'total_area': sum(f.area for f in foundations),
            'warnings': []
        }

# Streamlit Uygulaması
def main():
    st.title("🏗️ CAD Dosya Analiz Uygulaması")
    st.markdown("DWG/DXF dosyalarınızı yükleyip yapısal elemanları analiz edin")
    
    # Sidebar
    st.sidebar.header("📁 Dosya Yükleme")
    uploaded_file = st.sidebar.file_uploader(
        "DXF dosyası seçin",
        type=['dxf'],
        help="Sadece DXF formatı desteklenmektedir"
    )
    
    if uploaded_file is not None:
        # Dosya yüklendi
        st.sidebar.success(f"✅ {uploaded_file.name} yüklendi")
        
        # Analiz sınıfını başlat
        analyzer = CADAnalyzer()
        
        # Dosyayı analiz et
        with st.spinner('Dosya analiz ediliyor...'):
            file_content = uploaded_file.read()
            result = analyzer.analyze_dxf_file(file_content)
        
        if result['success']:
            st.success(f"✅ Dosya başarıyla analiz edildi! {result['total_elements']} eleman bulundu.")
            
            # Ana içerik
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Genel Özet", "📈 Grafikler", "🔍 Detaylı Analiz", "⚠️ Kontroller"])
            
            with tab1:
                st.header("Eleman Özeti")
                summary_df = analyzer.get_element_summary()
                
                if not summary_df.empty:
                    st.dataframe(summary_df, use_container_width=True)
                    
                    # İstatistikler
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_elements = summary_df['Adet'].sum()
                        st.metric("Toplam Eleman", total_elements)
                    
                    with col2:
                        total_length = summary_df['Toplam Uzunluk (m)'].sum()
                        st.metric("Toplam Uzunluk", f"{total_length:.1f} m")
                    
                    with col3:
                        total_area = summary_df['Toplam Alan (m²)'].sum()
                        st.metric("Toplam Alan", f"{total_area:.1f} m²")
                    
                    with col4:
                        unique_types = len(summary_df)
                        st.metric("Eleman Çeşidi", unique_types)
                
                else:
                    st.warning("Analiz edilebilir eleman bulunamadı.")
            
            with tab2:
                st.header("Görselleştirmeler")
                summary_df = analyzer.get_element_summary()
                
                if not summary_df.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Eleman dağılım grafiği
                        fig_pie = px.pie(
                            summary_df, 
                            values='Adet', 
                            names='Eleman Tipi',
                            title="Eleman Dağılımı"
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Alan dağılım grafiği
                        fig_area = px.bar(
                            summary_df,
                            x='Eleman Tipi',
                            y='Toplam Alan (m²)',
                            title="Eleman Tiplerine Göre Alan Dağılımı"
                        )
                        st.plotly_chart(fig_area, use_container_width=True)
                    
                    # Uzunluk grafiği
                    fig_length = px.bar(
                        summary_df,
                        x='Eleman Tipi',
                        y='Toplam Uzunluk (m)',
                        title="Eleman Tiplerine Göre Uzunluk Dağılımı",
                        color='Eleman Tipi'
                    )
                    st.plotly_chart(fig_length, use_container_width=True)
            
            with tab3:
                st.header("Detaylı Analiz")
                detailed_analysis = analyzer.get_detailed_analysis()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Kolon analizi
                    st.subheader("🏛️ Kolon Analizi")
                    col_analysis = detailed_analysis['kolon_analysis']
                    st.write(f"**Adet:** {col_analysis['count']}")
                    if col_analysis['count'] > 0:
                        st.write(f"**Toplam Alan:** {col_analysis['total_area']:.2f} m²")
                        if 'avg_dimensions' in col_analysis:
                            avg_dims = col_analysis['avg_dimensions']
                            st.write(f"**Ortalama Boyutlar:** {avg_dims['width']:.1f} x {avg_dims['height']:.1f} cm")
                    
                    # Perde analizi
                    st.subheader("🧱 Perde Analizi")
                    wall_analysis = detailed_analysis['wall_analysis']
                    st.write(f"**Adet:** {wall_analysis['count']}")
                    if wall_analysis['count'] > 0:
                        st.write(f"**Toplam Alan:** {wall_analysis['total_area']:.2f} m²")
                        if wall_analysis['wall_ratio'] > 0:
                            st.write(f"**Perde Oranı:** %{wall_analysis['wall_ratio']:.2f}")
                
                with col2:
                    # Kiriş analizi
                    st.subheader("🏗️ Kiriş Analizi")
                    beam_analysis = detailed_analysis['beam_analysis']
                    st.write(f"**Adet:** {beam_analysis['count']}")
                    if beam_analysis['count'] > 0:
                        st.write(f"**Toplam Uzunluk:** {beam_analysis['total_length']:.2f} m")
                        st.write(f"**Maksimum Açıklık:** {beam_analysis['max_span']:.2f} m")
                        st.write(f"**Ortalama Açıklık:** {beam_analysis['avg_span']:.2f} m")
                    
                    # Döşeme analizi
                    st.subheader("🏢 Döşeme Analizi")
                    slab_analysis = detailed_analysis['slab_analysis']
                    st.write(f"**Adet:** {slab_analysis['count']}")
                    if slab_analysis['count'] > 0:
                        st.write(f"**Toplam Alan:** {slab_analysis['total_area']:.2f} m²")
                
                # Temel analizi
                st.subheader("🏗️ Temel Analizi")
                foundation_analysis = detailed_analysis['foundation_analysis']
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Adet:** {foundation_analysis['count']}")
                with col2:
                    if foundation_analysis['count'] > 0:
                        st.write(f"**Toplam Alan:** {foundation_analysis['total_area']:.2f} m²")
            
            with tab4:
                st.header("Statik Kontroller")
                detailed_analysis = analyzer.get_detailed_analysis()
                
                # Tüm uyarıları topla
                all_warnings = []
                for analysis_type, analysis in detailed_analysis.items():
                    all_warnings.extend(analysis.get('warnings', []))
                
                if all_warnings:
                    st.error("🚨 Tespit Edilen Sorunlar:")
                    for warning in all_warnings:
                        st.warning(warning)
                else:
                    st.success("✅ Kritik sorun tespit edilmedi!")
                
                # Kontrol kriterleri
                st.subheader("📋 Kontrol Kriterleri")
                
                criteria_data = [
                    {"Kriter": "Minimum Kolon Boyutu", "Değer": "25cm x 25cm", "Durum": "✅" if not any("kolon boyutu" in w for w in all_warnings) else "❌"},
                    {"Kriter": "Maksimum Kiriş Açıklığı", "Değer": "8.00m", "Durum": "✅" if not any("8m'den uzun" in w for w in all_warnings) else "❌"},
                    {"Kriter": "Minimum Perde Oranı", "Değer": "%0.2", "Durum": "✅" if not any("Perde alanı oranı" in w for w in all_warnings) else "❌"}
                ]
                
                criteria_df = pd.DataFrame(criteria_data)
                st.dataframe(criteria_df, use_container_width=True)
        
        else:
            st.error(f"❌ Dosya analizi sırasında hata: {result['error']}")
    
    else:
        # Dosya yüklenmemiş
        st.info("👆 Lütfen sidebar'dan bir DXF dosyası yükleyin")
        
        # Örnek kullanım
        with st.expander("ℹ️ Nasıl Kullanılır?"):
            st.markdown("""
            1. **DXF Dosyası Hazırlayın:** AutoCAD, QCAD veya benzeri programlardan DXF formatında dışa aktarın
            2. **Katman Adlandırması:** Elemanları uygun katmanlarda isimlendirin:
               - Kolonlar: 'kolon', 'column', 'col' içeren katmanlar
               - Kirişler: 'kiriş', 'beam' içeren katmanlar
               - Perdeler: 'perde', 'wall', 'shear_wall' içeren katmanlar
               - Döşemeler: 'döşeme', 'slab', 'floor' içeren katmanlar
               - Temeller: 'temel', 'foundation' içeren katmanlar
            3. **Dosyayı Yükleyin:** Sol menüden dosyanızı seçin
            4. **Sonuçları İnceleyin:** Farklı sekmelerden detaylı analiz sonuçlarına erişin
            
            **💡 İpucu:** En iyi sonuçlar için elemanları kapalı çokgen (polyline) olarak çizin.
            """)

if __name__ == "__main__":
    main()
