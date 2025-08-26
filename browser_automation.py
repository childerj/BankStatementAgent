"""
Browser Automation for SharePoint Downloads
Automatically handles authentication and downloads
"""

import json
import time
import os
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

def load_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        return {
            'username': values.get('SHAREPOINT_USERNAME', ''),
            'password': values.get('SHAREPOINT_PASSWORD', ''),
            'file_url': values.get('SHAREPOINT_FILE_URL', '')
        }
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {'username': '', 'password': '', 'file_url': ''}

def setup_chrome_driver():
    """Setup Chrome WebDriver with download preferences"""
    
    download_dir = str(Path.cwd())
    
    chrome_options = Options()
    
    # Set download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Try to find Chrome driver
    driver_paths = [
        './chromedriver.exe',
        './chromedriver',
        'chromedriver.exe',
        'chromedriver'
    ]
    
    for driver_path in driver_paths:
        if Path(driver_path).exists():
            service = Service(driver_path)
            return webdriver.Chrome(service=service, options=chrome_options)
    
    # Try using webdriver-manager if available
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    except ImportError:
        pass
    
    # Try system PATH
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Could not initialize Chrome driver: {e}")
        return None

def automate_sharepoint_download():
    """Automate SharePoint authentication and download"""
    
    if not SELENIUM_AVAILABLE:
        print("Selenium not available. Run: pip install selenium")
        return False
    
    settings = load_settings()
    username = settings['username']
    password = settings['password']
    file_url = settings['file_url']
    
    if not all([username, password, file_url]):
        print("Missing credentials in local.settings.json")
        return False
    
    print("Starting browser automation...")
    
    driver = setup_chrome_driver()
    if not driver:
        print("Could not setup Chrome WebDriver")
        return False
    
    try:
        # Navigate to SharePoint URL
        print(f"Navigating to: {file_url}")
        driver.get(file_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if sign-in is required
        if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
            print("Sign-in required, entering credentials...")
            
            # Enter username
            try:
                username_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "loginfmt"))
                )
                username_field.send_keys(username)
                
                # Click Next
                next_button = driver.find_element(By.ID, "idSIButton9")
                next_button.click()
                
                time.sleep(2)
                
                # Enter password
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "passwd"))
                )
                password_field.send_keys(password)
                
                # Click Sign In
                signin_button = driver.find_element(By.ID, "idSIButton9")
                signin_button.click()
                
                time.sleep(3)
                
                # Handle "Stay signed in?" prompt
                try:
                    stay_signed_in = driver.find_element(By.ID, "idSIButton9")
                    if "yes" in stay_signed_in.text.lower():
                        stay_signed_in.click()
                except:
                    pass
                
            except Exception as e:
                print(f"Authentication failed: {e}")
                return False
        
        # Wait for Excel Online to load
        print("Waiting for Excel Online to load...")
        time.sleep(5)
        
        # Try to find download option
        try:
            # Look for File menu
            file_menu = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'File')]"))
            )
            file_menu.click()
            
            time.sleep(2)
            
            # Look for Download option
            download_option = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
            download_option.click()
            
            time.sleep(2)
            
            # Look for "Download a copy" or similar
            download_copy = driver.find_element(By.XPATH, "//button[contains(text(), 'Download a copy')]")
            download_copy.click()
            
            print("Download initiated...")
            time.sleep(10)  # Wait for download to complete
            
            return True
            
        except Exception as e:
            print(f"Could not find download option: {e}")
            print("Please download manually using the browser window that opened")
            input("Press Enter after downloading manually...")
            return True
    
    except Exception as e:
        print(f"Browser automation failed: {e}")
        return False
    
    finally:
        # Keep browser open for manual intervention if needed
        input("Press Enter to close browser...")
        driver.quit()

def main():
    """Main function"""
    
    print("Browser Automation for SharePoint")
    print("=" * 40)
    
    if not SELENIUM_AVAILABLE:
        print("Selenium not installed.")
        print("Run: pip install selenium webdriver-manager")
        return
    
    result = automate_sharepoint_download()
    
    if result:
        print("\nDownload process completed!")
        print("Run 'python process_local_file.py' to process the downloaded file.")
    else:
        print("\nAutomation failed. Use manual download method instead.")

if __name__ == "__main__":
    main()
