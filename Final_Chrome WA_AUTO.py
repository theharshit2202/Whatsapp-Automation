"""
WhatsApp Automation Script
This script automates sending messages to contacts via WhatsApp Web using Selenium.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, Set, Dict, Any, Union
from dataclasses import dataclass
import tempfile
import shutil

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    WebDriverException,
    SessionNotCreatedException,
)

def get_resource_path(relative_path: str = "") -> Path:
    """Get the absolute path to a resource file, accounting for frozen(executable) vs. non-frozen (script) environments.
    """
    base_path = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    return base_path / relative_path if relative_path else base_path

# Ensure log file exists before configuring logging
log_file_path = get_resource_path('whatsapp_automation.log')
if not log_file_path.exists():
    log_file_path.touch()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

@dataclass
class Config:
    """Configuration settings for the WhatsApp automation."""
    def __init__(self):
        # Get user's home directory for Chrome profile
        self.user_home = os.path.expanduser("~")
        self.USER_PROFILE_PATH: str = os.path.join(self.user_home, "AppData", "Local", "Google", "Chrome", "User Data")
        
        # Set up paths for driver and contacts file using resource path
        self.CHROME_DRIVER_PATH: str = str(get_resource_path("chromedriver.exe"))
        self.CONTACTS_FILE_PATH: str = str(get_resource_path("contacts.xlsx"))
        
        # Other settings
        self.WAIT_TIMEOUT: int = 50
        self.LOGIN_TIMEOUT: int = 600
        self.MAX_RETRIES: int = 5
        self.RETRY_DELAY: int = 2

    def __post_init__(self):
        """Validate paths after initialization."""
        if not os.path.exists(self.CHROME_DRIVER_PATH):
            logging.warning(f"Chrome driver not found at: {self.CHROME_DRIVER_PATH}. WhatsApp automation will be disabled.")
        
        if not os.path.exists(self.USER_PROFILE_PATH):
            logging.warning(f"Chrome user profile not found at: {self.USER_PROFILE_PATH}. WhatsApp automation will be disabled.")
        
        if not os.path.exists(self.CONTACTS_FILE_PATH):
            raise FileNotFoundError(f"Contacts file not found at: {self.CONTACTS_FILE_PATH}")

class ProcessManager:
    """Manages browser and driver processes."""
    
    @staticmethod
    def kill_chrome_processes() -> None:
        """Kill all running Chrome and ChromeDriver processes."""
        try:
            subprocess.run('taskkill /F /IM chrome.exe', check=False, shell=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run('taskkill /F /IM chromedriver.exe', check=False, shell=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("Closed all running Chrome and ChromeDriver processes.")
        except Exception as e:
            logging.warning(f"Could not kill Chrome processes: {e}")

class WhatsAppDriver:
    """Manages the WhatsApp Web driver instance."""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    def create_driver(self) -> webdriver.Chrome:
        """Create and configure the Chrome WebDriver instance using existing user profile."""
        ProcessManager.kill_chrome_processes()
        options = Options()
        
        # Configure Chrome options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--log-level=3")
        
        # Use existing Chrome user profile with proper configuration
        user_data_dir = os.path.join(self.config.USER_PROFILE_PATH, "WhatsApp")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--profile-directory=Default")
        
        try:
            if os.path.exists(self.config.CHROME_DRIVER_PATH):
                service = Service(executable_path=self.config.CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
                
            self.wait = WebDriverWait(self.driver, self.config.WAIT_TIMEOUT)
            return self.driver
        except Exception as e:
            logging.error(f"Failed to create Chrome driver: {str(e)}")
            raise

    def initialize_whatsapp(self) -> bool:
        """Initialize WhatsApp Web and wait for it to be ready."""
            
        try:
            self.driver.get("https://web.whatsapp.com/")
            WebDriverWait(self.driver, self.config.LOGIN_TIMEOUT).until(
                EC.presence_of_element_located(
                    # (By.XPATH, "//p[contains(@class, 'selectable-text')][1]")
                    (By.CSS_SELECTOR, "button[aria-label*='New chat']")
                )
                # <button aria-expanded="false" aria-disabled="false" role="button" tabindex="0" class="x78zum5 x6s0dn4 x1afcbsf x1heor9g x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x1y1aw1k x1sxyh0 xwib8y2 xurb0ha xtnn1bt x9v5kkp xmw7ebm xrdum7p" data-tab="2" 
                # title="New chat" aria-label="New chat"><span aria-hidden="true" data-icon="new-chat-outline" class=""><svg viewBox="0 0 24 24" height="24" width="24" preserveAspectRatio="xMidYMid meet" class="" fill="none"><title>new-chat-outline</title><path d="M9.53277 12.9911H11.5086V14.9671C11.5086 15.3999 11.7634 15.8175 12.1762 15.9488C12.8608 16.1661 13.4909 15.6613 13.4909 15.009V12.9911H15.4672C15.9005 12.9911 16.3181 12.7358 16.449 12.3226C16.6659 11.6381 16.1606 11.0089 15.5086 11.0089H13.4909V9.03332C13.4909 8.60007 13.2361 8.18252 12.8233 8.05119C12.1391 7.83391 11.5086 8.33872 11.5086 8.991V11.0089H9.49088C8.83941 11.0089 8.33411 11.6381 8.55097 12.3226C8.68144 12.7358 9.09947 12.9911 9.53277 12.9911Z" fill="currentColor" data-darkreader-inline-fill="" style="--darkreader-inline-fill: currentColor;"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M0.944298 5.52617L2.99998 8.84848V17.3333C2.99998 18.8061 4.19389 20 5.66665 20H19.3333C20.8061 20 22 18.8061 22 17.3333V6.66667C22 5.19391 20.8061 4 19.3333 4H1.79468C1.01126 4 0.532088 4.85997 0.944298 5.52617ZM4.99998 8.27977V17.3333C4.99998 17.7015 5.29845 18 5.66665 18H19.3333C19.7015 18 20 17.7015 20 17.3333V6.66667C20 6.29848 19.7015 6 19.3333 6H3.58937L4.99998 8.27977Z" fill="currentColor" data-darkreader-inline-fill="" style="--darkreader-inline-fill: currentColor;"></path></svg></span></button>
            )
            logging.info("WhatsApp Web is ready to use.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize WhatsApp Web: {e}")
            return False

    def quit(self) -> None:
        """Safely quit the driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error while quitting driver: {e}")

    def cleanup(self):
        """No cleanup needed as we're using the existing profile."""
        pass

class ContactManager:
    """Manages contact data and message sending."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sent_numbers: Set[str] = set()
        self.supported_encodings = ['utf-8', 'latin1', 'cp1252', 'utf-16']
        self.supported_extensions = ['.csv', '.xlsx', '.xls']
        self.required_packages = {
            '.xlsx': 'openpyxl',
            '.xls': 'xlrd'
        }

    def install_required_package(self, package_name: str) -> bool:
        """Install required package using pip."""
        try:
            import subprocess
            import sys
            logging.info(f"Installing required package: {package_name}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            logging.info(f"Successfully installed {package_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to install {package_name}: {e}")
            return False

    def ensure_dependencies(self, file_extension: str) -> bool:
        """Ensure all required dependencies are installed."""
        if file_extension in self.required_packages:
            package_name = self.required_packages[file_extension]
            try:
                __import__(package_name)
            except ImportError:
                return self.install_required_package(package_name)
        return True

    def detect_file_encoding(self, file_path: str) -> str:
        """Detect the encoding of the file."""
        encodings = self.supported_encodings
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'  # Default to utf-8 if no encoding works

    def load_contacts(self) -> Optional[pd.DataFrame]:
        """Load contacts from file (CSV or Excel) with automatic encoding detection."""
        try:
            file_path = self.config.CONTACTS_FILE_PATH
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension not in self.supported_extensions:
                logging.error(f"Unsupported file format. Supported formats: {', '.join(self.supported_extensions)}")
                return None

            # Ensure required dependencies are installed
            if not self.ensure_dependencies(file_extension):
                logging.error("Failed to install required dependencies")
                return None

            if file_extension == '.csv':
                # Try different encodings for CSV
                encoding = self.detect_file_encoding(file_path)
                logging.info(f"Detected encoding: {encoding}")
                
                try:
                    excel = pd.read_csv(file_path, encoding=encoding)
                except Exception as e:
                    logging.error(f"Error reading CSV with {encoding} encoding: {e}")
                    # Try with error handling
                    excel = pd.read_csv(file_path, encoding=encoding, errors='replace')
            else:
                # For Excel files
                try:
                    excel = pd.read_excel(file_path)
                except Exception as e:
                    logging.error(f"Error reading Excel file: {e}")
                    return None

            if excel.empty:
                logging.error("The contacts file is empty.")
                return None

            # Clean column names
            excel.columns = excel.columns.str.strip()
            
            # Validate required columns
            required_columns = ['First Name', 'Mobile Phone', 'Message']
            missing_columns = [col for col in required_columns if col not in excel.columns]
            
            if missing_columns:
                logging.error(f"Missing required columns: {', '.join(missing_columns)}")
                return None

            # Clean data
            excel['First Name'] = excel['First Name'].astype(str).str.strip()
            excel['Mobile Phone'] = excel['Mobile Phone'].astype(str)
            excel['Message'] = excel['Message'].astype(str)

            logging.info(f"Contacts loaded successfully. Total contacts: {len(excel)}")
            return excel

        except FileNotFoundError:
            logging.error(f"Contacts file not found: {self.config.CONTACTS_FILE_PATH}")
            return None
        except Exception as e:
            logging.error(f"Error loading contacts: {e}")
            return None

    def clean_phone_number(self, number: str) -> str:
        """Clean and format phone number."""
        # Remove all non-numeric characters except '+'
        cleaned = ''.join(c for c in str(number) if c.isdigit() or c == '+')
        # Remove any leading zeros after the country code
        if cleaned.startswith('+'):
            country_code = cleaned[:cleaned.find('0', 1) if '0' in cleaned[1:] else len(cleaned)]
            number_part = cleaned[len(country_code):].lstrip('0')
            return country_code + number_part
        return cleaned.lstrip('0')

class MessageSender:
    """Handles sending messages to WhatsApp contacts."""
    
    def __init__(self, driver: WhatsAppDriver, config: Config):
        self.driver = driver
        self.config = config

    @staticmethod
    def retry_on_stale(max_retries: int = 5, retry_delay: int = 2):
        """Decorator for retrying operations on stale elements."""
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(self, *args, **kwargs)
                    except StaleElementReferenceException:
                        if attempt == max_retries - 1:
                            logging.error(f"Failed after {max_retries} attempts")
                            return False
                        logging.warning(f"Stale element, retrying ({attempt+1}/{max_retries})...")
                        time.sleep(retry_delay)
                return False
            return wrapper
        return decorator

    @retry_on_stale(max_retries=5, retry_delay=2)
    def find_element_with_retry(self, by: By, value: str, timeout: int = None) -> Any:
        """Find an element with retry mechanism."""
        if timeout is None:
            timeout = self.config.WAIT_TIMEOUT
            
        try:
            # First wait for element to be present
            element = WebDriverWait(self.driver.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Element not found: {by}={value}")
            return None
        except StaleElementReferenceException:
            logging.warning(f"Stale element while finding: {by}={value}")
            return None

    def safe_element_interaction(self, locator, action, *args, **kwargs):
        for attempt in range(self.config.MAX_RETRIES):
            try:
                element = self.driver.driver.find_element(*locator)
                if action == "click":
                    element.click()
                elif action == "send_keys":
                    element.send_keys(*args)
                elif action == "clear":
                    element.clear()
                return True
            except (StaleElementReferenceException, NoSuchElementException, TimeoutException, WebDriverException) as e:
                error_str = str(e)
                # Check for critical connection/session errors
                if (
                    'failed to establish a new connection' in error_str.lower() or
                    'max retries exceeded' in error_str.lower() or
                    'actively refused' in error_str.lower() or
                    'invalid session id' in error_str.lower() or
                    'session deleted as the browser has closed the connection' in error_str.lower() or
                    'not connected to devtools' in error_str.lower()
                ):
                    logging.error("\n" + "*"*50 + f"\nCRITICAL ERROR: {error_str}\nTerminating program immediately.")
                    sys.exit(1)
                if attempt == self.config.MAX_RETRIES - 1:
                    logging.error("\n" + "*"*50 + f"\nFailed to interact with element after {self.config.MAX_RETRIES} attempts: {e}")
                    return False
                logging.warning("\n" + "*"*50 + f"\nException during {action} ({type(e).__name__}), retrying ({attempt+1}/{self.config.MAX_RETRIES})...")
                time.sleep(self.config.RETRY_DELAY)
        return False

    @retry_on_stale(max_retries=3, retry_delay=1)
    def send_message(self, contact_mobile_number: str, contact_message: str) -> bool:
        """Send a message to a contact."""
        try:
            # Define locators
            search_box_locator = (By.XPATH, "//p[contains(@class, 'selectable-text')][1]")
            search_result_locator = (By.XPATH, "//div[contains(@aria-label, 'Search results')][1]")
            search_item_locator = (By.XPATH, "(.//div[@role='listitem'])[2]")
            message_box_locator = (
                By.CSS_SELECTOR,
                "div[aria-label*='Type a message'][aria-owns='emoji-suggestion'] > p[class*='selectable-text']"
            )

            # Search contact
            logging.info("Attempting to find search box...")
            if not self.safe_element_interaction(search_box_locator, "clear"):
                logging.error("Could not clear search box")
                return False
            if not self.safe_element_interaction(search_box_locator, "send_keys", Keys.CONTROL + "a"):
                return False
            if not self.safe_element_interaction(search_box_locator, "send_keys", Keys.DELETE):
                return False
            if not self.safe_element_interaction(search_box_locator, "send_keys", contact_mobile_number):
                return False
            time.sleep(2)
            if not self.safe_element_interaction(search_box_locator, "send_keys", Keys.ENTER):
                return False

            # Click search result
            logging.info("Attempting to find search results...")
            if not self.safe_element_interaction(search_result_locator, "click"):
                logging.error("Could not click search results")
                return False

            logging.info("Attempting to find specific search item...")
            if not self.safe_element_interaction(search_item_locator, "click"):
                logging.error("Could not click search item")
                return False
            time.sleep(2)

            # Send message
            logging.info("Attempting to find message box...")
            if not self.safe_element_interaction(message_box_locator, "click"):
                logging.error("Could not click message box")
                return False
            time.sleep(2)

            # Clear message box thoroughly
            if not self.safe_element_interaction(message_box_locator, "clear"):
                return False
            if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.CONTROL + "a"):
                return False
            if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.DELETE):
                return False
            time.sleep(1)

            # Handle multi-line messages using clipboard
            try:
                lines = contact_message.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():  # Only process non-empty lines
                        # Use clipboard to paste the text
                        script = f"""
                        function setClipboard(text) {{
                            const input = document.createElement('textarea');
                            input.value = text;
                            document.body.appendChild(input);
                            input.select();
                            document.execCommand('copy');
                            document.body.removeChild(input);
                        }}
                        setClipboard(`{line}`);
                        """
                        self.driver.driver.execute_script(script)
                        time.sleep(0.5)

                        # Paste the text using keyboard shortcut
                        if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.CONTROL + "v"):
                            logging.warning(f"Failed to paste line {i+1}, trying alternative method")
                            # Alternative method if paste fails
                            if not self.safe_element_interaction(message_box_locator, "send_keys", line):
                                logging.error(f"Failed to send line {i+1}")
                                return False

                    if i < len(lines) - 1:  # If not the last line
                        if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.SHIFT + Keys.ENTER):
                            return False
                        time.sleep(0.5)

                time.sleep(1)
                # Send the message
                if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.ENTER):
                    return False
                return True

            except Exception as e:
                logging.error(f"Error in message sending method: {str(e)}")
                # Fallback to simple character-by-character method
                try:
                    lines = contact_message.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip():  # Only process non-empty lines
                            # Try sending the line as a whole first
                            if not self.safe_element_interaction(message_box_locator, "send_keys", line):
                                # If that fails, try character by character
                                for char in line:
                                    if not self.safe_element_interaction(message_box_locator, "send_keys", char):
                                        logging.warning(f"Failed to send character, continuing with next")
                                    time.sleep(0.1)
                        
                        if i < len(lines) - 1:  # If not the last line
                            if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.SHIFT + Keys.ENTER):
                                return False
                            time.sleep(0.5)

                    time.sleep(1)
                    # Send the message
                    if not self.safe_element_interaction(message_box_locator, "send_keys", Keys.ENTER):
                        return False
                    return True
                except Exception as e2:
                    logging.error(f"Error in fallback message sending method: {str(e2)}")
                    return False

        except (NoSuchElementException, TimeoutException, 
                ElementClickInterceptedException, ElementNotInteractableException,
                WebDriverException) as e:
            error_str = str(e)
            if (
                'failed to establish a new connection' in error_str.lower() or
                'max retries exceeded' in error_str.lower() or
                'actively refused' in error_str.lower() or
                'invalid session id' in error_str.lower() or
                'session deleted as the browser has closed the connection' in error_str.lower() or
                'not connected to devtools' in error_str.lower()
            ):
                logging.error("\n" + "*"*50 + f"\nCRITICAL ERROR: {error_str}\nTerminating program immediately.")
                sys.exit(1)
            logging.error("\n" + "*"*50 + f"\nError sending message: {error_str}")
            return False

def main():
    """Main execution function."""
    logging.info("\n" + "*"*50)
    logging.info(f"************ NEW RUN: {time.strftime('%Y-%m-%d %H:%M:%S')} ********")
    logging.info("*"*50 + "\n")
    try:
        config = Config()
    except FileNotFoundError as e:
        logging.error(f"Configuration error: {e}")
        logging.error(f"\nError: {e}")
        logging.info("\nPlease ensure:")
        logging.info("1. Chrome driver (chromedriver.exe) is in the same folder as this script")
        logging.info("2. Contacts file (contacts.xlsx) is in the same folder as this script")
        logging.info("3. Chrome browser is installed with a user profile")
        return

    whatsapp_driver = WhatsAppDriver(config)
    contact_manager = ContactManager(config)
    message_sender = None

    # Initialize tracking dictionaries
    successful_sends = {}  # phone_number: name
    failed_sends = {}      # phone_number: (name, reason)
    total_contacts = 0

    try:
        # Load contacts first
        contacts_df = contact_manager.load_contacts()
        if contacts_df is None:
            return

        total_contacts = len(contacts_df)
        logging.info(f"\nTotal contacts to process: {total_contacts}")

        # Try to initialize WhatsApp automation
        try:
            driver = whatsapp_driver.create_driver()
            if whatsapp_driver.initialize_whatsapp():
                message_sender = MessageSender(whatsapp_driver, config)
                logging.info("WhatsApp Web initialized successfully")
            else:
                logging.error("Failed to initialize WhatsApp Web")
                return
        except Exception as e:
            logging.error(f"Could not initialize WhatsApp automation: {e}")
            return

        # Process each contact
        for index, row in contacts_df.iterrows():
            current_contact = index + 1
            contact_name = f"{row['First Name']} ".strip()
            contact_message = row['Message']
            contact_mobile_number = contact_manager.clean_phone_number(row['Mobile Phone'])

            logging.info(f"\nProcessing contact {current_contact}/{total_contacts}: {contact_name} ({contact_mobile_number})")

            if contact_mobile_number in contact_manager.sent_numbers:
                logging.info(f"Message already sent to {contact_name}. Skipping...")
                failed_sends[contact_mobile_number] = (contact_name, "Message already sent previously")
                continue

            contact_manager.sent_numbers.add(contact_mobile_number)
            logging.info(f"Sending message to {contact_name}...")

            try:
                if message_sender.send_message(contact_mobile_number, contact_message):
                    logging.info(f"✓ Message sent successfully to {contact_name}")
                    successful_sends[contact_mobile_number] = contact_name
                else:
                    logging.info(f"✗ Failed to send message to {contact_name}")
                    failed_sends[contact_mobile_number] = (contact_name, "Failed to send message - Element interaction failed")
            except Exception as e:
                error_msg = str(e)
                logging.info(f"✗ Error sending message to {contact_name}: {error_msg}")
                failed_sends[contact_mobile_number] = (contact_name, f"Error: {error_msg}")

            # Add a small delay between contacts
            time.sleep(2)

    except SessionNotCreatedException as e:
        logging.error(f"Session not created: {e}")
        logging.error("Chrome driver version mismatch or profile issue. Terminating program.")
        return
    except WebDriverException as e:
        logging.error(f"WebDriver exception: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if whatsapp_driver:
            time.sleep(5)
            whatsapp_driver.quit()

        # print summary report
        logging.info("\n" + "="*50)
        logging.info("MESSAGE SENDING SUMMARY")
        logging.info("="*50)
        logging.info(f"Total contacts processed: {total_contacts}")
        logging.info(f"Successfully sent: {len(successful_sends)}")
        logging.info(f"Failed to send: {len(failed_sends)}")
        
        # if successful_sends:
        #     logging.info("\nSuccessfully sent messages to:")
        #     for phone, name in successful_sends.items():
        #         logging.info(f"✓ {name} ({phone})")
        
        if failed_sends:
            logging.info("\nFailed to send messages to:")
            for phone, (name, reason) in failed_sends.items():
                logging.info(f"✗ {name} ({phone})")
                logging.info(f"  Reason: {reason}")
        logging.info("="*50 + "\n")

if __name__ == "__main__":
    main() 