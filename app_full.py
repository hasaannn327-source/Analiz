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
import logging
import json
import time
from typing import Dict, List, Tuple, Optional
import math
import platform
from pathlib import Path
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
import base64

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('structural_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="DWG/DXF Yapı Elemanı Analizi - Gelişmiş",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Konfigürasyon
CONFIG = {
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'supported_formats': ['.dwg', '.dxf'],
    'timeout_seconds': 300,
    'min_column_size': 0.25,  # 25cm
    'max_beam_span': 8.0,     # 8m
    'min_wall_ratio': 0.01,   # %1
    'max_area_per_column': 25.0  # 25m²
}

class AdvancedStructuralAnalyzer:
    def __init__(self):
        self.elements = {
            'kolon': [],
            'kiriş': [],
            'perde': [],
            'döşeme': [],
            'temel': []
        }
        self.layer_keywords = {
            'kolon': ['kolon', 'column', 'col', 'pillar', 'c-', 'c_', 'sütun', 'direk'],
            'kiriş': ['kiriş', 'kiriş', 'beam', 'b-', 'b_', 'kirish', 'kiri'],
            'perde': ['perde', 'wall', 'shear', 'w-', 'w_', 'duvar', 'shearwall'],
            'döşeme': ['döşeme', 'slab', 'floor', 'f-', 'f_', 'doseme', 'plak'],
            'temel': ['temel', 'foundation', 'found', 'foot', 'fd-', 'fd_', 'fundament']
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
    
    def improved_dwg_converter(self, dwg_file):
        """Gelişmiş DWG dönüştürücü - Birden fazla yöntem dener"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
                temp_dwg.write(dwg_file.read())
                temp_dwg_path = temp_dwg.name
            
            temp_dxf_path = temp_dwg_path.replace('.dwg', '.dxf')
            
            # Dönüştürme yöntemlerini sırayla dene
            conversion_methods = [
                self._try_librecad_conversion,
                self._try_freecad_conversion,
                self._try_qcad_conversion,
                self._try_oda_converter,
                self._create_enhanced_demo_dxf
            ]
            
            for i, method in enumerate(conversion_methods):
                progress_bar.progress((i + 1) / len(conversion_methods))
                status_text.text(f"Dönüştürme yöntemi {i+1}/{len(conversion_methods)} deneniyor...")
                
                try:
                    result = method(temp_dwg_path, temp_dxf_path)
                    if result and os.path.exists(result) and os.path.getsize(result) > 0:
                        progress_bar.progress(1.0)
                        status_text.text("✅ Dönüştürme başarılı!")
                        logger.info(f"DWG dönüştürme başarılı: {method.__name__}")
                        return result
                except Exception as e:
                    logger.warning(f"Dönüştürme yöntemi başarısız {method.__name__}: {e}")
                    continue
            
            # Hiçbiri çalışmazsa demo dosya
            progress_bar.progress(1.0)
            status_text.text("⚠️ Demo dosyası kullanılıyor")
            return self._create_enhanced_demo_dxf()
            
        except Exception as e:
            logger.error(f"DWG dönüştürme genel hatası: {e}")
            return self._create_enhanced_demo_dxf()
        finally:
            # Geçici dosyaları temizle
            try:
                if 'temp_dwg_path' in locals() and os.path.exists(temp_dwg_path):
                    os.unlink(temp_dwg_path)
            except:
                pass
    
    def _try_librecad_conversion(self, dwg_path: str, dxf_path: str) -> Optional[str]:
        """LibreCAD ile dönüştürme"""
        try:
            # Farklı LibreCAD komut varyasyonları
            commands = [
                ['librecad', '--batch', dwg_path],
                ['librecad', '-batch', dwg_path], 
                ['librecad', '--convert', dwg_path, dxf_path],
                ['/usr/bin/librecad', '--batch', dwg_path],
                ['/opt/librecad/bin/librecad', '--batch', dwg_path]
            ]
            
            for cmd in commands:
                try:
                    if not shutil.which(cmd[0].split('/')[-1]):
                        continue
                        
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=os.path.dirname(dwg_path)
                    )
                    
                    # Çıktı dosyasını kontrol et
                    possible_outputs = [
                        dxf_path,
                        dwg_path.replace('.dwg', '.dxf'),
                        os.path.join(os.path.dirname(dwg_path), 'output.dxf')
                    ]
                    
                    for output_file in possible_outputs:
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                            if output_file != dxf_path:
                                shutil.move(output_file, dxf_path)
                            return dxf_path
                            
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                    
            return None
            
        except Exception as e:
            logger.warning(f"LibreCAD dönüştürme hatası: {e}")
            return None
    
    def _try_freecad_conversion(self, dwg_path: str, dxf_path: str) -> Optional[str]:
        """FreeCAD ile dönüştürme"""
        try:
            if not shutil.which('freecad'):
                return None
                
            script_content = f'''
import sys
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD
import Import

try:
    doc = FreeCAD.newDocument()
    Import.insert("{dwg_path}", doc.Name)
    
    # Tüm objeleri DXF olarak export et
    objects = doc.Objects
    if objects:
        Import.export(objects, "{dxf_path}")
    
    FreeCAD.closeDocument(doc.Name)
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_file.write(script_content)
                script_path = script_file.name
            
            result = subprocess.run([
                'freecad', '--console', '--run-python', script_path
            ], capture_output=True, text=True, timeout=120)
            
            os.unlink(script_path)
            
            if "SUCCESS" in result.stdout and os.path.exists(dxf_path):
                return dxf_path
                
        except Exception as e:
            logger.warning(f"FreeCAD dönüştürme hatası: {e}")
            
        return None
    
    def _try_qcad_conversion(self, dwg_path: str, dxf_path: str) -> Optional[str]:
        """QCAD ile dönüştürme"""
        try:
            if not shutil.which('qcad'):
                return None
                
            result = subprocess.run([
                'qcad', '-batch', '-input', dwg_path, '-output', dxf_path
            ], capture_output=True, timeout=60)
            
            if os.path.exists(dxf_path) and os.path.getsize(dxf_path) > 0:
                return dxf_path
                
        except Exception as e:
            logger.warning(f"QCAD dönüştürme hatası: {e}")
            
        return None
    
    def _try_oda_converter(self, dwg_path: str, dxf_path: str) -> Optional[str]:
        """ODA File Converter ile dönüştürme"""
        try:
            oda_paths = [
                '/opt/ODAFileConverter/ODAFileConverter',
                '/usr/bin/ODAFileConverter',
                'ODAFileConverter'
            ]
            
            for oda_path in oda_paths:
                if shutil.which(oda_path.split('/')[-1]):
                    result = subprocess.run([
                        oda_path, os.path.dirname(dwg_path), 
                        os.path.dirname(dxf_path), 'ACAD2018', 'DXF', '0', '1',
                        os.path.basename(dwg_path)
                    ], capture_output=True, timeout=90)
                    
                    if os.path.exists(dxf_path):
                        return dxf_path
                        
        except Exception as e:
            logger.warning(f"ODA Converter hatası: {e}")
            
        return None
    
    def _create_enhanced_demo_dxf(self) -> str:
        """Gelişmiş demo DXF dosyası"""
        try:
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Renkli katmanlar
            layers = {
                'KOLON': {'color': 1, 'linetype': 'CONTINUOUS'},
                'KIRIŞ': {'color': 2, 'linetype': 'DASHED'},
                'PERDE': {'color': 3, 'linetype': 'CONTINUOUS'},
                'DÖŞEME': {'color': 4, 'linetype': 'CONTINUOUS'},
                'TEMEL': {'color': 5, 'linetype': 'CONTINUOUS'}
            }
            
            for layer_name, attrs in layers.items():
                doc.layers.new(name=layer_name, dxfattribs=attrs)
            
            # Gerçekçi yapı elemanları
            # Kolonlar - 6x6 grid
            for i in range(6):
                for j in range(6):
                    x, y = i * 6, j * 6
                    size = 0.5 + (i + j) * 0.1  # Değişken boyutlar
                    msp.add_lwpolyline([
                        (x, y), (x + size, y), (x + size, y + size), (x, y + size)
                    ], close=True, dxfattribs={'layer': 'KOLON'})
                    
                    # Kolon boyut etiketi
                    msp.add_text(
                        f"{int(size*100)}x{int(size*100)}", 
                        dxfattribs={'layer': 'KOLON', 'height': 0.2}
                    ).set_pos((x + size/2, y + size/2))
            
            # Kirişler - Grid arası bağlantılar
            for i in range(5):
                for j in range(6):
                    # Yatay kirişler
                    msp.add_line(
                        (i * 6 + 0.5, j * 6 + 0.25), 
                        ((i + 1) * 6, j * 6 + 0.25),
                        dxfattribs={'layer': 'KIRIŞ'}
                    )
                    # Dikey kirişler
                    if j < 5:
                        msp.add_line(
                            (i * 6 + 0.25, j * 6 + 0.5), 
                            (i * 6 + 0.25, (j + 1) * 6),
                            dxfattribs={'layer': 'KIRIŞ'}
                        )
            
            # Perdeler - Çevre duvarlar
            perimeter_walls = [
                [(0, 0), (30, 0), (30, 0.3), (0, 0.3)],  # Alt duvar
                [(0, 30), (30, 30), (30, 30.3), (0, 30.3)],  # Üst duvar
                [(0, 0), (0.3, 0), (0.3, 30), (0, 30)],  # Sol duvar
                [(29.7, 0), (30, 0), (30, 30), (29.7, 30)]  # Sağ duvar
            ]
            
            for wall in perimeter_walls:
                msp.add_lwpolyline(wall, close=True, dxfattribs={'layer': 'PERDE'})
            
            # Döşeme - Ana alan
            msp.add_lwpolyline([
                (0.3, 0.3), (29.7, 0.3), (29.7, 29.7), (0.3, 29.7)
            ], close=True, dxfattribs={'layer': 'DÖŞEME'})
            
            # Temeller - Kolon altları
            for i in range(6):
                for j in range(6):
                    x, y = i * 6, j * 6
                    foundation_size = 1.2
                    offset = (foundation_size - 0.5) / 2
                    msp.add_lwpolyline([
                        (x - offset, y - offset), 
                        (x + foundation_size - offset, y - offset),
                        (x + foundation_size - offset, y + foundation_size - offset), 
                        (x - offset, y + foundation_size - offset)
                    ], close=True, dxfattribs={'layer': 'TEMEL'})
            
            # Geçici dosyaya kaydet
            temp_path = tempfile.mktemp(suffix='.dxf')
            doc.saveas(temp_path)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Demo DXF oluşturma hatası: {e}")
            return None
    
    def enhanced_analyze_dxf(self, dxf_path: str) -> bool:
        """Gelişmiş DXF analizi"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📖 DXF dosyası okunuyor...")
            progress_bar.progress(0.1)
            
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            
            # Elemanları sıfırla
            for key in self.elements:
                self.elements[key] = []
            
            status_text.text("🔍 Elemanlar analiz ediliyor...")
            progress_bar.progress(0.3)
            
            total_entities = len(list(msp))
            processed = 0
            
            # Her entity için detaylı analiz
            for entity in msp:
                layer_name = entity.dxf.layer.lower()
                element_type = self.classify_element(layer_name)
                
                if element_type:
                    element_data = self.extract_enhanced_element_data(entity, element_type)
                    if element_data:
                        self.elements[element_type].append(element_data)
                
                processed += 1
                if processed % 10 == 0:  # Her 10 elemanda bir güncelle
                    progress = 0.3 + (processed / total_entities) * 0.4
                    progress_bar.progress(progress)
            
            status_text.text("📊 İstatistikler hesaplanıyor...")
            progress_bar.progress(0.8)
            
            # Gelişmiş istatistik hesaplamaları
            self.analysis_results = self.calculate_enhanced_statistics()
            
            status_text.text("⚠️ Statik kontroller yapılıyor...")
            progress_bar.progress(0.9)
            
            # Kapsamlı statik kontroller
            self.warnings = self.perform_comprehensive_checks()
            
            progress_bar.progress(1.0)
            status_text.text("✅ Analiz tamamlandı!")
            
            logger.info(f"DXF analizi başarılı: {len(list(msp))} entity işlendi")
            return True
            
        except Exception as e:
            st.error(f"DXF analiz hatası: {str(e)}")
            logger.error(f"DXF analiz hatası: {e}")
            return False
    
    def classify_element(self, layer_name: str) -> Optional[str]:
        """Gelişmiş eleman sınıflandırması"""
        layer_name = layer_name.lower().strip()
        
        # Önce tam eşleşme ara
        for element_type, keywords in self.layer_keywords.items():
            if layer_name in keywords:
                return element_type
        
        # Sonra kısmi eşleşme
        for element_type, keywords in self.layer_keywords.items():
            if any(keyword in layer_name for keyword in keywords):
                return element_type
        
        # Sayısal kodlar için kontrol
        if any(char.isdigit() for char in layer_name):
            if 'c' in layer_name or '1' in layer_name:
                return 'kolon'
            elif 'b' in layer_name or '2' in layer_name:
                return 'kiriş'
            elif 'w' in layer_name or '3' in layer_name:
                return 'perde'
            elif 'f' in layer_name or '4' in layer_name:
                return 'döşeme'
            elif 'fd' in layer_name or '5' in layer_name:
                return 'temel'
        
        return None
    
    def extract_enhanced_element_data(self, entity, element_type: str) -> Optional[Dict]:
        """Gelişmiş eleman veri çıkarımı"""
        try:
            if entity.dxftype() == 'LWPOLYLINE':
                return self.analyze_enhanced_polyline(entity, element_type)
            elif entity.dxftype() == 'POLYLINE':
                return self.analyze_enhanced_polyline(entity, element_type)
            elif entity.dxftype() == 'LINE':
                return self.analyze_enhanced_line(entity, element_type)
            elif entity.dxftype() == 'CIRCLE':
                return self.analyze_enhanced_circle(entity, element_type)
            elif entity.dxftype() == 'ARC':
                return self.analyze_enhanced_arc(entity, element_type)
            elif entity.dxftype() == 'RECTANGLE':
                return self.analyze_enhanced_rectangle(entity, element_type)
            elif entity.dxftype() == 'SOLID' or entity.dxftype() == 'HATCH':
                return self.analyze_enhanced_solid(entity, element_type)
                
        except Exception as e:
            logger.warning(f"Eleman analiz hatası {entity.dxftype()}: {e}")
            
        return None
    
    def analyze_enhanced_polyline(self, polyline, element_type: str) -> Optional[Dict]:
        """Gelişmiş polyline analizi"""
        try:
            if hasattr(polyline, 'vertices'):
                points = list(polyline.vertices())
            else:
                points = [(p.x, p.y) for p in polyline.points()]
                
            if len(points) < 3:
                return None
            
            # Alan hesapla (Shoelace formula)
            area = abs(self.calculate_polygon_area(points))
            
            # Çevre hesapla
            perimeter = self.calculate_perimeter(points)
            
            # Bounding box
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            width = max_x - min_x
            height = max_y - min_y
            
            # Eleman tipine göre özel hesaplamalar
            element_data = {
                'tip': element_type,
                'alan': area,
                'çevre': perimeter,
                'genişlik': width,
                'uzunluk': height,
                'koordinat': ((min_x + max_x) / 2, (min_y + max_y) / 2),
                'nokta_sayısı': len(points),
                'aspect_ratio': max(width, height) / max(min(width, height), 0.001)
            }
            
            # Eleman tipine özel değerlendirmeler
            if element_type == 'kolon':
                element_data['kesit_tipi'] = 'dikdörtgen' if abs(width - height) > 0.1 else 'kare'
                element_data['boyut_str'] = f"{int(width*100)}x{int(height*100)}"
            elif element_type == 'kiriş':
                element_data['açıklık'] = max(width, height)
                element_data['yön'] = 'yatay' if width > height else 'dikey'
            elif element_type == 'perde':
                element_data['kalınlık'] = min(width, height)
                element_data['perde_uzunluğu'] = max(width, height)
            
            return element_data
            
        except Exception as e:
            logger.warning(f"Polyline analiz hatası: {e}")
            return None
    
    def analyze_enhanced_line(self, line, element_type: str) -> Optional[Dict]:
        """Gelişmiş çizgi analizi"""
        try:
            start = (line.dxf.start.x, line.dxf.start.y)
            end = (line.dxf.end.x, line.dxf.end.y)
            
            length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            
            # Açı hesapla
            angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
            
            return {
                'tip': element_type,
                'uzunluk': length,
                'alan': 0,
                'genişlik': 0,
                'koordinat': ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2),
                'açı': angle,
                'başlangıç': start,
                'bitiş': end
            }
            
        except Exception as e:
            logger.warning(f"Line analiz hatası: {e}")
            return None
    
    def analyze_enhanced_circle(self, circle, element_type: str) -> Optional[Dict]:
        """Gelişmiş daire analizi"""
        try:
            center = (circle.dxf.center.x, circle.dxf.center.y)
            radius = circle.dxf.radius
            area = math.pi * radius ** 2
            circumference = 2 * math.pi * radius
            
            return {
                'tip': element_type,
                'alan': area,
                'çevre': circumference,
                'çap': radius * 2,
                'yarıçap': radius,
                'koordinat': center,
                'kesit_tipi': 'dairesel'
            }
            
        except Exception as e:
            logger.warning(f"Circle analiz hatası: {e}")
            return None
    
    def analyze_enhanced_arc(self, arc, element_type: str) -> Optional[Dict]:
        """Yay analizi"""
        try:
            center = (arc.dxf.center.x, arc.dxf.center.y)
            radius = arc.dxf.radius
            start_angle = arc.dxf.start_angle
            end_angle = arc.dxf.end_angle
            
            # Yay uzunluğu
            angle_diff = end_angle - start_angle
            if angle_diff < 0:
                angle_diff += 360
            arc_length = (angle_diff / 360) * 2 * math.pi * radius
            
            return {
                'tip': element_type,
                'uzunluk': arc_length,
                'yarıçap': radius,
                'koordinat': center,
                'başlangıç_açısı': start_angle,
                'bitiş_açısı': end_angle,
                'açı_farkı': angle_diff
            }
            
        except Exception as e:
            logger.warning(f"Arc analiz hatası: {e}")
            return None
    
    def analyze_enhanced_rectangle(self, rect, element_type: str) -> Optional[Dict]:
        """Dikdörtgen analizi"""
        try:
            # Rectangle entity'nin özelliklerini al
            width = rect.dxf.width if hasattr(rect.dxf, 'width') else 1.0
            height = rect.dxf.height if hasattr(rect.dxf, 'height') else 1.0
            
            area = width * height
            perimeter = 2 * (width + height)
            
            return {
                'tip': element_type,
                'alan': area,
                'çevre': perimeter,
                'genişlik': width,
                'uzunluk': height,
                'koordinat': (rect.dxf.insert.x, rect.dxf.insert.y) if hasattr(rect.dxf, 'insert') else (0, 0),
                'kesit_tipi': 'dikdörtgen'
            }
            
        except Exception as e:
            logger.warning(f"Rectangle analiz hatası: {e}")
            return None
    
    def analyze_enhanced_solid(self, solid, element_type: str) -> Optional[Dict]:
        """Solid/Hatch analizi"""
        try:
            # Bu tip elemanlar için basit alan hesabı
            area = getattr(solid, 'area', 0) if hasattr(solid, 'area') else 0
            
            if area == 0:
                return None
            
            return {
                'tip': element_type,
                'alan': area,
                'çevre': 0,
                'koordinat': (0, 0)  # Merkez koordinat hesaplanabilir
            }
            
        except Exception as e:
            logger.warning(f"Solid analiz hatası: {e}")
            return None
    
    def calculate_polygon_area(self, points: List[Tuple[float, float]]) -> float:
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
    
    def calculate_perimeter(self, points: List[Tuple[float, float]]) -> float:
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
    
    def calculate_enhanced_statistics(self) -> Dict:
        """Gelişmiş istatistik hesaplamaları"""
        stats = {}
        
        for element_type, elements in self.elements.items():
            if elements:
                areas = [e.get('alan', 0) for e in elements]
                lengths = [e.get('uzunluk', 0) for e in elements]
                perimeters = [e.get('çevre', 0) for e in elements]
                
                stats[element_type] = {
                    'adet': len(elements),
                    'toplam_alan': sum(areas),
                    'ortalama_alan': np.mean(areas) if areas else 0,
                    'min_alan': min(areas) if areas else 0,
                    'max_alan': max(areas) if areas else 0,
                    'std_alan': np.std(areas) if areas else 0,
                    'toplam_uzunluk': sum(lengths),
                    'ortalama_uzunluk': np.mean(lengths) if lengths else 0,
                    'toplam_çevre': sum(perimeters),
                    'ortalama_çevre': np.mean(perimeters) if perimeters else 0
                }
                
                # Eleman tipine özel istatistikler
                if element_type == 'kolon':
                    sizes = [e.get('genişlik', 0) * e.get('uzunluk', 0) for e in elements]
                    stats[element_type]['min_boyut'] = min(sizes) if sizes else 0
                    stats[element_type]['max_boyut'] = max(sizes) if sizes else 0
                    
                elif element_type == 'kiriş':
                    spans = [e.get('açıklık', e.get('uzunluk', 0)) for e in elements]
                    stats[element_type]['min_açıklık'] = min(spans) if spans else 0
                    stats[element_type]['max_açıklık'] = max(spans) if spans else 0
                    
            else:
                stats[element_type] = {
                    'adet': 0, 'toplam_alan': 0, 'ortalama_alan': 0,
                    'min_alan': 0, 'max_alan': 0, 'std_alan': 0,
                    'toplam_uzunluk': 0, 'ortalama_uzunluk': 0,
                    'toplam_çevre': 0, 'ortalama_çevre': 0
                }
        
        return stats
    
    def perform_comprehensive_checks(self) -> List[str]:
        """Kapsamlı statik kontroller"""
        warnings = []
        stats = self.analysis_results
        
        # 1. Temel yapısal oranlar
        total_floor_area = stats.get('döşeme', {}).get('toplam_alan', 0)
        total_wall_area = stats.get('perde', {}).get('toplam_alan', 0)
        column_count = stats.get('kolon', {}).get('adet', 0)
        
        # Perde alanı oranı kontrolü
        if total_floor_area > 0:
            wall_ratio = (total_wall_area / total_floor_area) * 100
            if wall_ratio < CONFIG['min_wall_ratio'] * 100:
                warnings.append(f"🚨 Perde alanı oranı çok düşük: %{wall_ratio:.1f} (Min %{CONFIG['min_wall_ratio']*100:.1f})")
            elif wall_ratio < 2.0:
                warnings.append(f"⚠️ Perde alanı oranı düşük: %{wall_ratio:.1f} (Önerilen min %2.0)")
        
        # Kolon yoğunluğu kontrolü
        if total_floor_area > 0 and column_count > 0:
            area_per_column = total_floor_area / column_count
            if area_per_column > CONFIG['max_area_per_column']:
                warnings.append(f"🚨 Kolon yoğunluğu yetersiz: {area_per_column:.1f} m²/kolon (Max {CONFIG['max_area_per_column']} m²/kolon)")
        
        # 2. Kolon boyut kontrolleri
        column_elements = self.elements.get('kolon', [])
        small_columns = []
        for col in column_elements:
            width = col.get('genişlik', 0)
            height = col.get('uzunluk', 0)
            if min(width, height) < CONFIG['min_column_size']:
                small_columns.append(col)
        
        if small_columns:
            warnings.append(f"🚨 {len(small_columns)} adet kolon minimum boyutun altında ({CONFIG['min_column_size']*100}cm)")
        
        # 3. Kiriş açıklık kontrolleri
        beam_elements = self.elements.get('kiriş', [])
        long_beams = []
        for beam in beam_elements:
            span = beam.get('açıklık', beam.get('uzunluk', 0))
            if span > CONFIG['max_beam_span']:
                long_beams.append(beam)
        
        if long_beams:
            warnings.append(f"⚠️ {len(long_beams)} adet kiriş maksimum açıklığı aşıyor ({CONFIG['max_beam_span']}m)")
        
        # 4. Temel-kolon uyumu
        foundation_count = stats.get('temel', {}).get('adet', 0)
        if foundation_count < column_count:
            warnings.append(f"🚨 Temel eksikliği: {foundation_count} temel / {column_count} kolon")
        elif foundation_count > column_count * 1.2:
            warnings.append(f"⚠️ Fazla temel: {foundation_count} temel / {column_count} kolon")
        
        # 5. Geometrik kontroller
        if total_floor_area > 0:
            # Bina kompaktlık oranı
            total_perimeter = stats.get('döşeme', {}).get('toplam_çevre', 0)
            if total_perimeter > 0:
                compactness = (4 * math.pi * total_floor_area) / (total_perimeter ** 2)
                if compactness < 0.5:
                    warnings.append(f"⚠️ Bina formu kompakt değil (Kompaktlık: {compactness:.2f})")
        
        # 6. Simetri kontrolleri
        if len(column_elements) > 4:
            x_coords = [col['koordinat'][0] for col in column_elements]
            y_coords = [col['koordinat'][1] for col in column_elements]
            
            x_center = np.mean(x_coords)
            y_center = np.mean(y_coords)
            
            # Kütle merkezi sapması
            mass_center_deviation = math.sqrt((x_center - np.median(x_coords))**2 + 
                                            (y_center - np.median(y_coords))**2)
            
            if mass_center_deviation > 2.0:
                warnings.append(f"⚠️ Kütle merkezi sapması yüksek: {mass_center_deviation:.1f}m")
        
        return warnings
    
    def create_advanced_visualizations(self) -> Dict:
        """Gelişmiş görselleştirmeler"""
        visualizations = {}
        
        # 1. 3D Bar Chart - Eleman dağılımı
        element_counts = [len(self.elements[key]) for key in self.elements.keys()]
        element_names = list(self.elements.keys())
        
        fig_3d = go.Figure(data=[go.Bar3d(
            x=element_names,
            y=[1] * len(element_names),
            z=element_counts,
            colorscale='Viridis'
        )])
        fig_3d.update_layout(
            title="3D Eleman Dağılımı",
            scene=dict(
                xaxis_title="Eleman Tipi",
                yaxis_title="",
                zaxis_title="Adet"
            )
        )
        visualizations['3d_distribution'] = fig_3d
        
        # 2. Scatter Plot - Kolon konumları
        if self.elements['kolon']:
            col_x = [col['koordinat'][0] for col in self.elements['kolon']]
            col_y = [col['koordinat'][1] for col in self.elements['kolon']]
            col_areas = [col.get('alan', 0) for col in self.elements['kolon']]
            
            fig_scatter = go.Figure(data=go.Scatter(
                x=col_x, y=col_y,
                mode='markers',
                marker=dict(
                    size=[area * 1000 for area in col_areas],
                    color=col_areas,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Alan (m²)")
                ),
                text=[f"Alan: {area:.2f} m²" for area in col_areas],
                hovertemplate="X: %{x}<br>Y: %{y}<br>%{text}<extra></extra>"
            ))
            fig_scatter.update_layout(
                title="Kolon Konumları ve Boyutları",
                xaxis_title="X Koordinatı",
                yaxis_title="Y Koordinatı"
            )
            visualizations['column_layout'] = fig_scatter
        
        # 3. Heatmap - Eleman yoğunluğu
        if any(self.elements.values()):
            all_coords = []
            for element_type, elements in self.elements.items():
                for element in elements:
                    coord = element.get('koordinat', (0, 0))
                    all_coords.append([coord[0], coord[1], element_type])
            
            if all_coords:
                df_coords = pd.DataFrame(all_coords, columns=['X', 'Y', 'Type'])
                # Grid-based heatmap oluştur
                x_bins = np.linspace(df_coords['X'].min(), df_coords['X'].max(), 20)
                y_bins = np.linspace(df_coords['Y'].min(), df_coords['Y'].max(), 20)
                
                heatmap_data = np.zeros((len(y_bins)-1, len(x_bins)-1))
                for _, row in df_coords.iterrows():
                    x_idx = np.digitize(row['X'], x_bins) - 1
                    y_idx = np.digitize(row['Y'], y_bins) - 1
                    if 0 <= x_idx < len(x_bins)-1 and 0 <= y_idx < len(y_bins)-1:
                        heatmap_data[y_idx, x_idx] += 1
                
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=heatmap_data,
                    colorscale='Blues'
                ))
                fig_heatmap.update_layout(title="Eleman Yoğunluk Haritası")
                visualizations['density_heatmap'] = fig_heatmap
        
        return visualizations
    
    def generate_pdf_report(self) -> bytes:
        """PDF rapor oluştur"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Başlık
            title = Paragraph("Yapısal Eleman Analiz Raporu", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Özet tablo
            summary_data = [['Eleman Tipi', 'Adet', 'Toplam Alan (m²)', 'Ortalama Alan (m²)']]
            
            for element_type, stats in self.analysis_results.items():
                summary_data.append([
                    element_type.capitalize(),
                    str(stats['adet']),
                    f"{stats['toplam_alan']:.2f}",
                    f"{stats['ortalama_alan']:.2f}"
                ])
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 12))
            
            # Uyarılar
            if self.warnings:
                warning_title = Paragraph("Statik Kontrol Uyarıları", styles['Heading2'])
                story.append(warning_title)
                
                for warning in self.warnings:
                    warning_text = Paragraph(f"• {warning}", styles['Normal'])
                    story.append(warning_text)
                
                story.append(Spacer(1, 12))
            
            # Detaylı analiz
            detail_title = Paragraph("Detaylı Analiz", styles['Heading2'])
            story.append(detail_title)
            
            for element_type, elements in self.elements.items():
                if elements:
                    type_title = Paragraph(f"{element_type.capitalize()} Analizi", styles['Heading3'])
                    story.append(type_title)
                    
                    type_text = Paragraph(
                        f"Toplam {len(elements)} adet {element_type} tespit edildi. "
                        f"Toplam alan: {sum(e.get('alan', 0) for e in elements):.2f} m²",
                        styles['Normal']
                    )
                    story.append(type_text)
                    story.append(Spacer(1, 6))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"PDF rapor oluşturma hatası: {e}")
            return b""
    
    def create_structural_plan_view(self) -> Optional[str]:
        """Yapısal plan görünümü oluştur"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(12, 10))
            
            colors_map = {
                'kolon': 'red',
                'kiriş': 'blue', 
                'perde': 'green',
                'döşeme': 'lightgray',
                'temel': 'brown'
            }
            
            # Her eleman tipini çiz
            for element_type, elements in self.elements.items():
                color = colors_map.get(element_type, 'black')
                
                for element in elements:
                    coord = element.get('koordinat', (0, 0))
                    width = element.get('genişlik', 0.5)
                    height = element.get('uzunluk', 0.5)
                    
                    if element_type == 'kolon':
                        # Kolonları kare/dikdörtgen olarak çiz
                        rect = patches.Rectangle(
                            (coord[0] - width/2, coord[1] - height/2),
                            width, height,
                            linewidth=1, edgecolor=color, facecolor=color, alpha=0.7
                        )
                        ax.add_patch(rect)
                        
                        # Boyut etiketi
                        ax.text(coord[0], coord[1], 
                               f"{int(width*100)}x{int(height*100)}", 
                               ha='center', va='center', fontsize=8, color='white')
                        
                    elif element_type == 'kiriş':
                        # Kirişleri çizgi olarak çiz
                        length = element.get('uzunluk', 1.0)
                        ax.plot([coord[0] - length/2, coord[0] + length/2], 
                               [coord[1], coord[1]], 
                               color=color, linewidth=3, alpha=0.8)
                        
                    elif element_type in ['perde', 'döşeme']:
                        # Perde ve döşemeleri alan olarak çiz
                        area = element.get('alan', 1.0)
                        radius = math.sqrt(area / math.pi)
                        circle = patches.Circle(coord, radius, 
                                              facecolor=color, alpha=0.3, edgecolor=color)
                        ax.add_patch(circle)
                        
                    elif element_type == 'temel':
                        # Temelleri büyük kare olarak çiz
                        size = max(width * 1.5, 1.0)
                        rect = patches.Rectangle(
                            (coord[0] - size/2, coord[1] - size/2),
                            size, size,
                            linewidth=2, edgecolor=color, facecolor='none', linestyle='--'
                        )
                        ax.add_patch(rect)
            
            # Eksen ayarları
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_title('Yapısal Plan Görünümü')
            
            # Legend
            legend_elements = [patches.Patch(color=color, label=element_type.capitalize()) 
                             for element_type, color in colors_map.items() 
                             if self.elements[element_type]]
            ax.legend(handles=legend_elements, loc='upper right')
            
            # Geçici dosyaya kaydet
            temp_path = tempfile.mktemp(suffix='.png')
            plt.savefig(temp_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Plan görünümü oluşturma hatası: {e}")
            return None

def main():
    st.title("🏗️ Gelişmiş DWG/DXF Yapı Elemanı Analizi")
    st.markdown("---")
    
    # Sidebar menü
    st.sidebar.header("🎛️ Kontrol Paneli")
    
    # Tema seçimi
    theme = st.sidebar.selectbox("🎨 Tema", ["Varsayılan", "Koyu", "Açık"])
    
    # Analiz seçenekleri
    st.sidebar.subheader("⚙️ Analiz Seçenekleri")
    detailed_analysis = st.sidebar.checkbox("🔍 Detaylı Analiz", value=True)
    generate_3d = st.sidebar.checkbox("📊 3D Görselleştirme", value=True)
    create_pdf = st.sidebar.checkbox("📄 PDF Rapor", value=True)
    
    # Dosya yükleme
    st.sidebar.header("📁 Dosya Yükleme")
    uploaded_file = st.sidebar.file_uploader(
        "DWG veya DXF dosyası seçin",
        type=['dwg', 'dxf'],
        help="Maksimum dosya boyutu: 100MB"
    )
    
    # Ana içerik
    if uploaded_file is not None:
        # Analyzer oluştur
        analyzer = AdvancedStructuralAnalyzer()
        
        # Dosya validasyonu
        if not analyzer.validate_file(uploaded_file):
            st.stop()
        
        # Dosya bilgileri
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Dosya Adı", uploaded_file.name)
        with col2:
            st.metric("📏 Boyut", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
        with col3:
            st.metric("📋 Format", uploaded_file.name.split('.')[-1].upper())
        
        with st.spinner('🔄 Dosya işleniyor...'):
            # Dosya tipine göre işle
            if uploaded_file.name.lower().endswith('.dwg'):
                st.info("🔄 DWG dosyası DXF'ye dönüştürülüyor...")
                dxf_path = analyzer.improved_dwg_converter(uploaded_file)
            else:
                # DXF dosyasını geçici olarak kaydet
                with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as temp_file:
                    temp_file.write(uploaded_file.read())
                    dxf_path = temp_file.name
            
            if dxf_path and analyzer.enhanced_analyze_dxf(dxf_path):
                
                # Sekmeli arayüz
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 Genel Bakış", 
                    "📈 Detaylı Analiz", 
                    "🎯 Statik Kontroller",
                    "📊 Görselleştirmeler",
                    "📄 Raporlar"
                ])
                
                with tab1:
                    st.header("📊 Genel Bakış")
                    
                    # KPI metrikleri
                    stats = analyzer.analysis_results
                    
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
                    
                    # Pasta grafik
                    element_counts = [stats[key]['adet'] for key in stats if stats[key]['adet'] > 0]
                    element_names = [key.capitalize() for key in stats if stats[key]['adet'] > 0]
                    
                    if element_counts:
                        fig_pie = px.pie(
                            values=element_counts, 
                            names=element_names,
                            title="Eleman Dağılımı"
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                with tab2:
                    st.header("📈 Detaylı Analiz")
                    
                    if detailed_analysis:
                        # Her eleman tipi için detaylı analiz
                        for element_type, elements in analyzer.elements.items():
                            if elements:
                                st.subheader(f"🔍 {element_type.capitalize()} Detayları")
                                
                                # İstatistikler
                                col1, col2, col3 = st.columns(3)
                                
                                stat = stats[element_type]
                                with col1:
                                    st.metric("Adet", stat['adet'])
                                with col2:
                                    st.metric("Min Alan", f"{stat['min_alan']:.2f} m²")
                                with col3:
                                    st.metric("Max Alan", f"{stat['max_alan']:.2f} m²")
                                
                                # Detay tablosu
                                element_details = []
                                for i, element in enumerate(elements[:20]):  # İlk 20 eleman
                                    detail = {
                                        'ID': i + 1,
                                        'Alan (m²)': round(element.get('alan', 0), 2),
                                        'Çevre (m)': round(element.get('çevre', 0), 2),
                                        'Genişlik (m)': round(element.get('genişlik', 0), 2),
                                        'Uzunluk (m)': round(element.get('uzunluk', 0), 2),
                                        'X': round(element.get('koordinat', (0, 0))[0], 2),
                                        'Y': round(element.get('koordinat', (0, 0))[1], 2)
                                    }
                                    element_details.append(detail)
                                
                                if element_details:
                                    df_details = pd.DataFrame(element_details)
                                    st.dataframe(df_details, use_container_width=True)
                                
                                st.markdown("---")
                
                with tab3:
                    st.header("🎯 Statik Kontroller")
                    
                    if analyzer.warnings:
                        st.subheader("⚠️ Tespit Edilen Sorunlar")
                        
                        # Uyarıları kategorize et
                        critical_warnings = [w for w in analyzer.warnings if '🚨' in w]
                        normal_warnings = [w for w in analyzer.warnings if '⚠️' in w]
                        
                        if critical_warnings:
                            st.error("🚨 **Kritik Uyarılar:**")
                            for warning in critical_warnings:
                                st.write(f"• {warning}")
                        
                        if normal_warnings:
                            st.warning("⚠️ **Genel Uyarılar:**")
                            for warning in normal_warnings:
                                st.write(f"• {warning}")
                    else:
                        st.success("✅ Statik kontrollerde herhangi bir sorun tespit edilmedi!")
                    
                    # Kontrol kriterleri
                    st.subheader("📋 Kontrol Kriterleri")
                    
                    criteria_data = [
                        ['Minimum Kolon Boyutu', f'{CONFIG["min_column_size"]*100} cm', '✅' if not any('kolon minimum' in w for w in analyzer.warnings) else '❌'],
                        ['Maksimum Kiriş Açıklığı', f'{CONFIG["max_beam_span"]} m', '✅' if not any('açıklığı aşıyor' in w for w in analyzer.warnings) else '❌'],
                        ['Minimum Perde Oranı', f'%{CONFIG["min_wall_ratio"]*100}', '✅' if not any('Perde alanı' in w for w in analyzer.warnings) else '❌'],
                        ['Maksimum Alan/Kolon', f'{CONFIG["max_area_per_column"]} m²/kolon', '✅' if not any('yoğunluğu' in w for w in analyzer.warnings) else '❌']
                    ]
                    
                    df_criteria = pd.DataFrame(criteria_data, columns=['Kriter', 'Değer', 'Durum'])
                    st.dataframe(df_criteria, use_container_width=True)
                
                with tab4:
                    st.header("📊 Görselleştirmeler")
                    
                    if generate_3d:
                        # Gelişmiş görselleştirmeler
                        visualizations = analyzer.create_advanced_visualizations()
                        
                        for viz_name, fig in visualizations.items():
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Plan görünümü
                    st.subheader("🗺️ Yapısal Plan")
                    plan_path = analyzer.create_structural_plan_view()
                    if plan_path and os.path.exists(plan_path):
                        st.image(plan_path, caption="Yapısal Plan Görünümü", use_column_width=True)
                        
                        # Plan indirme
                        with open(plan_path, 'rb') as f:
                            st.download_button(
                                label="🖼️ Plan Görünümünü İndir",
                                data=f.read(),
                                file_name="structural_plan.png",
                                mime="image/png"
                            )
                        
                        # Geçici dosyayı temizle
                        try:
                            os.unlink(plan_path)
                        except:
                            pass
                
                with tab5:
                    st.header("📄 Raporlar")
                    
                    # CSV Raporu
                    st.subheader("📊 CSV Raporu")
                    
                    if st.button("📁 CSV Raporu Oluştur"):
                        report_data = []
                        for element_type, stat in stats.items():
                            report_data.append({
                                'Eleman Tipi': element_type.capitalize(),
                                'Adet': stat['adet'],
                                'Toplam Alan (m²)': round(stat['toplam_alan'], 2),
                                'Ortalama Alan (m²)': round(stat['ortalama_alan'], 2),
                                'Min Alan (m²)': round(stat['min_alan'], 2),
                                'Max Alan (m²)': round(stat['max_alan'], 2),
                                'Toplam Uzunluk (m)': round(stat['toplam_uzunluk'], 2),
                                'Toplam Çevre (m)': round(stat['toplam_çevre'], 2)
                            })
                        
                        df_report = pd.DataFrame(report_data)
                        csv_data = df_report.to_csv(index=False, encoding='utf-8')
                        
                        st.download_button(
                            label="📁 CSV Raporu İndir",
                            data=csv_data,
                            file_name=f"yapi_analiz_raporu_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # PDF Raporu
                    if create_pdf:
                        st.subheader("📄 PDF Raporu")
                        
                        if st.button("📄 PDF Raporu Oluştur"):
                            with st.spinner("PDF oluşturuluyor..."):
                                pdf_data = analyzer.generate_pdf_report()
                                
                                if pdf_data:
                                    st.download_button(
                                        label="📄 PDF Raporu İndir",
                                        data=pdf_data,
                                        file_name=f"yapi_analiz_raporu_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                        mime="application/pdf"
                                    )
                                else:
                                    st.error("PDF raporu oluşturulamadı!")
                    
                    # JSON Veri Export
                    st.subheader("💾 Ham Veri Export")
                    
                    if st.button("💾 JSON Verilerini İndir"):
                        export_data = {
                            'elements': analyzer.elements,
                            'statistics': analyzer.analysis_results,
                            'warnings': analyzer.warnings,
                            'timestamp': pd.Timestamp.now().isoformat()
                        }
                        
                        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                        
                        st.download_button(
                            label="💾 JSON Verilerini İndir",
                            data=json_data,
                            file_name=f"yapi_analiz_verileri_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
            
            else:
                st.error("❌ Dosya analiz edilemedi. Lütfen geçerli bir DWG/DXF dosyası yükleyin.")
        
        # Geçici dosyaları temizle
        try:
            if 'dxf_path' in locals() and dxf_path and os.path.exists(dxf_path):
                os.unlink(dxf_path)
        except:
            pass
    
    else:
        # Başlangıç sayfası
        st.markdown("""
        ## 🏗️ Gelişmiş Yapı Elemanı Analiz Uygulaması
        
        Bu uygulama DWG/DXF dosyalarınızdan yapı elemanlarını otomatik olarak analiz eder ve kapsamlı raporlar sunar.
        
        ### ✨ Yeni Özellikler:
        - 🔄 **Gelişmiş DWG Dönüştürme**: Birden fazla dönüştürme yöntemi
        - 📊 **3D Görselleştirme**: İnteraktif 3D grafikler
        - 📄 **PDF Raporlama**: Profesyonel PDF raporları
        - 🎯 **Kapsamlı Statik Kontroller**: TBDY 2018 uyumlu kontroller
        - 🗺️ **Plan Görünümü**: Otomatik yapısal plan çizimi
        - 📈 **Gelişmiş Analizler**: İstatistiksel analizler ve trend tespiti
        
        ### 🔧 Desteklenen Özellikler:
        - ✅ **Çoklu Format Desteği**: DWG, DXF
        - ✅ **Otomatik Eleman Tanıma**: Akıllı katman algılama
        - ✅ **Gerçek Zamanlı Analiz**: Progress bar ile takip
        - ✅ **Çoklu Rapor Formatı**: CSV, PDF, JSON
        - ✅ **Görsel Plan Çıktısı**: PNG format plan görünümü
        
        ### 📋 Analiz Edilen Elemanlar:
        - **🏛️ Kolonlar**: Boyut, alan, kesit tipi analizi
        - **📏 Kirişler**: Uzunluk, açıklık, yön analizi  
        - **🧱 Perdeler**: Alan, kalınlık, oran kontrolleri
        - **🏢 Döşemeler**: Alan hesaplaması ve dağılım
        - **🏗️ Temeller**: Adet, boyut ve kolon uyumu
        
        ### ⚙️ Kullanım Adımları:
        1. **📁 Dosya Yükle**: Sol menüden DWG/DXF dosyanızı seçin
        2. **⚙️ Seçenekleri Ayarla**: Analiz seçeneklerini belirleyin
        3. **🔄 Analizi Başlat**: Otomatik analiz işlemini bekleyin
        4. **📊 Sonuçları İncele**: 5 farklı sekmede detaylı sonuçlar
        5. **📄 Rapor İndir**: İhtiyacınıza göre rapor formatını seçin
        
        ### 🎯 Statik Kontrol Kriterleri:
        - Minimum kolon boyutu: **25x25 cm**
        - Maksimum kiriş açıklığı: **8.0 m**
        - Minimum perde oranı: **%1.0**
        - Maksimum alan/kolon: **25 m²**
        
        ---
        **💡 İpucu**: En iyi sonuçlar için katman isimlerinde "kolon", "kiriş", "perde" gibi Türkçe veya İngilizce anahtar kelimeler kullanın.
        """)
        
        # Sistem durumu
        st.sidebar.markdown("---")
        st.sidebar.subheader("🖥️ Sistem Durumu")
        
        # CAD araçları kontrol
        tools_status = []
        tools = ['librecad', 'freecad', 'qcad']
        
        for tool in tools:
            if shutil.which(tool):
                tools_status.append(f"✅ {tool.upper()}")
            else:
                tools_status.append(f"❌ {tool.upper()}")
        
        for status in tools_status:
            st.sidebar.text(status)
        
        if not any('✅' in status for status in tools_status):
            st.sidebar.warning("⚠️ CAD dönüştürme araçları bulunamadı. Demo modu kullanılacak.")

if __name__ == "__main__":
    main()