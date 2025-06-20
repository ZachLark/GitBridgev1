#!/usr/bin/env python3
"""
GitBridge Phase 24 - Accessibility & Internationalization Module
Comprehensive accessibility features and multi-language support for web UI.

MAS Lite Protocol v2.1 Compliance
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class AccessibilityManager:
    """Manages accessibility features and internationalization for the web UI."""
    
    def __init__(self, language: str = "en"):
        """Initialize accessibility manager."""
        self.language = language
        self.translations = self._load_translations()
        self.accessibility_config = self._load_accessibility_config()
        self.current_theme = "light"
        self.font_size = "medium"
        self.high_contrast = False
        self.reduced_motion = False
        
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation files."""
        translations = {}
        translations_dir = os.path.join(os.path.dirname(__file__), "translations")
        
        if os.path.exists(translations_dir):
            for filename in os.listdir(translations_dir):
                if filename.endswith(".json"):
                    lang_code = filename.replace(".json", "")
                    filepath = os.path.join(translations_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            translations[lang_code] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load translation file {filepath}: {e}")
        
        # Fallback to English if no translations found
        if not translations:
            translations = {
                "en": self._get_default_translations()
            }
        
        return translations
    
    def _get_default_translations(self) -> Dict[str, str]:
        """Get default English translations."""
        return {
            # Dashboard
            "dashboard_title": "GitBridge Collaboration Dashboard",
            "dashboard_subtitle": "Phase 24 - Real-time collaboration and attribution tracking",
            "total_contributors": "Total Contributors",
            "total_tasks": "Total Tasks",
            "recent_activities": "Recent Activities",
            "active_collaborations": "Active Collaborations",
            "recent_activity_feed": "Recent Activity Feed",
            "navigation": "Navigation",
            "quick_actions": "Quick Actions",
            "attribution_overview": "Attribution Overview",
            "changelog": "Changelog",
            "activity_feed": "Activity Feed",
            "diff_viewer": "Diff Viewer",
            "export_attribution": "Export Attribution",
            "export_changelog": "Export Changelog",
            "export_activity": "Export Activity",
            "dark_mode": "Dark Mode",
            "light_mode": "Light Mode",
            "connected": "Connected",
            "disconnected": "Disconnected",
            "back_to_dashboard": "Back to Dashboard",
            "no_recent_activities": "No recent activities",
            "export_success": "Data exported successfully",
            "export_failed": "Export failed",
            
            # Attribution Overview
            "attribution_overview_title": "Attribution Overview",
            "attribution_subtitle": "Track contributor contributions and task attributions",
            "contributors": "Contributors",
            "tasks_with_attributions": "Tasks with Attributions",
            "detailed_attribution_analysis": "Detailed Attribution Analysis",
            "no_contributors": "No Contributors",
            "no_contributors_message": "No contributors have been registered yet.",
            "no_tasks": "No Tasks",
            "no_tasks_message": "No tasks with attributions found.",
            "no_detailed_attributions": "No Detailed Attributions",
            "no_detailed_attributions_message": "No detailed attribution data available.",
            "contributions": "contributions",
            "created": "Created",
            "id": "ID",
            
            # Activity Types
            "task_created": "Task Created",
            "task_updated": "Task Updated",
            "task_completed": "Task Completed",
            "contribution_added": "Contribution Added",
            "revision_added": "Revision Added",
            "user_registered": "User Registered",
            
            # Accessibility
            "toggle_dark_mode": "Toggle dark mode",
            "view_attribution_overview": "View attribution overview",
            "view_changelog": "View changelog",
            "view_activity_feed": "View activity feed",
            "view_diff_viewer": "View diff viewer",
            "export_attribution_data": "Export attribution data",
            "export_changelog_data": "Export changelog data",
            "export_activity_data": "Export activity data",
            "activity_feed": "Activity feed",
            "contributors_list": "Contributors list",
            "tasks_list": "Tasks list",
            "notification": "Notification",
            "close_notification": "Close notification",
            
            # Error Messages
            "error_loading_data": "Error loading data",
            "error_exporting_data": "Error exporting data",
            "error_connection_lost": "Connection lost",
            "error_connection_restored": "Connection restored",
            
            # Success Messages
            "success_data_loaded": "Data loaded successfully",
            "success_export_completed": "Export completed successfully",
            "success_connection_established": "Connection established",
            
            # Time Formats
            "time_format": "%H:%M",
            "date_format": "%Y-%m-%d",
            "datetime_format": "%Y-%m-%d %H:%M"
        }
    
    def _load_accessibility_config(self) -> Dict[str, Any]:
        """Load accessibility configuration."""
        return {
            "aria_labels": {
                "dashboard": "GitBridge collaboration dashboard",
                "activity_feed": "Real-time activity feed",
                "contributors_list": "List of project contributors",
                "tasks_list": "List of tasks with attributions",
                "navigation_menu": "Main navigation menu",
                "quick_actions": "Quick action buttons",
                "theme_toggle": "Toggle between light and dark themes",
                "connection_status": "Current connection status",
                "export_buttons": "Data export buttons",
                "statistics_cards": "Project statistics cards"
            },
            "keyboard_shortcuts": {
                "toggle_theme": "Ctrl+T",
                "navigate_dashboard": "Ctrl+1",
                "navigate_attribution": "Ctrl+2",
                "navigate_changelog": "Ctrl+3",
                "navigate_activity": "Ctrl+4",
                "navigate_diff": "Ctrl+5",
                "export_attribution": "Ctrl+Shift+A",
                "export_changelog": "Ctrl+Shift+C",
                "export_activity": "Ctrl+Shift+F",
                "close_notification": "Escape"
            },
            "focus_indicators": {
                "color": "#667eea",
                "width": "3px",
                "style": "solid",
                "offset": "2px"
            },
            "screen_reader": {
                "announce_changes": True,
                "announce_notifications": True,
                "announce_activity_updates": True,
                "announce_connection_status": True
            }
        }
    
    def get_text(self, key: str, language: str = None) -> str:
        """Get translated text for a given key."""
        if language is None:
            language = self.language
        
        translations = self.translations.get(language, self.translations.get("en", {}))
        return translations.get(key, key)
    
    def get_aria_label(self, element: str) -> str:
        """Get ARIA label for an element."""
        return self.accessibility_config["aria_labels"].get(element, element)
    
    def get_keyboard_shortcut(self, action: str) -> str:
        """Get keyboard shortcut for an action."""
        return self.accessibility_config["keyboard_shortcuts"].get(action, "")
    
    def generate_aria_attributes(self, element_type: str, **kwargs) -> Dict[str, str]:
        """Generate ARIA attributes for an element."""
        attributes = {}
        
        if element_type == "button":
            attributes.update({
                "role": "button",
                "tabindex": "0"
            })
            if "label" in kwargs:
                attributes["aria-label"] = kwargs["label"]
            if "pressed" in kwargs:
                attributes["aria-pressed"] = str(kwargs["pressed"]).lower()
        
        elif element_type == "list":
            attributes.update({
                "role": "list",
                "aria-label": kwargs.get("label", "List")
            })
        
        elif element_type == "listitem":
            attributes.update({
                "role": "listitem",
                "tabindex": "0"
            })
        
        elif element_type == "feed":
            attributes.update({
                "role": "feed",
                "aria-label": kwargs.get("label", "Activity feed"),
                "aria-live": "polite"
            })
        
        elif element_type == "article":
            attributes.update({
                "role": "article"
            })
        
        elif element_type == "alert":
            attributes.update({
                "role": "alert",
                "aria-live": "polite"
            })
        
        elif element_type == "status":
            attributes.update({
                "role": "status",
                "aria-live": "polite"
            })
        
        elif element_type == "navigation":
            attributes.update({
                "role": "navigation",
                "aria-label": kwargs.get("label", "Navigation")
            })
        
        elif element_type == "main":
            attributes.update({
                "role": "main"
            })
        
        elif element_type == "complementary":
            attributes.update({
                "role": "complementary",
                "aria-label": kwargs.get("label", "Sidebar")
            })
        
        return attributes
    
    def generate_css_variables(self) -> Dict[str, str]:
        """Generate CSS variables for accessibility features."""
        variables = {
            "--focus-color": self.accessibility_config["focus_indicators"]["color"],
            "--focus-width": self.accessibility_config["focus_indicators"]["width"],
            "--focus-style": self.accessibility_config["focus_indicators"]["style"],
            "--focus-offset": self.accessibility_config["focus_indicators"]["offset"]
        }
        
        # High contrast mode
        if self.high_contrast:
            variables.update({
                "--text-primary": "#000000",
                "--text-secondary": "#000000",
                "--border-color": "#000000",
                "--bg-primary": "#ffffff",
                "--bg-secondary": "#ffffff"
            })
        
        # Font size adjustments
        font_sizes = {
            "small": "0.875rem",
            "medium": "1rem",
            "large": "1.125rem",
            "xlarge": "1.25rem"
        }
        variables["--font-size-base"] = font_sizes.get(self.font_size, "1rem")
        
        # Reduced motion
        if self.reduced_motion:
            variables.update({
                "--transition-duration": "0.01ms",
                "--animation-duration": "0.01ms"
            })
        
        return variables
    
    def generate_javascript_accessibility(self) -> str:
        """Generate JavaScript code for accessibility features."""
        js_code = """
        // Accessibility Manager JavaScript
        
        class AccessibilityManager {
            constructor() {
                this.currentFocus = null;
                this.notifications = [];
                this.init();
            }
            
            init() {
                this.setupKeyboardNavigation();
                this.setupFocusManagement();
                this.setupScreenReaderAnnouncements();
                this.setupNotifications();
            }
            
            setupKeyboardNavigation() {
                document.addEventListener('keydown', (e) => {
                    // Theme toggle
                    if (e.ctrlKey && e.key === 't') {
                        e.preventDefault();
                        this.toggleTheme();
                    }
                    
                    // Navigation shortcuts
                    if (e.ctrlKey) {
                        switch(e.key) {
                            case '1':
                                e.preventDefault();
                                window.location.href = '/';
                                break;
                            case '2':
                                e.preventDefault();
                                window.location.href = '/attribution';
                                break;
                            case '3':
                                e.preventDefault();
                                window.location.href = '/changelog';
                                break;
                            case '4':
                                e.preventDefault();
                                window.location.href = '/activity-feed';
                                break;
                            case '5':
                                e.preventDefault();
                                window.location.href = '/diff';
                                break;
                        }
                    }
                    
                    // Export shortcuts
                    if (e.ctrlKey && e.shiftKey) {
                        switch(e.key) {
                            case 'A':
                                e.preventDefault();
                                this.exportData('attribution');
                                break;
                            case 'C':
                                e.preventDefault();
                                this.exportData('changelog');
                                break;
                            case 'F':
                                e.preventDefault();
                                this.exportData('activity');
                                break;
                        }
                    }
                    
                    // Close notifications
                    if (e.key === 'Escape') {
                        this.closeAllNotifications();
                    }
                });
            }
            
            setupFocusManagement() {
                // Track focus changes
                document.addEventListener('focusin', (e) => {
                    this.currentFocus = e.target;
                    this.announceFocus(e.target);
                });
                
                // Ensure focus is visible
                document.addEventListener('focus', (e) => {
                    e.target.style.outline = 'var(--focus-width) var(--focus-style) var(--focus-color)';
                    e.target.style.outlineOffset = 'var(--focus-offset)';
                });
                
                document.addEventListener('blur', (e) => {
                    e.target.style.outline = '';
                    e.target.style.outlineOffset = '';
                });
            }
            
            setupScreenReaderAnnouncements() {
                // Create announcement region
                const announcementRegion = document.createElement('div');
                announcementRegion.setAttribute('aria-live', 'polite');
                announcementRegion.setAttribute('aria-atomic', 'true');
                announcementRegion.className = 'sr-only';
                document.body.appendChild(announcementRegion);
                
                this.announcementRegion = announcementRegion;
            }
            
            setupNotifications() {
                // Create notification container
                const notificationContainer = document.createElement('div');
                notificationContainer.setAttribute('role', 'log');
                notificationContainer.setAttribute('aria-live', 'polite');
                notificationContainer.setAttribute('aria-label', 'Notifications');
                notificationContainer.className = 'notification-container sr-only';
                document.body.appendChild(notificationContainer);
                
                this.notificationContainer = notificationContainer;
            }
            
            announce(message, priority = 'polite') {
                if (this.announcementRegion) {
                    this.announcementRegion.textContent = message;
                    setTimeout(() => {
                        this.announcementRegion.textContent = '';
                    }, 1000);
                }
                
                // Also log to console for debugging
                console.log(`[Accessibility] ${message}`);
            }
            
            announceFocus(element) {
                const label = element.getAttribute('aria-label') || 
                             element.getAttribute('title') || 
                             element.textContent || 
                             element.tagName.toLowerCase();
                
                this.announce(`Focused on ${label}`);
            }
            
            addNotification(message, type = 'info') {
                const notification = {
                    id: Date.now(),
                    message,
                    type,
                    timestamp: new Date()
                };
                
                this.notifications.push(notification);
                
                // Announce to screen reader
                this.announce(`${type} notification: ${message}`);
                
                // Add to notification container
                if (this.notificationContainer) {
                    const notificationElement = document.createElement('div');
                    notificationElement.setAttribute('role', 'alert');
                    notificationElement.textContent = `${type}: ${message}`;
                    this.notificationContainer.appendChild(notificationElement);
                    
                    // Remove after 5 seconds
                    setTimeout(() => {
                        if (notificationElement.parentNode) {
                            notificationElement.parentNode.removeChild(notificationElement);
                        }
                    }, 5000);
                }
                
                return notification.id;
            }
            
            closeAllNotifications() {
                this.notifications = [];
                if (this.notificationContainer) {
                    this.notificationContainer.innerHTML = '';
                }
                
                // Close visible notifications
                const visibleNotifications = document.querySelectorAll('.notification.show');
                visibleNotifications.forEach(notification => {
                    notification.classList.remove('show');
                });
            }
            
            toggleTheme() {
                const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                
                this.announce(`Switched to ${newTheme} theme`);
            }
            
            exportData(type) {
                this.announce(`Exporting ${type} data...`);
                
                fetch(`/api/mas/export/${type}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'exported') {
                            this.announce(`${type} data exported successfully`);
                            this.addNotification(`${type} data exported successfully`, 'success');
                        } else {
                            this.announce(`Export failed: ${data.error}`);
                            this.addNotification(`Export failed: ${data.error}`, 'error');
                        }
                    })
                    .catch(error => {
                        this.announce(`Export failed: ${error.message}`);
                        this.addNotification(`Export failed: ${error.message}`, 'error');
                    });
            }
            
            // Utility methods
            isScreenReaderActive() {
                return window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
                       document.querySelector('[aria-live]') !== null;
            }
            
            getAccessibilityInfo() {
                return {
                    theme: document.documentElement.getAttribute('data-theme') || 'light',
                    fontSize: getComputedStyle(document.documentElement).getPropertyValue('--font-size-base'),
                    highContrast: this.high_contrast,
                    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
                    screenReader: this.isScreenReaderActive()
                };
            }
        }
        
        // Initialize accessibility manager
        const accessibilityManager = new AccessibilityManager();
        window.accessibilityManager = accessibilityManager;
        """
        
        return js_code
    
    def generate_html_attributes(self, element_type: str, **kwargs) -> str:
        """Generate HTML attributes string for an element."""
        attributes = self.generate_aria_attributes(element_type, **kwargs)
        
        if not attributes:
            return ""
        
        return " " + " ".join([f'{key}="{value}"' for key, value in attributes.items()])
    
    def get_language_meta_tags(self) -> str:
        """Generate language meta tags for HTML head."""
        return f"""
        <meta http-equiv="Content-Language" content="{self.language}">
        <meta name="language" content="{self.language}">
        <html lang="{self.language}">
        """
    
    def get_accessibility_meta_tags(self) -> str:
        """Generate accessibility meta tags for HTML head."""
        return """
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="GitBridge Collaboration Dashboard - Real-time collaboration and attribution tracking">
        <meta name="keywords" content="collaboration, attribution, git, development, tracking">
        <meta name="author" content="GitBridge Team">
        <meta name="robots" content="index, follow">
        <meta name="theme-color" content="#667eea">
        <meta name="color-scheme" content="light dark">
        """
    
    def get_css_accessibility_styles(self) -> str:
        """Generate CSS styles for accessibility features."""
        variables = self.generate_css_variables()
        css_variables = "\n".join([f"    {key}: {value};" for key, value in variables.items()])
        
        return f"""
        :root {{
{css_variables}
        }}
        
        /* Screen reader only content */
        .sr-only {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}
        
        /* Focus styles */
        *:focus {{
            outline: var(--focus-width) var(--focus-style) var(--focus-color) !important;
            outline-offset: var(--focus-offset) !important;
        }}
        
        /* Skip links */
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1000;
        }}
        
        .skip-link:focus {{
            top: 6px;
        }}
        
        /* High contrast mode */
        @media (prefers-contrast: high) {{
            :root {{
                --text-primary: #000000;
                --text-secondary: #000000;
                --border-color: #000000;
                --bg-primary: #ffffff;
                --bg-secondary: #ffffff;
            }}
        }}
        
        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        
        /* Large text support */
        @media (prefers-reduced-motion: no-preference) {{
            .large-text {{
                font-size: 1.2em;
                line-height: 1.6;
            }}
        }}
        
        /* Notification container */
        .notification-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 1px;
            height: 1px;
            overflow: hidden;
            z-index: -1;
        }}
        """

class InternationalizationManager:
    """Manages internationalization features."""
    
    def __init__(self, default_language: str = "en"):
        """Initialize internationalization manager."""
        self.default_language = default_language
        self.supported_languages = ["en", "es", "fr", "de", "ja", "zh", "ko"]
        self.current_language = default_language
        
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages with names."""
        language_names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어"
        }
        
        return [
            {"code": lang, "name": language_names.get(lang, lang)}
            for lang in self.supported_languages
        ]
    
    def format_date(self, date: datetime, format_type: str = "default", language: str = None) -> str:
        """Format date according to language preferences."""
        if language is None:
            language = self.current_language
        
        # Language-specific date formats
        date_formats = {
            "en": {
                "short": "%m/%d/%Y",
                "default": "%B %d, %Y",
                "long": "%A, %B %d, %Y",
                "time": "%H:%M",
                "datetime": "%B %d, %Y at %H:%M"
            },
            "es": {
                "short": "%d/%m/%Y",
                "default": "%d de %B de %Y",
                "long": "%A, %d de %B de %Y",
                "time": "%H:%M",
                "datetime": "%d de %B de %Y a las %H:%M"
            },
            "fr": {
                "short": "%d/%m/%Y",
                "default": "%d %B %Y",
                "long": "%A %d %B %Y",
                "time": "%H:%M",
                "datetime": "%d %B %Y à %H:%M"
            },
            "de": {
                "short": "%d.%m.%Y",
                "default": "%d. %B %Y",
                "long": "%A, %d. %B %Y",
                "time": "%H:%M",
                "datetime": "%d. %B %Y um %H:%M"
            },
            "ja": {
                "short": "%Y年%m月%d日",
                "default": "%Y年%m月%d日",
                "long": "%Y年%m月%d日 %A",
                "time": "%H:%M",
                "datetime": "%Y年%m月%d日 %H:%M"
            },
            "zh": {
                "short": "%Y年%m月%d日",
                "default": "%Y年%m月%d日",
                "long": "%Y年%m月%d日 %A",
                "time": "%H:%M",
                "datetime": "%Y年%m月%d日 %H:%M"
            },
            "ko": {
                "short": "%Y년 %m월 %d일",
                "default": "%Y년 %m월 %d일",
                "long": "%Y년 %m월 %d일 %A",
                "time": "%H:%M",
                "datetime": "%Y년 %m월 %d일 %H:%M"
            }
        }
        
        format_string = date_formats.get(language, date_formats["en"]).get(format_type, "%Y-%m-%d")
        return date.strftime(format_string)
    
    def get_number_format(self, number: float, language: str = None) -> str:
        """Format number according to language preferences."""
        if language is None:
            language = self.current_language
        
        # Language-specific number formats
        number_formats = {
            "en": {"decimal": ".", "thousands": ","},
            "es": {"decimal": ",", "thousands": "."},
            "fr": {"decimal": ",", "thousands": " "},
            "de": {"decimal": ",", "thousands": "."},
            "ja": {"decimal": ".", "thousands": ","},
            "zh": {"decimal": ".", "thousands": ","},
            "ko": {"decimal": ".", "thousands": ","}
        }
        
        format_config = number_formats.get(language, number_formats["en"])
        
        # Simple number formatting (for more complex formatting, use locale module)
        if isinstance(number, int):
            return f"{number:,}".replace(",", format_config["thousands"])
        else:
            return f"{number:.2f}".replace(".", format_config["decimal"])

def create_accessibility_manager(language: str = "en") -> AccessibilityManager:
    """Create and configure accessibility manager."""
    return AccessibilityManager(language)

def create_i18n_manager(default_language: str = "en") -> InternationalizationManager:
    """Create and configure internationalization manager."""
    return InternationalizationManager(default_language) 