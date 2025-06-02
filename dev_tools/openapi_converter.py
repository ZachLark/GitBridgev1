#!/usr/bin/env python3
"""
OpenAPI to Markdown Converter Hook for GitBridge
Converts OpenAPI specifications to various documentation formats.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Union, Literal
import yaml
import json
from jinja2 import Environment, FileSystemLoader
from jsonschema import validate as validate_schema
import markdown
import pdfkit
from openapi_spec_validator import validate_spec

logger = logging.getLogger(__name__)

class OpenAPIConverter:
    """Converts OpenAPI specifications to various documentation formats."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the converter.
        
        Args:
            template_dir: Optional directory containing Jinja2 templates
        """
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
    def convert_spec(
        self,
        spec_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: Literal["markdown", "html", "pdf"] = "markdown",
        validate_schema: bool = True
    ) -> bool:
        """
        Convert OpenAPI spec to desired format.
        
        Args:
            spec_path: Path to OpenAPI specification file
            output_path: Path to output file
            output_format: Desired output format (markdown, html, or pdf)
            validate_schema: Whether to validate the OpenAPI schema
            
        Returns:
            bool: True if conversion successful, False otherwise
        """
        try:
            spec_path = Path(spec_path)
            output_path = Path(output_path)
            
            # Load OpenAPI spec
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
                
            # Validate OpenAPI schema if requested
            if validate_schema:
                try:
                    validate_spec(spec)
                    logger.info("OpenAPI schema validation successful")
                except Exception as e:
                    logger.error(f"Schema validation failed: {str(e)}")
                    return False
                
            # Generate content based on format
            if output_format == "markdown":
                content = self._generate_markdown(spec)
                self._write_output(content, output_path)
            elif output_format == "html":
                markdown_content = self._generate_markdown(spec)
                html_content = markdown.markdown(markdown_content)
                self._write_output(html_content, output_path)
            elif output_format == "pdf":
                markdown_content = self._generate_markdown(spec)
                html_content = markdown.markdown(markdown_content)
                self._generate_pdf(html_content, output_path)
            else:
                logger.error(f"Unsupported output format: {output_format}")
                return False
                
            logger.info(f"Successfully converted {spec_path} to {output_format}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting OpenAPI spec: {str(e)}")
            return False
            
    def _generate_markdown(self, spec: Dict) -> str:
        """
        Generate Markdown from OpenAPI spec.
        
        Args:
            spec: Parsed OpenAPI specification
            
        Returns:
            str: Generated Markdown content
        """
        markdown = f"""# {spec.get('info', {}).get('title', 'API Documentation')}

## Overview

{spec.get('info', {}).get('description', 'No description available.')}

## Version

{spec.get('info', {}).get('version', 'Unknown')}

## Base URL

{spec.get('servers', [{'url': 'Not specified'}])[0]['url']}

## Endpoints

"""
        # Add endpoints
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            markdown += f"### {path}\n\n"
            for method, details in methods.items():
                markdown += f"#### {method.upper()}\n\n"
                markdown += f"**Description:** {details.get('description', 'No description')}\n\n"
                
                # Parameters
                if details.get('parameters'):
                    markdown += "**Parameters:**\n\n"
                    for param in details['parameters']:
                        markdown += f"- `{param['name']}` ({param['in']}): {param.get('description', 'No description')}\n"
                    markdown += "\n"
                
                # Request body
                if details.get('requestBody'):
                    markdown += "**Request Body:**\n\n"
                    content = details['requestBody'].get('content', {})
                    for content_type, schema in content.items():
                        markdown += f"Content-Type: `{content_type}`\n\n"
                        if 'schema' in schema:
                            markdown += "```json\n"
                            markdown += json.dumps(schema['schema'], indent=2)
                            markdown += "\n```\n\n"
                
                # Responses
                if details.get('responses'):
                    markdown += "**Responses:**\n\n"
                    for status, response in details['responses'].items():
                        markdown += f"- `{status}`: {response.get('description', 'No description')}\n"
                    markdown += "\n"
                
        return markdown
            
    def _write_output(self, content: str, output_path: Path):
        """Write content to output file."""
        with open(output_path, 'w') as f:
            f.write(content)
            
    def _generate_pdf(self, html_content: str, output_path: Path):
        """Generate PDF from HTML content using wkhtmltopdf."""
        try:
            pdfkit.from_string(html_content, str(output_path))
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert OpenAPI specs to documentation')
    parser.add_argument('spec_path', help='Path to OpenAPI specification file')
    parser.add_argument('output_path', help='Path to output file')
    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'pdf'],
        default='markdown',
        help='Output format'
    )
    parser.add_argument(
        '--template-dir',
        help='Custom template directory'
    )
    parser.add_argument(
        '--validate-schema',
        action='store_true',
        help='Validate OpenAPI schema'
    )
    
    args = parser.parse_args()
    
    converter = OpenAPIConverter(template_dir=args.template_dir)
    success = converter.convert_spec(
        args.spec_path,
        args.output_path,
        output_format=args.format,
        validate_schema=args.validate_schema
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 