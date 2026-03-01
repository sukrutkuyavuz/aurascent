"""
AuraScent Master Ultimate v9.2 - REFINED PRODUCTION READY
========================================================
"""

import streamlit as st
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import math
import warnings
import time
import datetime
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

warnings.filterwarnings('ignore')

# ============================================================================
# 1. CORE AYARLAR VE MARKA HİYERARŞİSİ
# ============================================================================

AURA_KEYS = ["confidence", "sensuality", "formality", "intensity", "uniqueness", "approachability", "maturity", "extroversion"]

MIDDLE_EAST_BRANDS = ["Rasasi", "Lattafa", "Afnan", "Alhambra", "Ajmal", "Al Haramain", "Swiss Arabian", "Armaf", "Fragrance World", "Paris Corner", "Maison Alhambra"]

BRAND_TIERS = {
    "niche": ["Tom Ford", "Creed", "Amouage", "Roja", "Clive Christian", "Byredo", "Le Labo", "Kilian", "Maison Francis Kurkdjian", "Parfums de Marly", "Initio", "Xerjoff", "Nishane", "Frederic Malle", "Penhaligon", "Atelier Cologne", "Acqua di Parma", "Hermès", "Hermes"],
    "premium": ["Dior", "Chanel", "Gucci", "Prada", "Versace", "Giorgio Armani", "Armani", "Yves Saint Laurent", "YSL", "Givenchy", "Burberry", "Dolce & Gabbana", "D&G", "Valentino", "Bvlgari", "Montblanc", "Boss", "Hugo Boss", "Issey Miyake", "Guerlain", "Ralph Lauren", "Calvin Klein"],
    "zara": ["Zara"],
    "middle_east": MIDDLE_EAST_BRANDS
}

def z(**kwargs):
    out = {k: 0.0 for k in AURA_KEYS}; out.update(kwargs); return out

# ============================================================================
# 2. SORU SETİ VE VEKTÖREL KARŞILIKLARI
# ============================================================================

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
    "Q1": {"Doğal Lider": z(confidence=+0.55, intensity=+0.30, extroversion=+0.25), "Klasik Beyefendi": z(formality=+0.55, maturity=+0.45), "Özgür Ruhlu / Asi": z(uniqueness=+0.60, intensity=+0.25), "Modern Minimalist": z(approachability=+0.40, formality=+0.30), "Romantik / Çekici": z(sensuality=+0.55), "Sportif / Enerjik": z(approachability=+0.45, extroversion=+0.30)},
    "Q2": {"Kapalı Ofis": z(formality=+0.55, approachability=+0.30, intensity=-0.30), "Randevu Gecesi": z(sensuality=+0.50, intensity=+0.25), "Gece Kulübü": z(intensity=+0.55, extroversion=+0.55), "Günlük Hayat": z(approachability=+0.45), "Spor/Aktiv Ortam": z(approachability=+0.35, intensity=-0.35), "Özel Etkinlik": z(formality=+0.30, confidence=+0.25)},
    "Q3": {"Sadece tenimde kalsın": z(intensity=-0.55), "Yakınımdakiler fark etsin": z(intensity=-0.15), "Geçtiğim yerde iz bıraksın": z(intensity=+0.30), "Odayı doldursun (statement)": z(intensity=+0.60, extroversion=+0.60)},
    "Q4": {"Takım Elbise": z(formality=+0.55, maturity=+0.25), "Smart Casual": z(formality=+0.25, approachability=+0.25), "Streetwear": z(extroversion=+0.25, uniqueness=+0.25), "Spor Giyim": z(approachability=+0.25, intensity=-0.25), "Klasik/Rahat": z(maturity=+0.15, approachability=+0.20)},
    "Q5": {"Doğal/Bitkisel": z(approachability=+0.25, formality=+0.10), "Tatlı/Gourmand": z(sensuality=+0.55, intensity=+0.25), "Baharatlı/Sıcak": z(intensity=+0.35, confidence=+0.20), "Odunsu/Dumanlı": z(confidence=+0.40, maturity=+0.35), "Taze/Temiz": z(approachability=+0.55, formality=+0.25), "Çiçeksi": z(formality=+0.30, sensuality=+0.20)},
    "Q6": {"Herkes beğensin (güvenli)": z(approachability=+0.55, uniqueness=-0.45), "Hem beğenilsin hem karakterli olsun (denge)": z(approachability=+0.25, uniqueness=+0.10), "İmza olsun, biraz risk alırım (farklı)": z(uniqueness=+0.55, confidence=+0.10)},
    "Q7": {"Beni yorar, hafif severim": z(intensity=-0.55), "Orta yoğunluk ideal": z(intensity=-0.05), "Yoğun severim": z(intensity=+0.30), "Ne kadar güçlü o kadar iyi": z(intensity=+0.60)},
    "Q8": {"Genç & enerjik": z(maturity=-0.35), "Modern yetişkin": z(maturity=+0.10), "Olgun & ağırbaşlı": z(maturity=+0.45, confidence=+0.15), "Klasik / zamansız": z(maturity=+0.35, formality=+0.25)},
    "Q9": {"Ofis-uyumlu / ölçülü": z(formality=+0.55, intensity=-0.25), "Her yere gider (all-rounder)": z(approachability=+0.25, formality=+0.10), "Gece / özel anlar için daha iddialı": z(intensity=+0.30, extroversion=+0.25), "Kuralları boşver, karakter öncelik": z(uniqueness=+0.35, intensity=+0.20)},
    "Q10": {"Sakin, yakın mesafe": z(extroversion=-0.45, intensity=-0.25), "Dengeli, ara sıra fark edilir": z(extroversion=-0.05), "Dikkat çeken, sosyal": z(extroversion=+0.35, intensity=+0.20), "Sahne ışığı gibi, 'ben buradayım'": z(extroversion=+0.60, intensity=+0.45)}
}

# ============================================================================
# 3. MASTER ENGINE V9.2
# ============================================================================

@dataclass
class ExpertRecommendation:
    perfume_name: str; brand: str; cluster: str; similarity_score: float; brand_tier: str

def _extract_base_refined(name):
    """Duplicates & Flankers Killer: Yıl ve özel şişe ibarelerini temizler."""
    clean = str(name).lower()
    clean = re.sub(r'\d{4}|flacon|limited|edition|anniversary|special|bottle|shaker|collector', '', clean)
    clean = re.sub(r'for men.*$|for women.*$', '', clean)
    words = [w for w in clean.split() if w not in ['h', 'limited', 'edition', 'parfum', 'toilette']]
    return " ".join(words[:2])

class MasterUltimateEngineV92:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df['brand_tier'] = self.df['brand'].apply(self._identify_tier)

    def _identify_tier(self, brand):
        brand_l = str(brand).lower()
        if "zara" in brand_l: return "zara"
        if any(b.lower() in brand_l for b in MIDDLE_EAST_BRANDS): return "middle_east"
        for tier, brands in BRAND_TIERS.items():
            if any(b.lower() in brand_l for b in brands): return tier
        return "premium"

    def _compute_aura(self, answers):
        raw = {k: 0.0 for k in AURA_KEYS}
        for qid, ans in answers.items():
            if qid in SURVEY_MAPPING and ans in SURVEY_MAPPING[qid]:
                for k, v in SURVEY_MAPPING[qid][ans].items(): raw[k] += v
        return {k: float(np.clip(1 / (1 + math.exp(-1.6 * raw[k])), 0, 1)) for k in AURA_KEYS}

    def recommend_balanced(self, answers):
        user_aura = self._compute_aura(answers)
        u_vec = np.array([user_aura[k] for k in AURA_KEYS])
        p_vecs = self.df[[f'aura_{k}' for k in AURA_KEYS]].values
        u_n = u_vec / (np.linalg.norm(u_vec) + 1e-12)
        p_norms = p_vecs / (np.linalg.norm(p_vecs, axis=1, keepdims=True) + 1e-12)
        
        # Tie-breaker: Çok küçük bir rastgelelik ekleyerek sıralamayı netleştiriyoruz
        # similarity = p_n . u_n + noise
        noise = np.random.uniform(0, 0.0001, size=len(self.df))
        self.df['similarity'] = (p_norms @ u_n) + noise
        
        valid = self.df[~self.df['name'].str.contains('Spiderman|Kids|Marvel|Disney', case=False, na=False)].sort_values('similarity', ascending=False)
        
        signature = []; used_bases = set()
        for tier in ["niche", "premium", "zara", "middle_east"]:
            pool = valid[valid['brand_tier'] == tier]
            count = 0
            for _, row in pool.iterrows():
                base = _extract_base_refined(row['name'])
                if base not in used_bases:
                    signature.append(ExpertRecommendation(row['name'], row['brand'], row['cluster'], row['similarity'], row['brand_tier']))
                    used_bases.add(base); count += 1
                if count >= 5: break
        
        wardrobe = {}
        for occ in ["Kapalı Ofis", "Randevu Gecesi", "Günlük Hayat"]:
            occ_ans = answers.copy(); occ_ans["Q2"] = occ
            u_aura_occ = self._compute_aura(occ_ans)
            u_v_occ = np.array([u_aura_occ[k] for k in AURA_KEYS])
            sim_occ = (p_norms @ (u_v_occ / (np.linalg.norm(u_v_occ) + 1e-12))) + noise
            self.df['similarity'] = sim_occ
            valid_occ = self.df[~self.df['name'].str.contains('Spiderman', case=False)].sort_values('similarity', ascending=False)
            occ_recs = []
            for _, row in valid_occ.iterrows():
                base = _extract_base_refined(row['name'])
                if base not in used_bases and len(occ_recs) < 5:
                    occ_recs.append(ExpertRecommendation(row['name'], row['brand'], row['cluster'], row['similarity'], row['brand_tier']))
                    used_bases.add(base)
            wardrobe[occ] = occ_recs
            
        return signature, wardrobe

# ============================================================================
# 4. REPORT & UI
# ============================================================================

def send_v92_report(answers, signature, wardrobe):
    try:
        if "EMAIL_ADDRESS" in st.secrets:
            sender = st.secrets["EMAIL_ADDRESS"]; psw = st.secrets["EMAIL_PASSWORD"]
            msg = MIMEMultipart(); msg['From'] = sender; msg['To'] = sender
            msg['Subject'] = f"🚀 AuraScent V9.2 Rapor - {datetime.date.today()}"
            body = "=== PROFİL ===\n"
            for k, v in answers.items(): body += f"{QUESTIONS[k]['question']} -> {v}\n"
            body += "\n=== 🌟 HİBRİT İMZALAR ===\n"
            for r in signature: body += f"[{r.brand_tier.upper()}] {r.perfume_name} (%{r.similarity_score*100:.1f})\n"
            body += "\n=== 👔 GARDIROP ===\n"
            for occ, items in wardrobe.items():
                body += f"\n> {occ}:\n"
                for r in items: body += f"  - {r.perfume_name} (%{r.similarity_score*100:.1f})\n"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(sender, psw)
            s.send_message(msg); s.quit(); return True
    except: return False

def run_streamlit_app():
    st.set_page_config(page_title="AuraScent Master V9.2", page_icon="✨", layout="wide")
    @st.cache_resource
    def load_engine(): return MasterUltimateEngineV92("aurascent_all_profiles.csv")
    engine = load_engine()

    if 'step' not in st.session_state: st.session_state.step = 0; st.session_state.answers = {}
    q_keys = list(QUESTIONS.keys())

    if st.session_state.step < len(q_keys):
        st.title("✨ AuraScent Master V9.2")
        q_key = q_keys[st.session_state.step]; q_data = QUESTIONS[q_key]
        ans = st.radio(q_data['question'], q_data['options'], key=f"r_{q_key}")
        if st.button("İlerle ➔"):
            st.session_state.answers[q_key] = ans
            st.session_state.step += 1; st.rerun()
    else:
        st.success("Analiz Tamamlandı! V9.2 motoru çalıştırıldı.")
        sig, wardrobe = engine.recommend_balanced(st.session_state.answers)
        if send_v92_report(st.session_state.answers, sig, wardrobe):
            st.info("📬 Rapor başarıyla gönderildi!")
        
        st.header("🌟 Hibrit İmzalar")
        cols = st.columns(4)
        for t, title, col in zip(["niche", "premium", "zara", "middle_east"], ["💎 NICHE", "👔 DESIGNER", "👗 ZARA", "🐪 CLONE"], cols):
            with col:
                st.subheader(title)
                for r in [x for x in sig if x.brand_tier == t]:
                    st.write(f"- {r.perfume_name} (%{r.similarity_score*100:.1f})")
        
        st.header("👔 Gardırop Stratejisi")
        occ_cols = st.columns(3)
        for (occ, items), o_col in zip(wardrobe.items(), occ_cols):
            with o_col:
                st.subheader(f"> {occ}")
                for r in items: st.write(f"- {r.perfume_name} (%{r.similarity_score*100:.1f})")
        
        if st.button("🔄 Yeniden Başlat"): st.session_state.step = 0; st.session_state.answers = {}; st.rerun()

if __name__ == "__main__":
    run_streamlit_app()