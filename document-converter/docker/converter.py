import os
import subprocess
import boto3
import json
import sys
from pathlib import Path

class DocumentConverter:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.input_bucket = os.environ.get('INPUT_BUCKET')
        self.output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    def convert_document(self, input_file, output_format):
        try:
            output_dir = "/tmp/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # High-quality PDF export for presentations (pptx, odp) - reduces text truncation
            ext = Path(input_file).suffix.lower()
            if output_format == 'pdf' and ext in ('.pptx', '.odp', '.ppt'):
                # impress_pdf_Export: mejor calidad, menos recorte de texto
                convert_to = 'pdf:impress_pdf_Export:{"UseLosslessCompression":{"type":"boolean","value":"true"},"Quality":{"type":"long","value":"100"},"ReduceImageResolution":{"type":"boolean","value":"false"}}'
            elif output_format == 'pdf' and ext in ('.docx', '.doc', '.odt'):
                # writer_pdf_Export para documentos - mejor calidad
                convert_to = 'pdf:writer_pdf_Export:{"UseLosslessCompression":{"type":"boolean","value":"true"},"Quality":{"type":"long","value":"100"},"ReduceImageResolution":{"type":"boolean","value":"false"}}'
            else:
                convert_to = output_format
            
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to',
                convert_to,
                input_file,
                '--outdir',
                output_dir
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                input_name = Path(input_file).stem
                converted_files = list(Path(output_dir).glob(f"{input_name}.*"))
                if converted_files:
                    return str(converted_files[0])
            return None
            
        except Exception as e:
            print(f"Error en conversión: {e}")
            return None
    
    def process_conversion_request(self, event):
        try:
            input_key = event['input_key']
            output_format = event['output_format']
            
            input_file = f"/tmp/{os.path.basename(input_key)}"
            self.s3.download_file(self.input_bucket, input_key, input_file)
            
            converted_file = self.convert_document(input_file, output_format)
            
            if converted_file:
                output_key = f"converted/{Path(converted_file).name}"
                self.s3.upload_file(converted_file, self.output_bucket, output_key)
                
                return {
                    'status': 'success',
                    'output_key': output_key,
                    'message': 'Conversión completada'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Error en conversión'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

if __name__ == "__main__":
    converter = DocumentConverter()
    if len(sys.argv) > 1:
        event = json.loads(sys.argv[1])
        result = converter.process_conversion_request(event)
        print(json.dumps(result))
    else:
        print("Converter ready")
