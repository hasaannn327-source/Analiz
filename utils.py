# Yardımcı fonksiyonlar
import math
import numpy as np
import logging
from typing import List, Tuple, Optional, Dict
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class GeometryUtils:
    """Geometri hesaplamaları için yardımcı sınıf"""
    
    @staticmethod
    def calculate_polygon_area(points: List[Tuple[float, float]]) -> float:
        """Polygon alanı hesapla (Shoelace formula)"""
        n = len(points)
        if n < 3:
            return 0
        
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area / 2)
    
    @staticmethod
    def calculate_perimeter(points: List[Tuple[float, float]]) -> float:
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
    
    @staticmethod
    def calculate_bounding_box(points: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """Bounding box hesapla (min_x, min_y, max_x, max_y)"""
        if not points:
            return 0, 0, 0, 0
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        return min(x_coords), min(y_coords), max(x_coords), max(y_coords)
    
    @staticmethod
    def calculate_centroid(points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Merkez nokta hesapla"""
        if not points:
            return 0, 0
        
        x_center = sum(p[0] for p in points) / len(points)
        y_center = sum(p[1] for p in points) / len(points)
        
        return x_center, y_center
    
    @staticmethod
    def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """İki nokta arası mesafe"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    @staticmethod
    def calculate_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """İki nokta arası açı (derece)"""
        return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    
    @staticmethod
    def is_point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        """Nokta polygon içinde mi kontrolü (Ray casting algorithm)"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

class ValidationUtils:
    """Validasyon yardımcıları"""
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Dosya boyutu kontrolü"""
        return file_size <= max_size
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Dosya uzantısı kontrolü"""
        return Path(filename).suffix.lower() in allowed_extensions
    
    @staticmethod
    def validate_coordinates(coords: List[Tuple[float, float]]) -> bool:
        """Koordinat validasyonu"""
        try:
            for x, y in coords:
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                    return False
                if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
                    return False
            return True
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_positive_number(value: float) -> bool:
        """Pozitif sayı kontrolü"""
        try:
            return isinstance(value, (int, float)) and value > 0 and not math.isnan(value)
        except (TypeError, ValueError):
            return False

class StatisticsUtils:
    """İstatistik hesaplamaları"""
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """Temel istatistikler hesapla"""
        if not values:
            return {
                'count': 0, 'sum': 0, 'mean': 0, 'median': 0,
                'min': 0, 'max': 0, 'std': 0, 'var': 0
            }
        
        values = [v for v in values if not math.isnan(v) and not math.isinf(v)]
        
        if not values:
            return {
                'count': 0, 'sum': 0, 'mean': 0, 'median': 0,
                'min': 0, 'max': 0, 'std': 0, 'var': 0
            }
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': np.mean(values),
            'median': np.median(values),
            'min': min(values),
            'max': max(values),
            'std': np.std(values),
            'var': np.var(values)
        }
    
    @staticmethod
    def calculate_percentiles(values: List[float], percentiles: List[int] = [25, 50, 75]) -> Dict[str, float]:
        """Yüzdelik dilimler hesapla"""
        if not values:
            return {f'p{p}': 0 for p in percentiles}
        
        values = [v for v in values if not math.isnan(v) and not math.isinf(v)]
        
        if not values:
            return {f'p{p}': 0 for p in percentiles}
        
        return {f'p{p}': np.percentile(values, p) for p in percentiles}
    
    @staticmethod
    def detect_outliers(values: List[float], method: str = 'iqr') -> List[int]:
        """Aykırı değerleri tespit et"""
        if not values or len(values) < 4:
            return []
        
        values = np.array([v for v in values if not math.isnan(v) and not math.isinf(v)])
        
        if len(values) < 4:
            return []
        
        outliers = []
        
        if method == 'iqr':
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [i for i, v in enumerate(values) 
                       if v < lower_bound or v > upper_bound]
        
        elif method == 'zscore':
            mean = np.mean(values)
            std = np.std(values)
            if std > 0:
                z_scores = np.abs((values - mean) / std)
                outliers = [i for i, z in enumerate(z_scores) if z > 3]
        
        return outliers

class FileUtils:
    """Dosya işlemleri yardımcıları"""
    
    @staticmethod
    def create_temp_file(suffix: str = '.tmp', prefix: str = 'structural_') -> str:
        """Geçici dosya oluştur"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=suffix, 
                prefix=prefix
            )
            temp_file.close()
            return temp_file.name
        except Exception as e:
            logger.error(f"Geçici dosya oluşturma hatası: {e}")
            return ""
    
    @staticmethod
    def safe_delete_file(file_path: str) -> bool:
        """Dosyayı güvenli şekilde sil"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except Exception as e:
            logger.warning(f"Dosya silme hatası {file_path}: {e}")
        return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, any]:
        """Dosya bilgilerini al"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            stat = os.stat(file_path)
            path_obj = Path(file_path)
            
            return {
                'name': path_obj.name,
                'size': stat.st_size,
                'extension': path_obj.suffix.lower(),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }
        except Exception as e:
            logger.error(f"Dosya bilgisi alma hatası {file_path}: {e}")
            return {}

class ColorUtils:
    """Renk yardımcıları"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Hex rengi RGB'ye çevir"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """RGB'yi hex'e çevir"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    @staticmethod
    def generate_color_palette(n_colors: int, base_color: str = '#1f77b4') -> List[str]:
        """Renk paleti oluştur"""
        base_rgb = ColorUtils.hex_to_rgb(base_color)
        colors = []
        
        for i in range(n_colors):
            # HSV color space'te renk varyasyonları
            hue_shift = (i * 360 / n_colors) % 360
            
            # Basit renk varyasyonu
            factor = 0.7 + (i % 3) * 0.15
            new_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)
            colors.append(ColorUtils.rgb_to_hex(new_rgb))
        
        return colors

class UnitUtils:
    """Birim dönüşümleri"""
    
    UNIT_CONVERSIONS = {
        # Uzunluk (metre cinsinden)
        'mm': 0.001,
        'cm': 0.01,
        'm': 1.0,
        'km': 1000.0,
        'in': 0.0254,
        'ft': 0.3048,
        
        # Alan (m² cinsinden)
        'mm2': 0.000001,
        'cm2': 0.0001,
        'm2': 1.0,
        'km2': 1000000.0,
        'in2': 0.00064516,
        'ft2': 0.092903,
    }
    
    @staticmethod
    def convert_length(value: float, from_unit: str, to_unit: str) -> float:
        """Uzunluk birimi dönüştür"""
        try:
            from_factor = UnitUtils.UNIT_CONVERSIONS.get(from_unit.lower(), 1.0)
            to_factor = UnitUtils.UNIT_CONVERSIONS.get(to_unit.lower(), 1.0)
            
            # Önce metreye çevir, sonra hedef birime
            meters = value * from_factor
            result = meters / to_factor
            
            return result
        except (KeyError, TypeError, ValueError):
            logger.warning(f"Birim dönüştürme hatası: {value} {from_unit} -> {to_unit}")
            return value
    
    @staticmethod
    def format_dimension(value: float, unit: str = 'm', precision: int = 2) -> str:
        """Boyutu formatla"""
        try:
            if abs(value) < 0.01 and unit == 'm':
                # Küçük değerleri cm olarak göster
                cm_value = value * 100
                return f"{cm_value:.{precision}f} cm"
            else:
                return f"{value:.{precision}f} {unit}"
        except (TypeError, ValueError):
            return f"{value} {unit}"