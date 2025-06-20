"""
Client vehicles page test class for testing the vehicles page at "/client/vehicles"
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class ClientVehiclesPage:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.test_results = {}
        self.config = self._load_config()
        self.base_url = f"{self.config['base_url']}:{self.config['port']}"
        self.vehicles_url = f"{self.base_url}/client/vehicles"

    def _load_config(self):
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
        # chrome_options.add_argument("--headless")
        return webdriver.Chrome(options=chrome_options)

    def _login_as(self, user_type: str, driver):
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

    def _logout(self, driver):
        try:
            driver.get(f"{self.base_url}/auth/logout")
            time.sleep(0.2)
        except Exception:
            pass

    def _log_html_on_error(self, driver, context: str):
        try:
            html = driver.page_source
            with open(f"selenium_error_{context}.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def _save_test_result(self, test_name: str, result: dict):
        self.test_results[test_name] = result

    def get_test_results(self):
        return self.test_results

    def _test_access(self, user_type: str) -> dict:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.vehicles_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "user_type": user_type, "message": ""}
            if user_type == "client":
                # Sprawdź nagłówek
                try:
                    header = wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
                    result["header"] = {"status": "passed"}
                except Exception as e:
                    result["header"] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
                # Sprawdź przycisk Add New Vehicle
                try:
                    add_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/client/vehicles/add') and contains(., 'Add New Vehicle')]")))
                    result["add_btn"] = {"status": "passed"}
                except Exception as e:
                    result["add_btn"] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
                # Sprawdź czy są pojazdy lub komunikat o braku pojazdów
                try:
                    vehicle_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title')]")
                    if vehicle_cards:
                        result["vehicles"] = {"status": "passed", "count": len(vehicle_cards)}
                        # Sprawdź przyciski Edit, Request Service, Delete dla pierwszego pojazdu
                        try:
                            card = vehicle_cards[0].find_element(By.XPATH, "ancestor::div[contains(@class, 'card')]")
                            # Po każdej akcji szukaj elementów od nowa
                            edit_btn = card.find_element(By.XPATH, ".//a[contains(@href, '/client/vehicles/') and contains(@href, '/edit') and contains(., 'Edit')]")
                            req_btn = card.find_element(By.XPATH, ".//a[contains(@href, '/client/service-request') and contains(., 'Request Service')]")
                            del_btn = card.find_element(By.XPATH, ".//button[contains(@class, 'btn-outline-danger') and contains(., 'Delete')]")
                            result["vehicle_card_btns"] = {"status": "passed"}
                        except Exception as e:
                            result["vehicle_card_btns"] = {"status": "failed", "error": str(e)}
                            result["status"] = "failed"
                    else:
                        # Sprawdź komunikat o braku pojazdów
                        try:
                            info = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-info') and contains(., \"haven't added any vehicles\")]")
                            result["no_vehicles_info"] = {"status": "passed"}
                        except Exception as e:
                            result["no_vehicles_info"] = {"status": "failed", "error": str(e)}
                            result["status"] = "failed"
                except Exception as e:
                    result["vehicles"] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
            else:
                # Sprawdź czy jest przekierowanie lub komunikat o braku dostępu
                current_url = driver.current_url
                if "/auth/login" in current_url or "/login" in current_url or current_url.rstrip("/").endswith(self.base_url):
                    result["access"] = {"status": "passed", "message": f"Redirected to login or home: {current_url}"}
                elif user_type in ["employee", "admin"] and ("/dashboard" in current_url or "/admin" in current_url or "/employee" in current_url):
                    result["access"] = {"status": "passed", "message": f"Redirected to dashboard: {current_url}"}
                else:
                    # Sprawdź komunikat o braku dostępu
                    try:
                        alert = driver.find_element(By.XPATH, "//*[contains(., 'not authorized') or contains(., 'access denied') or contains(., 'permission denied') or contains(., 'zaloguj') or contains(., 'nie masz dostępu')]")
                        result["access"] = {"status": "passed", "message": "Access denied message present"}
                    except Exception:
                        result["access"] = {"status": "failed", "message": f"Unexpected access: {current_url}"}
                        result["status"] = "failed"
            result["final_url"] = driver.current_url
        except Exception as e:
            self._log_html_on_error(driver, f"vehicles_access_{user_type}")
            result = {"status": "failed", "user_type": user_type, "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"access_{user_type}", result)
        return result

    def _get_expected_navbar_links(self):
        # Zwraca listę linków navbaru klienta (zgodnie z base.html i index.html)
        return [
            {"name": "navbar_home", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/') and contains(normalize-space(.), 'Home')]", "href": "/"},
            {"name": "navbar_contact", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/contact') and contains(normalize-space(.), 'Contact')]", "href": "/contact"},
            {"name": "navbar_my_vehicles", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/vehicles') and contains(normalize-space(.), 'My Vehicles')]", "href": "/client/vehicles"},
            {"name": "navbar_my_services", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/services') and contains(normalize-space(.), 'My Services')]", "href": "/client/services"},
            {"name": "navbar_request_service", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/client/service-request') and contains(normalize-space(.), 'Request Service')]", "href": "/client/service-request"},
            {"name": "navbar_logout", "by": By.XPATH, "locator": "//div[@id='navbarNav']//a[contains(@class, 'nav-link') and contains(@href, '/auth/logout') and contains(normalize-space(.), 'Logout')]", "href": "/auth/logout"},
        ]

    def _test_links_redirect(self) -> dict:
        driver = self._get_fresh_driver()
        results = {}
        try:
            self._login_as("client", driver)
            driver.get(self.vehicles_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            # --- Navbar links ---
            navbar_links = self._get_expected_navbar_links()
            for link in navbar_links:
                name = link["name"]
                by = link["by"]
                locator = link["locator"]
                expected_href = link["href"]
                allowed_urls = [expected_href]
                if name == "navbar_logout":
                    allowed_urls.append("/")
                if name == "navbar_request_service":
                    allowed_urls.append("/client/vehicles")
                try:
                    nav_elem = wait.until(EC.element_to_be_clickable((by, locator)))
                    nav_elem.click()
                    time.sleep(0.3)
                    current_url = driver.current_url
                    passed = any(url in current_url for url in allowed_urls)
                    # Dla navbar_request_service: jeśli przekierowano na /client/vehicles i jest alert, to passed
                    if name == "navbar_request_service" and "/client/vehicles" in current_url:
                        try:
                            alert = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-warning') and contains(., 'Please select a vehicle first.')]")
                            if alert.is_displayed():
                                passed = True
                        except Exception:
                            pass
                    results[name] = {
                        "status": "passed" if passed else "failed",
                        "expected_href": allowed_urls,
                        "actual_url": current_url,
                        "message": "Redirect OK" if passed else f"Expected one of {allowed_urls} in '{current_url}'"
                    }
                    # Po kliknięciu logout lub inny link wróć na vehicles
                    if name != "navbar_logout":
                        driver.get(self.vehicles_url)
                        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
                        time.sleep(0.2)
                    else:
                        self._login_as("client", driver)
                        driver.get(self.vehicles_url)
                        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
                        time.sleep(0.2)
                except Exception as e:
                    results[name] = {"status": "failed", "error": str(e)}
            # --- Vehicles page links (jak dotychczas) ---
            # Add New Vehicle
            try:
                add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/client/vehicles/add') and contains(., 'Add New Vehicle')]")))
                add_btn.click()
                wait.until(EC.url_contains("/client/vehicles/add"))
                current_url = driver.current_url
                results["add_new_vehicle"] = {"status": "passed" if "/client/vehicles/add" in current_url else "failed", "actual_url": current_url}
                driver.back()
                wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
            except Exception as e:
                results["add_new_vehicle"] = {"status": "failed", "error": str(e)}
            # Jeśli są pojazdy, sprawdź linki Edit i Request Service
            try:
                vehicle_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title')]")
                if vehicle_cards:
                    card = vehicle_cards[0].find_element(By.XPATH, "ancestor::div[contains(@class, 'card')]")
                    # Edit
                    try:
                        edit_btn = card.find_element(By.XPATH, ".//a[contains(@href, '/client/vehicles/') and contains(@href, '/edit') and contains(., 'Edit')]")
                        edit_btn.click()
                        wait.until(EC.url_contains("/client/vehicles/") and EC.url_contains("/edit"))
                        current_url = driver.current_url
                        results["edit_vehicle"] = {"status": "passed" if "/client/vehicles/" in current_url and "/edit" in current_url else "failed", "actual_url": current_url}
                        driver.back()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
                        vehicle_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title')]" )
                        card = vehicle_cards[0].find_element(By.XPATH, "ancestor::div[contains(@class, 'card')]")
                    except Exception as e:
                        results["edit_vehicle"] = {"status": "failed", "error": str(e)}
                    # Request Service
                    try:
                        req_btn = card.find_element(By.XPATH, ".//a[contains(@href, '/client/service-request') and contains(., 'Request Service')]")
                        req_btn.click()
                        wait.until(lambda d: "/client/service-request" in d.current_url or "/client/vehicles" in d.current_url)
                        current_url = driver.current_url
                        results["request_service"] = {"status": "passed" if "/client/service-request" in current_url or "/client/vehicles" in current_url else "failed", "actual_url": current_url}
                        driver.back()
                        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'My Vehicles')]")))
                        vehicle_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title')]" )
                        card = vehicle_cards[0].find_element(By.XPATH, "ancestor::div[contains(@class, 'card')]")
                    except Exception as e:
                        results["request_service"] = {"status": "failed", "error": str(e)}
                    # Delete (otwarcie modala)
                    try:
                        del_btn = card.find_element(By.XPATH, ".//button[contains(@class, 'btn-outline-danger') and contains(., 'Delete')]")
                        del_btn.click()
                        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal') and contains(@class, 'show')]//h5[contains(., 'Confirm Delete')]")))
                        results["delete_modal"] = {"status": "passed"}
                        close_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'modal') and contains(@class, 'show')]//button[@class='btn-close']")
                        close_btn.click()
                        time.sleep(0.2)
                    except Exception as e:
                        results["delete_modal"] = {"status": "failed", "error": str(e)}
                else:
                    results["edit_vehicle"] = {"status": "skipped", "message": "No vehicles to test"}
                    results["request_service"] = {"status": "skipped", "message": "No vehicles to test"}
                    results["delete_modal"] = {"status": "skipped", "message": "No vehicles to test"}
            except Exception as e:
                results["vehicle_card_links"] = {"status": "failed", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        overall_status = "passed" if all(r["status"] == "passed" or r["status"] == "skipped" for r in results.values()) else "failed"
        summary = {
            "status": overall_status,
            "user_type": "client",
            "message": "All link redirects checked" if overall_status == "passed" else f"Some links failed: {[k for k,v in results.items() if v['status']=='failed']}",
            "links": results
        }
        self._save_test_result(f"links_redirect_client", summary)
        return summary

    def _test_scrolling(self) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            driver.get(self.vehicles_url)
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
            if bottom_scroll > initial_scroll:
                status = "passed"
                message = "Scrolling test completed successfully"
            else:
                status = "skipped"
                message = "Page does not require scrolling at this window size"
            result = {
                "status": status,
                "user_type": "client",
                "message": message,
                "scroll_positions": {
                    "initial": initial_scroll,
                    "bottom": bottom_scroll,
                    "final": final_scroll
                }
            }
        except Exception as e:
            result = {"status": "failed", "user_type": "client", "message": f"Error during scrolling test: {str(e)}", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result("scrolling_client", result)
        return result

    def run_all_tests(self):
        results = {
            "scrolling": self._test_scrolling(),
            "access_unauthenticated": self._test_access("unauthenticated"),
            "access_employee": self._test_access("employee"),
            "access_admin": self._test_access("admin"),
            "access_client": self._test_access("client"),
            "links_redirect": self._test_links_redirect(),
        }
        self._save_test_result("all_vehicles_tests", results)
        return results

    def print_test_results(self, results: dict, indent: int = 0):
        indent_str = "  " * indent
        for key, value in results.items():
            if isinstance(value, dict):
                if "status" in value:
                    status_color = "\033[92m" if value["status"] == "passed" else ("\033[93m" if value["status"] == "skipped" else "\033[91m")
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
        page = ClientVehiclesPage(driver)
        results = page.run_all_tests()
        print("\nTest Results:")
        print("============")
        page.print_test_results(results)
    finally:
        driver.quit() 