"""
Contact page test class for testing the contact page at "/contact"
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

class ContactPage:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.test_results = {}
        self.config = self._load_config()
        self.base_url = f"{self.config['base_url']}:{self.config['port']}"
        self.contact_url = f"{self.base_url}/contact"
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
        # chrome_options.add_argument("--headless")  # jeśli chcesz tryb headless
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

    def _check_page_load(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "elements_found": {}}
            elements = [
                ("form", (By.TAG_NAME, "form")),
                ("name_field", (By.ID, "name")),
                ("email_field", (By.ID, "email")),
                ("message_field", (By.ID, "message")),
                ("submit_button", (By.CSS_SELECTOR, "form button[type='submit']")),
            ]
            for name, locator in elements:
                try:
                    wait.until(EC.presence_of_element_located(locator))
                    result["elements_found"][name] = {"status": "passed"}
                except Exception as e:
                    result["elements_found"][name] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
                    self._log_html_on_error(driver, f"contact_{name}")
            result["message"] = "Page loaded successfully with all essential elements" if result["status"] == "passed" else f"Some elements missing: {[k for k,v in result['elements_found'].items() if v['status']=='failed']}"
        except Exception as e:
            self._log_html_on_error(driver, "contact_page_load")
            result = {"status": "failed", "message": f"Unexpected error: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("page_load", result)
        return result

    def _check_element_visibility(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            elements_to_check = {
                "form": (By.TAG_NAME, "form"),
                "name_field": (By.ID, "name"),
                "email_field": (By.ID, "email"),
                "message_field": (By.ID, "message"),
                "submit_button": (By.CSS_SELECTOR, "form button[type='submit']")
            }
            visibility_results = {}
            status = "passed"
            for element_name, locator in elements_to_check.items():
                try:
                    element = wait.until(EC.presence_of_element_located(locator))
                    is_visible = element.is_displayed()
                    is_enabled = element.is_enabled()
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
                "message": "All elements visibility check completed" if status == "passed" else "Some elements not visible or not enabled",
                "elements": visibility_results
            }
        except Exception as e:
            result = {"status": "failed", "message": f"Error checking element visibility: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("element_visibility", result)
        return result

    def _test_scrolling(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
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
                "message": "Scrolling test completed successfully",
                "scroll_positions": {
                    "initial": initial_scroll,
                    "bottom": bottom_scroll,
                    "final": final_scroll
                }
            }
        except Exception as e:
            result = {"status": "failed", "message": f"Error during scrolling test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("scrolling", result)
        return result

    def _test_responsive_design(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        results = {}
        try:
            for width, height in self.screen_resolutions:
                driver.get(self.contact_url)
                time.sleep(0.1)
                driver.set_window_size(width, height)
                time.sleep(0.1)
                overlaps = []
                rows = driver.find_elements(By.CSS_SELECTOR, ".container .row")
                for row in rows:
                    cards = row.find_elements(By.CSS_SELECTOR, ".card")
                    visible_cards = [el for el in cards if el.is_displayed() and el.rect['width'] > 0 and el.rect['height'] > 0]
                    for i, elem1 in enumerate(visible_cards):
                        rect1 = elem1.rect
                        for elem2 in visible_cards[i+1:]:
                            rect2 = elem2.rect
                            # Tolerancja 2px na marginesy
                            if (
                                rect1['x'] < rect2['x'] + rect2['width'] - 2 and
                                rect1['x'] + rect1['width'] - 2 > rect2['x'] and
                                rect1['y'] < rect2['y'] + rect2['height'] - 2 and
                                rect1['y'] + rect1['height'] - 2 > rect2['y']
                            ):
                                overlaps.append((elem1.tag_name, elem2.tag_name, rect1, rect2))
                results[f"{width}x{height}"] = {
                    "status": "failed" if overlaps else "passed",
                    "overlapping_elements": overlaps,
                    "message": "No overlapping cards found" if not overlaps else f"Found {len(overlaps)} overlapping cards"
                }
            final_result = {
                "status": "passed" if all(r["status"] == "passed" for r in results.values()) else "failed",
                "message": "Responsive design test completed",
                "resolution_results": results
            }
        except Exception as e:
            final_result = {"status": "failed", "message": f"Error during responsive design test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("responsive_design", final_result)
        return final_result

    def _test_links(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            link_results = {}
            def get_links():
                return driver.find_elements(By.TAG_NAME, "a")
            links = get_links()
            for i in range(len(links)):
                links = get_links()
                if i >= len(links):
                    break
                link = links[i]
                href = link.get_attribute("href")
                text = link.text or link.get_attribute("id") or href
                if not href or href.strip() == "" or href.startswith("javascript:") or href.startswith("data:") or href.strip() == "#" or not (href.startswith("/") or href.startswith("http")):
                    continue
                try:
                    if not link.is_displayed() or not link.is_enabled():
                        link_results[text] = {
                            "status": "failed",
                            "message": "Link not visible or not enabled"
                        }
                        continue
                    target = link.get_attribute("target")
                    if target == "_blank":
                        driver.execute_script("window.open(arguments[0].href, '_blank');", link)
                        driver.switch_to.window(driver.window_handles[-1])
                        time.sleep(0.1)
                        current_url = driver.current_url
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    else:
                        link.click()
                        time.sleep(0.1)
                        current_url = driver.current_url
                    if current_url.startswith("data:"):
                        link_results[text] = {
                            "status": "failed",
                            "expected_url": href,
                            "actual_url": current_url,
                            "message": "Clicking this link resulted in navigation to data:, which is invalid"
                        }
                    else:
                        link_results[text] = {
                            "status": "passed" if (current_url == href or href in current_url) else "failed",
                            "expected_url": href,
                            "actual_url": current_url,
                            "message": "Link works correctly" if (current_url == href or href in current_url) else f"Link did not redirect as expected (expected: {href}, got: {current_url})"
                        }
                    driver.get(self.contact_url)
                    time.sleep(0.1)
                except Exception as e:
                    link_results[text] = {
                        "status": "failed",
                        "expected_url": href,
                        "message": "Link click failed",
                        "error": str(e)
                    }
                    self._log_html_on_error(driver, f"contact_link_{text}")
            result = {
                "status": "passed" if all(r["status"] == "passed" for r in link_results.values()) else "failed",
                "message": "Link testing completed" if all(r["status"] == "passed" for r in link_results.values()) else f"Some links failed: {[k for k,v in link_results.items() if v['status']=='failed']}",
                "links": link_results
            }
        except Exception as e:
            self._log_html_on_error(driver, "contact_links")
            result = {"status": "failed", "message": f"Error during link testing: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("links", result)
        return result

    def _test_field_constraints(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            fields_to_test = {
                "name": (By.ID, "name"),
                "email": (By.ID, "email"),
                "message": (By.ID, "message")
            }
            constraints_results = {}
            status = "passed"
            for field_name, locator in fields_to_test.items():
                try:
                    field = wait.until(EC.presence_of_element_located(locator))
                    min_length = field.get_attribute("minlength")
                    max_length = field.get_attribute("maxlength")
                    required = driver.execute_script("return arguments[0].required", field)
                    # Każde pole: fail jeśli którakolwiek z wartości jest False lub None
                    checks = [
                        min_length is not None and min_length != "" and int(min_length) > 0,
                        max_length is not None and max_length != "" and int(max_length) > 0,
                        required is True
                    ]
                    field_status = "passed" if all(checks) else "failed"
                    constraints_results[field_name] = {
                        "min_length": min_length,
                        "max_length": max_length,
                        "required": required,
                        "status": field_status,
                        "details": {
                            "minlength_present": min_length is not None and min_length != "",
                            "maxlength_present": max_length is not None and max_length != "",
                            "required_present": required is not None,
                            "minlength_value": min_length,
                            "maxlength_value": max_length,
                            "required_value": required
                        }
                    }
                    if field_status == "failed":
                        status = "failed"
                except Exception as e:
                    constraints_results[field_name] = {"status": "failed", "error": str(e)}
                    status = "failed"
                    self._log_html_on_error(driver, f"contact_field_constraints_{field_name}")
            result = {
                "status": status,
                "message": "Field constraints test completed" if status == "passed" else f"Some field constraints missing or invalid: {[k for k,v in constraints_results.items() if v['status']=='failed']}",
                "fields": constraints_results
            }
        except Exception as e:
            self._log_html_on_error(driver, "contact_field_constraints")
            result = {"status": "failed", "message": f"Error during field constraints test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("field_constraints", result)
        return result

    def _test_empty_fields(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            wait = WebDriverWait(driver, 5)
            name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            message_field = wait.until(EC.presence_of_element_located((By.ID, "message")))
            submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form button[type='submit']")))
            test_cases = [
                {"name": "", "email": "", "message": "", "case": "all_empty"},
                {"name": "Test User", "email": "", "message": "", "case": "email_empty"},
                {"name": "", "email": "test@email.com", "message": "", "case": "name_empty"},
                {"name": "Test User", "email": "test@email.com", "message": "", "case": "message_empty"},
                {"name": "Test User", "email": "test@email.com", "message": "short", "case": "message_too_short"},
            ]
            results = {}
            status = "passed"
            for test_case in test_cases:
                name_field.clear()
                email_field.clear()
                message_field.clear()
                name_field.send_keys(test_case["name"])
                email_field.send_keys(test_case["email"])
                message_field.send_keys(test_case["message"])
                submit_button.click()
                time.sleep(0.2)
                current_url = driver.current_url
                focused_id = driver.execute_script("return document.activeElement.id")
                # Dodatkowa weryfikacja: checkValidity dla każdego pola
                invalid_fields = []
                if not driver.execute_script("return arguments[0].checkValidity()", name_field):
                    invalid_fields.append("name")
                if not driver.execute_script("return arguments[0].checkValidity()", email_field):
                    invalid_fields.append("email")
                if not driver.execute_script("return arguments[0].checkValidity()", message_field):
                    invalid_fields.append("message")
                if "/contact" in current_url:
                    results[test_case["case"]] = {
                        "status": "passed",
                        "message": f"Form not submitted, still on /contact (validation works, focus on {focused_id})",
                        "allowed": False,
                        "focused_field": focused_id,
                        "invalid_fields": invalid_fields
                    }
                else:
                    results[test_case["case"]] = {
                        "status": "failed",
                        "message": f"Form was submitted despite invalid fields (redirected to {current_url})",
                        "allowed": True,
                        "invalid_fields": invalid_fields
                    }
                    status = "failed"
                # Odśwież stronę i pobierz elementy na nowo, by uniknąć stale element reference
                driver.get(self.contact_url)
                time.sleep(0.1)
                name_field = driver.find_element(By.ID, "name")
                email_field = driver.find_element(By.ID, "email")
                message_field = driver.find_element(By.ID, "message")
                submit_button = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            result = {
                "status": status,
                "message": "Empty fields test completed" if status == "passed" else f"Some empty field cases failed: {[k for k,v in results.items() if v['status']=='failed']}",
                "test_cases": results
            }
        except Exception as e:
            self._log_html_on_error(driver, "contact_empty_fields")
            result = {"status": "failed", "message": f"Error during empty fields test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("empty_fields", result)
        return result

    def _test_valid_send(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            wait = WebDriverWait(driver, 5)
            name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            message_field = wait.until(EC.presence_of_element_located((By.ID, "message")))
            submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form button[type='submit']")))
            name_field.clear()
            email_field.clear()
            message_field.clear()
            name_field.send_keys("Test User")
            email_field.send_keys("testuser@example.com")
            message_field.send_keys("This is a test message from Selenium.")
            submit_button.click()
            time.sleep(0.5)
            current_url = driver.current_url
            if current_url.rstrip("/").endswith("/"):
                # Sprawdź czy na stronie głównej pojawił się komunikat flash
                try:
                    alert = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-success') and contains(text(), 'Your message has been sent. We will contact you soon.')]")
                    result = {
                        "status": "passed",
                        "message": alert.text
                    }
                except NoSuchElementException:
                    result = {
                        "status": "failed",
                        "message": "Redirected to home but no success message shown."
                    }
            else:
                result = {
                    "status": "failed",
                    "message": f"Not redirected to home after valid send (current_url: {current_url})"
                }
        except Exception as e:
            self._log_html_on_error(driver, "contact_valid_send")
            result = {"status": "failed", "message": f"Error during valid send test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("valid_send", result)
        return result

    def _test_invalid_email_format(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.contact_url)
            wait = WebDriverWait(driver, 5)
            name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            message_field = wait.until(EC.presence_of_element_located((By.ID, "message")))
            submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form button[type='submit']")))
            name_field.clear()
            email_field.clear()
            message_field.clear()
            name_field.send_keys("Test User")
            email_field.send_keys("notanemail")
            message_field.send_keys("This is a test message from Selenium.")
            submit_button.click()
            time.sleep(0.2)
            current_url = driver.current_url
            if "/contact" in current_url:
                result = {
                    "status": "passed",
                    "message": "Form not submitted, still on /contact (invalid email format blocked)",
                    "allowed": False
                }
            else:
                result = {
                    "status": "failed",
                    "message": f"Form was submitted despite invalid email format (redirected to {current_url})",
                    "allowed": True
                }
        except Exception as e:
            self._log_html_on_error(driver, "contact_invalid_email_format")
            result = {"status": "failed", "message": f"Error during invalid email format test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("invalid_email_format", result)
        return result

    def _login_as(self, user_type: str, driver) -> None:
        """Loguje się jako podany user_type (client, employee, admin) na danym driverze."""
        login_url = f"{self.base_url}/auth/login"
        driver.get(login_url)
        wait = WebDriverWait(driver, 5)
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
        credentials = self.config["test_users"][user_type]
        username_field.clear()
        password_field.clear()
        username_field.send_keys(credentials["login"])
        password_field.send_keys(credentials["password"])
        submit_button.click()
        time.sleep(0.2)

    def _logout(self, driver) -> None:
        try:
            driver.get(f"{self.base_url}/auth/logout")
            time.sleep(0.2)
        except Exception:
            pass

    def _test_page_load_as_user(self, user_type: str) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            if user_type != "unauthenticated":
                self._login_as(user_type, driver)
            driver.get(self.contact_url)
            time.sleep(0.2)
            wait = WebDriverWait(driver, 5)
            # Sprawdź czy strona się ładuje i czy jest formularz kontaktowy
            try:
                form = wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
                # Dla klienta i niezalogowanego: passed, dla innych: failed
                if user_type in ["client", "unauthenticated"]:
                    result = {"status": "passed", "user_type": user_type, "message": "Contact page accessible."}
                else:
                    result = {"status": "failed", "user_type": user_type, "message": "Contact page should not be accessible for this user type."}
            except Exception as e:
                # Dla admina/employee: passed jeśli nie ma dostępu, dla innych: failed
                if user_type in ["admin", "employee"]:
                    result = {"status": "passed", "user_type": user_type, "message": "Contact page not accessible as expected."}
                else:
                    result = {"status": "failed", "user_type": user_type, "message": f"Contact page not accessible: {str(e)}"}
        finally:
            self._logout(driver)
            driver.quit()
        return result

    def test_page_load_by_user(self) -> Dict[str, Any]:
        results = {}
        for user_type in ["unauthenticated", "client", "employee", "admin"]:
            results[user_type] = self._test_page_load_as_user(user_type)
        self._save_test_result("page_load_by_user", results)
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        all_results = {
            "page_load": self._check_page_load(),
            "element_visibility": self._check_element_visibility(),
            "scrolling": self._test_scrolling(),
            "responsive_design": self._test_responsive_design(),
            "links": self._test_links(),
            "field_constraints": self._test_field_constraints(),
            "empty_fields": self._test_empty_fields(),
            "invalid_email_format": self._test_invalid_email_format(),
            "valid_send": self._test_valid_send(),
            "page_load_by_user": self.test_page_load_by_user()
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
        contact_page = ContactPage(driver)
        results = contact_page.run_all_tests()
        print("\nTest Results:")
        print("============")
        contact_page.print_test_results(results)
    finally:
        driver.quit() 