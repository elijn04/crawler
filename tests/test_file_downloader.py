import asyncio
import os
from file_downloader import (
    is_downloadable_file, 
    check_content_type, 
    download_file_to_s3,
    process_file_download
)

async def test_url_detection():
    """Test URL detection by extension."""
    print("=" * 50)
    print("Testing URL Detection by Extension")
    print("=" * 50)
    
    test_urls = [
        "https://example.com/document.pdf",  # Should be downloadable
        "https://example.com/image.jpg",     # Should be downloadable
        "https://example.com/archive.zip",   # Should be downloadable
        "https://example.com/page.html",     # Should NOT be downloadable
        "https://example.com/",              # Should NOT be downloadable
        "https://news.ycombinator.com",      # Should NOT be downloadable
    ]
    
    for url in test_urls:
        is_downloadable = is_downloadable_file(url)
        status = "✓ DOWNLOADABLE" if is_downloadable else "✗ NOT DOWNLOADABLE"
        print(f"{status}: {url}")

async def test_content_type_check():
    """Test content type checking with real URLs."""
    print("\n" + "=" * 50)
    print("Testing Content Type Detection")
    print("=" * 50)
    
    test_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # Real PDF
        "https://httpbin.org/image/png",  # PNG image
        "https://httpbin.org/html",       # HTML page
        "https://news.ycombinator.com",   # HTML page
    ]
    
    for url in test_urls:
        try:
            is_downloadable, content_type = await check_content_type(url)
            status = "✓ DOWNLOADABLE" if is_downloadable else "✗ NOT DOWNLOADABLE"
            print(f"{status}: {url}")
            print(f"   Content-Type: {content_type}")
        except Exception as e:
            print(f"✗ ERROR: {url} - {e}")

async def test_file_download_mock():
    """Test file download functionality (without actual S3 upload)."""
    print("\n" + "=" * 50)
    print("Testing File Download (Mock Mode)")
    print("=" * 50)
    
    # Test with a small real file
    test_url = "https://httpbin.org/image/png"
    
    print(f"Testing download from: {test_url}")
    
    # Temporarily modify S3 settings to avoid actual upload
    original_bucket = os.environ.get('AWS_BUCKET_NAME')
    original_region = os.environ.get('AWS_REGION')
    
    # Set mock values (this will cause S3 upload to fail, but we can test the download part)
    os.environ['AWS_BUCKET_NAME'] = 'test-bucket'
    os.environ['AWS_REGION'] = 'us-east-1'
    
    try:
        result = await process_file_download(test_url)
        
        if result['success']:
            print("✓ Download successful!")
            print(f"   File size: {result['file_size']} bytes")
            print(f"   Content type: {result['content_type']}")
            print(f"   S3 URL: {result['s3_url']}")
        else:
            print("✗ Download failed (expected if no S3 credentials):")
            print(f"   Error: {result['error']}")
            
            # This is expected if we don't have real S3 credentials
            if "credentials" in result['error'].lower() or "aws" in result['error'].lower():
                print("   ℹ️  This is expected without proper AWS credentials")
            
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
    
    # Restore original environment
    if original_bucket:
        os.environ['AWS_BUCKET_NAME'] = original_bucket
    if original_region:
        os.environ['AWS_REGION'] = original_region

async def test_integration():
    """Test the complete workflow."""
    print("\n" + "=" * 50)
    print("Testing Integration Workflow")
    print("=" * 50)
    
    test_urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "https://news.ycombinator.com",
        "https://httpbin.org/image/jpeg",
    ]
    
    for url in test_urls:
        print(f"\nProcessing: {url}")
        
        # Step 1: Check by extension
        by_extension = is_downloadable_file(url)
        print(f"  Extension check: {'✓' if by_extension else '✗'}")
        
        # Step 2: Check by content type
        try:
            by_content_type, content_type = await check_content_type(url)
            print(f"  Content-type check: {'✓' if by_content_type else '✗'} ({content_type})")
            
            # Step 3: Decision
            should_download = by_extension or by_content_type
            print(f"  Decision: {'DOWNLOAD' if should_download else 'SCRAPE'}")
            
        except Exception as e:
            print(f"  Content-type check: ✗ Error - {e}")

async def main():
    """Run all tests."""
    print("🧪 File Downloader Test Suite")
    print("=" * 60)
    
    await test_url_detection()
    await test_content_type_check()
    await test_file_download_mock()
    await test_integration()
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Complete!")
    print("\nTo test actual S3 uploads, configure:")
    print("  - AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
    print("  - Update S3_BUCKET_NAME and S3_REGION in file_downloader.py")

if __name__ == "__main__":
    asyncio.run(main()) 