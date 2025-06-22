#!/bin/bash

echo "🚀 MyScapper Setup Script"
echo "========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your AWS credentials and settings"
    echo "   Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME"
else
    echo "✅ .env file already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p downloads
mkdir -p logs
mkdir -p results

# Check AWS credentials
echo "🔐 Checking AWS configuration..."
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✅ AWS credentials found in environment"
else
    echo "⚠️  AWS credentials not found in environment"
    echo "   Make sure to set them in .env file"
fi

# Test installation
echo "🧪 Testing installation..."
python3 -c "import crawl4ai; import fastapi; import boto3; print('✅ All dependencies installed successfully')"

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Test the integration module:"
echo "   python3 myscapper.py"
echo ""
echo "3. Or run standalone scraping:"
echo "   python3 main.py"
echo ""
echo "4. Import in your mainframe:"
echo "   from myscapper import MyScapper, scrape_urls"
echo "" 