#!/usr/bin/env python
"""
Test connectivity to local Linux CVE server
"""
import requests
import re

def test_server_connectivity(base_url='http://localhost:8080/linux-cve-announce'):
    """Test if the local Linux CVE server is accessible."""
    print(f"Testing connectivity to {base_url}...")
    
    try:
        response = requests.get(f'{base_url}/', timeout=10)
        response.raise_for_status()
        
        print(f"✓ Server is accessible")
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Length: {len(response.text)} bytes")
        
        # Try to extract some links to see the structure
        patterns = [
            r'href="([^"]*[0-9a-f-]+/T/#[tu])"',  # Main pattern for message threads
            r'href="([^"]*[0-9a-f-]+)"',  # Fallback for direct message IDs
        ]
        
        all_links = []
        for pattern in patterns:
            links = re.findall(pattern, response.text)
            # Clean up the links
            for link in links:
                clean_link = link.replace('/T/#t', '').replace('/T/#u', '')
                if re.search(r'[0-9a-f-]{10,}', clean_link):
                    all_links.append(clean_link)
        
        unique_links = list(set(all_links))
        print(f"  Found {len(unique_links)} potential message links")
        
        if unique_links:
            print("  Sample links:")
            for link in unique_links[:5]:  # Show first 5 links
                print(f"    - {link}")
        
        # Test a sample message link if available
        if unique_links:
            sample_link = unique_links[0]
            if not sample_link.startswith('http'):
                if sample_link.startswith('/'):
                    sample_url = f"http://localhost:8080{sample_link}"
                else:
                    sample_url = f"{base_url}/{sample_link}"
            else:
                sample_url = sample_link
            
            print(f"\nTesting sample message: {sample_url}")
            try:
                msg_response = requests.get(sample_url, timeout=10)
                print(f"  ✓ Sample message accessible (Status: {msg_response.status_code})")
                
                # Try to get raw content
                raw_urls = [
                    f"{sample_url}/raw",
                    f"{sample_url}.txt",
                    sample_url.replace('/linux-cve-announce/', '/linux-cve-announce/raw/'),
                ]
                
                for raw_url in raw_urls:
                    try:
                        raw_response = requests.get(raw_url, timeout=10)
                        if raw_response.status_code == 200:
                            print(f"  ✓ Raw content available at: {raw_url}")
                            break
                    except:
                        continue
                else:
                    print(f"  ⚠ No raw content found for sample message")
                    
            except Exception as e:
                print(f"  ✗ Sample message not accessible: {e}")
        
        return True
        
    except requests.RequestException as e:
        print(f"✗ Server not accessible: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your local server is running on port 8080")
        print("2. Check if the URL path '/linux-cve-announce/' is correct")
        print("3. Verify firewall settings allow connections to localhost:8080")
        return False

def main():
    """Test the local Linux CVE server."""
    print("=" * 60)
    print("Linux CVE Local Server Connectivity Test")
    print("=" * 60)
    
    success = test_server_connectivity()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Local server test passed!")
        print("\nYou can now run:")
        print("  python manage.py import_linux_cve --limit 5")
    else:
        print("✗ Local server test failed!")
        print("Please check your server configuration.")

if __name__ == '__main__':
    main()