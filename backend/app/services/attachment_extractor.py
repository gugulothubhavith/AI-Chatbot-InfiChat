import httpx
import os
import base64
import logging
import io
import mimetypes
from fastapi import HTTPException
from app.core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

# Base URL for the local Unstructured Omni-Parser
UNSTRUCTURED_URL = os.getenv("UNSTRUCTURED_URL", "http://unstructured-api:8000")
UNSTRUCTURED_API_KEY = os.getenv("UNSTRUCTURED_API_KEY", "local_dummy_key")

def parse_data_uri(data_uri: str):
    """
    Parses a data URI like 'data:image/png;base64,iVBORw...'
    Returns (mime_type, binary_data)
    """
    if not data_uri.startswith("data:"):
        raise ValueError("Invalid data URI format")

    try:
        header, encoded = data_uri.split(",", 1)
        mime_type = header.split(":", 1)[1].split(";", 1)[0]
        binary_data = base64.b64decode(encoded)
        return mime_type, binary_data
    except Exception as e:
        logger.error(f"Failed to decode base64 data URI: {e}")
        raise ValueError("Failed to parse attachment data")

async def process_attachment_via_unstructured(data_uri: str, file_name: Optional[str] = None) -> str:
    """
    Sends the base64 attachment to the highly advanced local Unstructured Omni-Parser.
    Returns structured Markdown.
    """
    try:
        mime_type, binary_data = parse_data_uri(data_uri)
    except ValueError as e:
        return f"Error: {str(e)}"
    
    # Guess extension for the multipart filename
    ext = mimetypes.guess_extension(mime_type) or ".bin"
    if mime_type == "text/plain":
        ext = ".txt"
        
    filename = file_name or f"attachment{ext}"
    
    logger.info(f"Sending {filename} ({mime_type}, {len(binary_data)} bytes) to Omni-Parser...")

    url = f"{UNSTRUCTURED_URL}/general/v0/general"
    
    headers = {
        "accept": "application/json",
        "unstructured-api-key": UNSTRUCTURED_API_KEY
    }
    
    # We use a file-like object for httpx
    files = {
        "files": (filename, io.BytesIO(binary_data), mime_type)
    }

    # Configuration for highly advanced, parallel parsing
    data = {
        "strategy": "auto", # 'auto' uses lightning-fast native parsing for Office docs, and heavy parallel layout parsing for PDFs/Images
        "output_format": "application/json", # Get JSON elements to format beautifully
        "chunking_strategy": "by_title", # Intelligent semantic chunking
        "split_pdf_page": "true", # Enables parallel PDF extraction
        "split_pdf_concurrency_level": "4", # Reduced to 4 workers to fit inside RTX 3050 4GB VRAM
        "split_pdf_allow_failed": "true" # Continue if a single page fails
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(url, headers=headers, data=data, files=files)
            if response.status_code != 200:
                logger.error(f"Unstructured API failed with status {response.status_code}: {response.text}")
                # Fallback to direct decoding for text/markdown if unstructured is unavailable
                if mime_type in ["text/plain", "text/markdown"]:
                    return binary_data.decode('utf-8', errors='replace')
                return f"[Failed to parse attachment. Error code: {response.status_code}]"
            
            elements = response.json()
            
            # Format the output elements into a cohesive Markdown document
            markdown_output = []
            for el in elements:
                el_type = el.get("type", "")
                text = el.get("text", "")
                
                if el_type == "Title":
                    markdown_output.append(f"\n## {text}\n")
                elif el_type == "Header":
                    markdown_output.append(f"\n### {text}\n")
                elif el_type == "ListItem":
                    markdown_output.append(f"- {text}")
                elif el_type == "Table":
                    # Unstructured often provides html for tables in the metadata
                    metadata = el.get("metadata", {})
                    if "text_as_html" in metadata:
                        markdown_output.append(f"\n{metadata['text_as_html']}\n")
                    else:
                        markdown_output.append(f"\n{text}\n")
                else:
                    markdown_output.append(text)
            
            final_text = "\n".join(markdown_output).strip()
            
            if not final_text:
                return "[Attachment successfully parsed but no readable text was found.]"
            
            return final_text

        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting Unstructured API {exc.request.url!r}.")
            
            # Pure text fallback
            if mime_type in ["text/plain", "text/markdown"]:
                return binary_data.decode('utf-8', errors='replace')
                
            return "[Error: Unstructured Omni-Parser is unreachable. Please ensure the unstructured-api Docker container is running.]"
