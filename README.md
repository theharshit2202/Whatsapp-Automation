# WhatsApp Automation Script

A robust Python-based automation tool for sending WhatsApp messages using Selenium and Chrome WebDriver. This tool allows you to send messages to multiple contacts from an Excel/CSV file while providing detailed logging and error handling.

## Features

- 🔄 Automated message sending to multiple contacts
- 📊 Support for Excel (.xlsx) and CSV files
- 📝 Detailed logging with UTF-8 support
- 🔍 Smart contact search and message delivery
- ⚡ Retry mechanism for failed operations
- 🔔 Windows notifications for status updates
- 🛡️ Robust error handling and recovery
- 📱 Support for special characters and emojis
- 📈 Progress tracking and summary reports

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- Chrome WebDriver (compatible with your Chrome version)
- Required Python packages (install using `pip install -r requirements.txt`):
  - selenium
  - pandas
  - openpyxl (for Excel files)
  - winotify (for Windows notifications)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/whatsapp-automation.git
   cd whatsapp-automation
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Place your Chrome WebDriver (chromedriver.exe) in the project directory

## Configuration

1. Prepare your contacts file (Excel or CSV) with the following columns:
   - First Name
   - Mobile Phone
   - Message

2. Place your contacts file in the project directory as `contacts.xlsx` or `contacts.csv`

## Usage

1. Run the script:
   ```bash
   python "Final_Chrome WA_AUTO.py"
   ```

2. The script will:
   - Load contacts from your file
   - Initialize Chrome with your WhatsApp Web session
   - Send messages to each contact
   - Provide real-time status updates
   - Generate a detailed log file

## Logging

The script creates a detailed log file (`whatsapp_automation.log`) that includes:
- Start and end times of each run
- Status of each message sent
- Success/failure details
- Summary report with statistics

## Error Handling

The script includes robust error handling for:
- Network issues
- Element not found errors
- Stale element references
- Invalid phone numbers
- Message sending failures

## Windows Notifications

The tool provides Windows notifications for:
- Critical errors
- Message sending status
- Process completion

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Please use it responsibly and in accordance with WhatsApp's terms of service.

## Support

If you encounter any issues or have questions, please:
1. Check the log file for detailed error messages
2. Ensure your Chrome and ChromeDriver versions match
3. Verify your contacts file format
4. Open an issue in this repository

## Acknowledgments

- Selenium WebDriver
- WhatsApp Web
- Python community 