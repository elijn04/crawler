#!/usr/bin/env python3

from agent_flow_link_scraper import AgentFlowLinkScrapper

def test_scrapper():
    """Test the scrapper and show file contents"""
    
    # Test URL
    url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    print(f"🔍 Testing scrapper with: {url}")
    
    # Create scrapper and get file
    scrapper = AgentFlowLinkScrapper()
    file_path = scrapper.get_file(url)
    
    if file_path:
        print(f"✅ Got file at: {file_path}")
        
        # Read and show file contents
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 File size: {len(content)} characters")
            print(f"📄 File type: {type(content)}")
            
            print("\n" + "="*50)
            print("📋 FILE CONTENTS:")
            print("="*50)
            print(content)
            print("="*50)
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            
    else:
        print("❌ Failed to get file - scrapper returned None")

if __name__ == "__main__":
    test_scrapper() 