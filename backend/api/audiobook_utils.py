from csv import reader
import json

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from PIL import Image
import PyPDF2
from bs4 import BeautifulSoup 
import zipfile 
import re
import os
import cv2
import numpy as np
from pydantic import BaseModel
import easyocr


router = APIRouter(
    prefix="/audiobook_utils",
    tags=["audiobook_utils"],
    responses={404: {"description": "Not found"}},
)



easyocr_reader_en = None
easyocr_reader_jp = None
manga_ocr_model = None



def get_easyocr_en():
    global easyocr_reader_en
    if easyocr_reader_en is None:
        print("Ładowanie modelu EasyOCR (Angielski)...")
        easyocr_reader_en = easyocr.Reader(['en'], gpu=True)
    return easyocr_reader_en

def get_easyocr_ja():
    global easyocr_reader_ja
    if easyocr_reader_jp is None:
        print("Ładowanie modelu EasyOCR (Detektor)...")
        easyocr_reader_ja = easyocr.Reader(['ja', 'en'], gpu=True)
    return easyocr_reader_ja

def get_manga_ocr():
    global manga_ocr_model
    if manga_ocr_model is None:
        print("Ładowanie modelu manga-ocr (Japoński)...")
        from manga_ocr import MangaOcr
        manga_ocr_model = MangaOcr()
    return manga_ocr_model




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
        
@router.post("/detect-bubbles")
async def detect_bubbles_endpoint(file: UploadFile = File(...), language: str = Form(...)):
    """ ETAP 1: Tylko znajduje dymki i zwraca ich koordynaty (bez czytania tekstu) """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Brak pliku")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img_cv is None:
        raise HTTPException(status_code=400, detail="Niepoprawny format obrazu")

    img_height, img_width, _ = img_cv.shape
    reader = get_easyocr_en() if language == "en" else get_easyocr_ja()
    
    results = reader.readtext(img_cv, paragraph=False)
    mask = np.zeros((img_height, img_width), dtype=np.uint8)
    
    pad_x = int(img_width * 0.025) if language == "ja" else int(img_width * 0.04)
    pad_y = int(img_height * 0.04) if language == "ja" else int(img_height * 0.025)
    
    valid_boxes = []
    for (bbox, text, prob) in results:
        if prob < 0.02: continue 
        
        (tl, tr, br, bl) = bbox
        x_min = int(min(tl[0], bl[0]))
        y_min = int(min(tl[1], tr[1]))
        x_max = int(max(tr[0], br[0]))
        y_max = int(max(br[1], bl[1]))
        
        valid_boxes.append({"coords": (x_min, y_min, x_max, y_max)})
        cv2.rectangle(mask, 
                      (max(0, x_min - pad_x), max(0, y_min - pad_y)), 
                      (min(img_width, x_max + pad_x), min(img_height, y_max + pad_y)), 
                      255, -1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    blocks = []
    for cnt in contours:
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        
        cluster_boxes = []
        for box_data in valid_boxes:
            vx_min, vy_min, vx_max, vy_max = box_data["coords"]
            center_x = (vx_min + vx_max) // 2
            center_y = (vy_min + vy_max) // 2
            
            if cx <= center_x <= cx + cw and cy <= center_y <= cy + ch:
                cluster_boxes.append((vx_min, vy_min, vx_max, vy_max))
                
        if not cluster_boxes:
            continue
            
        margin = 15 
        final_x_min = max(0, min([b[0] for b in cluster_boxes]) - margin)
        final_y_min = max(0, min([b[1] for b in cluster_boxes]) - margin)
        final_x_max = min(img_width, max([b[2] for b in cluster_boxes]) + margin)
        final_y_max = min(img_height, max([b[3] for b in cluster_boxes]) + margin)
        
        blocks.append({
            "id": f"box_{len(blocks)}", # Unikalne ID do śledzenia we frontendzie
            "box": {
                "x": (final_x_min / img_width) * 100,
                "y": (final_y_min / img_height) * 100,
                "width": ((final_x_max - final_x_min) / img_width) * 100,
                "height": ((final_y_max - final_y_min) / img_height) * 100
            }
        })
        
    # Sortowanie z góry na dół, od prawej do lewej (klasyczny japoński format)
    blocks = sorted(blocks, key=lambda b: (b["box"]["y"], -b["box"]["x"]))
    
    return {"status": "success", "blocks": blocks}

@router.post("/transcribe-bubbles")
async def transcribe_bubbles_endpoint(
    file: UploadFile = File(...), 
    language: str = Form(...),
    boxes_data: str = Form(...) # JSON ze sprawdzonymi ramkami z Frontendu
):
    """ ETAP 2: Otrzymuje zdjęcie + zatwierdzone ramki i wyciąga z nich tekst """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Brak pliku")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width, _ = img_cv.shape
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    
    try:
        user_boxes = json.loads(boxes_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Zły format JSON dla ramek")

    results = []
    
    # Ładujemy model OCR tylko ten, który jest potrzebny
    if language == "ja":
        mocr = get_manga_ocr()
    else:
        reader = get_easyocr_en()
    
    for block in user_boxes:
        b_id = block["id"]
        box = block["box"] # x, y, width, height (w procentach!)
        
        # Przeliczamy procenty z powrotem na piksele
        x_min = int((box["x"] / 100) * img_width)
        y_min = int((box["y"] / 100) * img_height)
        x_max = int(((box["x"] + box["width"]) / 100) * img_width)
        y_max = int(((box["y"] + box["height"]) / 100) * img_height)
        
        if language == "ja":
            cropped_bubble = img_pil.crop((x_min, y_min, x_max, y_max))
            try:
                text = mocr(cropped_bubble)
            except Exception:
                text = "Błąd OCR"
        else:
            cropped_cv = img_cv[y_min:y_max, x_min:x_max]
            try:
                ocr_result = reader.readtext(cropped_cv, paragraph=True)
                text = " ".join([t for _, t in ocr_result]) if ocr_result else ""
            except Exception:
                text = "Błąd OCR"
                
        results.append({
            "id": b_id,
            "text": text
        })

    return {"status": "success", "transcriptions": results}