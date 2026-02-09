"""
DOCX ↔ XML JATS Conversion Converters
Handles: Microsoft Word to JATS (Journal Article Tag Suite) XML format
Used for academic/scientific article publishing.
Extracts images and tables; produces XML + image files for OJS (ZIP download).
"""
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from lxml import etree
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import re
import zipfile
import shutil
from datetime import datetime

from app.utils.base_converter import BaseConverter, ConversionError


class DocxToJATSConverter(BaseConverter):
    """Convert Microsoft Word document to JATS XML format"""
    
    @property
    def source_formats(self) -> List[str]:
        return ['docx']
    
    @property
    def target_formats(self) -> List[str]:
        return ['xml']
    
    def _extract_images_from_docx(self, input_path: str) -> List[Tuple[bytes, str]]:
        """Extract image blobs from DOCX word/media/. Returns list of (bytes, extension)."""
        result: List[Tuple[bytes, str]] = []
        try:
            with zipfile.ZipFile(input_path, 'r') as z:
                for name in z.namelist():
                    if not name.startswith('word/media/'):
                        continue
                    data = z.read(name)
                    ext = Path(name).suffix.lstrip('.').lower() or 'png'
                    if ext not in ('png', 'jpeg', 'jpg', 'gif', 'emf', 'wmf'):
                        ext = 'png'
                    result.append((data, ext))
        except Exception:
            pass
        return result

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DOCX to JATS XML (hybrid: XML + images saved alongside).
        Expects Word document with standard academic structure:
        - Title (Heading 1)
        - Authors (Normal text after title)
        - Abstract/Resumen (section)
        - Body sections (Introduction, Methodology, Results, Conclusion) + tables in order
        - References
        Images from word/media/ are saved next to the XML and referenced in a Figuras section.
        """
        try:
            self.ensure_directory(output_path)
            output_dir = Path(output_path).parent
            output_base = Path(output_path).stem

            # Read DOCX
            doc = Document(input_path)

            # Extract images and save alongside XML
            image_filenames: List[str] = []
            for i, (data, ext) in enumerate(self._extract_images_from_docx(input_path), 1):
                fn = f"{output_base}_image_{i}.{ext}"
                out_fn = output_dir / fn
                with open(out_fn, 'wb') as f:
                    f.write(data)
                image_filenames.append(fn)

            # Extract content (pass input_path for title fallback from filename)
            metadata = self._extract_metadata(doc, input_path)
            abstract = self._extract_abstract(doc)
            body_sections = self._extract_body(doc)
            references = self._extract_references(doc)
            keywords = self._extract_keywords(doc)

            # Build JATS XML (with fig/table counts and Figuras section)
            jats_xml = self._build_jats_xml(
                metadata, abstract, body_sections, references, keywords,
                image_filenames=image_filenames,
            )

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
    
    def _extract_metadata(self, doc: Document, input_path: Optional[str] = None) -> Dict:
        """Extract title and authors from document. Title is never left empty (fallback: first Heading 1, then filename, then 'Sin título')."""
        metadata = {
            'title': '',
            'authors': []
        }
        
        # Section labels that must NOT be used as article title (Lens expects a real title)
        section_labels = {
            'abstract', 'resumen', 'introducción', 'introduction', 'keywords', 'palabras clave',
            'metodología', 'methodology', 'resultados', 'results', 'conclusión', 'conclusion',
            'discusión', 'discussion', 'referencias', 'bibliografía', 'references', 'bibliography',
            'agradecimiento', 'acknowledgments', 'tabla 1', 'tabla 2', 'figure 1', 'figura 1',
        }

        def _is_valid_title(t: str) -> bool:
            t = (t or '').strip()
            if not t or len(t) > 500:
                return False
            if t.lower() in section_labels:
                return False
            if any(t.lower().startswith(kw) for kw in ['palabras clave', 'keywords:', 'abstract:', 'resumen:']):
                return False
            return True

        # Title: first paragraph, then first Heading 1, then first long-ish paragraph, then filename
        if doc.paragraphs:
            metadata['title'] = (doc.paragraphs[0].text or '').strip()
        if not _is_valid_title(metadata['title']):
            metadata['title'] = ''
            for para in doc.paragraphs:
                style_name = getattr(getattr(para, 'style', None), 'name', '') or ''
                if style_name == 'Heading 1' and _is_valid_title(para.text):
                    metadata['title'] = (para.text or '').strip()
                    break
        if not _is_valid_title(metadata['title']):
            metadata['title'] = ''
            for para in doc.paragraphs:
                text = (para.text or '').strip()
                if len(text) >= 15 and len(text) <= 300 and _is_valid_title(text):
                    metadata['title'] = text
                    break
        if not _is_valid_title(metadata['title']) and input_path:
            metadata['title'] = Path(input_path).stem or 'Sin título'
        if not _is_valid_title(metadata['title']):
            metadata['title'] = 'Sin título'

        # Next few paragraphs might contain authors
        for i in range(1, min(8, len(doc.paragraphs))):
            text = (doc.paragraphs[i].text or '').strip()
            if not text or len(text) > 150:
                continue
            skip = any(word in text.lower() for word in ['phd', 'dr.', 'mg', 'university', 'universidad', 'abstract', 'resumen'])
            if skip:
                continue
            # Author-like: two or more words, starts with capital
            if re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ][^0-9]*\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]', text) and not text.startswith(('http', 'www.', 'DOI:', '©')):
                metadata['authors'].append(text)
        
        return metadata
    
    def _extract_abstract(self, doc: Document) -> str:
        """Extract abstract/resumen from document"""
        abstract_text = []
        in_abstract = False
        
        for para in doc.paragraphs:
            text = (para.text or '').strip().lower()
            
            # Detect start of abstract
            if any(keyword in text for keyword in ['resumen', 'abstract', 'resumen:']):
                in_abstract = True
                continue
            
            # Detect end of abstract (next section)
            if in_abstract and any(keyword in text for keyword in ['introducción', 'introduction', 'palabras clave', 'keywords']):
                break
            
            if in_abstract and (para.text or '').strip():
                abstract_text.append((para.text or '').strip())
        
        return '\n\n'.join(abstract_text)
    
    def _extract_body(self, doc: Document) -> List[Tuple[str, List[Union[str, List[List[str]]]]]]:
        """Extract body sections in document order: paragraphs and tables (mixed)."""
        sections: List[Tuple[str, List[Union[str, List[List[str]]]]]] = []
        current_section: Optional[str] = None
        current_items: List[Union[str, List[List[str]]]] = []
        section_keywords = {'introducción', 'introduction', 'metodología', 'methodology',
                            'resultados', 'results', 'conclusión', 'conclusion', 'discusión', 'discussion'}

        def flush_section() -> None:
            if current_section is not None and current_items:
                sections.append((current_section, list(current_items)))

        for block in doc.iter_inner_content():
            if isinstance(block, Table):
                rows = [[(c.text or '').strip() for c in row.cells] for row in block.rows]
                if rows:
                    if current_section is None:
                        current_section = 'Contenido'
                    current_items.append(rows)
                continue
            text = (block.text or '').strip()
            style_name = getattr(getattr(block, 'style', None), 'name', '') or ''
            if style_name.startswith('Heading') or (text.lower() in section_keywords):
                flush_section()
                current_section = text or 'Sección'
                current_items = []
            elif text:
                if current_section is None:
                    current_section = 'Contenido'
                current_items.append(text)
        flush_section()
        return sections
    
    def _extract_references(self, doc: Document) -> List[str]:
        """Extract bibliography/references"""
        references = []
        in_references = False
        
        for para in doc.paragraphs:
            text = (para.text or '').strip()
            
            # Detect start of references section
            if any(keyword in text.lower() for keyword in ['referencias', 'bibliografía', 'bibliography', 'references']):
                in_references = True
                continue
            
            if in_references and text:
                references.append(text)
        
        return references

    def _extract_keywords(self, doc: Document) -> List[str]:
        """Extract keywords from 'Palabras clave' or 'Keywords' paragraph."""
        keywords = []
        in_keywords = False
        for para in doc.paragraphs:
            text_lower = (para.text or '').strip().lower()
            if not text_lower:
                continue
            if any(prefix in text_lower for prefix in ['palabras clave', 'keywords', 'key words']):
                in_keywords = True
                # Same paragraph may contain keywords after colon
                after = (para.text or '').split(':', 1)[-1].strip()
                if after:
                    for part in re.split(r'[,;]', after):
                        kw = part.strip()
                        if kw and len(kw) < 80:
                            keywords.append(kw)
                continue
            if in_keywords:
                # Next section or long line ends keywords
                if getattr(getattr(para, 'style', None), 'name', '').startswith('Heading') or len((para.text or '').strip()) > 120:
                    break
                for part in re.split(r'[,;]', (para.text or '').strip()):
                    kw = part.strip()
                    if kw and len(kw) < 80:
                        keywords.append(kw)
        return keywords[:30]  # Reasonable limit

    # xlink namespace for ext-link href (JATS)
    XLINK_NS = 'http://www.w3.org/1999/xlink'

    def _build_mixed_citation_with_links(self, parent: etree.Element, ref_text: str) -> None:
        """Append mixed-citation with text and ext-link for URLs (JATS/OJS)."""
        if not ref_text or not ref_text.strip():
            return
        url_pattern = re.compile(r'https?://[^\s<>"\']+')
        parts = []
        last_end = 0
        for m in url_pattern.finditer(ref_text):
            if m.start() > last_end:
                parts.append(('text', ref_text[last_end:m.start()]))
            parts.append(('url', m.group(0)))
            last_end = m.end()
        if last_end < len(ref_text):
            parts.append(('text', ref_text[last_end:]))

        mixed_citation = etree.SubElement(parent, 'mixed-citation')
        if not parts:
            mixed_citation.text = ref_text
            return

        # Build interleaved text and ext-link: text segments and ext-link elements
        next_text = ''
        for i, (kind, content) in enumerate(parts):
            if kind == 'text':
                next_text = content
                if i == 0:
                    mixed_citation.text = next_text
            else:
                if i == 0:
                    mixed_citation.text = ''
                ext_link = etree.SubElement(mixed_citation, 'ext-link', {
                    'ext-link-type': 'uri',
                    f'{{{self.XLINK_NS}}}href': content,
                })
                ext_link.text = content
                ext_link.tail = next_text
                next_text = ''
        if next_text and len(mixed_citation) > 0:
            mixed_citation[-1].tail = (mixed_citation[-1].tail or '') + next_text
        elif next_text:
            mixed_citation.text = (mixed_citation.text or '') + next_text

    def _build_jats_xml(self, metadata: Dict, abstract: str,
                       body_sections: List[Tuple[str, List[Union[str, List[List[str]]]]]],
                       references: List[str],
                       keywords: Optional[List[str]] = None,
                       image_filenames: Optional[List[str]] = None) -> etree.Element:
        """Build JATS XML structure compatible with OJS/eLife Lens (JATS Publishing 1.1)."""
        keywords = keywords or []
        image_filenames = image_filenames or []
        fig_count = len(image_filenames)
        table_count = sum(
            1 for _sec, items in body_sections for item in items if isinstance(item, list)
        )

        # Root element: namespaces for xlink (inline-graphic, ext-link) and MathML (OJS/Lens)
        article = etree.Element('article', {
            'article-type': 'research-article',
            'dtd-version': '1.1',
            'specific-use': 'sps-1.9',
            '{http://www.w3.org/XML/1998/namespace}lang': 'es',
        }, nsmap={
            'xlink': 'http://www.w3.org/1999/xlink',
            'mml': 'http://www.w3.org/1998/Math/MathML',
        })
        # Ensure article-title is never empty (Lens fails on null/empty)
        title_text = (metadata.get('title') or '').strip() or 'Sin título'

        # Front matter – structure aligned with working OJS/Lens XML
        front = etree.SubElement(article, 'front')
        journal_meta = etree.SubElement(front, 'journal-meta')
        journal_id = etree.SubElement(journal_meta, 'journal-id', {'journal-id-type': 'publisher-id'})
        journal_id.text = 'converted'
        journal_title_group = etree.SubElement(journal_meta, 'journal-title-group')
        journal_title = etree.SubElement(journal_title_group, 'journal-title')
        journal_title.text = 'Article'
        abbrev = etree.SubElement(journal_title_group, 'abbrev-journal-title', {'abbrev-type': 'publisher'})
        abbrev.text = 'Article'

        article_meta = etree.SubElement(front, 'article-meta')
        article_id = etree.SubElement(article_meta, 'article-id', {'pub-id-type': 'other'})
        article_id.text = 'converted-1'

        article_cats = etree.SubElement(article_meta, 'article-categories')
        subj_group = etree.SubElement(article_cats, 'subj-group', {'subj-group-type': 'heading'})
        subject = etree.SubElement(subj_group, 'subject')
        subject.text = 'Artículo original'

        title_group = etree.SubElement(article_meta, 'title-group')
        article_title = etree.SubElement(title_group, 'article-title')
        article_title.text = title_text

        # contrib-group with aff and xref (Lens expects this structure)
        contrib_group = etree.SubElement(article_meta, 'contrib-group')
        authors = metadata.get('authors') or []
        if not authors:
            authors = ['Autor']
        for i, author in enumerate(authors):
            contrib = etree.SubElement(contrib_group, 'contrib', {'contrib-type': 'author'})
            name_elem = etree.SubElement(contrib, 'name')
            parts = [p for p in author.split() if p]
            if len(parts) >= 3:
                surname = etree.SubElement(name_elem, 'surname')
                surname.text = ' '.join(parts[-2:])
                given_names = etree.SubElement(name_elem, 'given-names')
                given_names.text = ' '.join(parts[:-2])
            elif len(parts) == 2:
                surname = etree.SubElement(name_elem, 'surname')
                surname.text = parts[-1]
                given_names = etree.SubElement(name_elem, 'given-names')
                given_names.text = parts[0]
            else:
                surname = etree.SubElement(name_elem, 'surname')
                surname.text = (author or 'Autor').strip() or 'Autor'
            xref_aff = etree.SubElement(contrib, 'xref', {'ref-type': 'aff', 'rid': 'aff1'})
            sup = etree.SubElement(xref_aff, 'sup')
            sup.text = '1'
        aff1 = etree.SubElement(contrib_group, 'aff', {'id': 'aff1'})
        label_aff = etree.SubElement(aff1, 'label')
        label_aff.text = '1 '
        inst = etree.SubElement(aff1, 'institution', {'content-type': 'original'})
        inst.text = 'Sin especificar'

        author_notes = etree.SubElement(article_meta, 'author-notes')
        corresp = etree.SubElement(author_notes, 'corresp', {'id': 'c1'})
        label_c = etree.SubElement(corresp, 'label')
        sup_c = etree.SubElement(label_c, 'sup')
        sup_c.text = '*'
        label_c.tail = ' Autor para la correspondencia.'

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

        if abstract:
            abstract_elem = etree.SubElement(article_meta, 'abstract')
            abstract_title = etree.SubElement(abstract_elem, 'title')
            abstract_title.text = 'Resumen'
            abstract_p = etree.SubElement(abstract_elem, 'p')
            abstract_p.text = abstract

        if keywords:
            kwd_group = etree.SubElement(article_meta, 'kwd-group', {'{http://www.w3.org/XML/1998/namespace}lang': 'es'})
            kwd_title = etree.SubElement(kwd_group, 'title')
            kwd_title.text = 'Palabras clave:'
            for kw in keywords:
                kwd = etree.SubElement(kwd_group, 'kwd')
                kwd.text = kw

        counts = etree.SubElement(article_meta, 'counts')
        etree.SubElement(counts, 'fig-count', {'count': str(fig_count)})
        etree.SubElement(counts, 'table-count', {'count': str(table_count)})
        etree.SubElement(counts, 'equation-count', {'count': '0'})
        etree.SubElement(counts, 'ref-count', {'count': str(len(references))})
        
        # Body (sec-type aligned with OJS/Lens: intro, methods, results|discussion, conclusions)
        body = etree.SubElement(article, 'body')
        intro_labels = {'introducción', 'introduction', 'introduccion'}
        methods_labels = {'metodología', 'methodology', 'metodos', 'methods'}
        results_labels = {'resultados', 'results', 'discusión', 'discussion', 'resultados y discusión'}
        concl_labels = {'conclusión', 'conclusion', 'conclusiones', 'conclusions'}

        for section_title, items in body_sections:
            sec_attrs = {}
            title_lower = (section_title or '').strip().lower()
            if title_lower in intro_labels:
                sec_attrs['sec-type'] = 'intro'
            elif title_lower in methods_labels:
                sec_attrs['sec-type'] = 'methods'
            elif title_lower in results_labels or 'resultados' in title_lower and 'discusión' in title_lower:
                sec_attrs['sec-type'] = 'results|discussion'
            elif title_lower in concl_labels:
                sec_attrs['sec-type'] = 'conclusions'
            sec = etree.SubElement(body, 'sec', sec_attrs)
            title = etree.SubElement(sec, 'title')
            title.text = section_title

            for item in items:
                if isinstance(item, str):
                    p = etree.SubElement(sec, 'p')
                    p.text = item
                else:
                    # item is list of rows (table)
                    tbl = etree.SubElement(sec, 'table')
                    tbody = etree.SubElement(tbl, 'tbody')
                    for row in item:
                        tr = etree.SubElement(tbody, 'tr')
                        for cell_text in row:
                            td = etree.SubElement(tr, 'td')
                            td.text = cell_text or ''

        # Figuras section (OJS: upload these as dependent files)
        if image_filenames:
            sec_fig = etree.SubElement(body, 'sec')
            title_fig = etree.SubElement(sec_fig, 'title')
            title_fig.text = 'Figuras'
            for fn in image_filenames:
                fig = etree.SubElement(sec_fig, 'fig')
                graphic = etree.SubElement(fig, 'graphic', {f'{{{self.XLINK_NS}}}href': fn})
        
        # Back matter (references; URLs wrapped in ext-link for JATS/OJS)
        if references:
            back = etree.SubElement(article, 'back')
            ref_list = etree.SubElement(back, 'ref-list')
            ref_list_title = etree.SubElement(ref_list, 'title')
            ref_list_title.text = 'Referencias'

            for i, ref_text in enumerate(references, 1):
                ref = etree.SubElement(ref_list, 'ref', {'id': f'B{i}'})
                self._build_mixed_citation_with_links(ref, ref_text)
        
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
