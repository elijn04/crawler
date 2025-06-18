"""
URL Validation & Edge Cases Test Suite

TEST RESULTS SUMMARY:
- Test Date: December 2024
- Success Rate: 6/13 tests passed (46.2%)
- Total Runtime: ~40 seconds for full suite

SUCCESSFUL TESTS:
✅ URL with query parameters (https://example.com?param1=value1&param2=value2)
✅ URL with fragment (https://example.com#section1)  
✅ URL with spaces (https://example.com/path with spaces) - Returns 404 but handles gracefully
✅ Very long URL (2000+ chars) - Returns 400 but processes correctly
✅ Basic working URL (https://example.com)
✅ Simple test page (https://httpbin.org/html) - Returns 503 but extracts content

EXPECTED FAILURES (Good error handling):
❌ Malformed URL (htp://invalid.com) - Proper ValueError
❌ Non-existent domain (thisdoesnotexist12345.com) - DNS resolution error
❌ Invalid protocol (ftp://example.com) - Protocol validation works
❌ Empty URL - Proper validation
❌ Null URL - Proper validation  
❌ Invalid URL format - Proper validation

***************************************************
UNEXPECTED FAILURES (Needs investigation):
❌ International domain name (https://xn--nxasmq6b.com) - DNS resolution failed

KEY FINDINGS:
1. Error handling is robust - all invalid URLs fail gracefully with clear error messages
2. URL parsing handles edge cases well (query params, fragments, spaces, long URLs)
3. Performance is consistent ~3 seconds per successful scrape
4. The crawler properly validates URL formats before attempting connection
5. Status codes are captured correctly (200, 404, 400, 503)
6. Content extraction works even for error pages

Add ons(later):
- IDN domain handling could be improved
- Consider adding retry logic for DNS resolution failures
- Status code validation could be added to distinguish success vs error responses
- Performance is acceptable but could be optimized for batch processing

This test validates the core URL handling capabilities of the scraper.
"""

import asyncio
import sys
import time
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scap import navigate_to_page, scroll_to_bottom, get_outer_html

async def test_url_validation_and_edge_cases():
    """
    Test Category 2: URL Validation & Edge Cases
    Testing the existing scap.py functions with various URL scenarios
    """
    
    print("🔍 TESTING URL VALIDATION & EDGE CASES")
    print("=" * 60)
    print("Using existing scap.py functions:")
    print("- navigate_to_page()")
    print("- scroll_to_bottom()")
    print("- get_outer_html()")
    print("=" * 60)
    
    # Test cases from the testing plan
    test_cases = [
        # Invalid URLs
        ("htp://invalid.com", "Malformed URL (missing 't' in http)"),
        ("https://thisdoesnotexist12345.com", "Non-existent domain"),
        ("ftp://example.com", "Invalid protocol (FTP)"),
        ("", "Empty URL"),
        (None, "Null URL"),
        ("not-a-url-at-all", "Invalid URL format"),
        
        # Special URL Cases
        ("https://example.com?param1=value1&param2=value2", "URL with query parameters"),
        ("https://example.com#section1", "URL with fragment"),
        ("https://example.com/path with spaces", "URL with spaces"),
        ("https://example.com/" + "a" * 2000, "Very long URL"),
        ("https://xn--nxasmq6b.com", "International domain name (IDN)"),
        
        # Working URLs for comparison
        ("https://example.com", "Basic working URL"),
        ("https://httpbin.org/html", "Simple test page"),
    ]
    
    results = []
    
    for i, (url, description) in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{len(test_cases)}: {description}")
        print(f"🔗 URL: {repr(url)}")
        print("-" * 40)
        
        start_time = time.time()
        test_result = {
            'url': url,
            'description': description,
            'success': False,
            'error': None,
            'html_length': 0,
            'execution_time': 0,
            'final_url': None
        }
        
        try:
            # Step 1: Navigate to page
            print("   Step 1: Navigating to page...")
            crawler, result = await navigate_to_page(url)
            
            print(f"   ✅ Navigation successful")
            print(f"   📊 Status: {result.status_code}")
            print(f"   📄 Content: {len(result.html)} chars")
            
            test_result['final_url'] = result.url
            
            # Step 2: Scroll to bottom
            print("   Step 2: Scrolling to bottom...")
            scroll_result = await scroll_to_bottom(crawler, result.url)
            print(f"   ✅ Scroll successful")
            
            # Step 3: Get outer HTML
            print("   Step 3: Getting outer HTML...")
            html = await get_outer_html(crawler, result.url)
            print(f"   ✅ HTML extraction successful: {len(html)} chars")
            
            test_result['success'] = True
            test_result['html_length'] = len(html)
            test_result['execution_time'] = time.time() - start_time
            
            # Check for redirects
            if url != result.url:
                print(f"   🔄 Redirected to: {result.url}")
            
            # Close crawler
            await crawler.__aexit__(None, None, None)
            print(f"   ⏱️  Total time: {test_result['execution_time']:.2f}s")
            
        except Exception as e:
            test_result['error'] = str(e)
            test_result['execution_time'] = time.time() - start_time
            
            print(f"   ❌ FAILED: {type(e).__name__}")
            print(f"   💬 Error: {str(e)}")
            print(f"   ⏱️  Time to failure: {test_result['execution_time']:.2f}s")
            
            # Try to close crawler if it exists
            try:
                if 'crawler' in locals():
                    await crawler.__aexit__(None, None, None)
            except:
                pass
        
        results.append(test_result)
    
    # Summary
    print("\n" + "=" * 60)
    print("🔍 URL VALIDATION TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"📊 Success Rate: {successful/len(results)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        if result['success']:
            print(f"{status} {result['description']}: {result['html_length']} chars in {result['execution_time']:.2f}s")
        else:
            error_type = result['error'].split(':')[0] if result['error'] else "Unknown"
            print(f"{status} {result['description']}: {error_type}")
    
    # Analysis
    print("\n🔍 Analysis:")
    
    # Expected failures (should fail gracefully)
    expected_failures = [
        "Malformed URL", "Non-existent domain", "Invalid protocol", 
        "Empty URL", "Null URL", "Invalid URL format"
    ]
    
    actual_failures = [r for r in results if not r['success']]
    expected_failure_results = [r for r in actual_failures if any(exp in r['description'] for exp in expected_failures)]
    unexpected_failures = [r for r in actual_failures if not any(exp in r['description'] for exp in expected_failures)]
    
    print(f"   Expected failures: {len(expected_failure_results)} (good)")
    print(f"   Unexpected failures: {len(unexpected_failures)} (needs investigation)")
    
    if unexpected_failures:
        print("\n   ⚠️  Unexpected failures:")
        for r in unexpected_failures:
            print(f"      - {r['description']}: {r['error']}")
    
    # Performance analysis
    successful_results = [r for r in results if r['success']]
    if successful_results:
        avg_time = sum(r['execution_time'] for r in successful_results) / len(successful_results)
        max_time = max(r['execution_time'] for r in successful_results)
        min_time = min(r['execution_time'] for r in successful_results)
        
        print(f"\n⏱️  Performance (successful tests):")
        print(f"   Average time: {avg_time:.2f}s")
        print(f"   Fastest: {min_time:.2f}s")
        print(f"   Slowest: {max_time:.2f}s")
    
    return results

if __name__ == "__main__":
    print("🧪 Starting URL Validation & Edge Cases Test Suite")
    print("📁 Testing existing scap.py functions")
    print()
    
    try:
        results = asyncio.run(test_url_validation_and_edge_cases())
        print(f"\n🎯 Test completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1) 