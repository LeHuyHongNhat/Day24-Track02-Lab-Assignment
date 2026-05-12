# src/pii/detector.py
import spacy
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine


class VietnameseNlpEngine(NlpEngine):
    """
    Minimal spaCy-backed NLP engine with a no-download fallback.

    Presidio expects an NLP engine even when we only use pattern-based
    recognizers. This engine tries vi_core_news_lg first, then en_core_web_sm,
    and finally falls back to a blank Vietnamese pipeline.
    """

    def __init__(self):
        self._nlp = {}
        self.load()

    def _load_model(self, model_name: str):
        try:
            return spacy.load(model_name, disable=["ner", "parser"])
        except Exception:
            return None

    def load(self) -> None:
        for model_name in ("vi_core_news_lg", "en_core_web_sm"):
            model = self._load_model(model_name)
            if model is not None:
                self._nlp["vi"] = model
                return

        # Use the generic multilingual tokenizer as the final fallback so the
        # engine works even when Vietnamese-specific tokenizers are absent.
        self._nlp["vi"] = spacy.blank("xx")

    def is_loaded(self) -> bool:
        return "vi" in self._nlp

    def process_text(self, text: str, language: str) -> NlpArtifacts:
        if language not in self._nlp:
            raise ValueError(f"Unsupported language: {language}")

        doc = self._nlp[language](text)
        return NlpArtifacts(
            entities=list(doc.ents),
            tokens=doc,
            tokens_indices=[token.idx for token in doc],
            lemmas=[token.lemma_ for token in doc],
            nlp_engine=self,
            language=language,
        )

    def process_batch(self, texts, language: str, batch_size: int = 1, n_process: int = 1):
        for text in texts:
            yield text, self.process_text(str(text), language)

    def is_stopword(self, word: str, language: str) -> bool:
        return bool(self._nlp[language].vocab[word].is_stop)

    def is_punct(self, word: str, language: str) -> bool:
        return bool(self._nlp[language].vocab[word].is_punct)

    def get_nlp(self, language: str):
        return self._nlp[language]

    def get_supported_entities(self):
        return []

    def get_supported_languages(self):
        return list(self._nlp.keys())


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """
    Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN.
    """

    # CCCD recognizer: 12 chữ số (có thể mất số 0 đầu khi pandas đọc CSV)
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"(?<!\d)\d{11,12}(?!\d)",
        score=0.9,
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"],
        supported_language="vi",
    )

    # Phone recognizer: SĐT Việt Nam (0[3|5|7|8|9]xxxxxxxx)
    # Có thể mất số 0 đầu khi pandas đọc CSV -> hỗ trợ cả 9 và 10 chữ số.
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[
            Pattern(
                name="vn_phone",
                regex=r"(?<!\d)0?[35789]\d{8}(?!\d)",
                score=0.85,
            )
        ],
        context=["điện thoại", "sdt", "phone", "liên hệ"],
        supported_language="vi",
    )

    # Custom email recognizer cho tiếng Việt (built-in chỉ hỗ trợ "en")
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[
            Pattern(
                name="email_pattern",
                regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
                score=0.95,
            )
        ],
        context=["email", "thư", "mail", "@"],
        supported_language="vi",
    )

    # Vietnamese name recognizer: handles common honorifics and 2-4 word names.
    vn_upper = (
        r"A-ZÀÁẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊ"
        r"ÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ"
    )
    vn_lower = (
        r"a-zàáảãạâấầẩẫậăắằẳẵặđèéẻẽẹêếềểễệìíỉĩị"
        r"òóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ"
    )
    vn_word = rf"[{vn_upper}][{vn_lower}]+"
    vn_title = r"(?:Quý\s+(?:cô|ông)|Ông|Bà|Anh|Chị|Cô|Bác)"
    vn_name_regex = rf"\b(?:{vn_title}\s+)?(?:{vn_word}\s+){{1,3}}{vn_word}\b"

    name_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[
            Pattern(
                name="vn_person_pattern",
                regex=vn_name_regex,
                score=0.7,
            )
        ],
        context=["bệnh nhân", "bác sĩ", "ông", "bà", "anh", "chị", "tên", "họ", "người"],
        supported_language="vi",
    )

    nlp_engine = VietnameseNlpEngine()
    registry = RecognizerRegistry(supported_languages=["vi"])
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)
    registry.add_recognizer(email_recognizer)
    registry.add_recognizer(name_recognizer)

    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["vi"],
    )

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities cần detect: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    results = analyzer.analyze(
        text=str(text),
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
    return results
