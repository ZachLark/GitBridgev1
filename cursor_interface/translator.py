#!/usr/bin/env python3
"""
GitBridge GPT Output → Cursor Translator
Task: P20P4S2 - GPT Output → Cursor Translator

This module translates GPT-4o responses into structured Cursor files
(.suggestion.md, .task.md, .log.md) using the format specification from P20P4S1.

Author: GitBridge Development Team
Date: 2025-01-11
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from cursor_interface.cursor_formats import (
    CursorFileFormatter, CursorFileMetadata, CursorFileType, ConfidenceLevel
)
from utils.schema_validator import GPT4oEventSchema, SchemaValidator
from tests.test_gpt4o_connection import GPT4oResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cursor_integration_trace.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CursorTranslator:
    """
    Translator that converts GPT-4o responses into Cursor workspace files.
    
    This class handles:
    - Parsing GPT-4o responses
    - Determining appropriate file types
    - Formatting content for Cursor
    - Writing files to cursor_workspace/
    """
    
    def __init__(self, workspace_dir: str = "cursor_workspace"):
        """
        Initialize the translator.
        
        Args:
            workspace_dir: Directory to write Cursor files to
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.formatter = CursorFileFormatter()
        self.schema_validator = SchemaValidator()
        
        logger.info(f"✅ CursorTranslator initialized with workspace: {self.workspace_dir}")
    
    def translate_gpt_response(self, gpt_response: GPT4oResponse, 
                             original_event: GPT4oEventSchema,
                             context: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate GPT-4o response into Cursor file format.
        
        Args:
            gpt_response: GPT-4o response object
            original_event: Original event that generated the response
            context: Optional additional context
            
        Returns:
            Dict containing translation results
        """
        if not gpt_response.success:
            logger.error(f"❌ Cannot translate failed GPT response: {gpt_response.error_message}")
            return {
                "success": False,
                "error": gpt_response.error_message,
                "files_created": []
            }
        
        try:
            # Create metadata for the file
            metadata = CursorFileMetadata(
                event_id=original_event.event_id,
                source=original_event.source.value,
                session_id=original_event.session_id or f"session_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=ConfidenceLevel.MEDIUM,  # Will be auto-determined
                file_type=CursorFileType.SUGGESTION,  # Will be auto-determined
                gpt_model=gpt_response.model
            )
            
            # Format the content
            formatted_content = self.formatter.format_content(
                content=gpt_response.content,
                metadata=metadata,
                context=context,
                requested_output=original_event.requested_output.value if original_event.requested_output else None
            )
            
            # Determine file extension based on file type
            file_extension = f".{metadata.file_type.value}.md"
            
            # Generate filename
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{original_event.event_id}_{timestamp_str}{file_extension}"
            file_path = self.workspace_dir / filename
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            # Log the translation
            self._log_translation(original_event, gpt_response, metadata, file_path)
            
            logger.info(f"✅ Created Cursor file: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "file_type": metadata.file_type.value,
                "confidence": metadata.confidence.value,
                "content_length": len(formatted_content),
                "files_created": [str(file_path)]
            }
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "files_created": []
            }
    
    def _log_translation(self, original_event: GPT4oEventSchema, 
                        gpt_response: GPT4oResponse,
                        metadata: CursorFileMetadata,
                        file_path: Path) -> None:
        """
        Log translation details for audit trail.
        
        Args:
            original_event: Original event
            gpt_response: GPT-4o response
            metadata: File metadata
            file_path: Path to created file
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "translation_id": f"trans_{int(datetime.now().timestamp())}",
            "original_event_id": original_event.event_id,
            "source": original_event.source.value,
            "event_type": original_event.event_type.value,
            "gpt_model": gpt_response.model,
            "gpt_response_time": gpt_response.response_time,
            "cursor_file_path": str(file_path),
            "cursor_file_type": metadata.file_type.value,
            "confidence": metadata.confidence.value,
            "content_preview": gpt_response.content[:200] + "..." if len(gpt_response.content) > 200 else gpt_response.content
        }
        
        # Write to log file
        with open('logs/cursor_integration_trace.log', 'a') as f:
            f.write(f"\n{json.dumps(log_entry, indent=2)}\n")
        
        logger.info(f"📝 Translation logged: {log_entry['translation_id']}")
    
    def batch_translate(self, responses: List[tuple[GPT4oResponse, GPT4oEventSchema]]) -> Dict[str, Any]:
        """
        Translate multiple GPT responses in batch.
        
        Args:
            responses: List of (GPT4oResponse, GPT4oEventSchema) tuples
            
        Returns:
            Dict containing batch results
        """
        results = {
            "total": len(responses),
            "successful": 0,
            "failed": 0,
            "files_created": [],
            "errors": []
        }
        
        for i, (gpt_response, original_event) in enumerate(responses):
            logger.info(f"🔄 Translating response {i+1}/{len(responses)}")
            
            result = self.translate_gpt_response(gpt_response, original_event)
            
            if result["success"]:
                results["successful"] += 1
                results["files_created"].extend(result["files_created"])
            else:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "event_id": original_event.event_id,
                    "error": result["error"]
                })
        
        logger.info(f"✅ Batch translation complete: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def list_workspace_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the Cursor workspace.
        
        Returns:
            List of file information dictionaries
        """
        files = []
        for file_path in self.workspace_dir.glob("*.md"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def cleanup_old_files(self, days: int = 7) -> int:
        """
        Clean up old Cursor files.
        
        Args:
            days: Number of days to keep files
            
        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in self.workspace_dir.glob("*.md"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"🗑️  Deleted old file: {file_path}")
        
        logger.info(f"🧹 Cleanup complete: {deleted_count} files deleted")
        return deleted_count


def create_sample_translation():
    """Create a sample translation for testing."""
    from utils.schema_validator import create_sample_events
    from tests.test_gpt4o_connection import GPT4oResponse
    
    # Create sample event
    samples = create_sample_events()
    sample_event = samples['github_pr']
    
    # Create mock GPT response
    mock_response = GPT4oResponse(
        content="This is a sample GPT-4o response for testing the translator. It contains suggestions for improving code quality and security.",
        model="gpt-4o",
        usage={"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
        finish_reason="stop",
        response_time=2.5,
        success=True
    )
    
    # Test translation
    translator = CursorTranslator()
    result = translator.translate_gpt_response(mock_response, sample_event)
    
    return result


def main():
    """Main function for testing and demonstration."""
    print("🔄 GitBridge GPT Output → Cursor Translator")
    print("Task: P20P4S2 - GPT Output → Cursor Translator")
    print("=" * 60)
    
    # Test sample translation
    print("\n🧪 Testing sample translation...")
    result = create_sample_translation()
    
    if result["success"]:
        print(f"✅ Translation successful!")
        print(f"📁 File created: {result['file_path']}")
        print(f"📝 File type: {result['file_type']}")
        print(f"🎯 Confidence: {result['confidence']}")
    else:
        print(f"❌ Translation failed: {result['error']}")
    
    # List workspace files
    translator = CursorTranslator()
    files = translator.list_workspace_files()
    
    print(f"\n📂 Workspace files ({len(files)} total):")
    for file_info in files[:5]:  # Show first 5 files
        print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
    
    print("\n✅ Cursor translator ready for integration!")
    print("📁 Files will be written to cursor_workspace/")
    print("📝 Logs will be written to logs/cursor_integration_trace.log")


if __name__ == "__main__":
    main() 