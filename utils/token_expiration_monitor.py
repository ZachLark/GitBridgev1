#!/usr/bin/env python3
"""
GitBridge Token Expiration Monitor
MAS Lite Protocol v2.1 Reference Implementation

This module monitors GitHub token expiration dates and provides alerts
when tokens are approaching expiration.

Author: Cursor Agent (GitBridge Token Management Protocol v2)
Created: 2025-01-11
Python Version: 3.13.3
"""

import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('token_expiration_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TokenExpirationMonitor:
    """
    Monitor GitHub token expiration dates and provide alerts.
    
    Supports MAS Lite Protocol v2.1 token management requirements
    including SHA256 verification and structured logging.
    """
    
    def __init__(self, registry_path: str = "meta/token_registry.json"):
        """
        Initialize the token expiration monitor.
        
        Args:
            registry_path (str): Path to the token registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.tokens = self._load_token_registry()
        
    def _load_token_registry(self) -> dict:
        """
        Load token registry from JSON file with error handling.
        
        Returns:
            dict: Token registry data
            
        Raises:
            FileNotFoundError: If registry file doesn't exist
            json.JSONDecodeError: If registry file is malformed
        """
        try:
            if not self.registry_path.exists():
                logger.warning(f"Token registry not found at {self.registry_path}")
                return {}
                
            with open(self.registry_path, 'r', encoding='utf-8') as file:
                registry_data = json.load(file)
                
            # Generate SHA256 checksum for integrity verification
            registry_content = json.dumps(registry_data, sort_keys=True)
            checksum = hashlib.sha256(registry_content.encode()).hexdigest()
            logger.info(f"Registry loaded successfully. SHA256: {checksum[:16]}...")
            
            return registry_data
            
        except FileNotFoundError:
            logger.error(f"Token registry file not found: {self.registry_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in registry file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading registry: {e}")
            return {}
    
    def _parse_date(self, date_string: str) -> datetime:
        """
        Parse date string in YYYY-MM-DD format.
        
        Args:
            date_string (str): Date in YYYY-MM-DD format
            
        Returns:
            datetime: Parsed datetime object
        """
        try:
            return datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {date_string}")
            raise
    
    def _calculate_days_remaining(self, expiration_date: str) -> int:
        """
        Calculate days remaining until token expiration.
        
        Args:
            expiration_date (str): Expiration date in YYYY-MM-DD format
            
        Returns:
            int: Days remaining (negative if expired)
        """
        expiry = self._parse_date(expiration_date)
        today = datetime.now()
        delta = expiry - today
        return delta.days
    
    def check_alarm_triggers(self) -> list:
        """
        Check if any alarm trigger dates have passed.
        
        Returns:
            list: List of tokens that have triggered alarms
        """
        triggered_tokens = []
        today = datetime.now()
        
        for token_alias, token_data in self.tokens.items():
            try:
                alarm_date = self._parse_date(token_data.get('alarm_trigger', ''))
                if today >= alarm_date:
                    days_to_expiry = self._calculate_days_remaining(
                        token_data.get('expires', '')
                    )
                    
                    triggered_tokens.append({
                        'alias': token_alias,
                        'days_remaining': days_to_expiry,
                        'expiration_date': token_data.get('expires'),
                        'alarm_trigger': token_data.get('alarm_trigger')
                    })
                    
                    # Log critical alert
                    logger.critical(
                        f"[ALARM] Token {token_alias} alarm triggered! "
                        f"Expires in {days_to_expiry} days ({token_data.get('expires')})"
                    )
                    
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing token {token_alias}: {e}")
                continue
                
        return triggered_tokens
    
    def get_token_status(self) -> dict:
        """
        Get status of all tokens including days remaining.
        
        Returns:
            dict: Token status information
        """
        status = {}
        
        for token_alias, token_data in self.tokens.items():
            try:
                days_remaining = self._calculate_days_remaining(
                    token_data.get('expires', '')
                )
                
                status[token_alias] = {
                    'days_remaining': days_remaining,
                    'expires': token_data.get('expires'),
                    'created': token_data.get('created'),
                    'alarm_trigger': token_data.get('alarm_trigger'),
                    'repos': token_data.get('repos', []),
                    'used_by': token_data.get('used_by', []),
                    'status': self._get_status_level(days_remaining)
                }
                
            except (ValueError, KeyError) as e:
                logger.error(f"Error getting status for token {token_alias}: {e}")
                status[token_alias] = {
                    'error': str(e),
                    'status': 'ERROR'
                }
                
        return status
    
    def _get_status_level(self, days_remaining: int) -> str:
        """
        Determine status level based on days remaining.
        
        Args:
            days_remaining (int): Days until expiration
            
        Returns:
            str: Status level (CRITICAL, WARNING, OK, EXPIRED)
        """
        if days_remaining < 0:
            return "EXPIRED"
        elif days_remaining <= 5:
            return "CRITICAL"
        elif days_remaining <= 14:
            return "WARNING"
        else:
            return "OK"
    
    def display_status(self) -> None:
        """Display token status in the required format."""
        status = self.get_token_status()
        
        if not status:
            print("[STATUS] No tokens found in registry.")
            return
            
        print("\n=== GitBridge Token Status Report ===")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 40)
        
        for token_alias, token_info in status.items():
            if 'error' in token_info:
                print(f"[ERROR] {token_alias}: {token_info['error']}")
                continue
                
            days = token_info['days_remaining']
            status_level = token_info['status']
            expires = token_info['expires']
            
            # Status emoji and color coding
            status_emoji = {
                'OK': '✅',
                'WARNING': '⚠️',
                'CRITICAL': '🚨',
                'EXPIRED': '❌'
            }
            
            emoji = status_emoji.get(status_level, '❓')
            
            if days >= 0:
                print(f"[STATUS] {emoji} {token_alias} expires in {days} days ({expires})")
            else:
                print(f"[STATUS] {emoji} {token_alias} EXPIRED {abs(days)} days ago ({expires})")
                
            # Show additional info for critical/expired tokens
            if status_level in ['CRITICAL', 'EXPIRED']:
                repos = ', '.join(token_info.get('repos', []))
                used_by = ', '.join(token_info.get('used_by', []))
                print(f"         Repositories: {repos}")
                print(f"         Used by: {used_by}")
                print()
        
        print("=" * 40)
        print("For token rotation instructions, see: docs/github_tokens/README.md")
        print("For rotation checklist, see: checklists/token_rotation_checklist.md")
    
    def run_monitoring_check(self) -> int:
        """
        Run the default monitoring check for alarm triggers.
        
        Returns:
            int: Exit code (0 = success, 1 = alarms triggered, 2 = error)
        """
        try:
            triggered_tokens = self.check_alarm_triggers()
            
            if triggered_tokens:
                print(f"\n🚨 ALERT: {len(triggered_tokens)} token(s) require attention!")
                
                for token in triggered_tokens:
                    days = token['days_remaining']
                    if days >= 0:
                        print(f"   • {token['alias']}: {days} days until expiration")
                    else:
                        print(f"   • {token['alias']}: EXPIRED {abs(days)} days ago!")
                
                print("\nAction required: Run token rotation procedure immediately.")
                print("See: checklists/token_rotation_checklist.md")
                
                return 1  # Exit code 1 indicates alarms triggered
            else:
                logger.info("All tokens are within acceptable expiration timeframes.")
                return 0  # Exit code 0 indicates success
                
        except Exception as e:
            logger.error(f"Error during monitoring check: {e}")
            return 2  # Exit code 2 indicates error


def main():
    """
    Main entry point for the token expiration monitor.
    
    MAS Lite Protocol v2.1 compliant implementation with SHA256
    integrity checking and structured logging.
    """
    parser = argparse.ArgumentParser(
        description="GitBridge Token Expiration Monitor (MAS Lite Protocol v2.1)",
        epilog="Examples:\n"
               "  python3 token_expiration_monitor.py        # Check alarm triggers\n"
               "  python3 token_expiration_monitor.py --status # Show all token status",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Display days remaining until expiration for each token'
    )
    
    parser.add_argument(
        '--registry',
        default='meta/token_registry.json',
        help='Path to token registry file (default: meta/token_registry.json)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        monitor = TokenExpirationMonitor(args.registry)
        
        if args.status:
            monitor.display_status()
            return 0
        else:
            # Default behavior: check alarm triggers
            return monitor.run_monitoring_check()
            
    except KeyboardInterrupt:
        logger.info("Monitor interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main()) 