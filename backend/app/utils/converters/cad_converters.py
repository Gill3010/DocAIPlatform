"""
DWG/DXF ↔ PNG Conversion Converters
Uses LibreDWG (dwg2dxf, dxf2dwg) or ODA File Converter when available.
"""
import ezdxf
import subprocess
import shutil
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from PIL import Image
from typing import List
import os
import tempfile

from app.utils.base_converter import BaseConverter, ConversionError


class DXFToPNGConverter(BaseConverter):
    """
    Convert DXF (AutoCAD Drawing Exchange Format) to PNG
    DXF is the open format that DWG files can be exported to
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['dxf']
    
    @property
    def target_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DXF to PNG, JPG or JPEG using ezdxf and matplotlib
        """
        try:
            self.ensure_directory(output_path)
            
            try:
                doc = ezdxf.readfile(input_path)
            except IOError:
                raise ConversionError(f"No se pudo leer el archivo DXF: {input_path}")
            except ezdxf.DXFStructureError:
                raise ConversionError(f"Archivo DXF inválido o corrupto: {input_path}")
            
            msp = doc.modelspace()
            fig = plt.figure(figsize=(16, 12), dpi=150)
            ax = fig.add_axes([0, 0, 1, 1])
            
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)
            Frontend(ctx, backend).draw_layout(msp, finalize=True)
            
            ext = str(output_path).lower().split('.')[-1] if '.' in output_path else 'png'
            fmt = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none', format=fmt)
            plt.close(fig)
            
            return True
            
        except Exception as e:
            raise ConversionError(f"Conversión DXF a imagen falló: {str(e)}")


class DWGToImageConverter(BaseConverter):
    """
    Convert DWG to PNG, JPG or JPEG.
    Uses LibreDWG (dwg2dxf) or ODA File Converter when available.
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['dwg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    def _convert_via_libredwg(self, input_path: str, output_path: str) -> bool:
        """DWG → DXF (dwg2dxf) → imagen (ezdxf/matplotlib)."""
        dwg2dxf_cmd = shutil.which('dwg2dxf')
        if not dwg2dxf_cmd:
            return False
        self.ensure_directory(output_path)
        fd, tmp_dxf = tempfile.mkstemp(suffix='.dxf')
        os.close(fd)
        try:
            result = subprocess.run(
                [dwg2dxf_cmd, '-y', '--minimal', '-o', tmp_dxf, input_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise ConversionError(
                    f"dwg2dxf falló: {(result.stderr or result.stdout or '').strip()[:200]}"
                )
            doc = ezdxf.readfile(tmp_dxf)
            msp = doc.modelspace()
            fig = plt.figure(figsize=(16, 12), dpi=150)
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)
            Frontend(ctx, backend).draw_layout(msp, finalize=True)
            ext = str(output_path).lower().split('.')[-1] if '.' in output_path else 'png'
            fmt = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight',
                        facecolor='white', edgecolor='none', format=fmt)
            plt.close(fig)
            return True
        finally:
            try:
                os.unlink(tmp_dxf)
            except OSError:
                pass

    def convert(self, input_path: str, output_path: str) -> bool:
        try:
            if self._convert_via_libredwg(input_path, output_path):
                return True
        except ConversionError:
            raise
        except Exception:
            pass
        try:
            from ezdxf.addons import odafc
            if odafc.is_installed():
                self.ensure_directory(output_path)
                doc = odafc.readfile(input_path)
                msp = doc.modelspace()
                fig = plt.figure(figsize=(16, 12), dpi=150)
                ax = fig.add_axes([0, 0, 1, 1])
                ctx = RenderContext(doc)
                backend = MatplotlibBackend(ax)
                Frontend(ctx, backend).draw_layout(msp, finalize=True)
                ext = str(output_path).lower().split('.')[-1] if '.' in output_path else 'png'
                fmt = 'jpeg' if ext in ('jpg', 'jpeg') else 'png'
                plt.savefig(output_path, dpi=150, bbox_inches='tight',
                            facecolor='white', edgecolor='none', format=fmt)
                plt.close(fig)
                return True
        except Exception:
            pass
        raise ConversionError(
            "Conversión DWG → imagen requiere LibreDWG (dwg2dxf) u ODA File Converter. "
            "Instala LibreDWG o convierte DWG a DXF manualmente."
        )


class PNGToDXFConverter(BaseConverter):
    """
    Convert PNG to DXF (basic implementation)
    Creates a DXF with the image as a raster entity
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['dxf']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert PNG to DXF by embedding image
        Note: This creates a DXF with the image, not a vectorized drawing
        """
        try:
            self.ensure_directory(output_path)
            
            # Open image to get dimensions
            img = Image.open(input_path)
            width, height = img.size
            
            # Create new DXF document
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Add image definition (size_in_pixel is singular in ezdxf API)
            image_def = doc.add_image_def(
                filename=input_path,
                size_in_pixel=(width, height)
            )
            
            # Insert image into modelspace
            # Scale to reasonable size (100 units wide)
            scale = 100.0 / width
            msp.add_image(
                image_def=image_def,
                insert=(0, 0),
                size_in_units=(width * scale, height * scale)
            )
            
            # Save DXF
            doc.saveas(output_path)
            
            return True
            
        except Exception as e:
            raise ConversionError(f"Conversión PNG a DXF falló: {str(e)}")


class ImageToDWGConverter(BaseConverter):
    """
    Convert PNG/JPG/JPEG to DWG.
    Creates DXF with embedded image, then converts to DWG via dxf2dwg (LibreDWG) or ODA.
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['dwg']
    
    def _convert_dxf_to_dwg_via_libredwg(self, tmp_dxf: str, output_path: str) -> bool:
        dxf2dwg_cmd = shutil.which('dxf2dwg')
        if not dxf2dwg_cmd:
            return False
        result = subprocess.run(
            [dxf2dwg_cmd, '-y', '-o', output_path, tmp_dxf],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0

    def convert(self, input_path: str, output_path: str) -> bool:
        self.ensure_directory(output_path)
        img = Image.open(input_path)
        width, height = img.size
        img.close()

        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        image_def = doc.add_image_def(filename=input_path, size_in_pixel=(width, height))
        scale = 100.0 / width
        msp.add_image(image_def=image_def, insert=(0, 0),
                      size_in_units=(width * scale, height * scale))

        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            doc.saveas(tmp.name)
            tmp_path = tmp.name
        try:
            if self._convert_dxf_to_dwg_via_libredwg(tmp_path, output_path):
                return True
            try:
                from ezdxf.addons import odafc
                if odafc.is_installed():
                    odafc.convert(tmp_path, output_path, replace=True)
                    return True
            except Exception:
                pass
            raise ConversionError(
                "Conversión DXF → DWG requiere LibreDWG (dxf2dwg) u ODA File Converter. "
                "Alternativa: usa imagen → DXF."
            )
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(
                f"Conversión imagen → DWG falló: {e}. Alternativa: imagen → DXF."
            ) from e
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
