"""
AuraScent Master Ultimate v8.7 FIXED + TIER DIVERSITY (1 Niche, 1 Designer, 1 Clone)
==================================================================================
"""

import streamlit as st
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import math
import warnings
import time
import datetime
import re
from collections import defaultdict, Counter

warnings.filterwarnings('ignore')

# ============================================================================
# CORE VERİ VE AYARLAR
# ============================================================================

AURA_KEYS = [
    "confidence", "sensuality", "formality", "intensity",
    "uniqueness", "approachability", "maturity", "extroversion"
]

def z(**kwargs):
    out = {k: 0.0 for k in AURA_KEYS}
    out.update(kwargs)
    return out

BRAND_TIERS = {
    "niche": ["Tom Ford", "Creed", "Amouage", "Roja", "Clive Christian", "Byredo", "Le Labo", "Kilian", "Maison Francis Kurkdjian", "Parfums de Marly", "Initio", "Xerjoff", "Nishane", "Frederic Malle", "Penhaligon", "Atelier Cologne", "Acqua di Parma", "Hermès", "Hermes"],
    "premium": ["Dior", "Chanel", "Gucci", "Prada", "Versace", "Giorgio Armani", "Armani", "Yves Saint Laurent", "YSL", "Givenchy", "Burberry", "Dolce & Gabbana", "D&G", "Valentino", "Bvlgari", "Montblanc", "Boss", "Hugo Boss"],
    "mass": ["Zara", "Rasasi", "Lattafa", "Afnan", "Alhambra", "Ajmal", "Al Haramain", "Swiss Arabian", "Armaf", "Fragrance World", "Paris Corner", "Boticário", "Bath & Body Works", "Works"]
}

def get_brand_tier(brand: str) -> str:
    brand_lower = brand.lower()
    for tier, brands in BRAND_TIERS.items():
        if any(b.lower() in brand_lower for b in brands):
            return tier
    return "premium"

def get_contextual_tier_multiplier(tier: str, mode: str, answers: Dict[str, str]) -> float:
    # V8.7: Seçim kuralı değiştiği için çarpanları daha dengeli hale getiriyoruz
    return 1.0 

SEASONAL_PROFILES = {
    "İlkbahar": {"clusters": ["Citrus-Aromatic", "Green-Fresh", "Floral-Musky", "Woody-Aromatic"], "intensity_range": (0.30, 0.65), "boost_factor": 1.10},
    "Yaz": {"clusters": ["Blue-Fresh", "Aquatic-Marine", "Citrus-Aromatic", "Green-Fresh"], "intensity_range": (0.20, 0.55), "boost_factor": 1.10},
    "Sonbahar": {"clusters": ["Spicy-Oriental", "Woody-Aromatic", "Sweet-Gourmand", "Leather-Smoky"], "intensity_range": (0.50, 0.80), "boost_factor": 1.10},
    "Kış": {"clusters": ["Dark-Oriental", "Leather-Smoky", "Sweet-Gourmand", "Spicy-Oriental"], "intensity_range": (0.65, 1.0), "boost_factor": 1.10}
}

OCCASION_PROFILES = {
    "Kapalı Ofis": {"clusters": ["Blue-Fresh", "Citrus-Aromatic", "Woody-Aromatic", "Green-Fresh"], "avoid_clusters": ["Sweet-Gourmand", "Dark-Oriental"], "max_intensity": 0.65, "max_sillage": 0.65, "min_approachability": 0.50},
    "Randevu Gecesi": {"clusters": ["Spicy-Oriental", "Sweet-Gourmand", "Woody-Aromatic", "Floral-Musky"], "avoid_clusters": [], "min_sensuality": 0.45, "sillage_range": (0.40, 0.75)},
    "Gece Kulübü": {"clusters": ["Sweet-Gourmand", "Spicy-Oriental", "Dark-Oriental"], "avoid_clusters": ["Green-Fresh", "Aquatic-Marine"], "min_intensity": 0.70, "min_sillage": 0.65},
    "Günlük Hayat": {"clusters": ["Blue-Fresh", "Citrus-Aromatic", "Woody-Aromatic", "Barbershop"], "avoid_clusters": [], "versatility_min": 0.70},
    "Spor/Aktif Ortam": {"clusters": ["Citrus-Aromatic", "Aquatic-Marine", "Green-Fresh"], "avoid_clusters": ["Sweet-Gourmand", "Leather-Smoky", "Dark-Oriental"], "max_intensity": 0.45},
    "Özel Etkinlik": {"clusters": ["Spicy-Oriental", "Woody-Aromatic", "Powdery-Iris", "Leather-Smoky"], "avoid_clusters": [], "min_formality": 0.60}
}

COMPLIMENT_BASE = {"Blue-Fresh": 0.90, "Citrus-Aromatic": 0.85, "Barbershop": 0.80, "Sweet-Gourmand": 0.80, "Spicy-Oriental": 0.75, "Aquatic-Marine": 0.75, "Woody-Aromatic": 0.70, "Green-Fresh": 0.65, "Floral-Musky": 0.60, "Powdery-Iris": 0.55, "Leather-Smoky": 0.45, "Dark-Oriental": 0.40, "Unique-Niche": 0.30}
VERSATILITY_BASE = {"Blue-Fresh": 0.90, "Woody-Aromatic": 0.90, "Citrus-Aromatic": 0.85, "Barbershop": 0.85, "Spicy-Oriental": 0.70, "Aquatic-Marine": 0.50, "Sweet-Gourmand": 0.60, "Green-Fresh": 0.65, "Floral-Musky": 0.60, "Powdery-Iris": 0.55, "Leather-Smoky": 0.40, "Dark-Oriental": 0.35, "Unique-Niche": 0.25}

QUESTIONS = {
    "Q1": {"question": "Kendinizi nasıl tanımlarsınız?", "options": ["Doğal Lider", "Klasik Beyefendi", "Özgür Ruhlu / Asi", "Modern Minimalist", "Romantik / Çekici", "Sportif / Enerjik"]},
    "Q2": {"question": "Parfümü en çok hangi ortamda kullanacaksınız?", "options": ["Kapalı Ofis", "Randevu Gecesi", "Gece Kulübü", "Günlük Hayat", "Spor/Aktiv Ortam", "Özel Etkinlik"]},
    "Q3": {"question": "Parfümünüzün ne kadar fark edilmesini istersiniz?", "options": ["Sadece tenimde kalsın", "Yakınımdakiler fark etsin", "Geçtiğim yerde iz bıraksın", "Odayı doldursun (statement)"]},
    "Q4": {"question": "Giyim tarzınız nedir?", "options": ["Takım Elbise", "Smart Casual", "Streetwear", "Spor Giyim", "Klasik/Rahat"]},
    "Q5": {"question": "Hangi koku ailesi size hitap eder?", "options": ["Doğal/Bitkisel", "Tatlı/Gourmand", "Baharatlı/Sıcak", "Odunsu/Dumanlı", "Taze/Temiz", "Çiçeksi"]},
    "Q6": {"question": "Parfüm seçiminde yaklaşımınız nedir?", "options": ["Herkes beğensin (güvenli)", "Hem beğenilsin hem karakterli olsun (denge)", "İmza olsun, biraz risk alırım (farklı)"]},
    "Q7": {"question": "Yoğunluk toleransınız nedir?", "options": ["Beni yorar, hafif severim", "Orta yoğunluk ideal", "Yoğun severim", "Ne kadar güçlü o kadar iyi"]},
    "Q8": {"question": "Kendinizi yaşınıza göre nasıl hissediyorsunuz?", "options": ["Genç & enerjik", "Modern yetişkin", "Olgun & ağırbaşlı", "Klasik / zamansız"]},
    "Q9": {"question": "Formalite seviyeniz nedir?", "options": ["Ofis-uyumlu / ölçülü", "Her yere gider (all-rounder)", "Gece / özel anlar için daha iddialı", "Kuralları boşver, karakter öncelik"]},
    "Q10": {"question": "Sosyal ortamlarda nasılsınız?", "options": ["Sakin, yakın mesafe", "Dengeli, ara sıra fark edilir", "Dikkat çeken, sosyal", "Sahne ışığı gibi, 'ben buradayım'"]}
}

QUESTION_WEIGHTS = {"Q1": 1.25, "Q2": 1.05, "Q3": 1.15, "Q4": 0.85, "Q5": 1.15, "Q6": 1.20, "Q7": 1.00, "Q8": 0.95, "Q9": 1.00, "Q10": 1.00}

SURVEY_MAPPING = {
    "Q1": {
        "Doğal Lider": z(confidence=+0.55, intensity=+0.30, extroversion=+0.25, maturity=+0.20, approachability=-0.10),
        "Klasik Beyefendi": z(formality=+0.55, maturity=+0.45, confidence=+0.25, approachability=+0.20, intensity=-0.05),
        "Özgür Ruhlu / Asi": z(uniqueness=+0.60, intensity=+0.25, extroversion=+0.25, confidence=+0.15, formality=-0.25, approachability=-0.15),
        "Modern Minimalist": z(approachability=+0.40, formality=+0.30, confidence=+0.15, intensity=-0.20, uniqueness=-0.10),
        "Romantik / Çekici": z(sensuality=+0.55, approachability=+0.25, extroversion=+0.10, intensity=+0.05, maturity=+0.05),
        "Sportif / Enerjik": z(approachability=+0.45, extroversion=+0.30, intensity=-0.15, formality=-0.20, maturity=-0.10),
    },
    "Q2": {
        "Kapalı Ofis": z(formality=+0.55, approachability=+0.30, intensity=-0.30, extroversion=-0.20, sensuality=-0.05),
        "Randevu Gecesi": z(sensuality=+0.50, intensity=+0.25, approachability=+0.05, extroversion=+0.05, confidence=+0.10),
        "Gece Kulübü": z(intensity=+0.55, extroversion=+0.55, confidence=+0.15, approachability=-0.15, formality=-0.25),
        "Günlük Hayat": z(approachability=+0.45, intensity=-0.05, formality=+0.10, extroversion=+0.10),
        "Spor/Aktiv Ortam": z(approachability=+0.35, intensity=-0.35, sensuality=-0.15, formality=-0.15, extroversion=+0.10),
        "Özel Etkinlik": z(formality=+0.30, confidence=+0.25, maturity=+0.25, intensity=+0.20, extroversion=+0.10),
    },
    "Q3": {
        "Sadece tenimde kalsın": z(intensity=-0.55, extroversion=-0.35, confidence=-0.10, approachability=+0.15),
        "Yakınımdakiler fark etsin": z(intensity=-0.15, extroversion=-0.05, approachability=+0.10),
        "Geçtiğim yerde iz bıraksın": z(intensity=+0.30, extroversion=+0.25, confidence=+0.15),
        "Odayı doldursun (statement)": z(intensity=+0.60, extroversion=+0.60, confidence=+0.20, approachability=-0.15),
    },
    "Q4": {
        "Takım Elbise": z(formality=+0.55, maturity=+0.25, confidence=+0.20, extroversion=-0.05),
        "Smart Casual": z(formality=+0.25, approachability=+0.25, confidence=+0.10, maturity=+0.10),
        "Streetwear": z(extroversion=+0.25, uniqueness=+0.25, formality=-0.25, intensity=+0.10),
        "Spor Giyim": z(approachability=+0.25, intensity=-0.25, formality=-0.20, extroversion=+0.10),
        "Klasik/Rahat": z(maturity=+0.15, approachability=+0.20, formality=+0.10, intensity=-0.05),
    },
    "Q5": {
        "Doğal/Bitkisel": z(approachability=+0.25, formality=+0.10, maturity=+0.10, uniqueness=+0.05, intensity=-0.10),
        "Tatlı/Gourmand": z(sensuality=+0.55, intensity=+0.25, extroversion=+0.15, maturity=-0.10, approachability=+0.05),
        "Baharatlı/Sıcak": z(intensity=+0.35, confidence=+0.20, sensuality=+0.20, maturity=+0.10, approachability=-0.05),
        "Odunsu/Dumanlı": z(confidence=+0.40, maturity=+0.35, uniqueness=+0.25, intensity=+0.25, approachability=-0.15, sensuality=+0.05),
        "Taze/Temiz": z(approachability=+0.55, formality=+0.25, intensity=-0.25, uniqueness=-0.15, sensuality=-0.05),
        "Çiçeksi": z(formality=+0.30, sensuality=+0.20, maturity=+0.10, approachability=+0.05, uniqueness=+0.05),
    },
    "Q6": {
        "Herkes beğensin (güvenli)": z(approachability=+0.55, uniqueness=-0.45, intensity=-0.05),
        "Hem beğenilsin hem karakterli olsun (denge)": z(approachability=+0.25, uniqueness=+0.10, confidence=+0.05),
        "İmza olsun, biraz risk alırım (farklı)": z(uniqueness=+0.55, approachability=-0.25, confidence=+0.10, intensity=+0.10),
    },
    "Q7": {
        "Beni yorar, hafif severim": z(intensity=-0.55, sensuality=-0.15, approachability=+0.20, extroversion=-0.10),
        "Orta yoğunluk ideal": z(intensity=-0.05, approachability=+0.05),
        "Yoğun severim": z(intensity=+0.30, sensuality=+0.15, extroversion=+0.10),
        "Ne kadar güçlü o kadar iyi": z(intensity=+0.60, extroversion=+0.25, confidence=+0.10, approachability=-0.10),
    },
    "Q8": {
        "Genç & enerjik": z(maturity=-0.35, extroversion=+0.20, approachability=+0.10),
        "Modern yetişkin": z(maturity=+0.10, approachability=+0.15, confidence=+0.05),
        "Olgun & ağırbaşlı": z(maturity=+0.45, confidence=+0.15, formality=+0.10),
        "Klasik / zamansız": z(maturity=+0.35, formality=+0.25, confidence=+0.10, uniqueness=+0.05),
    },
    "Q9": {
        "Ofis-uyumlu / ölçülü": z(formality=+0.55, intensity=-0.25, approachability=+0.20, extroversion=-0.10),
        "Her yere gider (all-rounder)": z(approachability=+0.25, formality=+0.10, intensity=-0.05),
        "Gece / özel anlar için daha iddialı": z(intensity=+0.30, extroversion=+0.25, sensuality=+0.10, formality=-0.10),
        "Kuralları boşver, karakter öncelik": z(uniqueness=+0.35, intensity=+0.20, extroversion=+0.15, approachability=-0.15, formality=-0.20),
    },
    "Q10": {
        "Sakin, yakın mesafe": z(extroversion=-0.45, intensity=-0.25, approachability=+0.15),
        "Dengeli, ara sıra fark edilir": z(extroversion=-0.05, intensity=-0.05),
        "Dikkat çeken, sosyal": z(extroversion=+0.35, intensity=+0.20, confidence=+0.10),
        "Sahne ışığı gibi, 'ben buradayım'": z(extroversion=+0.60, intensity=+0.45, confidence=+0.15, approachability=-0.10),
    },
}

def _sigmoid(x: float, k: float = 1.6) -> float:
    return 1.0 / (1.0 + math.exp(-k * x))

def compute_user_aura_from_answers(answers: Dict[str, str]) -> Dict[str, float]:
    raw = {k: 0.0 for k in AURA_KEYS}
    for qid, answer in answers.items():
        if qid not in SURVEY_MAPPING or answer not in SURVEY_MAPPING[qid]:
            continue
        contribution = SURVEY_MAPPING[qid][answer]
        weight = QUESTION_WEIGHTS.get(qid, 1.0)
        for key_survey, value in contribution.items():
            key_actual = key_survey.replace("confidence_level", "confidence")
            if key_actual in raw:
                raw[key_actual] += value * weight
    normalized = {}
    for key in AURA_KEYS:
        normalized[key] = float(np.clip(_sigmoid(raw[key], k=1.6), 0.0, 1.0))
    return normalized

def infer_mode_from_q6(q6_answer: str) -> str:
    if "güvenli" in q6_answer.lower(): return "SAFE"
    elif "farklı" in q6_answer.lower() or "risk" in q6_answer.lower(): return "SIGNATURE"
    else: return "BALANCED"

def get_mode_config(mode: str) -> Dict[str, Any]:
    mode = (mode or "BALANCED").upper().strip()
    configs = {
        "SAFE": {"weights": {"confidence": 1.05, "sensuality": 1.00, "formality": 1.15, "intensity": 0.85, "uniqueness": 0.65, "approachability": 1.35, "maturity": 1.10, "extroversion": 0.95}, "lambda_mmr": 0.70, "min_approachability": 0.55},
        "SIGNATURE": {"weights": {"confidence": 1.15, "sensuality": 1.05, "formality": 0.95, "intensity": 1.15, "uniqueness": 1.75, "approachability": 0.85, "maturity": 1.10, "extroversion": 1.05}, "lambda_mmr": 0.75, "min_approachability": 0.20},
        "BALANCED": {"weights": {"confidence": 1.10, "sensuality": 1.00, "formality": 1.00, "intensity": 1.10, "uniqueness": 1.20, "approachability": 1.00, "maturity": 1.10, "extroversion": 1.00}, "lambda_mmr": 0.72, "min_approachability": 0.35}
    }
    return configs.get(mode, configs["BALANCED"])

def calculate_dynamic_compliment(cluster: str, brand_tier: str, uniqueness: float) -> float:
    base = COMPLIMENT_BASE.get(cluster, 0.60)
    tier_adj = {"niche": -0.10, "premium": 0.0, "mass": +0.05}.get(brand_tier, 0.0)
    unique_penalty = uniqueness * 0.20 if uniqueness > 0.70 else 0.0
    return float(np.clip(base + tier_adj - unique_penalty, 0.20, 0.95))

def calculate_dynamic_versatility(cluster: str, intensity: float, approachability: float) -> float:
    base = VERSATILITY_BASE.get(cluster, 0.60)
    intensity_penalty = (intensity - 0.75) * 0.40 if intensity > 0.75 else 0.0
    app_boost = (approachability - 0.60) * 0.20 if approachability > 0.60 else 0.0
    return float(np.clip(base - intensity_penalty + app_boost, 0.20, 0.95))

def get_current_season() -> str:
    month = datetime.datetime.now().month
    if month in [3, 4, 5]: return "İlkbahar"
    elif month in [6, 7, 8]: return "Yaz"
    elif month in [9, 10, 11]: return "Sonbahar"
    else: return "Kış"

def extract_base_name(perfume_name: str) -> str:
    clean_name = perfume_name.lower()
    clean_name = re.sub(r'for men.*$', '', clean_name)
    clean_name = re.sub(r'for women.*$', '', clean_name)
    clean_name = clean_name.replace('è', 'e').replace('é', 'e')
    words_to_remove = ['eau', 'de', 'parfum', 'toilette', 'cologne', 'intense', 'flacon', 'edition', 'limited', 'vintage', 'extrait']
    words = clean_name.split()
    core_words = [w for w in words if w not in words_to_remove]
    return " ".join(core_words[:2]) if len(core_words) >= 2 else " ".join(core_words)

# ============================================================================
# MASTER PROFESSIONAL ENGINE SINIflARI
# ============================================================================

@dataclass
class ExpertRecommendation:
    perfume_name: str
    brand: str
    cluster: str
    similarity_score: float
    intensity: float
    longevity: float
    sillage: float
    why_recommended: str
    best_occasions: List[str]
    seasonal_fit: List[str]
    compliment_score: float
    versatility_score: float
    progression_level: str
    brand_tier: str
    expert_notes: List[str] = field(default_factory=list)

class MasterUltimateEngineV8:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df['brand_tier'] = self.df['brand'].apply(get_brand_tier)

    def recommend_comprehensive(self, answers: Dict[str, str], mode: Optional[str] = None, top_n: int = 10, enforce_diversity: bool = True, verbose: bool = False) -> Tuple[List[ExpertRecommendation], Dict]:
        user_aura = compute_user_aura_from_answers(answers)
        if mode is None:
            mode = infer_mode_from_q6(answers.get("Q6", "denge"))
        
        config = get_mode_config(mode)
        occasion = answers.get("Q2", "Günlük Hayat")
        current_season = get_current_season()

        weights = config["weights"]
        weights_array = np.array([weights[k] for k in AURA_KEYS])
        user_vec = np.array([user_aura[k] for k in AURA_KEYS]) * weights_array
        perf_vecs = self.df[[f'aura_{k}' for k in AURA_KEYS]].values * weights_array

        user_norm = user_vec / (np.linalg.norm(user_vec) + 1e-12)
        perf_norms = perf_vecs / (np.linalg.norm(perf_vecs, axis=1, keepdims=True) + 1e-12)
        self.df['base_similarity'] = perf_norms @ user_norm
        
        tier_multipliers = self.df['brand_tier'].apply(lambda t: get_contextual_tier_multiplier(t, mode, answers))
        self.df['similarity'] = self.df['base_similarity'] * tier_multipliers
        
        season_data = SEASONAL_PROFILES.get(current_season, {})
        season_boost = self.df['cluster'].isin(season_data.get("clusters", [])).astype(float) * 0.03
        self.df['similarity'] += season_boost

        mask = pd.Series([True] * len(self.df))
        is_alpha_formal = answers.get("Q4") == "Takım Elbise" or answers.get("Q1") in ["Doğal Lider", "Klasik Beyefendi"]
        if is_alpha_formal:
            mask &= (self.df['aura_maturity'] >= 0.60)
            mask &= (self.df['aura_formality'] >= 0.60)
            mask &= ~self.df['name'].str.contains('Spiderman|Kids|Marvel|Disney|Boy', case=False, na=False)

        if answers.get("Q8") == "Olgun & ağırbaşlı":
            mask &= (self.df['aura_maturity'] >= 0.65)
        
        if answers.get("Q2") == "Gece Kulübü":
            mask &= (self.df['aura_intensity'] >= 0.50)

        if config.get("min_approachability", 0.0) > 0:
            mask &= (self.df['aura_approachability'] >= config["min_approachability"])
        
        occasion_prof = OCCASION_PROFILES.get(occasion, {})
        if occasion_prof.get("avoid_clusters"):
            mask &= ~self.df['cluster'].isin(occasion_prof["avoid_clusters"])

        candidates = self.df[mask].copy().sort_values('similarity', ascending=False)

        # ====================================================================
        # V8.7: HİBRİT İMZA SEÇİM MANTIĞI (1 Niche, 1 Designer, 1 Clone)
        # ====================================================================
        if mode == "SIGNATURE":
            selected_indices = []
            used_base_names = set()
            
            # Her tier'dan en iyi uyanı seç
            for tier in ["niche", "premium", "mass"]:
                tier_candidates = candidates[candidates['brand_tier'] == tier]
                for idx, row in tier_candidates.iterrows():
                    base_name = extract_base_name(row['name'])
                    if base_name not in used_base_names:
                        selected_indices.append(idx)
                        used_base_names.add(base_name)
                        break
            
            # Eğer 3 tane seçemediysek (veri kısıtlıysa), en iyi benzerlikleri ekle
            if len(selected_indices) < 3:
                remaining = candidates[~candidates.index.isin(selected_indices)]
                for idx, row in remaining.iterrows():
                    base_name = extract_base_name(row['name'])
                    if base_name not in used_base_names:
                        selected_indices.append(idx)
                        used_base_names.add(base_name)
                    if len(selected_indices) >= 3: break
            
            selected_indices = selected_indices[:3]
        else:
            # Diğer modlar için klasik MMR çeşitliliği
            selected_indices = []
            used_bases = set()
            for idx, row in candidates.iterrows():
                base = extract_base_name(row['name'])
                if base not in used_bases:
                    selected_indices.append(idx)
                    used_bases.add(base)
                if len(selected_indices) >= top_n: break
        # ====================================================================

        final_recs = []
        for idx in selected_indices:
            row = candidates.loc[idx]
            compliment = calculate_dynamic_compliment(row['cluster'], row['brand_tier'], row.get('aura_uniqueness', 0.5))
            versatility = calculate_dynamic_versatility(row['cluster'], row.get('aura_intensity', 0.5), row.get('aura_approachability', 0.5))
            why = f"Karakterinize ve tercihlerinize {current_season} mevsiminde tam uyum sağlıyor."
            prog_level = "İleri" if row.get('aura_uniqueness', 0.5) > 0.75 else "Orta" if row.get('aura_uniqueness', 0.5) > 0.50 else "Başlangıç"
            
            rec = ExpertRecommendation(
                perfume_name=row['name'], brand=row['brand'], cluster=row['cluster'], similarity_score=row['similarity'],
                intensity=row.get('aura_intensity', 0.5), longevity=row.get('longevity', 0.5), sillage=row.get('sillage', 0.5),
                why_recommended=why, best_occasions=[occasion], seasonal_fit=[current_season], compliment_score=compliment,
                versatility_score=versatility, progression_level=prog_level, brand_tier=row['brand_tier'],
                expert_notes=[f"Sınıf: {row['brand_tier'].capitalize()}"]
            )
            final_recs.append(rec)

        return final_recs, {"mode": mode, "user_aura": user_aura}

    def build_wardrobe(self, answers: Dict[str, str], exclude_base_names: Set[str] = None) -> Dict[str, List[ExpertRecommendation]]:
        exclude_base_names = exclude_base_names or set()
        occasions = ["Kapalı Ofis", "Randevu Gecesi", "Günlük Hayat"]
        wardrobe = {}
        used_bases = set(exclude_base_names)
        
        for occ in occasions:
            occ_answers = answers.copy()
            occ_answers["Q2"] = occ
            all_recs, _ = self.recommend_comprehensive(occ_answers, mode="BALANCED", top_n=10, verbose=False)
            occ_recs = []
            for r in all_recs:
                base = extract_base_name(r.perfume_name)
                if base not in used_bases and len(occ_recs) < 2:
                    occ_recs.append(r)
                    used_bases.add(base)
            wardrobe[occ] = occ_recs
        return wardrobe


# ============================================================================
# E-POSTA GÖNDERME MODÜLÜ
# ============================================================================
def send_results_to_email(answers: Dict[str, str], signature_recs: List[ExpertRecommendation]):
    try:
        if "EMAIL_ADDRESS" in st.secrets and "EMAIL_PASSWORD" in st.secrets:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            sender_email = st.secrets["EMAIL_ADDRESS"]
            sender_password = st.secrets["EMAIL_PASSWORD"]
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = sender_email
            msg['Subject'] = "🌟 Yeni AuraScent Analizi Geldi!"
            body = "Birisi AuraScent testini tamamladı! İşte profili:\n\n=== VERİLEN YANITLAR ===\n"
            for k, v in answers.items():
                body += f"{QUESTIONS[k]['question']} -> {v}\n"
            body += "\n=== İMZA ÖNERİLERİ ===\n"
            for i, r in enumerate(signature_recs, 1):
                body += f"{i}. {r.perfume_name} ({r.brand}) - Sınıf: {r.brand_tier.upper()}\n"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
    except Exception: pass

# ============================================================================
# STREAMLIT WEB INTERFACE
# ============================================================================

def run_streamlit_app():
    st.set_page_config(page_title="AuraScent Master Ultimate", page_icon="✨", layout="centered")
    @st.cache_resource
    def load_engine(): return MasterUltimateEngineV8("aurascent_all_profiles.csv")
    try: engine = load_engine()
    except FileNotFoundError:
        st.error("❌ 'aurascent_all_profiles.csv' dosyası bulunamadı.")
        return
    if 'step' not in st.session_state:
        st.session_state.step = 0
        st.session_state.answers = {}
    question_keys = list(QUESTIONS.keys())
    total_steps = len(question_keys)
    st.title("✨ AuraScent Master Ultimate")
    if st.session_state.step < total_steps:
        st.progress(st.session_state.step / total_steps)
        current_q_key = question_keys[st.session_state.step]
        current_q_data = QUESTIONS[current_q_key]
        with st.container():
            st.markdown(f"### 💬 {current_q_data['question']}")
            choice = st.radio("Seçiminizi yapın:", current_q_data['options'], key=f"radio_{current_q_key}")
            if st.button("Sonraki Soru ➔", type="primary"):
                st.session_state.answers[current_q_key] = choice
                st.session_state.step += 1
                st.rerun()
    else:
        st.progress(1.0)
        st.success("Analiz tamamlandı!")
        with st.expander("📋 Verilen Yanıtlar", expanded=False):
            for q_key, ans in st.session_state.answers.items():
                st.markdown(f"- **{QUESTIONS[q_key]['question']}** ➔ {ans}")
        with st.spinner("Kokularınız harmanlanıyor..."):
            time.sleep(1.5) 
            st.markdown("---")
            st.header("🌟 SIGNATURE (İmza Karakter Önerileri)")
            recs, _ = engine.recommend_comprehensive(st.session_state.answers, mode="SIGNATURE", top_n=3)
            signature_base_names = {extract_base_name(r.perfume_name) for r in recs}
            send_results_to_email(st.session_state.answers, recs)
            for i, rec in enumerate(recs, 1):
                label = "🏆 Niş" if rec.brand_tier == "niche" else "👔 Designer" if rec.brand_tier == "premium" else "🕌 Orta Doğu (Clone)"
                with st.expander(f"{i}. {rec.perfume_name} - {rec.brand} ({label})", expanded=(i==1)):
                    col1, col2 = st.columns([1, 3])
                    with col1: st.image("https://via.placeholder.com/150?text=Sise+Gorseli", caption="Yakında Eklenecek")
                    with col2:
                        st.markdown(f"**Uyum Skoru:** `%{(rec.similarity_score * 100):.1f}`")
                        st.markdown(f"**Neden Önerildi:** {rec.why_recommended}")
                        st.markdown(f"**Master Notları:** {', '.join(rec.expert_notes)}")
            st.markdown("---")
            st.header("👔 WARDROBE (Kullanım Alanına Göre Gardırop)")
            wardrobe = engine.build_wardrobe(st.session_state.answers, exclude_base_names=signature_base_names)
            tabs = st.tabs(list(wardrobe.keys()))
            for index, (occ, items) in enumerate(wardrobe.items()):
                with tabs[index]:
                    for r in items: st.markdown(f"- **{r.perfume_name}** ({r.brand}) ➔ *Sınıf: {r.brand_tier.capitalize()}*")
            if st.button("🔄 Testi Yeniden Çöz"):
                st.session_state.step = 0
                st.session_state.answers = {}
                st.rerun()

if __name__ == "__main__":
    run_streamlit_app()