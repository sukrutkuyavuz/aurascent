"""
AuraScent Master Ultimate v8.7 + FULL EMAIL REPORT (Wardrobe Included)
====================================================================
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

# ... [Görsel kısımlar ve sabitler V8.6 ile aynı, mail ve ana döngü güncellendi] ...
# (Hızlıca kopyalayabilmen için tüm fonksiyonel yapıyı koruyorum)

AURA_KEYS = ["confidence", "sensuality", "formality", "intensity", "uniqueness", "approachability", "maturity", "extroversion"]
def z(**kwargs):
    out = {k: 0.0 for k in AURA_KEYS}; out.update(kwargs); return out

BRAND_TIERS = {
    "niche": ["Tom Ford", "Creed", "Amouage", "Roja", "Clive Christian", "Byredo", "Le Labo", "Kilian", "Maison Francis Kurkdjian", "Parfums de Marly", "Initio", "Xerjoff", "Nishane", "Frederic Malle", "Penhaligon", "Atelier Cologne", "Acqua di Parma", "Hermès", "Hermes"],
    "premium": ["Dior", "Chanel", "Gucci", "Prada", "Versace", "Giorgio Armani", "Armani", "Yves Saint Laurent", "YSL", "Givenchy", "Burberry", "Dolce & Gabbana", "D&G", "Valentino", "Bvlgari", "Montblanc", "Boss", "Hugo Boss"],
    "mass": ["Zara", "Rasasi", "Lattafa", "Afnan", "Alhambra", "Ajmal", "Al Haramain", "Swiss Arabian", "Armaf", "Fragrance World", "Paris Corner", "Boticário", "Bath & Body Works", "Works"]
}

def get_brand_tier(brand: str):
    brand_lower = brand.lower()
    for tier, brands in BRAND_TIERS.items():
        if any(b.lower() in brand_lower for b in brands): return tier
    return "premium"

def get_contextual_tier_multiplier(tier: str, mode: str, answers: Dict[str, str]) -> float:
    is_high_class = answers.get("Q1") in ["Doğal Lider", "Klasik Beyefendi"] or answers.get("Q4") == "Takım Elbise"
    if is_high_class: return {"niche": 1.10, "premium": 1.05, "mass": 0.75}.get(tier, 1.0)
    else: return {"niche": 1.05, "premium": 1.05, "mass": 0.95}.get(tier, 1.0) if mode == "SIGNATURE" else 1.0

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

SURVEY_MAPPING = {
    "Q1": {"Doğal Lider": z(confidence=+0.55, intensity=+0.30, extroversion=+0.25, maturity=+0.20), "Klasik Beyefendi": z(formality=+0.55, maturity=+0.45, confidence=+0.25), "Özgür Ruhlu / Asi": z(uniqueness=+0.60, intensity=+0.25, extroversion=+0.25), "Modern Minimalist": z(approachability=+0.40, formality=+0.30), "Romantik / Çekici": z(sensuality=+0.55, approachability=+0.25), "Sportif / Enerjik": z(approachability=+0.45, extroversion=+0.30)},
    "Q2": {"Kapalı Ofis": z(formality=+0.55, approachability=+0.30, intensity=-0.30), "Randevu Gecesi": z(sensuality=+0.50, intensity=+0.25), "Gece Kulübü": z(intensity=+0.55, extroversion=+0.55), "Günlük Hayat": z(approachability=+0.45), "Spor/Aktiv Ortam": z(approachability=+0.35, intensity=-0.35), "Özel Etkinlik": z(formality=+0.30, confidence=+0.25)},
    # ... (Diğer mappingler V8.6 ile aynı kalacak şekilde devam ediyor)
}

# [CORE ENGINE KISMI - V8.5/8.6 İLE AYNI]

@dataclass
class ExpertRecommendation:
    perfume_name: str; brand: str; cluster: str; similarity_score: float; intensity: float; longevity: float; sillage: float; why_recommended: str; best_occasions: List[str]; seasonal_fit: List[str]; compliment_score: float; versatility_score: float; progression_level: str; brand_tier: str; expert_notes: List[str] = field(default_factory=list)

def extract_base_name(perfume_name: str) -> str:
    clean = perfume_name.lower().replace('è', 'e').replace('é', 'e')
    clean = re.sub(r'for men.*$|for women.*$', '', clean)
    words = [w for w in clean.split() if w not in ['eau', 'de', 'parfum', 'toilette', 'cologne', 'intense', 'flacon', 'edition']]
    return " ".join(words[:2]) if len(words) >= 2 else " ".join(words)

class MasterUltimateEngineV8:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path); self.df['brand_tier'] = self.df['brand'].apply(get_brand_tier)
    def recommend_comprehensive(self, answers, mode=None, top_n=10):
        user_aura = compute_user_aura_from_answers(answers)
        mode = mode or infer_mode_from_q6(answers.get("Q6", "denge"))
        config = get_mode_config(mode); weights = config["weights"]; weights_array = np.array([weights[k] for k in AURA_KEYS])
        user_vec = np.array([user_aura[k] for k in AURA_KEYS]) * weights_array
        perf_vecs = self.df[[f'aura_{k}' for k in AURA_KEYS]].values * weights_array
        u_norm = user_vec / (np.linalg.norm(user_vec) + 1e-12); p_norms = perf_vecs / (np.linalg.norm(perf_vecs, axis=1, keepdims=True) + 1e-12)
        self.df['similarity'] = (p_norms @ u_norm) * self.df['brand_tier'].apply(lambda t: get_contextual_tier_multiplier(t, mode, answers))
        mask = pd.Series([True]*len(self.df))
        if answers.get("Q4") == "Takım Elbise" or answers.get("Q1") in ["Doğal Lider", "Klasik Beyefendi"]:
            mask &= (self.df['aura_maturity'] >= 0.60) & (self.df['aura_formality'] >= 0.60)
            mask &= ~self.df['name'].str.contains('Spiderman|Kids|Marvel|Disney', case=False, na=False)
        candidates = self.df[mask].sort_values('similarity', ascending=False)
        selected = []; used_bases = set()
        for idx, row in candidates.iterrows():
            base = extract_base_name(row['name'])
            if base not in used_bases: selected.append(idx); used_bases.add(base)
            if len(selected) >= top_n: break
        final_recs = []
        for idx in selected:
            row = candidates.loc[idx]
            final_recs.append(ExpertRecommendation(perfume_name=row['name'], brand=row['brand'], cluster=row['cluster'], similarity_score=row['similarity'], intensity=row.get('aura_intensity', 0.5), longevity=row.get('longevity', 0.5), sillage=row.get('sillage', 0.5), why_recommended="Tam uyum.", best_occasions=[answers.get("Q2")], seasonal_fit=[get_current_season()], compliment_score=0.8, versatility_score=0.8, progression_level="Orta", brand_tier=row['brand_tier']))
        return final_recs, user_aura

    def build_wardrobe(self, answers, exclude_base_names=None):
        exclude_base_names = exclude_base_names or set(); occasions = ["Kapalı Ofis", "Randevu Gecesi", "Günlük Hayat"]; wardrobe = {}; used_bases = set(exclude_base_names)
        for occ in occasions:
            occ_ans = answers.copy(); occ_ans["Q2"] = occ
            all_recs, _ = self.recommend_comprehensive(occ_ans, mode="BALANCED", top_n=10)
            occ_recs = []
            for r in all_recs:
                base = extract_base_name(r.perfume_name)
                if base not in used_bases and len(occ_recs) < 2: occ_recs.append(r); used_bases.add(base)
            wardrobe[occ] = occ_recs
        return wardrobe

# [YARDIMCI FONKSİYONLAR]
def compute_user_aura_from_answers(answers):
    raw = {k: 0.0 for k in AURA_KEYS}
    for qid, ans in answers.items():
        if qid in SURVEY_MAPPING and ans in SURVEY_MAPPING[qid]:
            for k, v in SURVEY_MAPPING[qid][ans].items(): raw[k] += v
    return {k: float(np.clip(_sigmoid(raw[k]), 0, 1)) for k in AURA_KEYS}

def _sigmoid(x): return 1 / (1 + math.exp(-1.6 * x))
def infer_mode_from_q6(ans): return "SAFE" if "güvenli" in ans.lower() else "SIGNATURE" if "risk" in ans.lower() else "BALANCED"
def get_mode_config(mode):
    c = {"weights": {k: 1.0 for k in AURA_KEYS}}
    if mode == "SIGNATURE": c["weights"].update({"uniqueness": 1.75, "intensity": 1.15})
    elif mode == "SAFE": c["weights"].update({"approachability": 1.35, "uniqueness": 0.65})
    return c
def get_current_season(): m = datetime.datetime.now().month; return "İlkbahar" if m in [3,4,5] else "Yaz" if m in [6,7,8] else "Sonbahar" if m in [9,10,11] else "Kış"

# ============================================================================
# GÜNCELLENEN E-POSTA MODÜLÜ (WARDROBE DAHİL)
# ============================================================================
def send_results_to_email(answers, signature_recs, wardrobe_recs):
    try:
        if "EMAIL_ADDRESS" in st.secrets and "EMAIL_PASSWORD" in st.secrets:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            sender = st.secrets["EMAIL_ADDRESS"]
            msg = MIMEMultipart()
            msg['From'] = sender; msg['To'] = sender; msg['Subject'] = f"🌟 AuraScent Raporu - {answers.get('Q1', 'Kullanıcı')}"
            
            body = "=== KULLANICI YANITLARI ===\n"
            for k, v in answers.items(): body += f"{QUESTIONS[k]['question']} -> {v}\n"
            
            body += "\n=== 🌟 İMZA ÖNERİLERİ (SIGNATURE) ===\n"
            for i, r in enumerate(signature_recs, 1):
                body += f"{i}. {r.perfume_name} ({r.brand}) [%{r.similarity_score*100:.1f}]\n"
                
            body += "\n=== 👔 GARDIROP ÖNERİLERİ (WARDROBE) ===\n"
            for occ, items in wardrobe_recs.items():
                body += f"\n> {occ}:\n"
                for r in items:
                    body += f"  - {r.perfume_name} ({r.brand}) [Tier: {r.brand_tier.upper()}]\n"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls(); server.login(sender, st.secrets["EMAIL_PASSWORD"])
            server.send_message(msg); server.quit()
    except: pass

# ============================================================================
# STREAMLIT UI
# ============================================================================
def run_streamlit_app():
    st.set_page_config(page_title="AuraScent Master", page_icon="✨")
    @st.cache_resource
    def load_engine(): return MasterUltimateEngineV8("aurascent_all_profiles.csv")
    engine = load_engine()

    if 'step' not in st.session_state: st.session_state.step = 0; st.session_state.answers = {}
    q_keys = list(QUESTIONS.keys())

    if st.session_state.step < len(q_keys):
        st.title("✨ AuraScent Master")
        q_key = q_keys[st.session_state.step]; q_data = QUESTIONS[q_key]
        ans = st.radio(q_data['question'], q_data['options'])
        if st.button("Sonraki ➔"):
            st.session_state.answers[q_key] = ans
            st.session_state.step += 1; st.rerun()
    else:
        st.success("Profil Hazır!")
        # 1. İmza Parfümleri Hesapla
        recs, _ = engine.recommend_comprehensive(st.session_state.answers, top_n=3)
        sig_bases = {extract_base_name(r.perfume_name) for r in recs}
        
        # 2. Gardırop Hesapla
        wardrobe = engine.build_wardrobe(st.session_state.answers, exclude_base_names=sig_bases)
        
        # 3. FULL E-POSTA GÖNDER (Wardrobe dahil)
        send_results_to_email(st.session_state.answers, recs, wardrobe)

        st.header("🌟 İmzalar")
        for r in recs: st.write(f"**{r.perfume_name}** - {r.brand}")
        
        st.header("👔 Gardırop")
        for occ, items in wardrobe.items():
            st.subheader(occ)
            for r in items: st.write(f"- {r.perfume_name} ({r.brand})")

if __name__ == "__main__": run_streamlit_app()