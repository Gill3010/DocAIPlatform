"""
GROBID API Client - Vía Estructural

Especializado en metadatos y bibliografía.
Documentación: https://grobid.readthedocs.io/
"""
from typing import Optional
import httpx
from lxml import etree


class GrobidClientError(Exception):
    """Error al comunicarse con GROBID."""


class GrobidClient:
    """Cliente para la API de GROBID (procesamiento de documentos científicos)."""

    def __init__(self, base_url: str = "http://localhost:8070", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_alive(self) -> bool:
        """Verifica si el servicio GROBID está disponible."""
        try:
            r = httpx.get(f"{self.base_url}/api/isalive", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def process_document(
        self,
        doc_bytes: bytes,
        filename: str = "document.docx",
        consolidate_header: bool = True,
        consolidate_citations: bool = True,
    ) -> Optional[etree._Element]:
        """
        Procesa un documento Word/PDF y devuelve el XML JATS generado por GROBID.

        Args:
            doc_bytes: Contenido binario del documento.
            filename: Nombre del archivo (extensión .docx o .pdf).
            consolidate_header: Consolidar metadatos del encabezado.
            consolidate_citations: Consolidar referencias.

        Returns:
            Elemento raíz del XML (article) o None si falla.
        """
        url = f"{self.base_url}/api/processFulltextDocument"
        files = {"input": (filename, doc_bytes)}
        params = {
            "consolidateHeader": str(consolidate_header).lower(),
            "consolidateCitations": str(consolidate_citations).lower(),
        }
        try:
            r = httpx.post(
                url,
                files=files,
                params=params,
                timeout=self.timeout,
            )
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise GrobidClientError(f"GROBID HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise GrobidClientError(f"GROBID request failed: {e}") from e

        try:
            root = etree.fromstring(r.content)
        except etree.XMLSyntaxError as e:
            raise GrobidClientError(f"Invalid XML from GROBID: {e}") from e

        # GROBID devuelve <TEI> o <article> según el endpoint
        if root.tag in ("article", "{http://jats.nlm.nih.gov}article"):
            return root
        # Si es TEI, podemos convertirlo o extraer metadatos; por ahora devolvemos el root
        return root

    def extract_references(self, doc_bytes: bytes, filename: str = "document.pdf") -> list[dict]:
        """
        Extrae referencias bibliográficas del documento.

        Returns:
            Lista de diccionarios con campos: authors, title, year, journal, doi, etc.
        """
        url = f"{self.base_url}/api/processReferences"
        files = {"input": (filename, doc_bytes)}
        try:
            r = httpx.post(url, files=files, timeout=self.timeout)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise GrobidClientError(f"GROBID references error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise GrobidClientError(f"GROBID request failed: {e}") from e

        root = etree.fromstring(r.content)
        refs = []
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        for bibl in root.iter(f"{{{ns['tei']}}}biblStruct"):
            refs.append(self._parse_bibl_struct(bibl, ns))
        return refs

    def _parse_bibl_struct(self, bibl: etree._Element, ns: dict) -> dict:
        """Convierte biblStruct TEI a diccionario."""
        out: dict = {}
        # Autor(es)
        authors = []
        for pers in bibl.iter(f"{{{ns['tei']}}}author"):
            surname = pers.find(f".//{{{ns['tei']}}}surname")
            forename = pers.find(f".//{{{ns['tei']}}}forename")
            if surname is not None and surname.text:
                name = surname.text
                if forename is not None and forename.text:
                    name = f"{forename.text} {name}"
                authors.append(name)
        if authors:
            out["authors"] = authors
        # Título
        title_e = bibl.find(f".//{{{ns['tei']}}}title")
        if title_e is not None and title_e.text:
            out["title"] = title_e.text
        # Año
        date_e = bibl.find(f".//{{{ns['tei']}}}date")
        if date_e is not None and date_e.get("when"):
            out["year"] = date_e.get("when", "")[:4]
        # DOI
        idno = bibl.find(f".//{{{ns['tei']}}}idno[@type='DOI']")
        if idno is not None and idno.text:
            out["doi"] = idno.text
        return out
