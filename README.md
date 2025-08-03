**Note:** This is a basic, proof-of-concept web browser. It is intended as a framework for building a more advanced browser, not as a full-featured application for daily use. Or hey, maybe you want the most dumbed-down web browser for daily use, well, here you go!

# Simple Python Browser (Blueprint)
This project is a functional, tabbed web browser built using Python with the PyQt5 and QtWebEngine libraries. It features a custom dark theme and essential browsing tools, serving as a great starting point for further development.

## Features

**Tabbed Interface:** Manage multiple web pages simultaneously with a clean, tabbed layout.

**Essential Navigation:** A complete toolbar with buttons for Back, Forward, Reload, and Stop, as well as a dedicated Home button that navigates to DuckDuckGo.

**Smart URL Bar:** The address bar handles both direct URLs and search queries. If you don't enter a valid URL, it automatically performs a search using DuckDuckGo.

**Integrated Search:** All searches are powered by DuckDuckGo, providing a privacy-focused browsing experience.

**Bookmark Management:** A dedicated bookmark manager allows you to add, view, and delete your favorite websites. Bookmarks are saved to a bookmarks.txt file.

**Download Handler:** The browser can handle file downloads, prompting you for a save location and offering to open the file once the download is complete.

**Status Bar:** A status bar at the bottom displays real-time loading progress and status messages, improving the user experience.

**About Dialog:** An informational dialog provides details about the application, version, and the current system time.

**Custom Dark Theme:** The entire application is styled with a sleek, custom dark mode, making it comfortable to use.

## Requirements
Before running the application, you need to install the necessary Python libraries. You can install them using pip:

```pip install PyQt5 PyQtWebEngine```

## How to Run

1. Save the provided code as a Python file, for example, browser.py.

2. Open your terminal or command prompt.

3. Navigate to the directory where you saved the file.

4. Run the script with the following command:

```python browser.py```

The browser window will open, and you can start navigating the web.

## Usage

- Open a New Tab: Double-click on the tab bar to open a new tab, or use the "New Tab" button.

- Navigate: Type a URL (e.g., google.com) or a search query (e.g., Python programming) into the address bar and press Enter.

- Bookmarks:

  - Click the "Add Bookmark" button to save the current page.

  - Click the "View Bookmarks" button to open the bookmark manager.

- Downloads: If you click a download link, a file dialog will appear to let you choose where to save the file. The status bar will show the download progress.
