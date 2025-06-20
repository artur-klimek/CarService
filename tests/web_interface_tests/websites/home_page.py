"""
Home page test class for testing the main page at "/"
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Dict, Any
from selenium.webdriver.chrome.options import Options

class HomePage:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.test_results = {}
        self.config = self._load_config()
        self.base_url = f"{self.config['base_url']}:{self.config['port']}"
        self.home_url = f"{self.base_url}/"
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1280, 720), (768, 1024), (414, 896), (375, 667)
        ]

    def _load_config(self) -> Dict[str, Any]:
        with open('tests/web_interface_tests/tests_config.json', 'r') as f:
            return json.load(f)

    def _get_fresh_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-features=PasswordManagerEnabled,PasswordLeakDetection,AutofillKeyedPasswords")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-save-password-bubble")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--incognito")
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        return webdriver.Chrome(options=chrome_options)

    def _log_html_on_error(self, driver, context: str):
        try:
            html = driver.page_source
            with open(f"selenium_error_{context}.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def _save_test_result(self, test_name: str, result: Dict[str, Any]) -> None:
        self.test_results[test_name] = result

    def get_test_results(self) -> Dict[str, Any]:
        return self.test_results

    def _login_as(self, user_type: str, driver) -> None:
        login_url = f"{self.base_url}/auth/login"
        driver.get(login_url)
        wait = WebDriverWait(driver, 5)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
        credentials = self.config["test_users"][user_type]
        username_field.clear()
        username_field.send_keys(credentials["login"])
        password_field.clear()
        password_field.send_keys(credentials["password"])
        submit_button.click()
        time.sleep(0.2)

    def _logout(self, driver) -> None:
        try:
            driver.get(f"{self.base_url}/auth/logout")
            time.sleep(0.2)
        except Exception:
            pass

    def _check_page_load(self, user_type: str) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.home_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "user_type": user_type, "elements_found": {}}
            elements = [
                ("navbar", (By.CLASS_NAME, "navbar")),
                ("welcome_header", (By.XPATH, "//h1[contains(text(), 'Welcome to CarService') or contains(text(), 'CarService') or contains(@class, 'display-4') or contains(@class, 'display')]")),
                ("footer", (By.CLASS_NAME, "footer")),
            ]
            for name, locator in elements:
                try:
                    wait.until(EC.presence_of_element_located(locator))
                    result["elements_found"][name] = {"status": "passed"}
                except Exception as e:
                    result["elements_found"][name] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
                    self._log_html_on_error(driver, f"home_{user_type}_{name}")
            result["message"] = "Page loaded successfully with all essential elements" if result["status"] == "passed" else f"Some elements missing: {[k for k,v in result['elements_found'].items() if v['status']=='failed']}"
        except Exception as e:
            self._log_html_on_error(driver, f"home_{user_type}_page_load")
            result = {"status": "failed", "user_type": user_type, "message": f"Unexpected error: {str(e)}", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"page_load_{user_type}", result)
        return result

    def _check_element_visibility(self, user_type: str) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.home_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            elements_to_check = {
                "navbar": (By.CLASS_NAME, "navbar"),
                "footer": (By.CLASS_NAME, "footer"),
                "welcome_header": (By.XPATH, "//h1[contains(text(), 'Welcome to CarService') or contains(text(), 'CarService') or contains(@class, 'display-4') or contains(@class, 'display')]")
            }
            visibility_results = {}
            status = "passed"
            for element_name, locator in elements_to_check.items():
                try:
                    element = wait.until(EC.presence_of_element_located(locator))
                    is_visible = element.is_displayed()
                    is_enabled = element.is_enabled() if hasattr(element, 'is_enabled') else True
                    visibility_results[element_name] = {
                        "visible": is_visible,
                        "enabled": is_enabled,
                        "status": "passed" if is_visible and is_enabled else "failed"
                    }
                    if not (is_visible and is_enabled):
                        status = "failed"
                except Exception as e:
                    visibility_results[element_name] = {"status": "failed", "error": str(e)}
                    status = "failed"
            result = {
                "status": status,
                "user_type": user_type,
                "message": "All elements visibility check completed" if status == "passed" else "Some elements not visible or not enabled",
                "elements": visibility_results
            }
        except Exception as e:
            result = {"status": "failed", "user_type": user_type, "message": f"Error checking element visibility: {str(e)}", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"element_visibility_{user_type}", result)
        return result

    def _get_expected_elements_flat(self, user_type: str):
        """
        Zwraca listę słowników opisujących konkretne elementy do sprawdzenia na stronie głównej dla danej roli.
        Każdy element to dict: {
            'name': opis,
            'by': By.XPATH/CSS_SELECTOR/ID/..., 
            'locator': ...,
            'text': oczekiwany tekst (opcjonalnie),
            'href': oczekiwany href (opcjonalnie)
        }
        """
        if user_type == "unauthenticated":
            return [
                {"name": "header_welcome", "by": By.CSS_SELECTOR, "locator": "h1.display-4", "text": "Welcome to CarService"},
                {"name": "lead_paragraph", "by": By.CSS_SELECTOR, "locator": "p.lead", "text": "Professional car maintenance and repair services."},
                {"name": "card_register_title", "by": By.XPATH, "locator": "//h5[contains(., 'Register') and not(contains(., 'User'))]", "text": "Register"},
                {"name": "card_register_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/auth/register') and contains(., 'Register Now')]", "text": "Register Now", "href": "/auth/register"},
                {"name": "card_signin_title", "by": By.XPATH, "locator": "//h5[contains(., 'Sign In')]", "text": "Sign In"},
                {"name": "card_signin_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/auth/login') and contains(., 'Sign In')]", "text": "Sign In", "href": "/auth/login"},
                {"name": "card_contact_title", "by": By.XPATH, "locator": "//h5[contains(., 'Contact Us')]", "text": "Contact Us"},
                {"name": "card_contact_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/contact') and contains(., 'Contact Support')]", "text": "Contact Support", "href": "/contact"},
                {"name": "navbar_home", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/') and contains(normalize-space(.), 'Home')]", "text": "Home", "href": "/"},
                {"name": "navbar_contact", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/contact') and contains(normalize-space(.), 'Contact')]", "text": "Contact", "href": "/contact"},
                {"name": "navbar_login", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/login') and contains(normalize-space(.), 'Login')]", "text": "Login", "href": "/auth/login"},
                {"name": "navbar_register", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/register') and contains(normalize-space(.), 'Register')]", "text": "Register", "href": "/auth/register"},
                {"name": "footer", "by": By.CLASS_NAME, "locator": "footer"}
            ]
        elif user_type == "client":
            return [
                {"name": "header_welcome", "by": By.CSS_SELECTOR, "locator": "h1.display-4", "text": "Welcome to CarService"},
                {"name": "lead_paragraph", "by": By.CSS_SELECTOR, "locator": "p.lead", "text": "Professional car maintenance and repair services."},
                # My Vehicles card
                {"name": "card_my_vehicles_title", "by": By.XPATH, "locator": "//h5[contains(., 'My Vehicles')]", "text": "My Vehicles"},
                {"name": "card_my_vehicles_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/client/vehicles') and contains(., 'View Vehicles')]", "text": "View Vehicles", "href": "/client/vehicles"},
                # My Services card
                {"name": "card_my_services_title", "by": By.XPATH, "locator": "//h5[contains(., 'My Services')]", "text": "My Services"},
                {"name": "card_my_services_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/client/services') and contains(., 'View Services')]", "text": "View Services", "href": "/client/services"},
                # Request Service card
                {"name": "card_request_service_title", "by": By.XPATH, "locator": "//h5[contains(., 'Request Service')]", "text": "Request Service"},
                {"name": "card_request_service_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/client/service-request') and contains(., 'New Service')]", "text": "New Service", "href": "/client/service-request"},
                # Contact Us card (dla klienta też jest)
                {"name": "card_contact_title", "by": By.XPATH, "locator": "//h5[contains(., 'Contact Us')]", "text": "Contact Us"},
                {"name": "card_contact_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/contact') and contains(., 'Contact Support')]", "text": "Contact Support", "href": "/contact"},
                # Navbar
                {"name": "navbar_home", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/') and contains(normalize-space(.), 'Home')]", "text": "Home", "href": "/"},
                {"name": "navbar_contact", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/contact') and contains(normalize-space(.), 'Contact')]", "text": "Contact", "href": "/contact"},
                {"name": "navbar_my_vehicles", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/vehicles') and contains(normalize-space(.), 'My Vehicles')]", "text": "My Vehicles", "href": "/client/vehicles"},
                {"name": "navbar_my_services", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/services') and contains(normalize-space(.), 'My Services')]", "text": "My Services", "href": "/client/services"},
                {"name": "navbar_request_service", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/service-request') and contains(normalize-space(.), 'Request Service')]", "text": "Request Service", "href": "/client/service-request"},
                {"name": "navbar_logout", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/logout') and contains(normalize-space(.), 'Logout')]", "text": "Logout", "href": "/auth/logout"},
                {"name": "footer", "by": By.CLASS_NAME, "locator": "footer"}
            ]
        elif user_type == "employee":
            return [
                {"name": "header_welcome", "by": By.CSS_SELECTOR, "locator": "h1.display-4", "text": "Welcome to CarService"},
                {"name": "lead_paragraph", "by": By.CSS_SELECTOR, "locator": "p.lead", "text": "Professional car maintenance and repair services."},
                # Service Management card
                {"name": "card_service_management_title", "by": By.XPATH, "locator": "//h5[contains(., 'Service Management') and not(contains(., 'User')) and not(contains(., 'Vehicle'))]", "text": "Service Management"},
                {"name": "card_service_management_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/employee/services') and contains(., 'Manage Services')]"},
                # Vehicle List card
                {"name": "card_vehicle_list_title", "by": By.XPATH, "locator": "//h5[contains(., 'Vehicle List')]", "text": "Vehicle List"},
                {"name": "card_vehicle_list_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/employee/vehicles') and contains(., 'View Vehicles')]", "text": "View Vehicles", "href": "/employee/vehicles"},
                # Client Management card
                {"name": "card_client_management_title", "by": By.XPATH, "locator": "//h5[contains(., 'Client Management')]", "text": "Client Management"},
                {"name": "card_client_management_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/employee/users') and contains(., 'Manage Clients')]", "text": "Manage Clients", "href": "/employee/users"},
                # Navbar
                {"name": "navbar_home", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/') and contains(normalize-space(.), 'Home')]", "text": "Home", "href": "/"},
                {"name": "navbar_dashboard", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/employee/dashboard') and contains(normalize-space(.), 'Dashboard')]", "text": "Dashboard", "href": "/employee/dashboard"},
                {"name": "navbar_services", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/employee/services') and contains(normalize-space(.), 'Services')]", "text": "Services", "href": "/employee/services"},
                {"name": "navbar_users", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/employee/users') and contains(normalize-space(.), 'Users')]", "text": "Users", "href": "/employee/users"},
                {"name": "navbar_vehicles", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/employee/vehicles') and contains(normalize-space(.), 'Vehicles')]", "text": "Vehicles", "href": "/employee/vehicles"},
                {"name": "navbar_logout", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/logout') and contains(normalize-space(.), 'Logout')]", "text": "Logout", "href": "/auth/logout"},
                {"name": "footer", "by": By.CLASS_NAME, "locator": "footer"}
            ]
        elif user_type == "admin":
            return [
                {"name": "header_welcome", "by": By.CSS_SELECTOR, "locator": "h1.display-4", "text": "Welcome to CarService"},
                {"name": "lead_paragraph", "by": By.CSS_SELECTOR, "locator": "p.lead", "text": "Professional car maintenance and repair services."},
                # User Management card
                {"name": "card_user_management_title", "by": By.XPATH, "locator": "//h5[contains(., 'User Management')]", "text": "User Management"},
                {"name": "card_user_management_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/admin/users') and contains(., 'Manage Users')]", "text": "Manage Users", "href": "/admin/users"},
                # Vehicle Management card
                {"name": "card_vehicle_management_title", "by": By.XPATH, "locator": "//h5[contains(., 'Vehicle Management')]", "text": "Vehicle Management"},
                {"name": "card_vehicle_management_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/admin/vehicles') and contains(., 'Manage Vehicles')]", "text": "Manage Vehicles", "href": "/admin/vehicles"},
                # Service Management card
                {"name": "card_service_management_title", "by": By.XPATH, "locator": "//h5[contains(., 'Service Management')]", "text": "Service Management"},
                {"name": "card_service_management_btn", "by": By.XPATH, "locator": "//a[contains(@href, '/admin/services') and contains(., 'Manage Services')]", "text": "Manage Services", "href": "/admin/services"},
                # Navbar
                {"name": "navbar_home", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/') and contains(normalize-space(.), 'Home')]", "text": "Home", "href": "/"},
                {"name": "navbar_dashboard", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/admin/dashboard') and contains(normalize-space(.), 'Dashboard')]", "text": "Dashboard", "href": "/admin/dashboard"},
                {"name": "navbar_users", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/admin/users') and contains(normalize-space(.), 'Users')]", "text": "Users", "href": "/admin/users"},
                {"name": "navbar_services", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/admin/services') and contains(normalize-space(.), 'Services')]", "text": "Services", "href": "/admin/services"},
                {"name": "navbar_vehicles", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/admin/vehicles') and contains(normalize-space(.), 'Vehicles')]", "text": "Vehicles", "href": "/admin/vehicles"},
                {"name": "navbar_logout", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/logout') and contains(normalize-space(.), 'Logout')]", "text": "Logout", "href": "/auth/logout"},
                {"name": "footer", "by": By.CLASS_NAME, "locator": "footer"}
            ]
        return []

    def _check_elements_flat(self, user_type: str) -> dict:
        driver = self._get_fresh_driver()
        results = {}
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.home_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            expected_elements = self._get_expected_elements_flat(user_type)
            for elem in expected_elements:
                name = elem["name"]
                by = elem["by"]
                locator = elem["locator"]
                try:
                    web_elem = wait.until(EC.presence_of_element_located((by, locator)))
                    is_visible = web_elem.is_displayed()
                    result = {"status": "passed" if is_visible else "failed", "visible": is_visible}
                    if "text" in elem:
                        actual_text = web_elem.text.strip()
                        expected_text = elem["text"].strip()
                        result["text_match"] = (expected_text in actual_text)
                        result["actual_text"] = actual_text
                        result["expected_text"] = expected_text
                        if not result["text_match"]:
                            result["status"] = "failed"
                    if "href" in elem:
                        actual_href = web_elem.get_attribute("href")
                        result["href_match"] = (elem["href"] in actual_href) if actual_href else False
                        result["actual_href"] = actual_href
                        result["expected_href"] = elem["href"]
                        if not result["href_match"]:
                            result["status"] = "failed"
                except Exception as e:
                    result = {"status": "failed", "error": str(e)}
                results[name] = result
        finally:
            self._logout(driver)
            driver.quit()
        overall_status = "passed" if all(r["status"] == "passed" for r in results.values()) else "failed"
        summary = {
            "status": overall_status,
            "user_type": user_type,
            "message": "All elements checked" if overall_status == "passed" else f"Some elements failed: {[k for k,v in results.items() if v['status']=='failed']}",
            "elements": results
        }
        self._save_test_result(f"elements_flat_{user_type}", summary)
        return summary

    def _test_scrolling(self, user_type: str) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.home_url)
            driver.set_window_size(375, 667)
            time.sleep(0.1)
            initial_scroll = driver.execute_script("return window.pageYOffset;")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.1)
            bottom_scroll = driver.execute_script("return window.pageYOffset;")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.1)
            final_scroll = driver.execute_script("return window.pageYOffset;")
            driver.set_window_size(1920, 1080)
            result = {
                "status": "passed",
                "user_type": user_type,
                "message": "Scrolling test completed successfully",
                "scroll_positions": {
                    "initial": initial_scroll,
                    "bottom": bottom_scroll,
                    "final": final_scroll
                }
            }
        except Exception as e:
            result = {"status": "failed", "user_type": user_type, "message": f"Error during scrolling test: {str(e)}", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"scrolling_{user_type}", result)
        return result

    def _check_links_redirect(self, user_type: str) -> dict:
        driver = self._get_fresh_driver()
        results = {}
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.home_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            expected_elements = self._get_expected_elements_flat(user_type)
            for elem in expected_elements:
                if "href" not in elem:
                    continue
                name = elem["name"]
                by = elem["by"]
                locator = elem["locator"]
                expected_href = elem["href"]

                allowed_urls = [expected_href]
                if name in ["navbar_logout"]:
                    allowed_urls.append("/")
                if name in ["navbar_request_service", "card_request_service_btn"] and user_type == "client":
                    allowed_urls.append("/client/vehicles")
                try:
                    web_elem = wait.until(EC.element_to_be_clickable((by, locator)))
                    web_elem.click()
                    time.sleep(0.3)
                    current_url = driver.current_url
                    # Sprawdź czy przekierowanie jest poprawne
                    passed = any(url in current_url for url in allowed_urls)
                    results[name] = {
                        "status": "passed" if passed else "failed",
                        "expected_href": allowed_urls,
                        "actual_url": current_url,
                        "message": "Redirect OK" if passed else f"Expected one of {allowed_urls} in '{current_url}'"
                    }
                    driver.get(self.home_url)
                    time.sleep(0.2)
                except Exception as e:
                    results[name] = {"status": "failed", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        overall_status = "passed" if all(r["status"] == "passed" for r in results.values()) else "failed"
        summary = {
            "status": overall_status,
            "user_type": user_type,
            "message": "All link redirects checked" if overall_status == "passed" else f"Some links failed: {[k for k,v in results.items() if v['status']=='failed']}",
            "links": results
        }
        self._save_test_result(f"links_redirect_{user_type}", summary)
        return summary

    def test_as_unauthenticated(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("unauthenticated"),
            "element_visibility": self._check_element_visibility("unauthenticated"),
            "elements_flat": self._check_elements_flat("unauthenticated"),
            "links_redirect": self._check_links_redirect("unauthenticated"),
            "scrolling": self._test_scrolling("unauthenticated"),
        }
        self._save_test_result("unauthenticated_tests", results)
        return results

    def test_as_client(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("client"),
            "element_visibility": self._check_element_visibility("client"),
            "elements_flat": self._check_elements_flat("client"),
            "links_redirect": self._check_links_redirect("client"),
            "scrolling": self._test_scrolling("client"),
        }
        self._save_test_result("client_tests", results)
        return results

    def test_as_employee(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("employee"),
            "element_visibility": self._check_element_visibility("employee"),
            "elements_flat": self._check_elements_flat("employee"),
            "links_redirect": self._check_links_redirect("employee"),
            "scrolling": self._test_scrolling("employee"),
        }
        self._save_test_result("employee_tests", results)
        return results

    def test_as_admin(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("admin"),
            "element_visibility": self._check_element_visibility("admin"),
            "elements_flat": self._check_elements_flat("admin"),
            "links_redirect": self._check_links_redirect("admin"),
            "scrolling": self._test_scrolling("admin"),
        }
        self._save_test_result("admin_tests", results)
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        all_results = {
            "unauthenticated": self.test_as_unauthenticated(),
            "client": self.test_as_client(),
            "employee": self.test_as_employee(),
            "admin": self.test_as_admin()
        }
        self._save_test_result("all_tests", all_results)
        return all_results

    def print_test_results(self, results: Dict[str, Any], indent: int = 0) -> None:
        indent_str = "  " * indent
        for key, value in results.items():
            if isinstance(value, dict):
                if "status" in value:
                    status_color = "\033[92m" if value["status"] == "passed" else "\033[91m"
                    print(f"{indent_str}{key}: {status_color}{value['status']}\033[0m")
                    if "message" in value:
                        print(f"{indent_str}  Message: {value['message']}")
                    if "error" in value:
                        print(f"{indent_str}  Error: {value['error']}")
                    for subkey in [k for k in value if isinstance(value[k], dict)]:
                        print(f"{indent_str}  {subkey}:")
                        self.print_test_results(value[subkey], indent + 2)
                else:
                    print(f"{indent_str}{key}:")
                    self.print_test_results(value, indent + 1)
            else:
                print(f"{indent_str}{key}: {value}")

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        home_page = HomePage(driver)
        results = home_page.run_all_tests()
        print("\nTest Results:")
        print("============")
        home_page.print_test_results(results)
    finally:
        driver.quit()
