import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import warnings
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
import os
from collections import Counter
import json
from datetime import datetime
import re
from natasha import (
    Doc,
    NewsEmbedding,
    NewsNERTagger,
    NewsMorphTagger,
    NewsSyntaxParser,
    Segmenter,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Setup NLTK data path
NLTK_DATA_PATH = os.path.join(os.path.dirname(__file__), 'nltk_data')
os.makedirs(NLTK_DATA_PATH, exist_ok=True)
nltk.data.path.append(NLTK_DATA_PATH)

# Download required NLTK data
for resource in ['punkt', 'stopwords', 'wordnet']:
    try:
        if resource == 'punkt':
            nltk.data.find(f'tokenizers/{resource}')
        else:
            nltk.data.find(f'corpora/{resource}')
    except LookupError:
        nltk.download(resource, download_dir=NLTK_DATA_PATH, quiet=True)

# Try to import pymorphy
try:
    import pymorphy3
    MORPH_ANALYZER = pymorphy3.MorphAnalyzer
except ImportError:
    try:
        import pymorphy2
        MORPH_ANALYZER = pymorphy2.MorphAnalyzer
    except ImportError:
        MORPH_ANALYZER = None
        print("Warning: pymorphy2/pymorphy3 not installed")

warnings.filterwarnings("ignore", category=FutureWarning)


class Rezumator:
    def __init__(self):
        self.dots = ['.', '!', '?']
        self.stop_words = set(stopwords.words('russian'))
        
        self.bad_words = set([
            'просто', 'как', 'это', 'очень', 'так', 'вот', 'даже', 'ещё',
            'уже', 'только', 'если', 'когда', 'потом', 'тут', 'там', 'вдруг',
            'конечно', 'наверное', 'казалось', 'стало', 'стал', 'начала',
            'начал', 'совсем', 'чуть', 'почти', 'прямо', 'сразу', 'наконец'
        ])
        self.title_stop_words = self.stop_words | {
            'текст', 'система', 'документ', 'анализ', 'обработка', 'данные',
            'работа', 'процесс', 'информация', 'материал', 'статья', 'раздел',
            'часть', 'вид', 'тип', 'форма', 'способ', 'метод', 'результат',
            'пример', 'случай', 'вопрос', 'ответ', 'задача', 'цель', 'средство',
            'резюмирование', 'суммаризация', 'ключевое', 'слово', 'тема',
            'основной', 'главный', 'общий', 'новый', 'старый', 'первый',
            'второй', 'третий', 'много', 'мало', 'несколько', 'разный',
        }
        
        self.model = None
        self.tokenizer = None
        
        # Load T5 model (fixed from BART)
        try:
            name = "IlyaGusev/rut5_base_sum_gazeta"
            self.tokenizer = T5Tokenizer.from_pretrained(name)
            self.model = T5ForConditionalGeneration.from_pretrained(name)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Model loading error: {e}")
            self.model = None
            self.tokenizer = None

        # Initialize morphological analyzer
        if MORPH_ANALYZER:
            try:
                self.morph = MORPH_ANALYZER()
                print("Morphological analyzer loaded")
            except Exception as e:
                print(f"Morph error: {e}")
                self.morph = None
        else:
            self.morph = None
        
        # Initialize NER pipeline
        self.segmenter = None
        self.morph_tagger = None
        self.syntax_parser = None
        self.ner_tagger = None
        self.ner_ok = False
        try:
            emb = NewsEmbedding()
            self.segmenter = Segmenter()
            self.morph_tagger = NewsMorphTagger(emb)
            self.syntax_parser = NewsSyntaxParser(emb)
            self.ner_tagger = NewsNERTagger(emb)
            self.ner_ok = True
            print("NER loaded")
        except Exception as e:
            print(f"NER error: {e}")

    def norm_word(self, w):
        if not self.morph or not w or not isinstance(w, str):
            return w
        try:
            w2 = w.strip('.,!?;:()[]{}"\'').lower()
            if not w2:
                return w
            p = self.morph.parse(w2)
            if p and len(p) > 0:
                return p[0].normal_form
            else:
                return w2
        except Exception:
            return w

    def norm_text(self, t):
        if not t or not self.morph:
            return t
        try:
            words = word_tokenize(t)
            res = []
            for w in words:
                res.append(self.norm_word(w))
            return ' '.join(res)
        except Exception:
            return t

    def get_stats(self, t):
        if not t:
            return {
                'chars': 0,
                'chars_no_space': 0,
                'sentences': 0,
                'words': 0,
                'unique': 0,
                'avg_w_len': 0,
                'avg_s_len': 0
            }
        no_space = t.replace(" ", "").replace("\n", "").replace("\t", "")
        sents = 0
        for c in t:
            if c in self.dots:
                sents += 1
        words = word_tokenize(t)
        uniq = set(word_tokenize(self.norm_text(t))) if self.morph else set(words)
        return {
            'chars': len(t),
            'chars_no_space': len(no_space),
            'sentences': sents,
            'words': len(words),
            'unique': len(uniq),
            'avg_w_len': round(sum(len(w) for w in words) / len(words), 2) if words else 0,
            'avg_s_len': round(len(words) / sents, 2) if sents else 0
        }

    def get_comp(self, orig, summ):
        if not orig or not summ:
            return 0
        ow = len(orig.split())
        sw = len(summ.split())
        if ow == 0:
            return 0
        return round((1 - sw / ow) * 100, 1)

    def _extr(self, t):
        s = sent_tokenize(t)
        if len(s) <= 2:
            return t
        return ' '.join(s[:2])

    def summ(self, t, max_len=60, min_len=15):
        if not t or len(t.strip()) < 10:
            return "text too short"
        if not self.model or not self.tokenizer:
            return self._extr(t)
        try:
            inp = self.tokenizer(t[:1000], return_tensors="pt", max_length=512, truncation=True, padding=True)
            with torch.no_grad():
                out = self.model.generate(
                    inp["input_ids"],
                    max_length=max_len,
                    min_length=min_len,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    repetition_penalty=2.0
                )
            res = self.tokenizer.decode(out[0], skip_special_tokens=True)
            return res.strip() if res else self._extr(t)
        except Exception as e:
            print(f"Summ error: {e}")
            return self._extr(t)

    def get_keywords(self, t, top=10):
        if not t:
            return []
        try:
            words = word_tokenize(t.lower())
            good = []
            for w in words:
                if (w.isalnum() 
                    and w not in self.stop_words 
                    and w not in self.bad_words
                    and len(w) > 2):
                    good.append(w)
            if self.morph:
                norm = []
                for w in good:
                    norm.append(self.norm_word(w))
            else:
                norm = good
            freq = Counter(norm)
            keys = []
            total = len(norm)
            for w, f in freq.most_common(top):
                score = f / total if total > 0 else 0
                keys.append({'word': w, 'freq': f, 'score': round(score, 4)})
            return keys
        except Exception:
            return []
    
    def extract_urls(self, text):
        pattern = r'https?://[^\s]+'
        urls = re.findall(pattern, text)
        return urls

    def make_plan(self, t, max_chars=1000):
        if not t or not self.model:
            return "Plan generation requires model"
        txt = t[:max_chars]
        try:
            inp = self.tokenizer(f"plan: {txt}", return_tensors="pt", max_length=512, truncation=True, padding=True)
            with torch.no_grad():
                out = self.model.generate(
                    inp["input_ids"],
                    max_length=200,
                    min_length=30,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.5
                )
            plan = self.tokenizer.decode(out[0], skip_special_tokens=True)
            return plan.strip() if plan else "Could not generate plan"
        except Exception as e:
            print(f"Plan error: {e}")
            return "Could not generate plan"

    def _capitalize_title(self, phrase: str) -> str:
        parts = phrase.split()
        return ' '.join(p[:1].upper() + p[1:] if p else '' for p in parts)

    def _trim_sentence(self, sentence: str, max_len: int = 72) -> str:
        s = sentence.strip()
        if len(s) <= max_len:
            return s
        cut = s[:max_len].rsplit(' ', 1)[0]
        return cut + '…'

    def get_title(self, t, keywords=None, entities=None, summary=None):
        if not t:
            return "Без названия"

        if entities is None:
            entities = self.get_entities(t)
        if keywords is None:
            keywords = self.get_keywords(t, 12)

        for key in ('persons', 'orgs', 'locs'):
            group = entities.get(key) or []
            if group:
                return group[0]['text']

        meaningful = []
        for item in keywords:
            word = item.get('word', '').strip()
            if len(word) > 3 and word not in self.title_stop_words:
                meaningful.append(word)
        if meaningful:
            if len(meaningful) >= 2:
                return self._capitalize_title(f"{meaningful[0]} — {meaningful[1]}")
            return self._capitalize_title(meaningful[0])

        if summary and summary.strip():
            headline = summary.strip().split('.')[0].strip()
            if 12 <= len(headline) <= 90:
                return self._capitalize_title(headline)

        try:
            sents = sent_tokenize(t.strip())
            if sents:
                return self._trim_sentence(sents[0])
        except Exception:
            pass

        return "Анализ текста"

    def get_entities(self, t):
        if not self.ner_ok or not t:
            return {'persons': [], 'orgs': [], 'locs': [], 'dates': []}
        try:
            doc = Doc(t[:5000])
            doc.segment(self.segmenter)
            doc.tag_morph(self.morph_tagger)
            doc.parse_syntax(self.syntax_parser)
            doc.tag_ner(self.ner_tagger)
            persons = []
            orgs = []
            locs = []
            dates = []
            seen = set()
            for span in doc.spans:
                label = (span.type, span.text)
                if label in seen:
                    continue
                seen.add(label)
                if span.type == 'PER':
                    persons.append({'text': span.text})
                elif span.type == 'ORG':
                    orgs.append({'text': span.text})
                elif span.type == 'LOC':
                    locs.append({'text': span.text})
                elif span.type == 'DATE':
                    dates.append({'text': span.text})
            return {
                'persons': persons,
                'orgs': orgs,
                'locs': locs,
                'dates': dates
            }
        except Exception as e:
            print(f"NER error: {e}")
            return {'persons': [], 'orgs': [], 'locs': [], 'dates': []}

    def check_plag(self, student, ref):
        if not student or not ref:
            return {"uniqueness": 100, "similarity": 0, "common": []}
        
        sw = set(word_tokenize(student.lower()))
        rw = set(word_tokenize(ref.lower()))
        
        sw = sw - self.stop_words
        rw = rw - self.stop_words
        
        if not sw:
            return {"uniqueness": 0, "similarity": 0, "common": []}
        
        common = sw & rw
        uniq = round((1 - len(common) / len(sw)) * 100, 1)
        
        try:
            vec = TfidfVectorizer(stop_words=list(self.stop_words))
            tfidf = vec.fit_transform([student, ref])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        except:
            sim = 0
        
        return {
            "uniqueness": uniq,
            "similarity": round(sim, 3),
            "common": list(common)[:10]
        }

    def full(self, t, ref=None):
        if not t or len(t.strip()) < 10:
            return {
                'error': 'text too short',
                'stats': self.get_stats(t) if t else {},
                'summary': 'no summary',
                'keywords': [],
                'title': 'no title',
                'plan': 'no plan',
                'compression': 0,
                'entities': {'persons': [], 'orgs': [], 'locs': [], 'dates': []},
                'plagiarism': {}
            }
        
        stats = self.get_stats(t)
        summary = self.summ(t)
        keywords = self.get_keywords(t, 5)
        entities = self.get_entities(t)
        title = self.get_title(t, keywords=keywords, entities=entities, summary=summary)
        plan = self.make_plan(t)
        comp = self.get_comp(t, summary)
        
        plag = {}
        if ref:
            plag = self.check_plag(t, ref)
        
        return {
            'stats': stats,
            'summary': summary,
            'keywords': keywords,
            'title': title,
            'plan': plan,
            'compression': comp,
            'entities': entities,
            'plagiarism': plag
        }

    def save_json(self, t, name="result.json"):
        res = self.full(t)
        res['time'] = datetime.now().isoformat()
        res['preview'] = t[:200] + ('...' if len(t) > 200 else '')
        try:
            with open(name, 'w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            return {"status": "ok", "file": name}
        except Exception as e:
            return {"status": "error", "msg": str(e)}