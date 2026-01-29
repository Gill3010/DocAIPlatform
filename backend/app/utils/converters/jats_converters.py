"""
DOCX ↔ XML JATS Conversion Converters
Handles: Microsoft Word to JATS (Journal Article Tag Suite) XML format
Used for academic/scientific article publishing
"""
from docx import Document
from lxml import etree
from typing import List, Dict, Tuple
import re
from datetime import datetime

from backend.app.utils.base_converter import BaseConverter, ConversionError


class DocxToJATSConverter(BaseConverter):
    """Convert Microsoft Word document to JATS XML format"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['docx']
    
    @property
    def target_formats(self) -> List[str]:
        return ['xml']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DOCX to JATS XML
        Expects Word document with standard academic structure:
        - Title (Heading 1)
        - Authors (Normal text after title)
        - Abstract/Resumen (section)
        - Body sections (Introduction, Methodology, Results, Conclusion)
        - References
        """
        try:
            self.ensure_directory(output_path)
            
            # Read DOCX
            doc = Document(input_path)
            
            # Extract content
            metadata = self._extract_metadata(doc)
            abstract = self._extract_abstract(doc)
            body_sections = self._extract_body(doc)
            references = self._extract_references(doc)
            
            # Build JATS XML
            jats_xml = self._build_jats_xml(metadata, abstract, body_sections, references)
            
            # Write XML file
            tree = etree.ElementTree(jats_xml)
            tree.write(
                output_path,
                pretty_print=True,
                xml_declaration=True,
                encoding='utf-8',
                doctype='<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
            )
            
            return True
            
        except Exception as e:
            raise ConversionError(f"Conversión DOCX a JATS XML falló: {str(e)}")
    
    def _extract_metadata(self, doc: Document) -> Dict:
        """Extract title and authors from document"""
        metadata = {
            'title': '',
            'authors': []
        }
        
        # First paragraph is usually the title
        if doc.paragraphs:
            metadata['title'] = doc.paragraphs[0].text.strip()
            
            # Next few paragraphs might contain authors
            for i in range(1, min(5, len(doc.paragraphs))):
                text = doc.paragraphs[i].text.strip()
                if text and len(text) < 100:  # Authors are usually short lines
                    # Check if it looks like an author name
                    if any(word in text.lower() for word in ['phd', 'dr.', 'mg', 'university', 'universidad']):
                        continue
                    if re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ]', text):
                        metadata['authors'].append(text)
        
        return metadata
    
    def _extract_abstract(self, doc: Document) -> str:
        """Extract abstract/resumen from document"""
        abstract_text = []
        in_abstract = False
        
        for para in doc.paragraphs:
            text = para.text.strip().lower()
            
            # Detect start of abstract
            if any(keyword in text for keyword in ['resumen', 'abstract', 'resumen:']):
                in_abstract = True
                continue
            
            # Detect end of abstract (next section)
            if in_abstract and any(keyword in text for keyword in ['introducción', 'introduction', 'palabras clave', 'keywords']):
                break
            
            if in_abstract and para.text.strip():
                abstract_text.append(para.text.strip())
        
        return '\n\n'.join(abstract_text)
    
    def _extract_body(self, doc: Document) -> List[Tuple[str, List[str]]]:
        """Extract body sections (Introduction, Methodology, Results, Conclusion)"""
        sections = []
        current_section = None
        current_paragraphs = []
        
        section_keywords = ['introducción', 'introduction', 'metodología', 'methodology', 
                          'resultados', 'results', 'conclusión', 'conclusion', 'discusión', 'discussion']
        
        for para in doc.paragraphs:
            text = para.text.strip()
            
            # Check if this is a section header
            if para.style.name.startswith('Heading') or text.lower() in section_keywords:
                # Save previous section
                if current_section and current_paragraphs:
                    sections.append((current_section, current_paragraphs))
                
                # Start new section
                current_section = text
                current_paragraphs = []
            elif current_section and text:
                # Add paragraph to current section
                current_paragraphs.append(text)
        
        # Add last section
        if current_section and current_paragraphs:
            sections.append((current_section, current_paragraphs))
        
        return sections
    
    def _extract_references(self, doc: Document) -> List[str]:
        """Extract bibliography/references"""
        references = []
        in_references = False
        
        for para in doc.paragraphs:
            text = para.text.strip()
            
            # Detect start of references section
            if any(keyword in text.lower() for keyword in ['referencias', 'bibliografía', 'bibliography', 'references']):
                in_references = True
                continue
            
            if in_references and text:
                references.append(text)
        
        return references
    
    def _build_jats_xml(self, metadata: Dict, abstract: str, 
                       body_sections: List[Tuple[str, List[str]]], 
                       references: List[str]) -> etree.Element:
        """Build JATS XML structure"""
        
        # Root element
        article = etree.Element('article', {
            'article-type': 'research-article',
            'dtd-version': '1.1',
            '{http://www.w3.org/XML/1998/namespace}lang': 'es'
        })
        
        # Front matter
        front = etree.SubElement(article, 'front')
        article_meta = etree.SubElement(front, 'article-meta')
        
        # Title
        title_group = etree.SubElement(article_meta, 'title-group')
        article_title = etree.SubElement(title_group, 'article-title')
        article_title.text = metadata['title']
        
        # Authors
        if metadata['authors']:
            contrib_group = etree.SubElement(article_meta, 'contrib-group')
            for i, author in enumerate(metadata['authors'], 1):
                contrib = etree.SubElement(contrib_group, 'contrib', {'contrib-type': 'author'})
                name_elem = etree.SubElement(contrib, 'name')
                
                # Try to split name into surname and given-names
                parts = author.split()
                if len(parts) >= 2:
                    surname = etree.SubElement(name_elem, 'surname')
                    surname.text = ' '.join(parts[:-1])
                    given_names = etree.SubElement(name_elem, 'given-names')
                    given_names.text = parts[-1]
                else:
                    surname = etree.SubElement(name_elem, 'surname')
                    surname.text = author
        
        # Abstract
        if abstract:
            abstract_elem = etree.SubElement(article_meta, 'abstract')
            abstract_title = etree.SubElement(abstract_elem, 'title')
            abstract_title.text = 'Resumen'
            abstract_p = etree.SubElement(abstract_elem, 'p')
            abstract_p.text = abstract
        
        # Publication date (current date)
        pub_date = etree.SubElement(article_meta, 'pub-date', {
            'date-type': 'pub',
            'publication-format': 'electronic'
        })
        now = datetime.now()
        day = etree.SubElement(pub_date, 'day')
        day.text = str(now.day)
        month = etree.SubElement(pub_date, 'month')
        month.text = str(now.month)
        year = etree.SubElement(pub_date, 'year')
        year.text = str(now.year)
        
        # Body
        body = etree.SubElement(article, 'body')
        
        for section_title, paragraphs in body_sections:
            sec = etree.SubElement(body, 'sec')
            title = etree.SubElement(sec, 'title')
            title.text = section_title
            
            for para_text in paragraphs:
                p = etree.SubElement(sec, 'p')
                p.text = para_text
        
        # Back matter (references)
        if references:
            back = etree.SubElement(article, 'back')
            ref_list = etree.SubElement(back, 'ref-list')
            ref_list_title = etree.SubElement(ref_list, 'title')
            ref_list_title.text = 'Referencias'
            
            for i, ref_text in enumerate(references, 1):
                ref = etree.SubElement(ref_list, 'ref', {'id': f'B{i}'})
                mixed_citation = etree.SubElement(ref, 'mixed-citation')
                mixed_citation.text = ref_text
        
        return article


class JATSToDocxConverter(BaseConverter):
    """Convert JATS XML to Microsoft Word document"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['xml']
    
    @property
    def target_formats(self) -> List[str]:
        return ['docx']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert JATS XML to DOCX
        Creates a formatted Word document from JATS structure
        """
        try:
            self.ensure_directory(output_path)
            
            # Parse XML
            tree = etree.parse(input_path)
            root = tree.getroot()
            
            # Check if it's JATS (look for article element)
            if root.tag not in ['article', '{http://jats.nlm.nih.gov}article']:
                raise ConversionError("El archivo XML no es formato JATS válido")
            
            # Create Word document
            doc = Document()
            
            # Extract and add content
            self._add_front_matter(doc, root)
            self._add_body(doc, root)
            self._add_references(doc, root)
            
            # Save document
            doc.save(output_path)
            
            return True
            
        except etree.XMLSyntaxError as e:
            raise ConversionError(f"Error de sintaxis XML: {str(e)}")
        except Exception as e:
            raise ConversionError(f"Conversión JATS XML a DOCX falló: {str(e)}")
    
    def _add_front_matter(self, doc: Document, root: etree.Element):
        """Add title, authors, and abstract to document"""
        
        # Find front element
        front = root.find('.//front')
        if front is None:
            return
        
        # Title
        title_elem = front.find('.//article-title')
        if title_elem is not None and title_elem.text:
            doc.add_heading(title_elem.text, level=1)
        
        # Authors
        authors = front.findall('.//contrib[@contrib-type="author"]')
        if authors:
            author_names = []
            for author in authors:
                surname = author.find('.//surname')
                given_names = author.find('.//given-names')
                if surname is not None:
                    name = surname.text or ''
                    if given_names is not None and given_names.text:
                        name = f"{given_names.text} {name}"
                    author_names.append(name)
            
            if author_names:
                doc.add_paragraph(', '.join(author_names))
        
        # Abstract
        abstract = front.find('.//abstract')
        if abstract is not None:
            doc.add_heading('Resumen', level=2)
            for p in abstract.findall('.//p'):
                if p.text:
                    doc.add_paragraph(p.text.strip())
        
        # Keywords
        kwd_groups = front.findall('.//kwd-group')
        if kwd_groups:
            doc.add_heading('Palabras clave', level=2)
            keywords = []
            for kwd_group in kwd_groups:
                for kwd in kwd_group.findall('.//kwd'):
                    if kwd.text:
                        keywords.append(kwd.text)
            if keywords:
                doc.add_paragraph(', '.join(keywords))
    
    def _add_body(self, doc: Document, root: etree.Element):
        """Add body sections to document"""
        
        body = root.find('.//body')
        if body is None:
            return
        
        for sec in body.findall('.//sec'):
            # Section title
            title = sec.find('.//title')
            if title is not None and title.text:
                doc.add_heading(title.text, level=2)
            
            # Section paragraphs
            for p in sec.findall('.//p'):
                text = ''.join(p.itertext()).strip()
                if text:
                    doc.add_paragraph(text)
    
    def _add_references(self, doc: Document, root: etree.Element):
        """Add references to document"""
        
        back = root.find('.//back')
        if back is None:
            return
        
        ref_list = back.find('.//ref-list')
        if ref_list is None:
            return
        
        doc.add_heading('Referencias', level=2)
        
        for ref in ref_list.findall('.//ref'):
            mixed_citation = ref.find('.//mixed-citation')
            if mixed_citation is not None:
                text = ''.join(mixed_citation.itertext()).strip()
                if text:
                    doc.add_paragraph(text, style='List Number')
