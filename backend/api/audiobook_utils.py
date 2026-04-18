from fastapi import APIRouter, UploadFile, File, HTTPException
import PyPDF2
from bs4 import BeautifulSoup 
import zipfile 
import re

router = APIRouter(
    prefix="/audiobook_utils",
    tags=["audiobook_utils"],
    responses={404: {"description": "Not found"}},
)

    
import re

def clean_extracted_text(text: str) -> str:
    # 1. Usuwanie znanych śmieci
    text = re.sub(r'Page\|\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Goldenagato\s*\|\s*(https?://)?mp4directs\.com', '', text, flags=re.IGNORECASE)
    reklama = r'Stay up to date On Light Novels by Downloading our mobile App\nZerobooks\nDownload all your Favourite Light Novels\nJnovels\.com'
    text = re.sub(reklama, '', text, flags=re.IGNORECASE)
    text = text.replace('\u0000', '')
    
    # Ujednolicenie znaków nowej linii
    text = text.replace('\r\n', '\n')
    
    # 2. Zabezpieczenie istniejących, jawnych akapitów (jeśli plik miał podwójne entery)
    text = re.sub(r'\n{2,}', ' __PARA__ ', text)
    
    # 3. INTELIGENTNE WYKRYWANIE AKAPITÓW Z PDF
    # Zasada A: Jeśli linia kończy się kropką, pytajnikiem, wykrzyknikiem lub cudzysłowem, 
    # a następna zaczyna od dużej litery lub cudzysłowu -> to jest nowy akapit.
    text = re.sub(r'([.!?\”\"\'’])\s*\n\s*([A-Z\”\"\'‘“])', r'\1 __PARA__ \2', text)
    
    # Zasada B: Jeśli jakakolwiek nowa linia zaczyna się od znaku dialogu (cudzysłowu),
    # wymuś nowy akapit (nawet jeśli poprzednia linia nie miała kropki, np. po tytule rozdziału).
    text = re.sub(r'\n\s*([\”\"\'‘“])', r' __PARA__ \1', text)
    
    # 4. Zniszcz wszystkie pozostałe, pojedyncze entery (sklejanie przerwanych zdań w środku akapitu z PDF)
    text = text.replace('\n', ' ')
    
    # 5. Zredukuj wszystkie wielokrotne spacje lub tabulacje do pojedynczej spacji
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 6. Przywróć prawdziwe akapity jako idealne podwójne entery
    text = text.replace(' __PARA__ ', '\n\n')
    
    # Na koniec, upewnijmy się, że nie ma "potrójnych" enterów, które mogły powstać w procesie
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

@router.get("/test")
async def test_endpoint():
    return {"message": "Audiobook utils endpoint is working!"}

@router.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    text = ""
    
    safe_filename = file.filename or ""
    extension = safe_filename.split('.')[-1].lower() if '.' in safe_filename else ""
    
    try:
        # --- TXT ---
        if extension == "txt":
            content = await file.read()
            text = content.decode("utf-8", errors="ignore")
            
        # --- PDF ---
        elif extension == "pdf":
            pdf_reader = PyPDF2.PdfReader(file.file)
            
            if pdf_reader.is_encrypted:
                try:
                    pdf_reader.decrypt('')
                except Exception:
                    pass 
                    
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    

        elif extension == "epub":

            with zipfile.ZipFile(file.file) as archive:
                for item in archive.namelist():
                    if item.lower().endswith(('.html', '.xhtml', '.htm')):
                        html_content = archive.read(item)
                        soup = BeautifulSoup(html_content, 'html.parser')
                        text += soup.get_text(separator='\n') + "\n"
            
        else:
            raise HTTPException(status_code=400, detail=f"Nieobsługiwany format pliku: {extension}")
            
        
        text = clean_extracted_text(text)
        print(f"Extracted text length: {len(text)} characters")
        return {"text": text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas przetwarzania pliku: {str(e)}")
        
    finally:
        file.file.close()