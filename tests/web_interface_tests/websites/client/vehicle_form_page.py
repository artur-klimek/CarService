"""
Client vehicle form page test class for testing vehicle add/edit at:
- /client/vehicles/add
- /client/vehicles/<id>/edit
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class ClientVehicleFormPage:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.test_results = {}
        self.config = self._load_config()
        self.base_url = f"{self.config['base_url']}:{self.config['port']}"
        self.vehicles_url = f"{self.base_url}/client/vehicles"
        self.add_url = f"{self.base_url}/client/vehicles/add"

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

    def _get_first_vehicle_id(self, driver):
        driver.get(self.vehicles_url)
        time.sleep(0.2)
        try:
            vehicle_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title')]")
            if vehicle_cards:
                card = vehicle_cards[0].find_element(By.XPATH, "ancestor::div[contains(@class, 'card')]")
                edit_btn = card.find_element(By.XPATH, ".//a[contains(@href, '/client/vehicles/') and contains(@href, '/edit') and contains(., 'Edit')]")
                href = edit_btn.get_attribute("href")
                # Extract vehicle id from href
                import re
                m = re.search(r"/client/vehicles/(\d+)/edit", href)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    def _get_first_vehicle_data(self, driver):
        driver.get(self.vehicles_url)
        time.sleep(0.2)
        try:
            # Znajdź pierwszy pojazd na liście i pobierz VIN oraz license_plate
            vin = None
            license_plate = None
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'card-body')]")
            for card in cards:
                try:
                    vin_el = card.find_element(By.XPATH, ".//div[contains(@class, 'card-text') and contains(., 'VIN:')]")
                    vin = vin_el.text.split('VIN:')[-1].strip()
                except Exception:
                    pass
                try:
                    lp_el = card.find_element(By.XPATH, ".//div[contains(@class, 'card-text') and contains(., 'License Plate:')]")
                    license_plate = lp_el.text.split('License Plate:')[-1].strip()
                except Exception:
                    pass
                if vin and license_plate:
                    return {"vin": vin, "license_plate": license_plate}
            return None
        except Exception:
            return None

    def _generate_valid_vin(self):
        import random
        allowed = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789'
        return ''.join(random.choices(allowed, k=17))

    def _test_access(self, user_type: str, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "user_type": user_type, "mode": mode, "message": ""}
            if user_type == "client":
                try:
                    form = wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
                    result["form"] = {"status": "passed"}
                except Exception as e:
                    result["form"] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
            else:
                current_url = driver.current_url
                if "/auth/login" in current_url or "/login" in current_url or current_url.rstrip("/").endswith(self.base_url):
                    result["access"] = {"status": "passed", "message": f"Redirected to login or home: {current_url}"}
                elif user_type in ["employee", "admin"] and ("/dashboard" in current_url or "/admin" in current_url or "/employee" in current_url):
                    result["access"] = {"status": "passed", "message": f"Redirected to dashboard: {current_url}"}
                else:
                    try:
                        alert = driver.find_element(By.XPATH, "//*[contains(., 'not authorized') or contains(., 'access denied') or contains(., 'permission denied') or contains(., 'zaloguj') or contains(., 'nie masz dostępu')]")
                        result["access"] = {"status": "passed", "message": "Access denied message present"}
                    except Exception:
                        result["access"] = {"status": "failed", "message": f"Unexpected access: {current_url}"}
                        result["status"] = "failed"
            result["final_url"] = driver.current_url
        except Exception as e:
            self._log_html_on_error(driver, f"vehicle_form_access_{user_type}_{mode}")
            result = {"status": "failed", "user_type": user_type, "mode": mode, "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"access_{user_type}_{mode}", result)
        return result

    def _test_form_fields(self, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "mode": mode, "message": ""}
            # Check form fields
            fields = [
                ("make", By.NAME, "make"),
                ("model", By.NAME, "model"),
                ("year", By.NAME, "year"),
                ("license_plate", By.NAME, "license_plate"),
                ("vin", By.NAME, "vin"),
            ]
            for fname, by, locator in fields:
                try:
                    field = wait.until(EC.presence_of_element_located((by, locator)))
                    result[fname] = {"status": "passed"}
                except Exception as e:
                    result[fname] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
            # Submit button
            try:
                submit_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='submit' and @id='submit']")))
                result["submit_btn"] = {"status": "passed"}
            except Exception as e:
                result["submit_btn"] = {"status": "failed", "error": str(e)}
                result["status"] = "failed"
            # Cancel button
            try:
                cancel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'btn-secondary') and contains(., 'Cancel')]")))
                result["cancel_btn"] = {"status": "passed"}
            except Exception as e:
                result["cancel_btn"] = {"status": "failed", "error": str(e)}
                result["status"] = "failed"
            # Title
            try:
                title = wait.until(EC.presence_of_element_located((By.XPATH, "//h2")))
                result["title"] = {"status": "passed", "text": title.text}
            except Exception as e:
                result["title"] = {"status": "failed", "error": str(e)}
                result["status"] = "failed"
        except Exception as e:
            self._log_html_on_error(driver, f"vehicle_form_fields_{mode}")
            result = {"status": "failed", "mode": mode, "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"form_fields_{mode}", result)
        return result

    def _test_add_vehicle(self) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            driver.get(self.add_url)
            wait = WebDriverWait(driver, 5)
            # Fill form with valid data
            test_data = {
                "make": "TestMake",
                "model": "TestModel",
                "year": "2022",
                "license_plate": f"TEST{int(time.time())%10000}",
                "vin": self._generate_valid_vin()
            }
            for fname, value in test_data.items():
                field = wait.until(EC.presence_of_element_located((By.NAME, fname)))
                field.clear()
                field.send_keys(value)
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @id='submit']")))
            submit_btn.click()
            wait.until(EC.url_contains("/client/vehicles"))
            time.sleep(0.2)
            # Check for success alert
            try:
                alert = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-success') and contains(., 'Vehicle has been added successfully.')]")
                alert_present = alert.is_displayed()
            except Exception:
                alert_present = False
            # Check if vehicle appears in list
            try:
                vehicle_cards = driver.find_elements(By.XPATH, f"//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title') and contains(., '{test_data['make']}') and contains(., '{test_data['model']}')]")
                vehicle_found = bool(vehicle_cards)
            except Exception:
                vehicle_found = False
            result = {
                "status": "passed" if alert_present and vehicle_found else "failed",
                "mode": "add",
                "alert_present": alert_present,
                "vehicle_found": vehicle_found,
                "test_data": test_data
            }
            # If failed, collect form errors and alerts
            if result["status"] == "failed":
                # Collect form errors (text-danger)
                try:
                    errors = driver.find_elements(By.XPATH, "//div[contains(@class, 'text-danger')]")
                    result["form_errors"] = [e.text for e in errors if e.text.strip()]
                except Exception:
                    result["form_errors"] = []
                # Collect all alerts (Bootstrap)
                try:
                    alerts = driver.find_elements(By.XPATH, "//div[contains(@class, 'alert')]")
                    result["alerts"] = [a.text for a in alerts if a.text.strip()]
                except Exception:
                    result["alerts"] = []
        except Exception as e:
            self._log_html_on_error(driver, "vehicle_form_add")
            result = {"status": "failed", "mode": "add", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result("add_vehicle", result)
        return result

    def _test_edit_vehicle(self) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            # Find a vehicle to edit, or add one if none exists
            vehicle_id = self._get_first_vehicle_id(driver)
            if not vehicle_id:
                # Add a vehicle first
                self._logout(driver)
                driver.quit()
                self._test_add_vehicle()
                driver = self._get_fresh_driver()
                self._login_as("client", driver)
                vehicle_id = self._get_first_vehicle_id(driver)
                if not vehicle_id:
                    raise Exception("Could not find or create a vehicle to edit.")
            edit_url = f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(edit_url)
            wait = WebDriverWait(driver, 5)
            # Change model field
            model_field = wait.until(EC.presence_of_element_located((By.NAME, "model")))
            new_model = f"EditedModel{int(time.time())%1000}"
            model_field.clear()
            model_field.send_keys(new_model)
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @id='submit']")))
            submit_btn.click()
            wait.until(EC.url_contains("/client/vehicles"))
            time.sleep(0.2)
            # Check for success alert
            try:
                alert = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-success') and contains(., 'Vehicle has been updated successfully.')]")
                alert_present = alert.is_displayed()
            except Exception:
                alert_present = False
            # Check if vehicle appears in list with new model
            try:
                vehicle_cards = driver.find_elements(By.XPATH, f"//div[contains(@class, 'card-body')]/h5[contains(@class, 'card-title') and contains(., '{new_model}')]")
                vehicle_found = bool(vehicle_cards)
            except Exception:
                vehicle_found = False
            result = {
                "status": "passed" if alert_present and vehicle_found else "failed",
                "mode": "edit",
                "alert_present": alert_present,
                "vehicle_found": vehicle_found,
                "vehicle_id": vehicle_id,
                "new_model": new_model
            }
        except Exception as e:
            self._log_html_on_error(driver, "vehicle_form_edit")
            result = {"status": "failed", "mode": "edit", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result("edit_vehicle", result)
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

    def _test_links_redirect(self, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        results = {}
        try:
            self._login_as("client", driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
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
                    # Po kliknięciu logout lub inny link wróć na form
                    if name != "navbar_logout":
                        driver.get(url)
                        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
                        time.sleep(0.2)
                    else:
                        self._login_as("client", driver)
                        driver.get(url)
                        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
                        time.sleep(0.2)
                except Exception as e:
                    results[name] = {"status": "failed", "error": str(e)}
            # --- Cancel button ---
            try:
                cancel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-secondary') and contains(., 'Cancel')]")))
                cancel_btn.click()
                wait.until(EC.url_contains("/client/vehicles"))
                current_url = driver.current_url
                results["cancel_btn"] = {"status": "passed" if "/client/vehicles" in current_url else "failed", "actual_url": current_url}
                # wróć na form
                driver.get(url)
                wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            except Exception as e:
                results["cancel_btn"] = {"status": "failed", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        overall_status = "passed" if all(r["status"] == "passed" for r in results.values()) else "failed"
        summary = {
            "status": overall_status,
            "mode": mode,
            "message": "All link redirects checked" if overall_status == "passed" else f"Some links failed: {[k for k,v in results.items() if v['status']=='failed']}",
            "links": results
        }
        self._save_test_result(f"links_redirect_{mode}", summary)
        return summary

    def _test_scrolling(self, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
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
                "mode": mode,
                "message": message,
                "scroll_positions": {
                    "initial": initial_scroll,
                    "bottom": bottom_scroll,
                    "final": final_scroll
                }
            }
        except Exception as e:
            result = {"status": "failed", "mode": mode, "message": f"Error during scrolling test: {str(e)}", "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"scrolling_{mode}", result)
        return result

    def _test_field_constraints(self, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
            wait = WebDriverWait(driver, 5)
            fields = {
                "make": (By.ID, "make"),
                "model": (By.ID, "model"),
                "year": (By.ID, "year"),
                "license_plate": (By.ID, "license_plate"),
                "vin": (By.ID, "vin"),
            }
            constraints_results = {}
            status = "passed"
            for fname, locator in fields.items():
                try:
                    field = wait.until(EC.presence_of_element_located(locator))
                    min_length = field.get_attribute("minlength")
                    max_length = field.get_attribute("maxlength")
                    required = driver.execute_script("return arguments[0].required", field)
                    field_type = field.get_attribute("type")
                    min_val = field.get_attribute("min")
                    max_val = field.get_attribute("max")
                    checks = []
                    details = {
                        "minlength_present": min_length is not None and min_length != "",
                        "maxlength_present": max_length is not None and max_length != "",
                        "required_present": required is not None,
                        "minlength_value": min_length,
                        "maxlength_value": max_length,
                        "required_value": required,
                        "type_value": field_type,
                        "min_value": min_val,
                        "max_value": max_val
                    }
                    if fname in ["make", "model"]:
                        checks = [
                            min_length is not None and int(min_length) == 2,
                            max_length is not None and int(max_length) == 50,
                            required is True,
                            field_type == "text"
                        ]
                    elif fname == "year":
                        checks = [
                            min_val is not None and int(min_val) == 1900,
                            max_val is not None and int(max_val) >= 2024,
                            required is True,
                            field_type == "number"
                        ]
                    elif fname == "license_plate":
                        checks = [
                            min_length is not None and int(min_length) == 2,
                            max_length is not None and int(max_length) == 20,
                            required is True,
                            field_type == "text"
                        ]
                    elif fname == "vin":
                        checks = [
                            min_length is not None and int(min_length) == 17,
                            max_length is not None and int(max_length) == 17,
                            required is True,
                            field_type == "text"
                        ]
                    field_status = "passed" if all(checks) else "failed"
                    constraints_results[fname] = {
                        "min_length": min_length,
                        "max_length": max_length,
                        "required": required,
                        "type": field_type,
                        "min": min_val,
                        "max": max_val,
                        "status": field_status,
                        "details": details
                    }
                    if field_status == "failed":
                        status = "failed"
                except Exception as e:
                    constraints_results[fname] = {"status": "failed", "error": str(e)}
                    status = "failed"
            result = {
                "status": status,
                "mode": mode,
                "message": "Field constraints test completed" if status == "passed" else f"Some field constraints missing or invalid: {[k for k,v in constraints_results.items() if v['status']=='failed']}",
                "fields": constraints_results
            }
        except Exception as e:
            self._log_html_on_error(driver, f"vehicle_field_constraints_{mode}")
            result = {"status": "failed", "mode": mode, "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"field_constraints_{mode}", result)
        return result

    def _test_html5_validation(self, mode: str = "add", vehicle_id: str = None) -> dict:
        driver = self._get_fresh_driver()
        try:
            self._login_as("client", driver)
            url = self.add_url if mode == "add" else f"{self.base_url}/client/vehicles/{vehicle_id}/edit"
            driver.get(url)
            wait = WebDriverWait(driver, 5)
            # Pobierz wszystkie pola
            fields = {
                "make": driver.find_element(By.ID, "make"),
                "model": driver.find_element(By.ID, "model"),
                "year": driver.find_element(By.ID, "year"),
                "license_plate": driver.find_element(By.ID, "license_plate"),
                "vin": driver.find_element(By.ID, "vin"),
            }
            submit_btn = driver.find_element(By.ID, "submit")
            # Pobierz dane istniejącego pojazdu do testu duplikatu
            existing_vehicle = self._get_first_vehicle_data(driver)
            if existing_vehicle:
                dupe_vin = existing_vehicle["vin"]
                dupe_lp = existing_vehicle["license_plate"]
            else:
                # Dodaj poprawny pojazd, jeśli nie ma żadnego
                valid_data = {
                    "make": "TestMake",
                    "model": "TestModel",
                    "year": "2022",
                    "license_plate": f"TEST{int(time.time())%10000}",
                    "vin": self._generate_valid_vin()
                }
                driver.get(self.add_url)
                wait = WebDriverWait(driver, 5)
                for fname, value in valid_data.items():
                    field = wait.until(EC.presence_of_element_located((By.ID, fname)))
                    field.clear()
                    field.send_keys(value)
                submit_btn = wait.until(EC.presence_of_element_located((By.ID, "submit")))
                submit_btn.click()
                wait.until(EC.url_contains("/client/vehicles"))
                dupe_vin = valid_data["vin"]
                dupe_lp = valid_data["license_plate"]
            # wróć na form
            driver.get(url)
            wait = WebDriverWait(driver, 5)
            fields = {
                "make": driver.find_element(By.ID, "make"),
                "model": driver.find_element(By.ID, "model"),
                "year": driver.find_element(By.ID, "year"),
                "license_plate": driver.find_element(By.ID, "license_plate"),
                "vin": driver.find_element(By.ID, "vin"),
            }
            submit_btn = driver.find_element(By.ID, "submit")
            # Testy walidacji HTML5 i duplikatów
            test_cases = [
                ("make", "", "empty", True),
                ("make", "A", "too_short", True),
                ("make", "A"*51, "too_long", True),
                ("model", "", "empty", True),
                ("model", "A", "too_short", True),
                ("model", "A"*51, "too_long", True),
                ("year", "", "empty", True),
                ("year", "1799", "too_small", True),
                ("year", str(int(time.strftime('%Y'))+2), "too_big", True),
                ("license_plate", "", "empty", True),
                ("license_plate", "A", "too_short", True),
                ("license_plate", "A"*21, "too_long", True),
                ("vin", "", "empty", True),
                ("vin", "A"*16, "too_short", True),
                ("vin", "A"*18, "too_long", True),
                ("vin", "INVALID!@#VIN12345", "bad_format", True),
                ("vin", dupe_vin, "duplicate_vin", True),
                ("license_plate", dupe_lp, "duplicate_license_plate", True),
            ]
            results = {}
            dupe_error = None
            if not dupe_vin or not dupe_lp:
                dupe_error = "Nie znaleziono VIN/lic_plate do testu duplikatu. Pozostałe przypadki przetestowane."
            for fname, value, desc, should_block in test_cases:
                if desc in ["duplicate_vin", "duplicate_license_plate"] and dupe_error:
                    results[f"{fname}_{desc}"] = {
                        "status": "skipped",
                        "desc": desc,
                        "error": dupe_error
                    }
                    continue
                # Sprawdzenie 'too_long' dla pól z maxlength
                is_too_long_case = desc == "too_long"
                maxlength = None
                if is_too_long_case:
                    try:
                        maxlength = int(fields[fname].get_attribute("maxlength") or 0)
                    except Exception:
                        maxlength = 0
                for f2, field in fields.items():
                    field.clear()
                    driver.execute_script("arguments[0].value = '';", field)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", field)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", field)
                    if f2 == fname:
                        field.send_keys(value)
                    else:
                        if desc == "duplicate_license_plate" and f2 == "license_plate":
                            field.send_keys(dupe_lp)
                        elif desc == "duplicate_vin" and f2 == "vin":
                            field.send_keys(dupe_vin)
                        else:
                            if f2 == "make":
                                field.send_keys("EditMake2")
                            elif f2 == "model":
                                field.send_keys("EditModel2")
                            elif f2 == "year":
                                field.send_keys("2022")
                            elif f2 == "license_plate":
                                field.send_keys(f"EDIT{int(time.time())%10000+1}")
                            elif f2 == "vin":
                                field.send_keys(f"EDITVIN{int(time.time())%100000+1:07d}BB")
                # Dla too_long: sprawdź ile znaków faktycznie zostało wpisanych
                if is_too_long_case and maxlength:
                    actual_value = fields[fname].get_attribute("value")
                    if len(actual_value) == maxlength and len(value) > maxlength:
                        results[f"{fname}_{desc}"] = {
                            "status": "skipped",
                            "desc": desc,
                            "message": f"Pole nie pozwala wpisać więcej niż {maxlength} znaków, wpisana wartość została obcięta do {maxlength} znaków.",
                            "input_value": value,
                            "actual_value": actual_value
                        }
                        continue
                    elif len(actual_value) > maxlength:
                        results[f"{fname}_{desc}"] = {
                            "status": "failed",
                            "desc": desc,
                            "message": f"Pole przyjęło więcej znaków ({len(actual_value)}) niż maxlength={maxlength}.",
                            "input_value": value,
                            "actual_value": actual_value
                        }
                        continue
                submit_btn.click()
                time.sleep(0.2)
                current_url = driver.current_url
                # Po kliknięciu submit i odświeżeniu strony, pobierz na nowo wszystkie pola i submit_btn
                driver.get(url)
                time.sleep(0.1)
                wait = WebDriverWait(driver, 5)
                fields = {
                    "make": driver.find_element(By.ID, "make"),
                    "model": driver.find_element(By.ID, "model"),
                    "year": driver.find_element(By.ID, "year"),
                    "license_plate": driver.find_element(By.ID, "license_plate"),
                    "vin": driver.find_element(By.ID, "vin"),
                }
                submit_btn = driver.find_element(By.ID, "submit")
                focused_id = driver.execute_script("return document.activeElement.id")
                is_invalid = not driver.execute_script("return arguments[0].checkValidity()", fields[fname])
                blocked = (url in current_url) or (current_url == url) or ("/add" in current_url) or ("/edit" in current_url)
                error_message = None
                error_messages = []
                html_fragment = None
                if desc in ["duplicate_vin", "duplicate_license_plate"]:
                    try:
                        # Szukaj komunikatu bezpośrednio pod polem VIN/lic_plate
                        if desc == "duplicate_vin":
                            vin_input = driver.find_element(By.ID, "vin")
                            vin_parent = vin_input.find_element(By.XPATH, "..")
                            vin_errors = vin_parent.find_elements(By.XPATH, ".//div[contains(@class, 'text-danger')]")
                            for div in vin_errors:
                                txt = div.text.strip()
                                error_messages.append(f"VIN field: {txt}")
                                if "VIN is already registered" in txt:
                                    error_message = txt
                            html_fragment = vin_parent.get_attribute("outerHTML")
                        if desc == "duplicate_license_plate":
                            lp_input = driver.find_element(By.ID, "license_plate")
                            lp_parent = lp_input.find_element(By.XPATH, "..")
                            lp_errors = lp_parent.find_elements(By.XPATH, ".//div[contains(@class, 'text-danger')]")
                            for div in lp_errors:
                                txt = div.text.strip()
                                error_messages.append(f"LP field: {txt}")
                                if "license plate is already registered" in txt:
                                    error_message = txt
                            html_fragment = lp_parent.get_attribute("outerHTML")
                    except Exception:
                        pass
                if desc in ["duplicate_vin", "duplicate_license_plate"]:
                    # Uznaj za passed, jeśli system zablokował przejście dalej (pozostał na stronie formularza)
                    status = "passed" if blocked else "failed"
                elif desc == "too_long" and fname == "vin":
                    # VIN za długi: sprawdź, czy system blokuje przejście dalej (nie przechodzi do listy pojazdów)
                    status = "passed" if blocked else "failed"
                else:
                    status = "passed" if (should_block == blocked and is_invalid == should_block) else "failed"
                results[f"{fname}_{desc}"] = {
                    "status": status,
                    "desc": desc,
                    "should_block": should_block,
                    "blocked": blocked,
                    "is_invalid": is_invalid,
                    "focused_field": focused_id,
                    "current_url": current_url,
                    "error_message": error_message,
                    "all_error_messages": error_messages,
                    "html_fragment": html_fragment
                }
            result = {
                "status": "passed" if all(r["status"] in ["passed", "skipped"] for r in results.values()) else "failed",
                "mode": mode,
                "message": "HTML5 validation test completed" if all(r["status"] in ["passed", "skipped"] for r in results.values()) else f"Some validation cases failed: {[k for k,v in results.items() if v['status']=='failed']}",
                "test_cases": results
            }
        except Exception as e:
            self._log_html_on_error(driver, f"vehicle_html5_validation_{mode}")
            result = {"status": "failed", "mode": mode, "error": str(e)}
        finally:
            self._logout(driver)
            driver.quit()
        self._save_test_result(f"html5_validation_{mode}", result)
        return result

    def run_all_tests(self):
        # Find a vehicle id for edit tests (if possible)
        driver = self._get_fresh_driver()
        self._login_as("client", driver)
        vehicle_id = self._get_first_vehicle_id(driver)
        self._logout(driver)
        driver.quit()
        results = {
            "access_add": self._test_access("client", "add"),
            "access_edit": self._test_access("client", "edit", vehicle_id),
            "access_unauthenticated_add": self._test_access("unauthenticated", "add"),
            "access_unauthenticated_edit": self._test_access("unauthenticated", "edit", vehicle_id),
            "access_employee_add": self._test_access("employee", "add"),
            "access_employee_edit": self._test_access("employee", "edit", vehicle_id),
            "access_admin_add": self._test_access("admin", "add"),
            "access_admin_edit": self._test_access("admin", "edit", vehicle_id),
            "form_fields_add": self._test_form_fields("add"),
            "form_fields_edit": self._test_form_fields("edit", vehicle_id),
            "add_vehicle": self._test_add_vehicle(),
            "edit_vehicle": self._test_edit_vehicle(),
            "links_redirect_add": self._test_links_redirect("add"),
            "links_redirect_edit": self._test_links_redirect("edit", vehicle_id),
            "scrolling_add": self._test_scrolling("add"),
            "scrolling_edit": self._test_scrolling("edit", vehicle_id),
            "field_constraints_add": self._test_field_constraints("add"),
            "field_constraints_edit": self._test_field_constraints("edit", vehicle_id),
            "validation_add": self._test_html5_validation("add"),
            # "validation_edit": self._test_html5_validation("edit", vehicle_id),
        }
        self._save_test_result("all_vehicle_form_tests", results)
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
        page = ClientVehicleFormPage(driver)
        results = page.run_all_tests()
        print("\nTest Results:")
        print("============")
        page.print_test_results(results)
    finally:
        driver.quit() 