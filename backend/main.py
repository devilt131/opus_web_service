from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import json
import time
import os
from datetime import datetime

from database import engine, get_db
from models import Base, User, Analysis
from schemas import UserRegister, UserLogin, TokenResponse, UserResponse, HistoryItem, ExportRequest
from export_utils import build_pdf_report
from auth import (
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_username,
    get_user_by_email,
    get_current_user,
    get_optional_user,
)
from rezumator import Rezumator

# Optional imports with fallbacks
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PyPDF2 = None
    PDF_SUPPORT = False
    print("Warning: PyPDF2 not installed. PDF support disabled.")

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    Document = None
    DOCX_SUPPORT = False
    print("Warning: python-docx not installed. DOCX support disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Rezumator
rez = Rezumator()
app = FastAPI(title="Opus API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    ref_text: Optional[str] = Field(None, description="reference text for plagiarism")


class AnalyzeResponse(BaseModel):
    stats: dict
    summary: str
    keywords: list
    title: str
    plan: str
    compression: float
    entities: dict
    plagiarism: dict = Field(default_factory=dict)


def _save_analysis(db: Session, user: User, text: str, result: dict) -> None:
    record = Analysis(
        user_id=user.id,
        text_preview=text[:200],
        summary=result.get("summary", ""),
        title=result.get("title", ""),
    )
    db.add(record)
    db.commit()


def _history_items(db: Session, user_id: int) -> List[HistoryItem]:
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        HistoryItem(
            id=row.id,
            title=row.title or "Untitled",
            preview=row.text_preview or "",
            summary=row.summary or "",
            date=row.created_at.isoformat() if row.created_at else "",
        )
        for row in rows
    ]


@app.get('/')
async def root():
    return {'service': 'Opus API', 'status': 'running', 'docs': '/docs'}


@app.get('/health')
async def health():
    return {
        'status': 'ok',
        'model': rez.model is not None,
        'morph': rez.morph is not None,
        'ner': rez.ner_ok
    }


@app.post('/analyze', response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    try:
        text = req.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="empty text")

        words = len(text.split())
        if words < 5:
            raise HTTPException(status_code=400, detail=f"too few words: {words}")

        result = rez.full(text, req.ref_text)

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        if user:
            _save_analysis(db, user, text, result)

        logger.info(f"analyzed: {words} words")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error: {e}")
        raise HTTPException(status_code=500, detail="server error")


@app.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    ref_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    filename = (file.filename or "").lower()
    text = ''

    if filename.endswith('.txt'):
        cont = await file.read()
        text = cont.decode('utf-8')

    elif filename.endswith('.pdf'):
        if not PDF_SUPPORT:
            raise HTTPException(status_code=400, detail="PDF support not available. Install PyPDF2.")
        try:
            reader = PyPDF2.PdfReader(file.file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF parsing error: {e}")

    elif filename.endswith('.docx'):
        if not DOCX_SUPPORT:
            raise HTTPException(status_code=400, detail="DOCX support not available. Install python-docx.")
        try:
            doc = Document(file.file)
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX parsing error: {e}")

    else:
        raise HTTPException(status_code=400, detail="Only TXT, PDF, DOCX files are allowed")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found in file")

    if len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="text too short")

    ref = ref_text.strip() if ref_text and ref_text.strip() else None
    result = rez.full(text, ref)
    if user:
        _save_analysis(db, user, text, result)
    return result


def _resolve_export_result(req: ExportRequest) -> dict:
    cached = req.result
    if cached and isinstance(cached, dict) and cached.get("summary"):
        return cached
    return rez.full(req.text.strip(), req.ref_text)


def _build_report_content(res: dict) -> str:
    plag = res.get('plagiarism') or {}
    return f"""OPUS REPORT
================================

TITLE: {res['title']}

SUMMARY:
{res['summary']}

COMPRESSION: {res['compression']}%

PLAN:
{res['plan']}

KEYWORDS:
{', '.join([f"{k['word']} ({k['freq']})" for k in res['keywords']]) if res['keywords'] else 'none'}

STATS:
Chars: {res['stats']['chars']}
Words: {res['stats']['words']}
Sentences: {res['stats']['sentences']}
Unique words: {res['stats']['unique']}
Average word length: {res['stats']['avg_w_len']}
Average sentence length: {res['stats']['avg_s_len']}

ENTITIES:
Persons: {', '.join([p['text'] for p in res['entities']['persons']]) if res['entities']['persons'] else 'none'}
Organizations: {', '.join([o['text'] for o in res['entities']['orgs']]) if res['entities']['orgs'] else 'none'}
Locations: {', '.join([l['text'] for l in res['entities']['locs']]) if res['entities']['locs'] else 'none'}
Dates: {', '.join([d['text'] for d in res['entities']['dates']]) if res['entities']['dates'] else 'none'}

PLAGIARISM:
Uniqueness: {plag.get('uniqueness', 'n/a')}%
Similarity: {plag.get('similarity', 'n/a')}
Common words: {', '.join(plag.get('common', [])) if plag.get('common') else 'none'}

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


@app.post('/export/txt')
async def export_txt(req: ExportRequest):
    res = _resolve_export_result(req)
    content = _build_report_content(res)

    filename = os.path.join(EXPORT_DIR, f"opus_{int(time.time())}.txt")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    return FileResponse(filename, media_type='text/plain', filename=os.path.basename(filename))


@app.post('/export/json')
async def export_json(req: ExportRequest):
    res = dict(_resolve_export_result(req))
    res['exported'] = datetime.now().isoformat()

    filename = os.path.join(EXPORT_DIR, f"opus_{int(time.time())}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    return FileResponse(filename, media_type='application/json', filename=os.path.basename(filename))


@app.post('/export/pdf')
async def export_pdf(req: ExportRequest):
    try:
        import reportlab  # noqa: F401
    except ImportError:
        raise HTTPException(status_code=500, detail="ReportLab not installed. Run: pip install reportlab")

    res = _resolve_export_result(req)
    filename = os.path.join(EXPORT_DIR, f"opus_{int(time.time())}.pdf")
    try:
        build_pdf_report(res, filename)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail="PDF export failed")

    return FileResponse(filename, media_type='application/pdf', filename=os.path.basename(filename))


@app.post('/register', response_model=UserResponse, status_code=201)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = create_user(db, data.username, data.email, data.password)
        logger.info(f"User registered: {user.username}")
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Could not create user")


@app.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Wrong username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.username, "id": user.id})
    logger.info(f"User logged in: {user.username}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        email=user.email
    )


@app.get("/profile", response_model=UserResponse)
async def profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )


@app.get("/history", response_model=List[HistoryItem])
async def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _history_items(db, current_user.id)


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total = db.query(Analysis).count()
    return {
        "total_analyses": total,
        "model_loaded": rez.model is not None,
        "morph_loaded": rez.morph is not None,
        "ner_loaded": rez.ner_ok,
        "pdf_support": PDF_SUPPORT,
        "docx_support": DOCX_SUPPORT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
