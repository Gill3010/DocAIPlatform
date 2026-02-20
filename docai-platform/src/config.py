"""
Configuración para DocAI Platform
"""
import os

# Configuración de AWS Bedrock - Modelo compatible
AWS_REGION = 'us-east-1'
BEDROCK_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'

# Configuración del sistema
SYSTEM_PROMPT = """You are DocAI Platform, an AI assistant specialized in processing Word documents and converting them to XML format. You help users extract, analyze, and transform document content efficiently.

Your capabilities include:
- Extracting text content from Word documents
- Converting document structure to XML
- Analyzing document formatting and metadata
- Providing structured output in XML format

Always respond in a helpful and professional manner."""

# Configuración de tokens
MAX_TOKENS = 4000
TEMPERATURE = 0.1

# Directorios
INPUT_DIR = '../input'
OUTPUT_DIR = '../output'
