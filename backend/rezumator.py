import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import warnings
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
import nltk
from collections import Counter
import json
from datetime import datetime


try:
    import pymorphy3
    MORPH_ANALYZER = pymorphy3.MorphAnalyzer
except ImportError:
    try:
        import pymorphy2
        MORPH_ANALYZER = pymorphy2.MorphAnalyzer
    except ImportError:
        MORPH_ANALYZER = None


nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('vader_lexicon', quiet=True)

warnings.filterwarnings("ignore", category=FutureWarning)


class Rezumator:  
    def __init__(self):
        self.dots = ['.', '!', '?']
        self.sia = SentimentIntensityAnalyzer()
        self.lemmatizer = WordNetLemmatizer()
        self.russian_stopwords = set(stopwords.words('russian'))
        self.t5_model = None
        self.t5_tokenizer = None
        
        try:
            model_name = "IlyaGusev/rut5_base_sum_gazeta"
            self.t5_tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.t5_model = T5ForConditionalGeneration.from_pretrained(model_name)
            print("T5 модель загружена")
        except Exception as e:
            print(f"Не удалось загрузить T5: {e}")

        if MORPH_ANALYZER:
            try:
                self.morph = MORPH_ANALYZER()
                print("Морфологический анализатор загружен")
            except Exception as e:
                print(f"Ошибка инициализации морфологического анализатора: {e}")
                self.morph = None
        else:
            print("Морфологический анализатор не установлен")
            self.morph = None

    def normalize_word(self, word):
        if not self.morph or not word or not isinstance(word, str):
            return word
            
        try:
            word_clean = word.strip('.,!?;:()[]{}"\'').lower()
            if not word_clean:
                return word
                
            parses = self.morph.parse(word_clean)
            
            if parses and len(parses) > 0:
                parsed = parses[0]
                return parsed.normal_form
            else:
                return word_clean
                
        except Exception:
            return word

    def normalize_text(self, text):
        if not text or not self.morph:
            return text
            
        try:
            words = word_tokenize(text)
            normalized_words = []
            
            for word in words:
                normalized = self.normalize_word(word)
                normalized_words.append(normalized)
                
            return ' '.join(normalized_words)
            
        except Exception:
            return text

    def get_statistics(self, text):
        if not text:
            return {
                'total_characters': 0,
                'characters_without_spaces': 0,
                'sentences': 0,
                'words': 0,
                'unique_words': 0,
                'average_word_length': 0,
                'average_sentence_length': 0
            }
        
        normalized_text = self.normalize_text(text) if self.morph else text
        text_without_spaces = text.replace(" ", "").replace("\n", "").replace("\t", "")
        
        sentences = 0
        for char in text:
            if char in self.dots:
                sentences += 1
        
        words = word_tokenize(text)
        unique_words = set(word_tokenize(normalized_text))
        
        return {
            'total_characters': len(text),
            'characters_without_spaces': len(text_without_spaces),
            'sentences': sentences,
            'words': len(words),
            'unique_words': len(unique_words),
            'average_word_length': round(sum(len(word) for word in words) / len(words), 2) if words else 0,
            'average_sentence_length': round(len(words) / sentences, 2) if sentences else 0
        }

    def summarize(self, text, max_length=50, min_length=30):
        if not text:
            return "Текст не предоставлен"
        
        if not self.t5_model or not self.t5_tokenizer:
            return "Ошибка: T5 модель не загружена"
        
        try:
            text_preview = text[:512]
            input_text = f"summarize: {text_preview}"
            
            inputs = self.t5_tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.t5_model.generate(
                    inputs["input_ids"],
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=2
                )
            
            summary = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return summary.strip()
            
        except Exception as e:
            return f"Ошибка суммаризации: {str(e)}"

    def get_compression(self, original_text, summary):
        if not original_text or not summary:
            return 0
        original_words = len(original_text.split())
        summary_words = len(summary.split())
        if original_words == 0:
            return 0
        return round((1 - summary_words / original_words) * 100, 1)

    def analyze_sentiment(self, text):
        if not text:
            return {
                'sentiment': 'НЕИЗВЕСТНО',
                'score': 0,
                'positive_words': 0,
                'negative_words': 0,
                'confidence': 0
            }
        
        try:
            if self.morph:
                words = word_tokenize(text.lower())
                normalized_words = [self.normalize_word(word) for word in words]
                words_set = set(normalized_words)
            else:
                words_set = set(word_tokenize(text.lower()))
            
            positive_words = {   
                'хорошо', 'отлично', 'прекрасно', 'замечательно', 'великолепно', 'идеально',
                'безупречно', 'превосходно', 'блестяще', 'чудесно', 'восхитительно', 'успех',
                'достижение', 'победа', 'триумф', 'результат', 'прогресс', 'развитие', 'рост',
                'улучшение', 'прорыв', 'качественный', 'профессиональный', 'надежный', 'эффективный',
                'удобный', 'полезный', 'функциональный', 'практичный', 'инновационный', 'рад',
                'счастлив', 'восторг', 'удовольствие', 'ликование', 'восхищение', 'веселье',
                'упоение', 'эйфория', 'блаженство', 'торжество', 'любовь', 'обожание', 'нежность',
                'страсть', 'привязанность', 'симпатия', 'влюбленность', 'преданность', 'уважение',
                'ласка', 'надежда', 'оптимизм', 'уверенность', 'вера', 'ожидание', 'перспектива',
                'предвкушение', 'гордость', 'достоинство', 'самоуважение', 'честь', 'величие',
                'достигнуть', 'рекомендую', 'советую', 'предлагаю', 'одобряю', 'поддерживаю',
                'поощряю', 'приветствую', 'согласен', 'разделяю'
            }
            
            negative_words = {
                'плохо', 'тоска', 'ужасно', 'кошмарно', 'отвратительно', 'скверно', 'неудовлетворительно',
                'неприемлемо', 'недопустимо', 'катастрофически', 'плачевно', 'проблема', 'ошибка',
                'недочет', 'недоработка', 'дефект', 'брак', 'сбой', 'неполадка', 'трудность',
                'препятствие', 'помеха', 'злой', 'раздраженный', 'яростный', 'негодующий',
                'взбешенный', 'возмущенный', 'разъяренный', 'сердитый', 'недовольный', 'раздражение',
                'ярость', 'грустный', 'печальный', 'тоскливый', 'унылый', 'скорбный', 'депрессивный',
                'подавленный', 'несчастный', 'одинокий', 'безнадежный', 'отчаяние', 'боязнь',
                'страх', 'опасение', 'тревога', 'паника', 'испуг', 'ужас', 'напряжение', 'нервозность',
                'беспокойство', 'отвращение', 'омерзение', 'неприязнь', 'антипатия', 'ненависть',
                'презрение', 'пренебрежение', 'брезгливость', 'критикую', 'осуждаю', 'обвиняю',
                'жалуюсь', 'протестую', 'возражаю', 'не согласен', 'опровергаю', 'отрицаю',
                'оспариваю', 'отказываюсь', 'отвергаю', 'отклоняю', 'запрещаю', 'не позволяю',
                'не рекомендую', 'не советую', 'не одобряю', 'не поддерживаю'
            }
            
            pos_count = len(words_set.intersection(positive_words))
            neg_count = len(words_set.intersection(negative_words))
            
            total = pos_count + neg_count
            if total > 0:
                score = (pos_count - neg_count) / total
            else:
                score = 0
            
            if score > 0.1:
                sentiment = "ПОЛОЖИТЕЛЬНЫЙ"
            elif score < -0.1:
                sentiment = "ОТРИЦАТЕЛЬНЫЙ"
            else:
                sentiment = "НЕЙТРАЛЬНЫЙ"
            
            return {
                'sentiment': sentiment,
                'score': round(score, 3),
                'positive_words': pos_count,
                'negative_words': neg_count,
                'confidence': abs(round(score, 3))
            }
            
        except Exception:
            return {
                'sentiment': 'НЕИЗВЕСТНО',
                'score': 0,
                'positive_words': 0,
                'negative_words': 0,
                'confidence': 0
            }

    def extract_keywords(self, text, top_n=10):
        if not text:
            return []
        
        try:
            words = word_tokenize(text.lower())
            
            filtered_words = []
            for word in words:
                if (word.isalnum() 
                    and word not in self.russian_stopwords 
                    and len(word) > 2):
                    filtered_words.append(word)
            
            if self.morph:
                normalized_words = []
                for word in filtered_words:
                    normalized = self.normalize_word(word)
                    normalized_words.append(normalized)
            else:
                normalized_words = filtered_words
            
            word_freq = Counter(normalized_words)
            
            keywords = []
            total_words = len(normalized_words)
            
            for word, freq in word_freq.most_common(top_n):
                score = freq / total_words if total_words > 0 else 0
                    
                keywords.append({
                    'word': word,
                    'frequency': freq,
                    'score': round(score, 4)
                })
            
            return keywords
            
        except Exception:
            return []

    def generate_title(self, text):
        if not text:
            return "Анализ текста"
            
        if not self.t5_model:
            keywords = self.extract_keywords(text, top_n=3)
            if keywords and len(keywords) > 0:
                main_words = [kw['word'] for kw in keywords[:2]]
                return " ".join(main_words).capitalize()
            return "Анализ текста"
        
        try:
            text_preview = text[:200].strip()
            input_text = f"заголовок: {text_preview}"
            
            inputs = self.t5_tokenizer(
                input_text,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.t5_model.generate(
                    inputs["input_ids"],
                    max_length=20,
                    min_length=3,
                    num_beams=4,
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True,
                    early_stopping=True,
                    no_repeat_ngram_size=2
                )
            
            title = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
            title = title.strip()

            prefixes = ["заголовок:", "Заголовок:", "Название:", "название:"]
            for prefix in prefixes:
                if title.lower().startswith(prefix.lower()):
                    title = title[len(prefix):].strip()

            title = title.replace('"', '').replace("'", "").replace('«', '').replace('»', '')

            for char in ['.', ',', ';', ':', '-', '–', '—']:
                if char in title:
                    parts = title.split(char)
                    if parts[0].strip():
                        title = parts[0].strip()
                        break
            
            title = ' '.join(title.split())
            
            if title and len(title) > 1:
                title = title[0].upper() + title[1:]

            words = title.split()
            if len(words) > 8:
                title = ' '.join(words[:8])
                title = title.rstrip(' ,;:-')
            
            if not title or len(title) < 4 or len(words) < 2:
                keywords = self.extract_keywords(text, top_n=3)
                if keywords and len(keywords) > 0:
                    main_words = [kw['word'] for kw in keywords[:2]]
                    return " ".join(main_words).capitalize()
                return "Программирование на Python"
            
            return title
    
        except Exception as e:
            print(f"Ошибка генерации заголовка: {e}")
            keywords = self.extract_keywords(text, top_n=2)
            if keywords and len(keywords) > 0:
                main_words = [kw['word'] for kw in keywords[:2]]
                return " ".join(main_words).capitalize()
            return "Анализ текста"

    def full_analysis(self, text):
        if not text or len(text.strip()) < 10:
            return {
                'error': 'Текст слишком короткий (минимум 10 символов)',
                'statistics': self.get_statistics(text) if text else {},
                'summary': 'Невозможно создать краткое содержание',
                'sentiment': self.analyze_sentiment(text) if text else {},
                'keywords': [],
                'title': 'Анализ текста',
                'compression': 0
            }
        
        stats = self.get_statistics(text)
        summary = self.summarize(text)
        sentiment = self.analyze_sentiment(text)
        keywords = self.extract_keywords(text, top_n=5)
        title = self.generate_title(text)
        compression = self.get_compression(text, summary)
        
        return {
            'statistics': stats,
            'summary': summary,
            'sentiment': sentiment,
            'keywords': keywords,
            'title': title,
            'compression': compression
        }

    def save_to_json(self, text, filename="analysis_result.json"):
        result = self.full_analysis(text)
        result['timestamp'] = datetime.now().isoformat()
        result['text_preview'] = text[:200] + ('...' if len(text) > 200 else '')
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return {"status": "success", "filename": filename}
        except Exception as e:
            return {"status": "error", "message": str(e)}