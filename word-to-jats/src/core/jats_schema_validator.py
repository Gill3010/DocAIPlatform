"""
JATS Schema Validator - Validación contra JATS 1.3 y reglas de dominio.

Compatibilidad con OJS 3.x XML Gallery Plugin.
"""
from typing import Optional, Union
from pathlib import Path
from lxml import etree


class ValidationResult:
    """Resultado de la validación."""

    def __init__(
        self,
        is_valid: bool,
        quality_score: float = 0.0,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ):
        self.is_valid = is_valid
        self.quality_score = quality_score
        self.errors = errors or []
        self.warnings = warnings or []


class JatsSchemaValidator:
    """
    Valida XML JATS contra:
    - Esquema XSD JATS 1.3 (si está disponible)
    - Reglas de dominio: integridad de metadatos, cross-references
    """

    def __init__(self, xsd_path: Optional[Path] = None):
        self.xsd_path = xsd_path
        self._schema = None
        if xsd_path and xsd_path.exists():
            try:
                self._schema = etree.XMLSchema(etree.parse(str(xsd_path)))
            except etree.XMLSchemaParseError:
                pass

    def validate(
        self,
        xml_path: Optional[Union[str, Path]] = None,
        xml_content: Optional[Union[bytes, str]] = None,
    ) -> ValidationResult:
        """
        Valida el XML y aplica reglas de dominio.

        Args:
            xml_path: Ruta al archivo (opcional si se proporciona xml_content).
            xml_content: Contenido XML (para validación en memoria).
        """
        errors: list[str] = []
        warnings: list[str] = []

        if xml_content is None:
            if xml_path is None:
                raise ValueError("Debe proporcionar xml_path o xml_content")
            xml_content = Path(xml_path).read_bytes()

        if isinstance(xml_content, str):
            xml_content = xml_content.encode("utf-8")

        try:
            root = etree.fromstring(xml_content)
        except etree.XMLSyntaxError as e:
            return ValidationResult(is_valid=False, quality_score=0.0, errors=[str(e)])

        # Validación XSD si hay esquema
        if self._schema is not None:
            if not self._schema.validate(etree.fromstring(xml_content)):
                for err in self._schema.error_log:
                    errors.append(f"XSD: {err.message} (line {err.line})")

        # Reglas de dominio: número de autores
        contrib_count = len(root.findall(".//contrib[@contrib-type='author']"))
        if contrib_count == 0:
            warnings.append("No se encontraron autores (<contrib contrib-type='author'>)")

        # Reglas de dominio: cross-reference citas
        ref_ids = {r.get("id") for r in root.findall(".//ref-list/ref[@id]") if r.get("id")}
        for xref in root.iter("xref"):
            if xref.get("ref-type") == "bibr":
                rid = xref.get("rid")
                if rid and rid not in ref_ids and f"B{rid}" not in ref_ids:
                    # rid puede ser "B1" o "ref1" según convención
                    norm = rid if rid.startswith("B") else f"B{rid}"
                    if norm not in ref_ids:
                        warnings.append(f"Cita sin referencia: xref rid={rid}")

        # Cálculo de quality_score
        base = 1.0
        for _ in errors:
            base -= 0.3
        for _ in warnings:
            base -= 0.05
        quality_score = max(0.0, min(1.0, base))

        return ValidationResult(
            is_valid=len(errors) == 0,
            quality_score=quality_score,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
        )
