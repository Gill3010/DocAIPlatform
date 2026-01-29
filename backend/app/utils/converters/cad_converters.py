"""
DWG/DXF ↔ PNG Conversion Converters
Handles: AutoCAD DWG files to PNG images
Note: DWG files need to be converted to DXF first (using external tool or service)
"""
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from PIL import Image
from typing import List
import os
import tempfile

from backend.app.utils.base_converter import BaseConverter, ConversionError


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
        return ['png']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DXF to PNG using ezdxf and matplotlib
        """
        try:
            self.ensure_directory(output_path)
            
            # Read DXF file
            try:
                doc = ezdxf.readfile(input_path)
            except IOError:
                raise ConversionError(f"No se pudo leer el archivo DXF: {input_path}")
            except ezdxf.DXFStructureError:
                raise ConversionError(f"Archivo DXF inválido o corrupto: {input_path}")
            
            # Get modelspace
            msp = doc.modelspace()
            
            # Create figure for rendering
            fig = plt.figure(figsize=(16, 12), dpi=150)
            ax = fig.add_axes([0, 0, 1, 1])
            
            # Create render context and backend
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)
            
            # Render the DXF
            Frontend(ctx, backend).draw_layout(msp, finalize=True)
            
            # Save to PNG
            plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            raise ConversionError(f"Conversión DXF a PNG falló: {str(e)}")


class DWGToPNGConverter(BaseConverter):
    """
    Convert DWG to PNG
    Note: This is a placeholder that requires external conversion
    In production, use a service like AutoDesk API, LibreDWG, or ODA File Converter
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['dwg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['png']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert DWG to PNG
        
        NOTE: DWG is a proprietary format. Options:
        1. Use AutoDesk Forge API (cloud service)
        2. Use ODA File Converter (command-line tool)
        3. Use LibreDWG (open source but limited)
        4. Convert to DXF first, then to PNG
        
        For now, this raises an informative error
        """
        raise ConversionError(
            "Conversión DWG → PNG requiere configuración adicional. "
            "Por favor, convierte tu archivo DWG a DXF primero usando AutoCAD "
            "o una herramienta de conversión externa. "
            "Formatos alternativos soportados: DXF → PNG"
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
            
            # Add image definition
            image_def = doc.add_image_def(
                filename=input_path,
                size_in_pixels=(width, height)
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


class PNGToDWGConverter(BaseConverter):
    """
    Convert PNG to DWG
    Note: Similar limitation as DWG to PNG - requires external tools
    """
    
    @property
    def source_formats(self) -> List[str]:
        return ['png', 'jpg', 'jpeg']
    
    @property
    def target_formats(self) -> List[str]:
        return ['dwg']
    
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        Convert PNG to DWG - requires external tools
        """
        raise ConversionError(
            "Conversión PNG → DWG requiere configuración adicional. "
            "Por favor, usa el formato DXF como alternativa: PNG → DXF. "
            "Luego puedes abrir el DXF en AutoCAD y guardarlo como DWG."
        )
