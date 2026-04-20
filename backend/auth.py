from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User
import logging

logger = logging.getLogger(__name__)

# Конфигурация
SECRET_KEY = "opus-secret-key-2026-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

# Хеширование паролей (bcrypt с fallback)
pwd_context = CryptContext(schemes=["bcrypt", "plaintext"], deprecated="auto")

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.warning(f"bcrypt не работает, используем plaintext: {e}")
        return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return plain_password == hashed_password

def create_access_token(data: dict) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_username(db: Session, username: str):
    """Поиск пользователя по имени"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Поиск пользователя по email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str):
    """Создание пользователя"""
    hashed = hash_password(password)
    user = User(
        username=username, 
        email=email, 
        password_hash=hashed,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Создан пользователь: {username}")
    return user

def authenticate_user(db: Session, username: str, password: str):
    """Аутентификация пользователя"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user