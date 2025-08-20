#!/bin/bash

# Gelişmiş Yapısal Analiz Uygulaması Kurulum Scripti
# Kullanım: ./setup.sh [development|production]

set -e

ENV=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🏗️  Yapısal Analiz Uygulaması Kurulum Başlıyor..."
echo "📂 Kurulum dizini: $SCRIPT_DIR"
echo "🎯 Ortam: $ENV"

# Sistem güncellemesi
echo "📦 Sistem paketleri güncelleniyor..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv curl
elif command -v yum >/dev/null 2>&1; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip curl
elif command -v brew >/dev/null 2>&1; then
    brew update
    brew install python3
fi

# CAD araçlarını yükle
echo "🔧 CAD dönüştürme araçları kuruluyor..."

if command -v apt-get >/dev/null 2>&1; then
    # Ubuntu/Debian
    sudo apt-get install -y librecad freecad qcad
    
    # LibreOffice (DWG desteği için)
    sudo apt-get install -y libreoffice
    
    # Ek kütüphaneler
    sudo apt-get install -y \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libxrender1 \
        libxext6 \
        libsm6 \
        libice6 \
        libfontconfig1 \
        libxss1
        
elif command -v yum >/dev/null 2>&1; then
    # CentOS/RHEL
    sudo yum install -y epel-release
    sudo yum install -y librecad freecad
    
elif command -v brew >/dev/null 2>&1; then
    # macOS
    brew install --cask librecad
    brew install --cask freecad
    brew install --cask qcad
fi

# Python sanal ortamı oluştur
echo "🐍 Python sanal ortamı oluşturuluyor..."
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Python paketlerini yükle
echo "📚 Python paketleri yükleniyor..."
pip install --upgrade pip

if [ "$ENV" = "development" ]; then
    pip install -r requirements.txt
    # Geliştirme araçları
    pip install black flake8 pytest pytest-cov
else
    pip install -r requirements.txt
fi

# Gerekli dizinleri oluştur
echo "📁 Dizin yapısı oluşturuluyor..."
mkdir -p data logs temp reports

# Yetkileri ayarla
chmod +x setup.sh
chmod 755 data logs temp reports

# Konfigürasyon dosyasını kontrol et
if [ ! -f ".env" ]; then
    echo "⚙️  Konfigürasyon dosyası oluşturuluyor..."
    cat > .env << EOF
# Yapısal Analiz Uygulaması Konfigürasyonu
MAX_FILE_SIZE=100
ANALYSIS_TIMEOUT=300
LOG_LEVEL=INFO
ENVIRONMENT=$ENV
EOF
fi

# Servis scripti oluştur (Linux için)
if command -v systemctl >/dev/null 2>&1; then
    echo "🔧 Sistem servisi oluşturuluyor..."
    
    sudo tee /etc/systemd/system/structural-analyzer.service > /dev/null << EOF
[Unit]
Description=Structural Analysis Application
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv/bin
ExecStart=$SCRIPT_DIR/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo "✅ Servis oluşturuldu. Başlatmak için: sudo systemctl start structural-analyzer"
fi

# Test çalıştır
echo "🧪 Kurulum testi yapılıyor..."
python -c "
import streamlit as st
import ezdxf
import pandas as pd
import plotly
import numpy as np
import reportlab
import matplotlib
print('✅ Tüm paketler başarıyla yüklendi!')
"

# Başlatma scripti oluştur
echo "🚀 Başlatma scripti oluşturuluyor..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🏗️  Yapısal Analiz Uygulaması başlatılıyor..."
echo "🌐 Tarayıcınızda http://localhost:8501 adresini açın"
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
EOF

chmod +x start.sh

# Docker kurulumu (isteğe bağlı)
if command -v docker >/dev/null 2>&1; then
    echo "🐳 Docker image oluşturuluyor..."
    docker build -t structural-analyzer .
    echo "✅ Docker image hazır. Çalıştırmak için: docker-compose up"
fi

echo ""
echo "🎉 Kurulum tamamlandı!"
echo ""
echo "📋 Başlatma seçenekleri:"
echo "   1. Doğrudan: ./start.sh"
echo "   2. Servis: sudo systemctl start structural-analyzer"
echo "   3. Docker: docker-compose up"
echo ""
echo "🌐 Uygulama adresi: http://localhost:8501"
echo "📊 Sistem durumu: http://localhost:8501/_stcore/health"
echo ""
echo "📖 Daha fazla bilgi için README.md dosyasını okuyun."