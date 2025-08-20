#!/usr/bin/env python3
"""
Performans test scripti
Yapısal analiz uygulamasının performansını test eder
"""

import time
import psutil
import os
import sys
from pathlib import Path
import tempfile
import ezdxf
import numpy as np
from typing import Dict, List

# Ana uygulama modüllerini import et
sys.path.append(str(Path(__file__).parent))
from app import AdvancedStructuralAnalyzer
from utils import GeometryUtils, StatisticsUtils

class PerformanceTest:
    def __init__(self):
        self.analyzer = AdvancedStructuralAnalyzer()
        self.results = {}
        
    def create_test_dxf(self, element_count: int = 100) -> str:
        """Test için DXF dosyası oluştur"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Katmanlar oluştur
        doc.layers.new(name='KOLON', dxfattribs={'color': 1})
        doc.layers.new(name='KIRIŞ', dxfattribs={'color': 2})
        doc.layers.new(name='PERDE', dxfattribs={'color': 3})
        doc.layers.new(name='DÖŞEME', dxfattribs={'color': 4})
        doc.layers.new(name='TEMEL', dxfattribs={'color': 5})
        
        # Test elemanları ekle
        layers = ['KOLON', 'KIRIŞ', 'PERDE', 'DÖŞEME', 'TEMEL']
        
        for i in range(element_count):
            layer = layers[i % len(layers)]
            x, y = i % 20 * 2, i // 20 * 2
            
            if layer == 'KOLON':
                # Kolon - kare
                size = 0.3 + (i % 5) * 0.1
                msp.add_lwpolyline([
                    (x, y), (x + size, y), (x + size, y + size), (x, y + size)
                ], close=True, dxfattribs={'layer': layer})
                
            elif layer == 'KIRIŞ':
                # Kiriş - çizgi
                length = 2 + (i % 10) * 0.5
                msp.add_line((x, y), (x + length, y), dxfattribs={'layer': layer})
                
            elif layer == 'PERDE':
                # Perde - dikdörtgen
                width, height = 0.2, 3 + (i % 5) * 0.5
                msp.add_lwpolyline([
                    (x, y), (x + width, y), (x + width, y + height), (x, y + height)
                ], close=True, dxfattribs={'layer': layer})
                
            elif layer == 'DÖŞEME':
                # Döşeme - büyük alan
                width, height = 5 + (i % 3), 5 + (i % 3)
                msp.add_lwpolyline([
                    (x, y), (x + width, y), (x + width, y + height), (x, y + height)
                ], close=True, dxfattribs={'layer': layer})
                
            elif layer == 'TEMEL':
                # Temel - büyük kare
                size = 1 + (i % 3) * 0.2
                msp.add_lwpolyline([
                    (x, y), (x + size, y), (x + size, y + size), (x, y + size)
                ], close=True, dxfattribs={'layer': layer})
        
        # Geçici dosyaya kaydet
        temp_path = tempfile.mktemp(suffix='.dxf')
        doc.saveas(temp_path)
        return temp_path
    
    def measure_performance(self, func, *args, **kwargs) -> Dict:
        """Fonksiyon performansını ölç"""
        # Başlangıç değerleri
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Fonksiyonu çalıştır
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        
        # Bitiş değerleri
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return {
            'success': success,
            'result': result,
            'execution_time': end_time - start_time,
            'memory_usage': end_memory - start_memory,
            'peak_memory': end_memory
        }
    
    def test_file_analysis(self, element_counts: List[int]) -> Dict:
        """Farklı boyutlardaki dosyaları analiz et"""
        results = {}
        
        for count in element_counts:
            print(f"🧪 {count} elemanlı dosya testi...")
            
            # Test dosyası oluştur
            test_file = self.create_test_dxf(count)
            
            try:
                # Analiz performansını ölç
                perf = self.measure_performance(
                    self.analyzer.enhanced_analyze_dxf, 
                    test_file
                )
                
                results[count] = perf
                
                print(f"   ⏱️  Süre: {perf['execution_time']:.2f}s")
                print(f"   💾 Bellek: {perf['memory_usage']:.1f}MB")
                print(f"   ✅ Başarı: {perf['success']}")
                
            finally:
                # Geçici dosyayı temizle
                try:
                    os.unlink(test_file)
                except:
                    pass
        
        return results
    
    def test_geometry_calculations(self, point_counts: List[int]) -> Dict:
        """Geometri hesaplama performansını test et"""
        results = {}
        
        for count in point_counts:
            print(f"📐 {count} noktalı geometri testi...")
            
            # Test noktaları oluştur
            points = [(np.random.random() * 100, np.random.random() * 100) 
                     for _ in range(count)]
            
            # Alan hesaplama testi
            area_perf = self.measure_performance(
                GeometryUtils.calculate_polygon_area, 
                points
            )
            
            # Çevre hesaplama testi
            perimeter_perf = self.measure_performance(
                GeometryUtils.calculate_perimeter, 
                points
            )
            
            results[count] = {
                'area_calculation': area_perf,
                'perimeter_calculation': perimeter_perf
            }
            
            print(f"   🔺 Alan: {area_perf['execution_time']:.4f}s")
            print(f"   ⭕ Çevre: {perimeter_perf['execution_time']:.4f}s")
        
        return results
    
    def test_statistics_calculations(self, data_sizes: List[int]) -> Dict:
        """İstatistik hesaplama performansını test et"""
        results = {}
        
        for size in data_sizes:
            print(f"📊 {size} verili istatistik testi...")
            
            # Test verisi oluştur
            data = np.random.random(size) * 1000
            
            # İstatistik hesaplama testi
            stats_perf = self.measure_performance(
                StatisticsUtils.calculate_statistics, 
                data.tolist()
            )
            
            results[size] = stats_perf
            
            print(f"   📈 İstatistik: {stats_perf['execution_time']:.4f}s")
        
        return results
    
    def run_all_tests(self) -> Dict:
        """Tüm testleri çalıştır"""
        print("🚀 Performans testleri başlıyor...\n")
        
        all_results = {}
        
        # 1. Dosya analiz testleri
        print("📁 Dosya Analiz Testleri")
        print("-" * 30)
        all_results['file_analysis'] = self.test_file_analysis([50, 100, 500, 1000])
        print()
        
        # 2. Geometri hesaplama testleri
        print("📐 Geometri Hesaplama Testleri")
        print("-" * 30)
        all_results['geometry'] = self.test_geometry_calculations([10, 100, 1000, 5000])
        print()
        
        # 3. İstatistik hesaplama testleri
        print("📊 İstatistik Hesaplama Testleri")
        print("-" * 30)
        all_results['statistics'] = self.test_statistics_calculations([100, 1000, 10000, 50000])
        print()
        
        return all_results
    
    def generate_performance_report(self, results: Dict) -> str:
        """Performans raporu oluştur"""
        report = []
        report.append("# 📊 Performans Test Raporu")
        report.append("")
        report.append(f"**Test Tarihi:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Sistem:** {psutil.cpu_count()} CPU, {psutil.virtual_memory().total // 1024**3:.1f}GB RAM")
        report.append("")
        
        # Dosya analiz sonuçları
        if 'file_analysis' in results:
            report.append("## 📁 Dosya Analiz Performansı")
            report.append("")
            report.append("| Element Sayısı | Süre (s) | Bellek (MB) | Başarı |")
            report.append("|----------------|----------|-------------|--------|")
            
            for count, result in results['file_analysis'].items():
                success_icon = "✅" if result['success'] else "❌"
                report.append(f"| {count:,} | {result['execution_time']:.2f} | {result['memory_usage']:.1f} | {success_icon} |")
            report.append("")
        
        # Geometri hesaplama sonuçları
        if 'geometry' in results:
            report.append("## 📐 Geometri Hesaplama Performansı")
            report.append("")
            report.append("| Nokta Sayısı | Alan (ms) | Çevre (ms) |")
            report.append("|--------------|-----------|------------|")
            
            for count, result in results['geometry'].items():
                area_time = result['area_calculation']['execution_time'] * 1000
                perimeter_time = result['perimeter_calculation']['execution_time'] * 1000
                report.append(f"| {count:,} | {area_time:.2f} | {perimeter_time:.2f} |")
            report.append("")
        
        # İstatistik hesaplama sonuçları
        if 'statistics' in results:
            report.append("## 📊 İstatistik Hesaplama Performansı")
            report.append("")
            report.append("| Veri Boyutu | Süre (ms) | Bellek (MB) |")
            report.append("|-------------|-----------|-------------|")
            
            for size, result in results['statistics'].items():
                time_ms = result['execution_time'] * 1000
                memory_mb = result['memory_usage']
                report.append(f"| {size:,} | {time_ms:.2f} | {memory_mb:.1f} |")
            report.append("")
        
        # Öneriler
        report.append("## 💡 Performans Önerileri")
        report.append("")
        
        # Dosya analiz önerileri
        if 'file_analysis' in results:
            max_elements = max(results['file_analysis'].keys())
            max_time = results['file_analysis'][max_elements]['execution_time']
            
            if max_time > 60:
                report.append("- ⚠️ Büyük dosyalar için işleme süresi uzun. Paralel işleme önerilir.")
            
            max_memory = max(r['memory_usage'] for r in results['file_analysis'].values())
            if max_memory > 500:
                report.append("- 💾 Bellek kullanımı yüksek. Lazy loading önerilir.")
        
        report.append("- ⚡ Numpy vectorization kullanarak hesaplamaları hızlandırabilirsiniz.")
        report.append("- 🔄 Streamlit cache ile tekrarlanan hesaplamaları önleyebilirsiniz.")
        report.append("- 📊 Büyük veri setleri için chunking kullanın.")
        
        return "\n".join(report)

def main():
    """Ana test fonksiyonu"""
    print("🏗️ Yapısal Analiz Uygulaması - Performans Testleri")
    print("=" * 50)
    
    # Test sınıfını oluştur
    tester = PerformanceTest()
    
    # Tüm testleri çalıştır
    results = tester.run_all_tests()
    
    # Rapor oluştur
    report = tester.generate_performance_report(results)
    
    # Raporu dosyaya kaydet
    report_path = "performance_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Performans raporu oluşturuldu: {report_path}")
    print("\n" + "=" * 50)
    print("✅ Tüm testler tamamlandı!")

if __name__ == "__main__":
    main()