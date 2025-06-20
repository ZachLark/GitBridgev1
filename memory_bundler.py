#!/usr/bin/env python3
"""
GitBridge Memory Bundling and Export System
Phase: GBP21
Part: P21P8
Step: P21P8S4
Task: P21P8S4T1 - Memory Bundling Implementation

Export/import a complete bundle of memory, plugin state, and routing logs for full reproducibility.

Author: GitBridge Development Team
Date: 2025-06-19
Schema: [P21P8 Schema]
"""

import json
import logging
import argparse
import zipfile
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class MemoryBundle:
    """Represents a complete memory bundle for export/import."""
    bundle_id: str
    created_at: datetime
    version: str = "1.0.0"
    description: str = ""
    components: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None

class MemoryBundler:
    """
    Memory bundling system for complete state export/import.
    
    Phase: GBP21
    Part: P21P8
    Step: P21P8S4
    Task: P21P8S4T1 - Core Implementation
    
    Features:
    - Export complete system state (memory, plugins, logs)
    - Import and restore system state
    - Bundle validation and checksums
    - Version compatibility checking
    """
    
    def __init__(self, base_path: str = "."):
        """
        Initialize memory bundler.
        
        Args:
            base_path: Base path for finding system components
        """
        self.base_path = Path(base_path)
        self.bundle_counter = 0
        
        logger.info(f"[P21P8S4T1] MemoryBundler initialized with base path: {base_path}")
        
    def create_bundle(
        self,
        description: str = "",
        include_memory: bool = True,
        include_plugins: bool = True,
        include_logs: bool = True,
        include_configs: bool = True
    ) -> MemoryBundle:
        """
        Create a complete memory bundle.
        
        Args:
            description: Description of the bundle
            include_memory: Include memory exports
            include_plugins: Include plugin state
            include_logs: Include audit logs
            include_configs: Include configuration files
            
        Returns:
            MemoryBundle: Complete bundle with all components
        """
        self.bundle_counter += 1
        bundle_id = f"bundle_{self.bundle_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        bundle = MemoryBundle(
            bundle_id=bundle_id,
            created_at=datetime.now(timezone.utc),
            description=description
        )
        
        # Collect components
        components = {}
        
        if include_memory:
            components['memory'] = self._collect_memory_data()
            
        if include_plugins:
            components['plugins'] = self._collect_plugin_data()
            
        if include_logs:
            components['logs'] = self._collect_log_data()
            
        if include_configs:
            components['configs'] = self._collect_config_data()
            
        bundle.components = components
        
        # Calculate checksum
        bundle.checksum = self._calculate_bundle_checksum(bundle)
        
        logger.info(f"[P21P8S4T1] Created bundle {bundle_id} with {len(components)} components")
        return bundle
        
    def _collect_memory_data(self) -> Dict[str, Any]:
        """Collect memory data from various sources."""
        memory_data = {}
        
        # Shared memory export
        shared_memory_path = self.base_path / "shared_memory_export.json"
        if shared_memory_path.exists():
            try:
                with open(shared_memory_path, 'r') as f:
                    memory_data['shared_memory'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load shared memory: {e}")
                
        # Async memory storage
        async_memory_path = self.base_path / "memory_storage"
        if async_memory_path.exists():
            memory_data['async_memory'] = {
                'storage_path': str(async_memory_path),
                'node_count': len(list(async_memory_path.glob("nodes/*.json")))
            }
            
        # Integration memory export
        integration_memory_path = self.base_path / "integration_memory_export.json"
        if integration_memory_path.exists():
            try:
                with open(integration_memory_path, 'r') as f:
                    memory_data['integration_memory'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load integration memory: {e}")
                
        return memory_data
        
    def _collect_plugin_data(self) -> Dict[str, Any]:
        """Collect plugin state and configuration."""
        plugin_data = {}
        
        # Plugin configuration
        plugin_config_path = self.base_path / "plugin_config.json"
        if plugin_config_path.exists():
            try:
                with open(plugin_config_path, 'r') as f:
                    plugin_data['config'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load plugin config: {e}")
                
        # Plugin directory structure
        plugin_dir = self.base_path / "plugins"
        if plugin_dir.exists():
            plugin_data['directory'] = {
                'path': str(plugin_dir),
                'structure': self._get_directory_structure(plugin_dir)
            }
            
        return plugin_data
        
    def _collect_log_data(self) -> Dict[str, Any]:
        """Collect audit logs and routing logs."""
        log_data = {}
        
        # Audit logs database
        audit_db_path = self.base_path / "audit_logs.db"
        if audit_db_path.exists():
            log_data['audit_db'] = {
                'path': str(audit_db_path),
                'size_bytes': audit_db_path.stat().st_size
            }
            
        # Routing logs
        routing_logs_path = self.base_path / "routing_logs.json"
        if routing_logs_path.exists():
            try:
                with open(routing_logs_path, 'r') as f:
                    log_data['routing_logs'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load routing logs: {e}")
                
        # Attribution logs
        attribution_logs_path = self.base_path / "attribution_log.json"
        if attribution_logs_path.exists():
            try:
                with open(attribution_logs_path, 'r') as f:
                    log_data['attribution_logs'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load attribution logs: {e}")
                
        return log_data
        
    def _collect_config_data(self) -> Dict[str, Any]:
        """Collect configuration files."""
        config_data = {}
        
        # Roles configuration
        roles_config_path = self.base_path / "roles_config.json"
        if roles_config_path.exists():
            try:
                with open(roles_config_path, 'r') as f:
                    config_data['roles'] = json.load(f)
            except Exception as e:
                logger.warning(f"[P21P8S4T1] Failed to load roles config: {e}")
                
        # Other configuration files
        config_files = [
            "plugin_config.json",
            "smart_router_config.json",
            "monitoring_config.json"
        ]
        
        for config_file in config_files:
            config_path = self.base_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data[config_file.replace('.json', '')] = json.load(f)
                except Exception as e:
                    logger.warning(f"[P21P8S4T1] Failed to load {config_file}: {e}")
                    
        return config_data
        
    def _get_directory_structure(self, directory: Path) -> Dict[str, Any]:
        """Get directory structure recursively."""
        structure = {}
        
        for item in directory.iterdir():
            if item.is_file():
                structure[item.name] = {
                    'type': 'file',
                    'size_bytes': item.stat().st_size
                }
            elif item.is_dir():
                structure[item.name] = {
                    'type': 'directory',
                    'contents': self._get_directory_structure(item)
                }
                
        return structure
        
    def _calculate_bundle_checksum(self, bundle: MemoryBundle) -> str:
        """Calculate checksum for bundle validation."""
        bundle_data = asdict(bundle)
        bundle_data['checksum'] = None  # Exclude checksum from calculation
        
        data_string = json.dumps(bundle_data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
        
    def export_bundle(self, bundle: MemoryBundle, output_path: str) -> bool:
        """
        Export bundle to file (JSON or ZIP).
        
        Args:
            bundle: Memory bundle to export
            output_path: Path to output file
            
        Returns:
            bool: True if export successful
        """
        try:
            output_path = Path(output_path)
            
            if output_path.suffix.lower() == '.zip':
                return self._export_bundle_zip(bundle, output_path)
            else:
                return self._export_bundle_json(bundle, output_path)
                
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to export bundle: {e}")
            return False
            
    def _export_bundle_json(self, bundle: MemoryBundle, output_path: Path) -> bool:
        """Export bundle as JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(asdict(bundle), f, indent=2, default=str)
            logger.info(f"[P21P8S4T1] Exported bundle to {output_path}")
            return True
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to export JSON bundle: {e}")
            return False
            
    def _export_bundle_zip(self, bundle: MemoryBundle, output_path: Path) -> bool:
        """Export bundle as ZIP file with all data."""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add bundle metadata
                zipf.writestr('bundle.json', json.dumps(asdict(bundle), indent=2, default=str))
                
                # Add actual files
                self._add_files_to_zip(zipf, self.base_path)
                
            logger.info(f"[P21P8S4T1] Exported bundle to {output_path}")
            return True
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to export ZIP bundle: {e}")
            return False
            
    def _add_files_to_zip(self, zipf: zipfile.ZipFile, base_path: Path):
        """Add relevant files to ZIP archive."""
        relevant_extensions = {'.json', '.db', '.py', '.md', '.txt'}
        relevant_files = {
            'shared_memory_export.json',
            'integration_memory_export.json',
            'routing_logs.json',
            'attribution_log.json',
            'roles_config.json',
            'plugin_config.json',
            'audit_logs.db'
        }
        
        for file_path in base_path.rglob('*'):
            if file_path.is_file():
                # Include files with relevant extensions or specific names
                if (file_path.suffix in relevant_extensions or 
                    file_path.name in relevant_files):
                    try:
                        zipf.write(file_path, file_path.relative_to(base_path))
                    except Exception as e:
                        logger.warning(f"[P21P8S4T1] Failed to add {file_path} to ZIP: {e}")
                        
    def import_bundle(self, bundle_path: str, restore_path: str = None) -> Optional[MemoryBundle]:
        """
        Import bundle from file.
        
        Args:
            bundle_path: Path to bundle file
            restore_path: Path to restore files (for ZIP bundles)
            
        Returns:
            MemoryBundle or None if import failed
        """
        try:
            bundle_path = Path(bundle_path)
            
            if bundle_path.suffix.lower() == '.zip':
                return self._import_bundle_zip(bundle_path, restore_path)
            else:
                return self._import_bundle_json(bundle_path)
                
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to import bundle: {e}")
            return None
            
    def _import_bundle_json(self, bundle_path: Path) -> Optional[MemoryBundle]:
        """Import bundle from JSON file."""
        try:
            with open(bundle_path, 'r') as f:
                bundle_data = json.load(f)
                
            # Reconstruct bundle
            bundle = MemoryBundle(
                bundle_id=bundle_data['bundle_id'],
                created_at=datetime.fromisoformat(bundle_data['created_at']),
                version=bundle_data.get('version', '1.0.0'),
                description=bundle_data.get('description', ''),
                components=bundle_data.get('components', {}),
                metadata=bundle_data.get('metadata', {}),
                checksum=bundle_data.get('checksum')
            )
            
            # Validate checksum
            if bundle.checksum and bundle.checksum != self._calculate_bundle_checksum(bundle):
                logger.warning("[P21P8S4T1] Bundle checksum validation failed")
                
            logger.info(f"[P21P8S4T1] Imported bundle {bundle.bundle_id}")
            return bundle
            
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to import JSON bundle: {e}")
            return None
            
    def _import_bundle_zip(self, bundle_path: Path, restore_path: str = None) -> Optional[MemoryBundle]:
        """Import bundle from ZIP file."""
        try:
            restore_path = Path(restore_path) if restore_path else self.base_path
            
            with zipfile.ZipFile(bundle_path, 'r') as zipf:
                # Extract bundle metadata
                bundle_json = zipf.read('bundle.json')
                bundle_data = json.loads(bundle_json)
                
                # Reconstruct bundle
                bundle = MemoryBundle(
                    bundle_id=bundle_data['bundle_id'],
                    created_at=datetime.fromisoformat(bundle_data['created_at']),
                    version=bundle_data.get('version', '1.0.0'),
                    description=bundle_data.get('description', ''),
                    components=bundle_data.get('components', {}),
                    metadata=bundle_data.get('metadata', {}),
                    checksum=bundle_data.get('checksum')
                )
                
                # Extract files
                zipf.extractall(restore_path)
                
            logger.info(f"[P21P8S4T1] Imported bundle {bundle.bundle_id} to {restore_path}")
            return bundle
            
        except Exception as e:
            logger.error(f"[P21P8S4T1] Failed to import ZIP bundle: {e}")
            return None
            
    def validate_bundle(self, bundle: MemoryBundle) -> Dict[str, Any]:
        """
        Validate bundle integrity and completeness.
        
        Args:
            bundle: Memory bundle to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'valid': True,
            'checksum_valid': True,
            'components_present': [],
            'warnings': [],
            'errors': []
        }
        
        # Check checksum
        if bundle.checksum:
            calculated_checksum = self._calculate_bundle_checksum(bundle)
            if bundle.checksum != calculated_checksum:
                validation['checksum_valid'] = False
                validation['valid'] = False
                validation['errors'].append("Checksum validation failed")
                
        # Check components
        expected_components = ['memory', 'plugins', 'logs', 'configs']
        for component in expected_components:
            if component in bundle.components:
                validation['components_present'].append(component)
            else:
                validation['warnings'].append(f"Component '{component}' not present")
                
        # Check version compatibility
        if bundle.version != "1.0.0":
            validation['warnings'].append(f"Bundle version {bundle.version} may not be compatible")
            
        return validation

def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description='GitBridge Memory Bundler')
    parser.add_argument('--create', action='store_true', help='Create a new bundle')
    parser.add_argument('--export', help='Export bundle to specified file')
    parser.add_argument('--import', dest='import_path', help='Import bundle from specified file')
    parser.add_argument('--validate', help='Validate bundle from specified file')
    parser.add_argument('--description', help='Bundle description')
    parser.add_argument('--format', choices=['json', 'zip'], default='json', help='Export format')
    parser.add_argument('--restore-path', help='Path to restore files (for ZIP import)')
    
    args = parser.parse_args()
    
    bundler = MemoryBundler()
    
    if args.create:
        bundle = bundler.create_bundle(description=args.description or "")
        print(f"✅ Created bundle: {bundle.bundle_id}")
        print(f"   Description: {bundle.description}")
        print(f"   Components: {list(bundle.components.keys())}")
        print(f"   Checksum: {bundle.checksum[:16]}...")
        
        if args.export:
            success = bundler.export_bundle(bundle, args.export)
            if success:
                print(f"✅ Bundle exported to {args.export}")
            else:
                print("❌ Failed to export bundle")
                
    elif args.import_path:
        bundle = bundler.import_bundle(args.import_path, args.restore_path)
        if bundle:
            print(f"✅ Imported bundle: {bundle.bundle_id}")
            print(f"   Created: {bundle.created_at}")
            print(f"   Components: {list(bundle.components.keys())}")
        else:
            print("❌ Failed to import bundle")
            
    elif args.validate:
        bundle = bundler.import_bundle(args.validate)
        if bundle:
            validation = bundler.validate_bundle(bundle)
            print(f"📋 Bundle validation results:")
            print(f"   Valid: {validation['valid']}")
            print(f"   Checksum valid: {validation['checksum_valid']}")
            print(f"   Components: {validation['components_present']}")
            if validation['warnings']:
                print(f"   Warnings: {validation['warnings']}")
            if validation['errors']:
                print(f"   Errors: {validation['errors']}")
        else:
            print("❌ Failed to load bundle for validation")
            
    else:
        # Demo mode
        print("🔍 Demo mode - creating sample bundle")
        bundle = bundler.create_bundle("Demo bundle for testing")
        print(f"✅ Created demo bundle: {bundle.bundle_id}")

if __name__ == "__main__":
    main() 