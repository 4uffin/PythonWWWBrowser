#
# A simple, tabbed web browser using PyQt5 and QtWebEngine.
#
# This script creates a functional web browser with a modern dark theme,
# a tabbed interface, a URL bar, and a bookmark manager.
#
# This file is the core of the browser application.
# For a full project structure, it is accompanied by:
# - README.md: A project description, installation, and usage instructions.
# - requirements.txt: To list dependencies like PyQt5.
# - LICENSE.txt: To specify the terms of use (e.g., MIT License).
#

import sys
import os
import datetime
import urllib.parse
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget, QVBoxLayout, QWidget, QDialog, QPushButton, QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox, QLabel, QStatusBar, QProgressBar, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.Qt import QDesktopServices
from PyQt5.QtCore import QT_VERSION_STR


# --- Application Data Path Helper ---
# This function creates and returns a platform-appropriate directory for
# application data, ensuring files like bookmarks.txt are stored reliably.
def get_data_path():
    """
    Returns the path to the application's data directory.
    Creates the directory if it does not exist.
    """
    # Use a hidden directory in the user's home folder for cross-platform compatibility
    app_data_dir = os.path.join(os.path.expanduser("~"), ".my_advanced_browser")
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    return app_data_dir

# --- Bookmark Manager Class ---
# A dialog to manage and interact with saved bookmarks.
class BookmarkManager(QDialog):
    def __init__(self, parent=None):
        super(BookmarkManager, self).__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.setGeometry(100, 100, 400, 300)
        self.setObjectName("BookmarkManager")

        self.layout = QVBoxLayout()
        self.bookmark_list = QListWidget()
        self.bookmark_list.setObjectName("BookmarkList")
        self.layout.addWidget(self.bookmark_list)

        self.button_layout = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.open_button.setObjectName("BookmarkButton")
        self.open_button.clicked.connect(self.open_bookmark)
        self.button_layout.addWidget(self.open_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("BookmarkButton")
        self.delete_button.clicked.connect(self.delete_bookmark)
        self.button_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        # Load bookmarks on initialization
        self.load_bookmarks()

    def load_bookmarks(self):
        """
        Loads bookmarks from the bookmarks file and populates the list widget.
        """
        self.bookmark_list.clear()
        bookmarks_file_path = os.path.join(get_data_path(), "bookmarks.txt")
        try:
            with open(bookmarks_file_path, "r") as f:
                for line in f:
                    parts = line.strip().split("|||")
                    if len(parts) == 2:
                        name, url = parts
                        item = QListWidgetItem(name)
                        item.setData(Qt.UserRole, url)
                        self.bookmark_list.addItem(item)
        except FileNotFoundError:
            # File doesn't exist yet, which is fine for the first run
            pass

    def add_bookmark(self, name, url):
        """
        Adds a new bookmark to the file, checking for duplicates.
        """
        bookmarks_file_path = os.path.join(get_data_path(), "bookmarks.txt")
        existing_urls = []
        try:
            with open(bookmarks_file_path, "r") as f:
                for line in f:
                    parts = line.strip().split("|||")
                    if len(parts) == 2:
                        existing_urls.append(parts[1])
        except FileNotFoundError:
            pass

        if url not in existing_urls:
            with open(bookmarks_file_path, "a") as f:
                f.write(f"{name}|||{url}\n")
            self.load_bookmarks()
        else:
            QMessageBox.warning(self, "Bookmark Exists", "This URL is already bookmarked.")

    def open_bookmark(self):
        """
        Opens the selected bookmark in a new tab of the main browser window.
        """
        selected_item = self.bookmark_list.currentItem()
        if selected_item:
            url = selected_item.data(Qt.UserRole)
            self.parent().add_new_tab(QUrl(url), selected_item.text())
            self.accept()

    def delete_bookmark(self):
        """
        Deletes the selected bookmark from the file and reloads the list.
        """
        selected_item = self.bookmark_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, 'Delete Bookmark', 'Are you sure you want to delete this bookmark?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                url_to_delete = selected_item.data(Qt.UserRole)
                bookmarks_to_keep = []
                bookmarks_file_path = os.path.join(get_data_path(), "bookmarks.txt")
                try:
                    with open(bookmarks_file_path, "r") as f:
                        for line in f:
                            parts = line.strip().split("|||")
                            if len(parts) == 2 and parts[1] != url_to_delete:
                                bookmarks_to_keep.append(line)
                    with open(bookmarks_file_path, "w") as f:
                        for bookmark_line in bookmarks_to_keep:
                            f.write(bookmark_line)
                except FileNotFoundError:
                    pass
                self.load_bookmarks()


# --- Main Browser Window Class ---
class Browser(QMainWindow):
    def __init__(self):
        super(Browser, self).__init__()
        self.setObjectName("BrowserWindow")
        self.setWindowTitle("My Advanced Browser")

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.setObjectName("BrowserTabs")

        self.setCentralWidget(self.tabs)
        self.showMaximized()

        navbar = QToolBar()
        navbar.setObjectName("BrowserToolbar")
        navbar.setIconSize(QSize(24, 24))
        self.addToolBar(navbar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.url_status_label = QLabel("Ready")
        self.status_bar.addWidget(self.url_status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.setup_toolbar_actions(navbar)

        # Set DuckDuckGo as default homepage
        self.add_new_tab(QUrl("https://duckduckgo.com/"), "Homepage")

        self.bookmark_manager = BookmarkManager(self)
        self._update_close_button_visibility()

    def _get_user_agent(self):
        """
        Returns a custom user-agent string to prevent websites from
        blocking or serving a non-optimal page due to an unrecognized browser.
        This provides better compatibility and a more consistent browsing experience.
        """
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 MyAdvancedBrowser/1.0"

    def _get_icon(self, icon_name, fallback_text):
        """
        Helper function to get an icon from the theme, or return a text label as a fallback.
        This prevents the app from having blank buttons if the icon theme is missing.
        """
        # Try to get the icon from the system theme
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            return icon, ""
        
        # Fallback to a text label if no icon is found
        return QIcon(), fallback_text

    def setup_toolbar_actions(self, navbar):
        """
        Sets up the actions and widgets for the browser's toolbar.
        Note: QIcon.fromTheme() requires a system icon theme to be installed.
        This is a common dependency on Linux desktops but may not be available
        on all systems, which is why a fallback is implemented.
        """
        back_icon, back_text = self._get_icon("go-previous", "Back")
        back_btn = QAction(back_icon, back_text, self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        forward_icon, forward_text = self._get_icon("go-next", "Forward")
        forward_btn = QAction(forward_icon, forward_text, self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)

        reload_icon, reload_text = self._get_icon("view-refresh", "Reload")
        reload_btn = QAction(reload_icon, reload_text, self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_btn)

        stop_icon, stop_text = self._get_icon("process-stop", "Stop")
        stop_btn = QAction(stop_icon, stop_text, self)
        stop_btn.triggered.connect(lambda: self.current_browser().stop())
        navbar.addAction(stop_btn)

        home_icon, home_text = self._get_icon("go-home", "Home")
        home_btn = QAction(home_icon, home_text, self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        navbar.addSeparator()

        new_tab_icon, new_tab_text = self._get_icon("tab-new", "New Tab")
        new_tab_btn = QAction(new_tab_icon, new_tab_text, self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        navbar.addAction(new_tab_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setObjectName("UrlBar")
        navbar.addWidget(self.url_bar)

        search_icon, search_text = self._get_icon("system-search", "Search")
        search_btn = QAction(search_icon, search_text, self)
        search_btn.triggered.connect(self.perform_search)
        navbar.addAction(search_btn)

        navbar.addSeparator()

        add_bookmark_icon, add_bookmark_text = self._get_icon("bookmark-new", "Add Bookmark")
        add_bookmark_btn = QAction(add_bookmark_icon, add_bookmark_text, self)
        add_bookmark_btn.triggered.connect(self.add_bookmark)
        navbar.addAction(add_bookmark_btn)

        view_bookmarks_icon, view_bookmarks_text = self._get_icon("bookmarks-organize", "View Bookmarks")
        view_bookmarks_btn = QAction(view_bookmarks_icon, view_bookmarks_text, self)
        view_bookmarks_btn.triggered.connect(self.view_bookmarks)
        navbar.addAction(view_bookmarks_btn)

        navbar.addSeparator()

        about_icon, about_text = self._get_icon("help-about", "About")
        about_btn = QAction(about_icon, about_text, self)
        about_btn.triggered.connect(self.show_about_dialog)
        navbar.addAction(about_btn)

    def add_new_tab(self, qurl=None, label="Blank"):
        """
        Creates a new browser tab with a QWebEngineView and connects its signals.
        """
        if qurl is None:
            # New tabs default to DuckDuckGo
            qurl = QUrl("https://duckduckgo.com/")

        browser = QWebEngineView()
        
        # Set a custom user-agent for the new page
        browser.page().profile().setHttpUserAgent(self._get_user_agent())

        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda q: self._update_browser_ui(browser))
        browser.loadProgress.connect(lambda p: self._update_browser_ui(browser))
        browser.loadFinished.connect(lambda s: self._update_browser_ui(browser))
        browser.titleChanged.connect(lambda t: self.update_tab_title(t, browser))
        browser.iconUrlChanged.connect(lambda u: self.update_tab_icon(u, browser))
        browser.page().profile().downloadRequested.connect(self.on_download_requested)
        browser.loadStarted.connect(lambda: self.set_status_message(f"Loading {browser.url().host()}"))

        self._update_close_button_visibility()
        self._update_browser_ui(browser)
        self.update_tab_title(label, browser)

    def _update_browser_ui(self, browser):
        """
        A helper function to update the UI elements based on the current browser tab state.
        This centralizes logic and avoids repetition.
        """
        if browser != self.current_browser():
            return

        qurl = browser.url()
        progress = browser.loadProgress()
        title = browser.page().title()
        
        # Update URL bar
        self.url_bar.setText(qurl.toDisplayString())
        self.url_bar.setCursorPosition(0)
        
        # Update progress bar and status bar
        if progress < 100:
            self.progress_bar.setValue(progress)
            self.progress_bar.setVisible(True)
            self.set_status_message(f"Loading... {progress}%")
        else:
            self.progress_bar.setVisible(False)
            self.set_status_message(qurl.toDisplayString())
        
        # Update the main window title
        self.update_tab_title(title, browser)
        
    def _update_close_button_visibility(self):
        """
        Disables the close button on the tab bar if there is only one tab.
        This prevents accidental closure of the last remaining tab.
        """
        if self.tabs.count() <= 1:
            self.tabs.setTabsClosable(False)
        else:
            self.tabs.setTabsClosable(True)

    def tab_open_doubleclick(self, i):
        """
        Handles double-clicking the tab bar to open a new tab.
        """
        if i == -1:
            self.add_new_tab()

    def current_browser(self):
        """
        Convenience method to get the currently active QWebEngineView widget.
        """
        return self.tabs.currentWidget()

    def current_tab_changed(self, i):
        """
        Updates the UI when the active tab changes.
        """
        if self.tabs.count() > 0:
            current_browser = self.current_browser()
            self._update_browser_ui(current_browser)
        else:
            self.url_bar.setText("")
            self.setWindowTitle("My Advanced Browser")
            self.set_status_message("No tabs open. Open a new tab.")
            self.progress_bar.setVisible(False)

    def close_current_tab(self, i):
        """
        Closes a tab. This function is only called when there is more than one tab.
        """
        self.tabs.removeTab(i)
        self._update_close_button_visibility()

    def navigate_home(self):
        """
        Navigates the current tab to the default homepage (DuckDuckGo).
        """
        self.current_browser().setUrl(QUrl("https://duckduckgo.com/"))

    def navigate_to_url(self):
        """
        Handles navigation from the URL bar, either to a URL or performing a search.
        """
        url = self.url_bar.text().strip()
        if not url:
            return

        # Check if it looks like a valid URL
        if not url.startswith(("http://", "https://")):
            # If it contains a dot and no spaces, assume it's a domain name and prepend http
            if "." in url and " " not in url and not url.startswith("localhost"):
                url = "http://" + url
            else:
                # Otherwise, treat it as a search query
                self.perform_search(url)
                return
        
        self.current_browser().setUrl(QUrl(url))

    def perform_search(self, query=None):
        """
        Performs a search using the DuckDuckGo search engine.
        """
        search_query = query if query else self.url_bar.text()
        if search_query:
            # URL-encode the search query to handle special characters
            encoded_query = urllib.parse.quote_plus(search_query)
            search_url = QUrl(f"https://duckduckgo.com/?q={encoded_query}")
            self.current_browser().setUrl(search_url)

    def update_tab_title(self, title, browser=None):
        """
        Updates the tab title and main window title.
        """
        if browser and browser != self.current_browser():
            return
        index = self.tabs.indexOf(browser)
        display_title = title if title else "New Tab"
        self.tabs.setTabText(index, display_title)
        if browser == self.current_browser():
            self.setWindowTitle(f"My Advanced Browser - {display_title}")

    def update_tab_icon(self, url, browser):
        """
        Updates the tab icon (favicon) when it becomes available.
        """
        index = self.tabs.indexOf(browser)
        if index != -1:
            if url.isValid():
                browser.page().icon().pixmap(QSize(16, 16)).save("temp_icon.png")
                self.tabs.setTabIcon(index, QIcon("temp_icon.png"))
                os.remove("temp_icon.png")
            else:
                # Fallback to a default icon or no icon if not available
                self.tabs.setTabIcon(index, QIcon())

    def set_status_message(self, message, timeout=0):
        """
        A helper function to display a message in the status bar.
        """
        self.status_bar.showMessage(message, timeout)

    def add_bookmark(self):
        """
        Prompts the user for a bookmark name and adds the current page to bookmarks.
        """
        current_url = self.current_browser().url().toString()
        if current_url and current_url != "about:blank":
            title = self.current_browser().page().title()
            # QMessageBox.getText returns a tuple of (text, bool)
            text, ok = QMessageBox.getText(self, 'Add Bookmark', 'Enter a name for this bookmark:', QLineEdit.Normal, title if title else current_url)
            if ok and text:
                self.bookmark_manager.add_bookmark(text, current_url)
        else:
            QMessageBox.warning(self, "Cannot Add Bookmark", "Cannot add a bookmark for a blank or invalid page.")

    def view_bookmarks(self):
        """
        Displays the bookmark manager dialog.
        """
        self.bookmark_manager.load_bookmarks()
        self.bookmark_manager.exec_()

    def on_download_requested(self, download):
        """
        Handles download requests, prompting the user for a save location.
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.url().fileName())
        if path:
            download.setPath(path)
            download.accept()
            # Connect the finished signal to a handler to show completion status
            download.finished.connect(lambda: self.download_finished(download))
            self.set_status_message(f"Downloading: {download.url().fileName()}")
        else:
            download.cancel()
            self.set_status_message("Download cancelled.")

    def download_finished(self, download):
        """
        Handles the download completion and shows a notification to the user.
        """
        if download.isFinished() and download.state() == download.Completed:
            reply = QMessageBox.question(self, "Download Complete",
                                         f"'{download.url().fileName()}' downloaded to:\n{download.path()}\n\nDo you want to open it?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(download.path()))
            self.set_status_message(f"Download complete: {download.url().fileName()}", timeout=3000)
        elif download.state() == download.Cancelled:
            self.set_status_message(f"Download cancelled: {download.url().fileName()}", timeout=3000)
        else:
            self.set_status_message(f"Download failed: {download.url().fileName()}", timeout=3000)

    def show_about_dialog(self):
        """
        Shows an 'About' dialog with application information.
        """
        now = datetime.datetime.now()
        current_time_str = now.strftime("%I:%M:%S %p")
        current_date = now.strftime("%B %d, %Y")
        timezone = now.astimezone().tzname()
        
        info_text = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background-color: #333; color: #eee; }}
                h3 {{ color: #007bff; }}
                p {{ margin: 5px 0; }}
                b {{ color: #ccc; }}
            </style>
        </head>
        <body>
            <h3>My Advanced Browser</h3>
            <p>Version: 1.0.0</p>
            <p>A simple, functional web browser built with PyQt5 and QtWebEngine.</p>
            <p><b>Current Time:</b> {current_time_str} {timezone}</p>
            <p><b>Current Date:</b> {current_date}</p>
            <p><b>System:</b> {sys.platform}</p>
            <p><b>Python Version:</b> {sys.version.split()[0]}</p>
            <p><b>Qt Version:</b> {QT_VERSION_STR}</p>
        </body>
        </html>
        """
        QMessageBox.about(self, "About My Advanced Browser", info_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("My Advanced Browser")

    # This stylesheet provides a modern, dark theme for the browser.
    app.setStyleSheet("""
        QMainWindow#BrowserWindow {
            background-color: #333;
            color: #eee;
        }

        QToolBar#BrowserToolbar {
            background-color: #222;
            border: none;
            padding: 5px;
            spacing: 10px;
        }

        QToolBar QAction {
            font-size: 14px;
            color: #ccc;
            padding: 5px 10px;
        }

        QToolBar QAction:hover {
            background-color: #444;
            border-radius: 3px;
        }

        QToolBar QAction::icon {
            background-color: transparent;
        }

        QLineEdit#UrlBar {
            border: 1px solid #555;
            border-radius: 8px;
            padding: 5px 10px;
            background-color: #444;
            color: #eee;
            selection-background-color: #007bff;
            font-size: 14px;
            margin-left: 10px;
            margin-right: 10px;
        }

        QTabWidget::pane {
            border-top: 1px solid #444;
            background-color: #1e1e1e;
        }

        QTabBar::tab {
            background: #444;
            border: 1px solid #555;
            border-bottom-color: #444;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 8px 15px;
            margin-right: 2px;
            color: #ccc;
            font-size: 13px;
        }

        QTabBar::tab:selected {
            background: #1e1e1e;
            border-bottom-color: #1e1e1e;
            color: #fff;
            font-weight: bold;
        }

        QTabBar::tab:hover:!selected {
            background: #555;
        }

        QStatusBar {
            background-color: #222;
            color: #ccc;
            border-top: 1px solid #444;
            padding: 2px;
        }

        QStatusBar QLabel {
            color: #ccc;
        }

        QProgressBar {
            border: 1px solid #555;
            border-radius: 5px;
            text-align: center;
            background-color: #444;
            color: #eee;
        }

        QProgressBar::chunk {
            background-color: #007bff;
            border-radius: 5px;
        }

        QDialog#BookmarkManager {
            background-color: #333;
            border: 1px solid #555;
            border-radius: 5px;
        }

        QListWidget#BookmarkList {
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            color: #eee;
            padding: 5px;
        }

        QListWidget::item {
            padding: 5px;
        }

        QListWidget::item:selected {
            background-color: #007bff;
            color: #fff;
        }

        QPushButton#BookmarkButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 14px;
            margin: 5px;
        }

        QPushButton#BookmarkButton:hover {
            background-color: #0056b3;
        }

        QMessageBox {
            background-color: #333;
            color: #eee;
        }

        QMessageBox QLabel {
            color: #eee;
        }

        QMessageBox QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
        }

        QMessageBox QPushButton:hover {
            background-color: #0056b3;
        }
    """)

    window = Browser()
    sys.exit(app.exec_())
