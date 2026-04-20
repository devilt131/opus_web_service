from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import logging
import json
import time
from datetime import datetime

from database import engine, get_db
from models import Base, User
from schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from auth import create_user, authenticate_user, create_access_token, get_user_by_username
from rezumator import Rezumator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=engine)


rez = Rezumator()
app = FastAPI(
    title="Opus API",
    description="Интеллектуальный анализ текста",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBearer()

SECRET_KEY = "opus-secret-key-2026-change-in-production"
ALGORITHM = "HS256"


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000, description="Текст для анализа")
    max_length: int = Field(50, ge=10, le=200, description="Максимальная длина суммаризации")
    min_length: int = Field(30, ge=5, le=100, description="Минимальная длина суммаризации")


class AnalyzeResponse(BaseModel):
    statistics: dict
    summary: str
    sentiment: dict
    keywords: list
    title: str
    compression: float


@app.get('/')
async def root():
    return {
        'service': 'Opus API',
        'version': '1.0.0',
        'status': 'running',
        'docs': '/docs'
    }


@app.get('/health')
async def health():
    return {
        'status': 'healthy',
        't5_loaded': rez.t5_model is not None,
        'morph_loaded': rez.morph is not None
    }


@app.post('/analyze', response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Текст не может быть пустым")
        
        words_count = len(text.split())
        if words_count < 5:
            raise HTTPException(
                status_code=400, 
                detail=f"Слишком мало слов: {words_count}. Минимум 5 слов"
            )
        
        result = rez.full_analysis(text)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        logger.info(f"Анализ выполнен: {words_count} слов")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@app.post('/export/txt')
async def export_txt(request: AnalyzeRequest):
    result = rez.full_analysis(request.text)
    
    content = f"""OPUS TEXT ANALYSIS REPORT
========================================

TITLE:
{result['title']}

SUMMARY:
{result['summary']}

COMPRESSION:
{result['compression']}%

SENTIMENT:
{result['sentiment']['sentiment']}
Confidence: {result['sentiment']['confidence']:.1%}
Positive words: {result['sentiment']['positive_words']}
Negative words: {result['sentiment']['negative_words']}

KEYWORDS:
{', '.join([f"{kw['word']} ({kw['frequency']})" for kw in result['keywords']])}

STATISTICS:
Characters: {result['statistics']['total_characters']}
Characters without spaces: {result['statistics']['characters_without_spaces']}
Words: {result['statistics']['words']}
Unique words: {result['statistics']['unique_words']}
Sentences: {result['statistics']['sentences']}
Average word length: {result['statistics']['average_word_length']}
Average sentence length: {result['statistics']['average_sentence_length']}

Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    filename = f"opus_analysis_{int(time.time())}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return FileResponse(filename, media_type='text/plain', filename=filename)


@app.post('/export/json')
async def export_json(request: AnalyzeRequest):
    result = rez.full_analysis(request.text)
    
    export_data = {
        'title': result['title'],
        'summary': result['summary'],
        'compression': result['compression'],
        'sentiment': result['sentiment'],
        'keywords': result['keywords'],
        'statistics': result['statistics'],
        'exported_at': datetime.now().isoformat()
    }
    
    filename = f"opus_analysis_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return FileResponse(filename, media_type='application/json', filename=filename)


@app.post('/export/pdf')
async def export_pdf(request: AnalyzeRequest):
    result = rez.full_analysis(request.text)
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed. Run: pip install reportlab")
    
    filename = f"opus_analysis_{int(time.time())}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=30)
    story.append(Paragraph("OPUS TEXT ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>Title:</b><br/>{result['title']}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Summary:</b><br/>{result['summary']}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Compression:</b> {result['compression']}%", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Sentiment:</b> {result['sentiment']['sentiment']}", styles['Normal']))
    story.append(Spacer(1, 5))
    
    keywords_text = ", ".join([f"{kw['word']} ({kw['frequency']})" for kw in result['keywords']])
    story.append(Paragraph(f"<b>Keywords:</b><br/>{keywords_text}", styles['Normal']))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"<b>Statistics:</b><br/>", styles['Normal']))
    story.append(Paragraph(f"Characters: {result['statistics']['total_characters']}", styles['Normal']))
    story.append(Paragraph(f"Words: {result['statistics']['words']}", styles['Normal']))
    story.append(Paragraph(f"Sentences: {result['statistics']['sentences']}", styles['Normal']))
    
    doc.build(story)
    
    return FileResponse(filename, media_type='application/pdf', filename=filename)


@app.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    
    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    
    try:
        user = create_user(db, user_data.username, user_data.email, user_data.password)
        logger.info(f"Зарегистрирован новый пользователь: {user.username}")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")


@app.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token({"sub": user.username, "user_id": user.id})
    
    logger.info(f"Вход пользователя: {user.username}")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        email=user.email
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError as e:
        logger.warning(f"Ошибка декодирования токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@app.get("/profile", response_model=UserResponse)
async def profile(current_user: User = Depends(get_current_user)):
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )


@app.get("/stats")
async def get_stats():
    return {
        "total_analyses": 0,
        "models": {
            "t5": rez.t5_model is not None,
            "morph": rez.morph is not None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)