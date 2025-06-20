"""
Main test runner that executes all test suites
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from websites.auth.login_page import LoginPage

def run_all_tests():
    """Run all test suites."""
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test login page
        login_page = LoginPage(driver)
        login_results = login_page.run_all_tests()
        print("\nFull Login Page Test Results:")
        print("==========================")
        login_page.print_test_results(login_results)
        
        # Add more page tests here
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_all_tests() 