"""
XML ↔ HTML Conversion Converters
Bidirectional conversion between XML and HTML formats
"""
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import List
import html

from backend.app.utils.base_converter import BaseConverter, ConversionError


class XMLToHTMLConverter(BaseConverter):
    """Convert XML to HTML with basic formatting"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['xml']
    
    @property
    def target_formats(self) -> List[str]:
        return ['html']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert XML to HTML
        Creates a readable HTML representation of the XML structure
        """
        try:
            self.ensure_directory(output_path)
            
            # Parse XML
            tree = ET.parse(input_path)
            root = tree.getroot()
            
            # Build HTML
            html_content = self._build_html_from_xml(root)
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            raise ConversionError(f"XML to HTML conversion failed: {str(e)}")
    
    def _build_html_from_xml(self, root: ET.Element) -> str:
        """Build HTML structure from XML element tree"""
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="es">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>{root.tag}</title>',
            '    <style>',
            '        body { font-family: Arial, sans-serif; margin: 20px; }',
            '        .xml-element { margin-left: 20px; margin-bottom: 10px; }',
            '        .xml-tag { color: #0066cc; font-weight: bold; }',
            '        .xml-attribute { color: #cc6600; }',
            '        .xml-text { color: #333; }',
            '    </style>',
            '</head>',
            '<body>',
            f'    <h1>XML: {root.tag}</h1>',
            '    <div class="xml-content">',
        ]
        
        # Convert XML tree to HTML
        html_parts.append(self._element_to_html(root, level=0))
        
        html_parts.extend([
            '    </div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _element_to_html(self, element: ET.Element, level: int = 0) -> str:
        """Recursively convert XML element to HTML"""
        indent = '    ' * level
        html_parts = []
        
        # Open tag
        tag_html = f'{indent}<div class="xml-element">'
        tag_html += f'<span class="xml-tag">&lt;{html.escape(element.tag)}'
        
        # Attributes
        if element.attrib:
            for key, value in element.attrib.items():
                tag_html += f' <span class="xml-attribute">{html.escape(key)}="{html.escape(value)}"</span>'
        
        tag_html += '&gt;</span>'
        html_parts.append(tag_html)
        
        # Text content
        if element.text and element.text.strip():
            html_parts.append(f'{indent}    <span class="xml-text">{html.escape(element.text.strip())}</span>')
        
        # Children
        for child in element:
            html_parts.append(self._element_to_html(child, level + 1))
        
        # Close tag
        html_parts.append(f'{indent}    <span class="xml-tag">&lt;/{html.escape(element.tag)}&gt;</span>')
        html_parts.append(f'{indent}</div>')
        
        return '\n'.join(html_parts)


class HTMLToXMLConverter(BaseConverter):
    """Convert HTML to XML structure"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['html', 'htm']
    
    @property
    def target_formats(self) -> List[str]:
        return ['xml']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert HTML to XML
        Parses HTML and creates an XML representation
        """
        try:
            self.ensure_directory(output_path)
            
            # Read HTML
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML to XML structure
            parser = HTMLToXMLParser()
            parser.feed(html_content)
            
            # Create XML tree
            root = ET.Element('html')
            current = root
            
            for tag, attrs, text in parser.elements:
                if tag.startswith('/'):
                    # Closing tag - move up
                    if current.getparent() is not None:
                        current = current.getparent()
                else:
                    # Opening tag
                    elem = ET.SubElement(current, tag)
                    
                    # Add attributes
                    for key, value in attrs:
                        elem.set(key, value)
                    
                    # Add text
                    if text:
                        elem.text = text
                    
                    current = elem
            
            # Write XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space='    ')
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            return True
            
        except Exception as e:
            raise ConversionError(f"HTML to XML conversion failed: {str(e)}")


class HTMLToXMLParser(HTMLParser):
    """Simple HTML parser to extract structure"""
    
    def __init__(self):
        super().__init__()
        self.elements = []
    
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, attrs, None))
    
    def handle_endtag(self, tag):
        self.elements.append((f'/{tag}', [], None))
    
    def handle_data(self, data):
        if data.strip() and self.elements:
            # Add text to last element
            last_elem = list(self.elements[-1])
            last_elem[2] = data.strip()
            self.elements[-1] = tuple(last_elem)
