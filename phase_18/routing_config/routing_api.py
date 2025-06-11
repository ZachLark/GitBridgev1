# P18P7S2 – Flask Hot Reload Handler

"""
GitBridge Phase 18P7 - Routing Configuration API with Hot Reload

This module implements Flask endpoints for managing AI routing configurations
with hot reload capabilities, validation, and comprehensive logging.

Author: GitBridge MAS Integration Team
Phase: 18P7 - Routing Configurator
MAS Lite Protocol: v2.1 Compliance
"""

import json
import time
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from flask import Flask, request, jsonify, Response
from dataclasses import asdict

# Import our routing loader
from routing_loader import RoutingConfigLoader, RoutingConfigValidationResult

# Global variables for hot reload management
app = Flask(__name__)
config_loader = None
reload_lock = threading.Lock()
reload_history = []
active_config_hash = None

# Initialize configuration loader
def initialize_loader():
    """Initialize the routing configuration loader"""
    global config_loader
    config_loader = RoutingConfigLoader()
    
    # Load initial configuration
    config, validation_result = config_loader.load_config()
    if validation_result.is_valid:
        print("✅ Initial routing configuration loaded successfully")
    else:
        print("⚠️  Initial routing configuration has validation issues")
        for error in validation_result.errors:
            print(f"   - {error}")


def generate_reload_uid() -> str:
    """Generate unique identifier for reload operations"""
    timestamp = datetime.now(timezone.utc).isoformat()
    unique_string = f"reload_{timestamp}_{hash(time.time())}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


def log_reload_event(reload_uid: str, event_type: str, details: Dict[str, Any]) -> None:
    """Log reload events with structured data"""
    global reload_history
    
    log_entry = {
        "reload_uid": reload_uid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
        "mas_lite_protocol": "v2.1"
    }
    
    # Add to history (keep last 100 entries)
    reload_history.append(log_entry)
    if len(reload_history) > 100:
        reload_history.pop(0)
    
    # Log to console
    print(f"🔄 [{reload_uid}] {event_type}: {details.get('summary', 'No summary')}")


@app.route('/reload-routing', methods=['POST'])
def reload_routing_config():
    """
    Hot reload endpoint for routing configuration.
    
    Detects file changes, validates configuration, and updates in-memory config.
    Logs all operations with unique UID tracking.
    """
    global config_loader, active_config_hash
    
    reload_uid = generate_reload_uid()
    
    # Log reload request
    log_reload_event(reload_uid, "RELOAD_REQUESTED", {
        "summary": "Hot reload request received",
        "request_ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    })
    
    try:
        with reload_lock:
            if not config_loader:
                error_msg = "Configuration loader not initialized"
                log_reload_event(reload_uid, "RELOAD_FAILED", {
                    "summary": error_msg,
                    "error": error_msg
                })
                return jsonify({
                    "success": False,
                    "reload_uid": reload_uid,
                    "error": error_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 500
            
            # Check if file has changed
            if not config_loader.has_file_changed():
                log_reload_event(reload_uid, "RELOAD_SKIPPED", {
                    "summary": "Configuration file unchanged",
                    "current_checksum": config_loader.file_checksum
                })
                return jsonify({
                    "success": True,
                    "reload_uid": reload_uid,
                    "message": "Configuration file unchanged, no reload needed",
                    "current_checksum": config_loader.file_checksum,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Store previous configuration hash
            previous_hash = active_config_hash
            
            # Load and validate new configuration
            log_reload_event(reload_uid, "VALIDATION_STARTED", {
                "summary": "Starting configuration validation",
                "config_file": str(config_loader.config_path)
            })
            
            config, validation_result = config_loader.load_config(force_reload=True)
            
            if not validation_result.is_valid:
                # Validation failed - log errors and reject reload
                log_reload_event(reload_uid, "VALIDATION_FAILED", {
                    "summary": f"Configuration validation failed with {len(validation_result.errors)} errors",
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                    "circular_references": validation_result.circular_references,
                    "missing_models": validation_result.missing_models
                })
                
                return jsonify({
                    "success": False,
                    "reload_uid": reload_uid,
                    "error": "Configuration validation failed",
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                    "circular_references": validation_result.circular_references,
                    "missing_models": validation_result.missing_models,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }), 400
            
            # Validation passed - update active configuration
            new_config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()
            active_config_hash = new_config_hash
            
            # Generate configuration summary
            config_summary = config_loader.export_config_summary()
            
            log_reload_event(reload_uid, "RELOAD_SUCCESS", {
                "summary": f"Configuration reloaded successfully",
                "previous_hash": previous_hash,
                "new_hash": new_config_hash,
                "total_policies": config_summary.get("total_policies", 0),
                "enabled_policies": config_summary.get("enabled_policies", 0),
                "total_models": config_summary.get("total_models", 0),
                "file_checksum": config_loader.file_checksum
            })
            
            return jsonify({
                "success": True,
                "reload_uid": reload_uid,
                "message": "Configuration reloaded successfully",
                "config_summary": {
                    "total_policies": config_summary.get("total_policies", 0),
                    "enabled_policies": config_summary.get("enabled_policies", 0),
                    "total_models": config_summary.get("total_models", 0),
                    "available_routes": list(config_summary.get("policies", {}).keys())
                },
                "validation_warnings": validation_result.warnings,
                "previous_hash": previous_hash,
                "new_hash": new_config_hash,
                "file_checksum": config_loader.file_checksum,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    except Exception as e:
        error_msg = f"Unexpected error during reload: {str(e)}"
        log_reload_event(reload_uid, "RELOAD_ERROR", {
            "summary": error_msg,
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        return jsonify({
            "success": False,
            "reload_uid": reload_uid,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/routing-status', methods=['GET'])
def get_routing_status():
    """Get current routing configuration status"""
    global config_loader, active_config_hash
    
    if not config_loader:
        return jsonify({
            "error": "Configuration loader not initialized"
        }), 500
    
    # Get current configuration summary
    config_summary = config_loader.export_config_summary()
    
    return jsonify({
        "status": "active",
        "current_hash": active_config_hash,
        "file_checksum": config_loader.file_checksum,
        "last_loaded": config_summary.get("last_loaded"),
        "config_summary": config_summary,
        "file_changed": config_loader.has_file_changed(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route('/reload-history', methods=['GET'])
def get_reload_history():
    """Get reload operation history"""
    global reload_history
    
    # Optional limit parameter
    limit = request.args.get('limit', 20, type=int)
    limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
    
    return jsonify({
        "reload_history": reload_history[-limit:],
        "total_entries": len(reload_history),
        "entries_returned": min(limit, len(reload_history)),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route('/validate-config', methods=['POST'])
def validate_config_endpoint():
    """Validate configuration without reloading"""
    global config_loader
    
    validation_uid = generate_reload_uid()
    
    if not config_loader:
        return jsonify({
            "error": "Configuration loader not initialized"
        }), 500
    
    try:
        # Load and validate current configuration
        config, validation_result = config_loader.load_config()
        
        log_reload_event(validation_uid, "VALIDATION_ONLY", {
            "summary": f"Configuration validation completed",
            "is_valid": validation_result.is_valid,
            "errors_count": len(validation_result.errors),
            "warnings_count": len(validation_result.warnings)
        })
        
        return jsonify({
            "validation_uid": validation_uid,
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "circular_references": validation_result.circular_references,
            "missing_models": validation_result.missing_models,
            "validation_timestamp": validation_result.validation_timestamp,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "validation_uid": validation_uid,
            "error": f"Validation failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/config-info/<route_name>', methods=['GET'])
def get_route_info(route_name: str):
    """Get detailed information about a specific route"""
    global config_loader
    
    if not config_loader:
        return jsonify({
            "error": "Configuration loader not initialized"
        }), 500
    
    route_info = config_loader.get_route_info(route_name)
    
    if not route_info:
        return jsonify({
            "error": f"Route '{route_name}' not found",
            "available_routes": config_loader.list_available_routes()
        }), 404
    
    return jsonify({
        "route_name": route_name,
        "route_info": route_info,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global config_loader
    
    return jsonify({
        "status": "healthy",
        "service": "routing-configurator",
        "version": "P18P7_v1.0",
        "mas_lite_protocol": "v2.1",
        "loader_initialized": config_loader is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


def run_api_server(host='127.0.0.1', port=5001, debug=True):
    """Run the Flask API server"""
    print(f"🚀 Starting Routing Configuration API on {host}:{port}")
    print(f"📋 Available endpoints:")
    print(f"   POST /reload-routing - Hot reload configuration")
    print(f"   GET  /routing-status - Get current status")
    print(f"   GET  /reload-history - Get reload history")
    print(f"   POST /validate-config - Validate configuration")
    print(f"   GET  /config-info/<route> - Get route details")
    print(f"   GET  /health - Health check")
    
    # Initialize configuration loader
    initialize_loader()
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    """
    Main CLI entry point for routing configuration API.
    
    Starts Flask server with hot reload capabilities.
    """
    import sys
    
    # Parse command line arguments
    port = 5001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 5001")
    
    run_api_server(port=port) 