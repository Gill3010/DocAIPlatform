"""
DocAI Platform - Sistema de procesamiento de documentos con AWS Bedrock
"""
import boto3
import json
import os
import sys
from datetime import datetime
from document_processor import DocumentProcessor
from config import *

class DocAIPlatform:
    def __init__(self):
        """Inicializar DocAI Platform"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        self.doc_processor = DocumentProcessor()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorios si no existen
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"🚀 DocAI Platform iniciado - Sesión: {self.session_id}")
        print(f"📍 Región AWS: {AWS_REGION}")
        print(f"🤖 Modelo: {BEDROCK_MODEL_ID}")
    
    def invoke_bedrock(self, prompt, context=""):
        """Invocar modelo Bedrock Claude"""
        try:
            # Preparar el cuerpo de la solicitud (formato Claude Bedrock API)
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": (f"{context}\n\n{prompt}" if context else prompt)}]
                    }
                ]
            }
            
            # Invocar el modelo
            response = self.bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            # Procesar respuesta
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"❌ Error invocando Bedrock: {str(e)}"
    
    def process_document_with_ai(self, file_path):
        """Procesar documento con IA"""
        try:
            print(f"📄 Procesando: {os.path.basename(file_path)}")
            
            # Procesar documento
            result = self.doc_processor.process_document(file_path, OUTPUT_DIR)
            
            # Leer el contenido XML generado
            with open(result['output_file'], 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Crear prompt para análisis con IA
            analysis_prompt = f"""
            Analiza el siguiente documento XML extraído de un archivo Word y proporciona:
            
            1. Resumen del contenido
            2. Estructura del documento
            3. Elementos clave identificados
            4. Sugerencias de mejora o insights
            
            Documento XML:
            {xml_content[:2000]}...  # Primeros 2000 caracteres
            """
            
            # Obtener análisis de IA
            ai_analysis = self.invoke_bedrock(analysis_prompt)
            
            # Crear archivo de análisis
            analysis_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(os.path.basename(file_path))[0]}_analysis.txt")
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"=== ANÁLISIS DocAI Platform ===\n")
                f.write(f"Archivo: {os.path.basename(file_path)}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Sesión: {self.session_id}\n\n")
                f.write(ai_analysis)
            
            return {
                'success': True,
                'xml_file': result['output_file'],
                'analysis_file': analysis_file,
                'summary': result['content_summary'],
                'ai_analysis': ai_analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def chat_mode(self):
        """Modo chat interactivo"""
        print("\n💬 Modo Chat DocAI Platform")
        print("Comandos disponibles:")
        print("  - 'process <archivo>' : Procesar documento")
        print("  - 'list' : Listar archivos en input/")
        print("  - 'help' : Mostrar ayuda")
        print("  - 'exit' : Salir")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\nDocAI> ").strip()
                
                if user_input.lower() == 'exit':
                    print("👋 ¡Hasta luego!")
                    break
                
                elif user_input.lower() == 'help':
                    self.show_help()
                
                elif user_input.lower() == 'list':
                    self.list_input_files()
                
                elif user_input.lower().startswith('process '):
                    filename = user_input[8:].strip()
                    self.process_file_command(filename)
                
                else:
                    # Chat general con IA
                    response = self.invoke_bedrock(user_input)
                    print(f"\n🤖 DocAI: {response}")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
        📚 AYUDA DocAI Platform
        
        🔧 Comandos:
        • process <archivo>  - Procesar documento Word
        • list              - Ver archivos en input/
        • help              - Mostrar esta ayuda
        • exit              - Salir del programa
        
        📄 Formatos soportados:
        • .docx (Word 2007+)
        • .doc (Word 97-2003)
        
        📁 Directorios:
        • input/  - Coloca aquí tus documentos
        • output/ - Archivos procesados (XML + análisis)
        
        💡 Ejemplo:
        DocAI> process mi_documento.docx
        """
        print(help_text)
    
    def list_input_files(self):
        """Listar archivos en directorio input"""
        try:
            files = [f for f in os.listdir(INPUT_DIR) if f.endswith(('.docx', '.doc'))]
            if files:
                print(f"\n📁 Archivos en {INPUT_DIR}/:")
                for i, file in enumerate(files, 1):
                    print(f"  {i}. {file}")
            else:
                print(f"\n📁 No hay archivos Word en {INPUT_DIR}/")
                print("💡 Copia tus archivos .docx o .doc al directorio input/")
        except Exception as e:
            print(f"❌ Error listando archivos: {str(e)}")
    
    def process_file_command(self, filename):
        """Procesar archivo por comando"""
        try:
            file_path = os.path.join(INPUT_DIR, filename)
            
            if not os.path.exists(file_path):
                print(f"❌ Archivo no encontrado: {filename}")
                print("💡 Usa 'list' para ver archivos disponibles")
                return
            
            print(f"⏳ Procesando {filename}...")
            result = self.process_document_with_ai(file_path)
            
            if result['success']:
                print(f"✅ Procesamiento completado!")
                print(f"📄 XML: {os.path.basename(result['xml_file'])}")
                print(f"📊 Análisis: {os.path.basename(result['analysis_file'])}")
                print(f"📈 Resumen: {result['summary']}")
                print(f"\n🤖 Análisis IA:")
                print(result['ai_analysis'][:500] + "..." if len(result['ai_analysis']) > 500 else result['ai_analysis'])
            else:
                print(f"❌ Error: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error procesando archivo: {str(e)}")

def main():
    """Función principal"""
    try:
        # Inicializar DocAI Platform
        docai = DocAIPlatform()
        
        # Verificar argumentos de línea de comandos
        if len(sys.argv) > 1:
            if sys.argv[1] == '--process' and len(sys.argv) > 2:
                # Modo procesamiento directo
                file_path = sys.argv[2]
                result = docai.process_document_with_ai(file_path)
                print(json.dumps(result, indent=2))
            else:
                print("Uso: python3 docai_platform.py [--process archivo.docx]")
        else:
            # Modo chat interactivo
            docai.chat_mode()
            
    except Exception as e:
        print(f"❌ Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
