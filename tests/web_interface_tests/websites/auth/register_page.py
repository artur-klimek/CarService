"""
Register page test class for testing the registration page at "/auth/register"
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
import random
import string

class RegisterPage:
    def __init__(self, driver: webdriver.Chrome = None):
        self.driver = driver
        self.test_results = {}
        self.config = self._load_config()
        self.base_url = f"{self.config['base_url']}:{self.config['port']}"
        self.register_url = f"{self.base_url}/auth/register"
        self.login_url = f"{self.base_url}/auth/login"
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1280, 720), (768, 1024), (414, 896), (375, 667)
        ]

    def _load_config(self) -> Dict[str, Any]:
        with open('tests/web_interface_tests/tests_config.json', 'r') as f:
            return json.load(f)

    def _get_fresh_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
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

    def _check_page_load(self, user_type: str = "unauthenticated") -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            if driver.current_url != self.register_url:
                driver.get(self.register_url)
                time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            result = {"status": "passed", "user_type": user_type, "elements_found": {}}
            elements = [
                ("form", (By.TAG_NAME, "form")),
                ("username_field", (By.ID, "username")),
                ("email_field", (By.ID, "email")),
                ("password_field", (By.ID, "password")),
                ("password2_field", (By.ID, "password2")),
                ("submit_button", (By.ID, "submit")),
                ("login_link", (By.XPATH, "//a[@href='/auth/login']")),
            ]
            for name, locator in elements:
                try:
                    wait.until(EC.presence_of_element_located(locator))
                    result["elements_found"][name] = {"status": "passed"}
                except Exception as e:
                    result["elements_found"][name] = {"status": "failed", "error": str(e)}
                    result["status"] = "failed"
                    self._log_html_on_error(driver, f"{user_type}_{name}")
            result["message"] = "Page loaded successfully with all essential elements" if result["status"] == "passed" else f"Some elements missing: {[k for k,v in result['elements_found'].items() if v['status']=='failed']}"
        except Exception as e:
            self._log_html_on_error(driver, f"{user_type}_page_load")
            result = {"status": "failed", "user_type": user_type, "message": f"Unexpected error: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result(f"page_load_{user_type}", result)
        return result

    def _check_element_visibility(self, user_type: str = "unauthenticated") -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            if driver.current_url != self.register_url:
                driver.get(self.register_url)
                time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            elements_to_check = {
                "form": (By.TAG_NAME, "form"),
                "username_field": (By.ID, "username"),
                "email_field": (By.ID, "email"),
                "password_field": (By.ID, "password"),
                "password2_field": (By.ID, "password2"),
                "submit_button": (By.ID, "submit"),
                "login_link": (By.XPATH, "//a[@href='/auth/login']")
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
                "user_type": user_type,
                "message": "All elements visibility check completed" if status == "passed" else "Some elements not visible or not enabled",
                "elements": visibility_results
            }
        except Exception as e:
            result = {"status": "failed", "user_type": user_type, "message": f"Error checking element visibility: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result(f"element_visibility_{user_type}", result)
        return result

    def _test_scrolling(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            if driver.current_url != self.register_url:
                driver.get(self.register_url)
                time.sleep(0.1)
            
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
            allowed_tags = {"input", "textarea", "button", "label"}
            for width, height in self.screen_resolutions:
                driver.get(self.register_url)
                time.sleep(0.1)
                driver.set_window_size(width, height)
                time.sleep(0.1)
                elements = driver.find_elements(By.CSS_SELECTOR, "form input, form textarea, form button, form label")
                visible_elements = [el for el in elements if el.is_displayed() and el.rect['width'] > 0 and el.rect['height'] > 0]
                overlaps = []
                for i, elem1 in enumerate(visible_elements):
                    rect1 = elem1.rect
                    tag1 = elem1.tag_name
                    id1 = elem1.get_attribute("id")
                    for elem2 in visible_elements[i+1:]:
                        rect2 = elem2.rect
                        tag2 = elem2.tag_name
                        id2 = elem2.get_attribute("id")
                        if id1 and id2 and id1 == id2:
                            continue
                        if tag1 not in allowed_tags or tag2 not in allowed_tags:
                            continue
                        if (rect1['x'] < rect2['x'] + rect2['width'] and
                            rect1['x'] + rect1['width'] > rect2['x'] and
                            rect1['y'] < rect2['y'] + rect2['height'] and
                            rect1['y'] + rect1['height'] > rect2['y']):
                            if (tag1 == "label" and tag2 in {"input", "textarea"}) or (tag2 == "label" and tag1 in {"input", "textarea"}):
                                continue
                            overlaps.append((id1 or tag1, id2 or tag2))
                results[f"{width}x{height}"] = {
                    "status": "failed" if overlaps else "passed",
                    "overlapping_elements": overlaps,
                    "message": "No overlapping elements found" if not overlaps else f"Found {len(overlaps)} overlapping elements"
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
            driver.get(self.register_url)
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
                    driver.get(self.register_url)
                    time.sleep(0.1)
                except Exception as e:
                    link_results[text] = {
                        "status": "failed",
                        "expected_url": href,
                        "message": "Link click failed",
                        "error": str(e)
                    }
                    self._log_html_on_error(driver, f"link_{text}")
            result = {
                "status": "passed" if all(r["status"] == "passed" for r in link_results.values()) else "failed",
                "message": "Link testing completed" if all(r["status"] == "passed" for r in link_results.values()) else f"Some links failed: {[k for k,v in link_results.items() if v['status']=='failed']}",
                "links": link_results
            }
        except Exception as e:
            self._log_html_on_error(driver, "links")
            result = {"status": "failed", "message": f"Error during link testing: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("links", result)
        return result

    def _test_field_constraints(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            fields_to_test = {
                "username": (By.ID, "username"),
                "email": (By.ID, "email"),
                "password": (By.ID, "password"),
                "password2": (By.ID, "password2")
            }
            constraints_results = {}
            status = "passed"
            for field_name, locator in fields_to_test.items():
                try:
                    field = wait.until(EC.presence_of_element_located(locator))
                    min_length = field.get_attribute("minlength")
                    max_length = field.get_attribute("maxlength")
                    required = driver.execute_script("return arguments[0].required", field)
                    if field_name in ["password", "password2", "email"]:
                        field_status = "passed" if (min_length and max_length and required) else "failed"
                    else:
                        field_status = "passed" if required else "failed"
                    constraints_results[field_name] = {
                        "min_length": min_length,
                        "max_length": max_length,
                        "required": required,
                        "status": field_status,
                        "details": {
                            "minlength_present": min_length is not None,
                            "maxlength_present": max_length is not None,
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
                    self._log_html_on_error(driver, f"field_constraints_{field_name}")
            result = {
                "status": status,
                "message": "Field constraints test completed" if status == "passed" else f"Some field constraints missing or invalid: {[k for k,v in constraints_results.items() if v['status']=='failed']}",
                "fields": constraints_results
            }
        except Exception as e:
            self._log_html_on_error(driver, "field_constraints")
            result = {"status": "failed", "message": f"Error during field constraints test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("field_constraints", result)
        return result

    def _test_empty_fields_register(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password2_field = wait.until(EC.presence_of_element_located((By.ID, "password2")))
            submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
            test_cases = [
                {"username": "", "email": "", "password": "", "password2": "", "case": "all_empty"},
                {"username": "testuser", "email": "", "password": "", "password2": "", "case": "email_empty"},
                {"username": "", "email": "test@email.com", "password": "", "password2": "", "case": "username_empty"},
                {"username": "", "email": "", "password": "testpass123", "password2": "testpass123", "case": "username_email_empty"},
                {"username": "testuser", "email": "test@email.com", "password": "", "password2": "", "case": "passwords_empty"},
                {"username": "testuser", "email": "test@email.com", "password": "testpass123", "password2": "", "case": "password2_empty"},
                {"username": "testuser", "email": "test@email.com", "password": "", "password2": "testpass123", "case": "password_empty"},
            ]
            results = {}
            status = "passed"
            for test_case in test_cases:
                username_field.clear()
                email_field.clear()
                password_field.clear()
                password2_field.clear()
                username_field.send_keys(test_case["username"])
                email_field.send_keys(test_case["email"])
                password_field.send_keys(test_case["password"])
                password2_field.send_keys(test_case["password2"])
                submit_button.click()
                username_valid = driver.execute_script("return arguments[0].checkValidity()", username_field)
                email_valid = driver.execute_script("return arguments[0].checkValidity()", email_field)
                password_valid = driver.execute_script("return arguments[0].checkValidity()", password_field)
                password2_valid = driver.execute_script("return arguments[0].checkValidity()", password2_field)
                if not username_valid or not email_valid or not password_valid or not password2_valid:
                    results[test_case["case"]] = {
                        "status": "passed",
                        "message": "HTML5 required validation triggered",
                        "allowed": False
                    }
                else:
                    try:
                        error_message = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger, .alert-warning, .alert-info, .alert")))
                        results[test_case["case"]] = {
                            "status": "passed",
                            "message": error_message.text,
                            "allowed": False
                        }
                    except TimeoutException:
                        results[test_case["case"]] = {
                            "status": "failed",
                            "message": "No error message shown for empty fields",
                            "allowed": True
                        }
                        status = "failed"
            result = {
                "status": status,
                "message": "Empty fields register test completed" if status == "passed" else f"Some empty field cases failed: {[k for k,v in results.items() if v['status']=='failed']}",
                "test_cases": results
            }
        except Exception as e:
            self._log_html_on_error(driver, "empty_fields_register")
            result = {"status": "failed", "message": f"Error during empty fields register test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("empty_fields_register", result)
        return result

    def _test_passwords_match(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password2_field = wait.until(EC.presence_of_element_located((By.ID, "password2")))
            submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
            username_field.clear()
            email_field.clear()
            password_field.clear()
            password2_field.clear()
            username_field.send_keys("testuser123")
            email_field.send_keys("testuser123@email.com")
            password_field.send_keys("testpass123")
            password2_field.send_keys("differentpass")
            submit_button.click()
            time.sleep(0.1)
            password2_field = driver.find_element(By.ID, "password2")
            parent = password2_field.find_element(By.XPATH, "..")
            danger_divs = parent.find_elements(By.XPATH, "./div[contains(@class, 'text-danger')]")
            found_msg = None
            for div in danger_divs:
                if "passwords must match" in div.text.lower():
                    found_msg = div.text
                    break
            if found_msg:
                result = {
                    "status": "passed",
                    "message": found_msg,
                    "passwords_match": False
                }
            else:
                try:
                    error_message = driver.find_element(By.CSS_SELECTOR, ".alert-danger, .alert-warning, .alert-info, .alert, .text-danger")
                    if "passwords must match" in error_message.text.lower():
                        result = {
                            "status": "passed",
                            "message": error_message.text,
                            "passwords_match": False
                        }
                    else:
                        result = {
                            "status": "failed",
                            "message": "No 'Passwords must match' message found.",
                            "passwords_match": False
                        }
                except NoSuchElementException:
                    result = {
                        "status": "failed",
                        "message": "No error message shown for mismatched passwords",
                        "passwords_match": False
                    }
        except Exception as e:
            self._log_html_on_error(driver, "passwords_match")
            result = {"status": "failed", "message": f"Error during passwords match test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("passwords_match", result)
        return result

    def _test_existing_account(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password2_field = wait.until(EC.presence_of_element_located((By.ID, "password2")))
            submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
            existing = self.config["test_users"]["client"]
            username_field.clear()
            email_field.clear()
            password_field.clear()
            password2_field.clear()
            username_field.send_keys(existing["login"])
            email_field.send_keys("client@email.com")
            password_field.send_keys(existing["password"])
            password2_field.send_keys(existing["password"])
            submit_button.click()
            time.sleep(0.1)
            username_field = driver.find_element(By.ID, "username")
            email_field = driver.find_element(By.ID, "email")
            username_parent = username_field.find_element(By.XPATH, "..")
            email_parent = email_field.find_element(By.XPATH, "..")
            found_username = None
            found_email = None
            username_divs = username_parent.find_elements(By.XPATH, "./div[contains(@class, 'text-danger')]")
            for div in username_divs:
                if "please use a different username" in div.text.lower():
                    found_username = div.text
                    break
            email_divs = email_parent.find_elements(By.XPATH, "./div[contains(@class, 'text-danger')]")
            for div in email_divs:
                if "please use a different email address" in div.text.lower():
                    found_email = div.text
                    break
            if found_username or found_email:
                result = {
                    "status": "passed",
                    "message": f"{found_username or ''} {found_email or ''}".strip(),
                    "existing_account": True
                }
            else:
                try:
                    error_message = driver.find_element(By.CSS_SELECTOR, ".alert-danger, .alert-warning, .alert-info, .alert, .text-danger")
                    if ("please use a different username" in error_message.text.lower() or
                        "please use a different email address" in error_message.text.lower()):
                        result = {
                            "status": "passed",
                            "message": error_message.text,
                            "existing_account": True
                        }
                    else:
                        result = {
                            "status": "failed",
                            "message": "No 'Please use a different username/email' message found.",
                            "existing_account": True
                        }
                except NoSuchElementException:
                    result = {
                        "status": "failed",
                        "message": "No error message shown for existing account registration",
                        "existing_account": True
                    }
        except Exception as e:
            self._log_html_on_error(driver, "existing_account")
            result = {"status": "failed", "message": f"Error during existing account test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("existing_account", result)
        return result

    def _generate_random_credentials(self):
        """Generuje losowy login i email do testu rejestracji."""
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        login = f"testuser_{rand_str}"
        email = f"{login}@example.com"
        password = "TestPass123!"
        return login, email, password

    def _test_valid_registration(self) -> Dict[str, Any]:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.register_url)
            time.sleep(0.1)
            wait = WebDriverWait(driver, 5)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password2_field = wait.until(EC.presence_of_element_located((By.ID, "password2")))
            submit_button = wait.until(EC.presence_of_element_located((By.ID, "submit")))
            login, email, password = self._generate_random_credentials()
            username_field.clear()
            email_field.clear()
            password_field.clear()
            password2_field.clear()
            username_field.send_keys(login)
            email_field.send_keys(email)
            password_field.send_keys(password)
            password2_field.send_keys(password)
            submit_button.click()
            time.sleep(0.1)
            current_url = driver.current_url
            try:
                success_msg = None
                error_message = driver.find_element(By.CSS_SELECTOR, ".alert-danger, .alert-warning, .alert-info, .alert, .text-danger")
                if ("congratulations" in error_message.text.lower() or "registered" in error_message.text.lower()):
                    success_msg = error_message.text
                if success_msg:
                    result = {
                        "status": "passed",
                        "message": success_msg,
                        "login": login,
                        "email": email,
                        "redirect_url": current_url
                    }
                else:
                    result = {
                        "status": "failed",
                        "message": f"Unexpected error message after registration: {error_message.text}",
                        "login": login,
                        "email": email,
                        "current_url": current_url
                    }
            except NoSuchElementException:
                if not current_url.endswith("/auth/register"):
                    result = {
                        "status": "passed",
                        "message": f"Registration successful, redirected to {current_url}",
                        "login": login,
                        "email": email,
                        "redirect_url": current_url
                    }
                else:
                    result = {
                        "status": "failed",
                        "message": "No error message, but still on register page after submit.",
                        "login": login,
                        "email": email,
                        "current_url": current_url
                    }
        except Exception as e:
            self._log_html_on_error(driver, "valid_registration")
            result = {"status": "failed", "message": f"Error during valid registration test: {str(e)}", "error": str(e)}
        finally:
            driver.quit()
        self._save_test_result("valid_registration", result)
        return result

    def test_register_page_when_logged_in(self, user_type: str) -> dict:
        driver = self._get_fresh_driver()
        try:
            driver.get(self.login_url)
            time.sleep(0.1)
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
            time.sleep(0.1)
            driver.get(self.register_url)
            time.sleep(0.1)
            current_url = driver.current_url
            if not current_url.endswith("/auth/register"):
                return {
                    "status": "passed",
                    "message": f"User was redirected to {current_url} when trying to access /auth/register while logged in. This is correct behavior.",
                    "redirect_url": current_url
                }
            try:
                alert = driver.find_element(By.CSS_SELECTOR, ".alert, .alert-info, .alert-warning, .alert-danger")
                alert_text = alert.text.strip()
                if "zalogowany" in alert_text.lower() or "already logged" in alert_text.lower():
                    return {
                        "status": "passed",
                        "message": f"Proper message shown: {alert_text}"
                    }
            except Exception:
                pass
            return {
                "status": "failed",
                "message": "Register page is accessible while already logged in. No redirect or warning message was shown. This is a security/UX issue.",
                "current_url": current_url
            }
        except Exception as e:
            self._log_html_on_error(driver, f"register_page_when_logged_in_{user_type}")
            return {
                "status": "failed",
                "message": f"Error during test_register_page_when_logged_in: {str(e)}",
                "error": str(e)
            }
        finally:
            driver.quit()

    def test_as_unauthenticated(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("unauthenticated"),
            "element_visibility": self._check_element_visibility("unauthenticated"),
            "scrolling": self._test_scrolling(),
            "responsive_design": self._test_responsive_design(),
            "links": self._test_links(),
            "field_constraints": self._test_field_constraints(),
            "empty_fields": self._test_empty_fields_register(),
            "passwords_match": self._test_passwords_match(),
            "existing_account": self._test_existing_account(),
            "valid_registration": self._test_valid_registration()
        }
        self._save_test_result("unauthenticated_tests", results)
        return results

    def test_as_client(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("client"),
            "register_page_when_logged_in": self.test_register_page_when_logged_in("client")
        }
        self._save_test_result("client_tests", results)
        return results

    def test_as_employee(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("employee"),
            "register_page_when_logged_in": self.test_register_page_when_logged_in("employee")
        }
        self._save_test_result("employee_tests", results)
        return results

    def test_as_admin(self) -> Dict[str, Any]:
        results = {
            "page_load": self._check_page_load("admin"),
            "register_page_when_logged_in": self.test_register_page_when_logged_in("admin")
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
        register_page = RegisterPage(driver)
        import sys
        if len(sys.argv) > 1:
            test_type = sys.argv[1]
            if test_type == "unauthenticated":
                results = register_page.test_as_unauthenticated()
            elif test_type == "client":
                results = register_page.test_as_client()
            elif test_type == "employee":
                results = register_page.test_as_employee()
            elif test_type == "admin":
                results = register_page.test_as_admin()
            else:
                print(f"Unknown test type: {test_type}")
                print("Available test types: unauthenticated, client, employee, admin")
                sys.exit(1)
        else:
            results = register_page.run_all_tests()
        print("\nTest Results:")
        print("============")
        register_page.print_test_results(results)
    finally:
        driver.quit()
