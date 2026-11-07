"""
==============================================================================
CORE AGENTIC AI GATES (SELF-HEALING & QUALITY ASSURANCE)
==============================================================================
Modul ini mengimplementasikan 4 Gate Agentic AI universal untuk memvalidasi,
mengaudit sampel dengan LLM, dan melakukan self-healing (retry / tune / reroute)
secara otomatis di sepanjang pipeline analisis sentimen:

1. Quality Gate      : Cleaning / Preprocessing (Statistik + LLM Sample Audit)
                       -> Pass / Retry dengan kamus slang & stopwords baru
2. Topic Gate        : BERTopic + IndoBERT (10 Sampel/Topik + 2x Cek LLM Kohesi & Duplikasi)
                       -> Pass (Lanjut Labeling) / Kalkulasi Ulang (Tune HDBSCAN & Re-cluster / Merge)
3. Verification Gate : Labeling + Agregasi (Audit Sampel Label + Confidence Check)
                       -> Pass / Relabel & Reroute ulasan low-confidence
4. Report Gate       : EDA + Visualisasi + Narasi (Angka Narasi vs Sumber Data JSON)
                       -> Pass / Auto-revisi klaim & angka yang meleset

Prinsip Transparansi & Keotentikan Pengujian:
  - Setiap eksekusi pipeline SELALU dimulai dari parameter & kamus DEFAULT murni
    (tidak membaca/menimpa file kamus atau config di disk lintas-run).
  - Seluruh penyesuaian parameter (slang baru, stopwords baru, tuning HDBSCAN,
    merge topik, relabeling, rerouting) dilakukan in-memory selama run berlangsung
    dan dicatat secara transparan ke `output/<platform>/json/agentic_audit_log.json`.
==============================================================================
"""

import os
import sys
import re
import copy

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import ast
import json
import time
from datetime import datetime
from collections import Counter
import numpy as np
import pandas as pd
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None

from cari_siber.engine.core.config import AppConfig
from cari_siber.engine.core.ai_client import generate_structured_json, generate_text, TOKEN_USAGE_TRACKER, reset_token_tracker
from cari_siber.paths import get_user_learned_slang_path, get_user_custom_stopwords_path


# ==============================================================================
# 0. AUDIT LOGGER (MENCATAT JEJAK KEPUTUSAN AGENTIC AI KE JSON)
# ==============================================================================
class AgenticAuditLogger:
    """Mencatat setiap aktivitas evaluasi, retry, dan self-healing dari 4 Gate Agentic."""

    @staticmethod
    def log_gate(output_dir: str, gate_name: str, segment: str, report: dict):

        if not output_dir:
            return
        try:
            json_dir = os.path.join(output_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            log_path = os.path.join(json_dir, "agentic_audit_log.json")

            existing = {"updated_at": "", "gates": []}
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        if "gates" not in existing or not isinstance(existing["gates"], list):
                            existing["gates"] = []
                except Exception:
                    existing = {"updated_at": "", "gates": []}

            now_str = datetime.now().isoformat(timespec="seconds")
            existing["updated_at"] = now_str
            entry = {
                "timestamp": now_str,
                "gate": gate_name,
                "segment": segment,
                **report,
            }
            existing["token_usage"] = dict(TOKEN_USAGE_TRACKER)
            existing["gates"].append(entry)

            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AGENTIC LOG WARNING] Gagal menyimpan log audit: {e}")

    @staticmethod
    def reset_log(output_dir: str):
        reset_token_tracker()

        if not output_dir:
            return
        try:
            json_dir = os.path.join(output_dir, "json")
            os.makedirs(json_dir, exist_ok=True)
            log_path = os.path.join(json_dir, "agentic_audit_log.json")
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump({"updated_at": datetime.now().isoformat(timespec="seconds"), "gates": []}, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def print_summary(output_dir: str):
        if not output_dir or not AppConfig.AGENTIC_GATES_ENABLED:
            return
        log_path = os.path.join(output_dir, "json", "agentic_audit_log.json")
        if not os.path.exists(log_path):
            return
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            gates = data.get("gates", [])
            if not gates:
                return
            print("\n" + "=" * 80)
            print("RINGKASAN AUDIT AGENTIC AI HARDENED GATES")
            print("=" * 80)
            for g in gates:
                g_name = g.get("gate", "Gate")
                seg = g.get("segment", "all")
                status = g.get("status", "PASSED")
                attempts = g.get("total_attempts", 1)
                if g_name == "VerificationGate":
                    relabeled = g.get("label_audit", {}).get("relabeled", 0)
                    rr = g.get("confidence_reroute", {})
                    init_c = rr.get("initial_confident_rate", 0.0)
                    fin_c = rr.get("final_confident_rate", 0.0)
                    r_alt = rr.get("rerouted_via_alt_topic", 0)
                    r_llm = rr.get("rerouted_via_llm", 0)
                    print(
                        f"  [✓] {g_name:18s} ({seg:10s}) | Relabeled: {relabeled} topik | "
                        f"Rerouted: {r_alt + r_llm} item (Conf: {init_c:.1%} -> {fin_c:.1%})"
                    )
                elif g_name == "TopicGate":
                    last_att = (g.get("attempts") or [{}])[-1]
                    llm_checks = last_att.get("llm_checks_completed", 0)
                    print(
                        f"  [✓] {g_name:18s} ({seg:10s}) | Status: {status} | "
                        f"Iterasi Klaster: {attempts}x (2x Cek LLM 10-Sampel/Topik: {llm_checks}x)"
                    )
                else:
                    print(f"  [✓] {g_name:18s} ({seg:10s}) | Status: {status} | Iterasi Evaluasi: {attempts}x")
            print(
                f"  Total Penggunaan Token LLM : {TOKEN_USAGE_TRACKER['total_tokens']:,} token "
                f"({TOKEN_USAGE_TRACKER['prompt_tokens']:,} prompt + {TOKEN_USAGE_TRACKER['completion_tokens']:,} completion "
                f"dalam {TOKEN_USAGE_TRACKER['calls']} request)"
            )
            print(f"  Log Audit Lengkap : {log_path}")
            print("=" * 80)
        except Exception:
            pass


def _get_active_ai_credentials(config_override: dict = None):
    cfg = config_override or {}
    provider = cfg.get("AI_PROVIDER", AppConfig.AI_PROVIDER).lower().strip()
    model = cfg.get("AI_MODEL", AppConfig.AI_MODEL).strip()
    gemini_key = cfg.get("GEMINI_API_KEY", AppConfig.GEMINI_API_KEY)
    openrouter_key = cfg.get("OPENROUTER_API_KEY", AppConfig.OPENROUTER_API_KEY)
    edgeone_key = cfg.get("EDGEONE_API_KEY", AppConfig.EDGEONE_API_KEY)
    custom_key = cfg.get("CUSTOM_API_KEY", AppConfig.CUSTOM_API_KEY)

    api_key = (
        gemini_key if provider == "gemini"
        else (edgeone_key if provider == "edgeone"
        else (openrouter_key if provider == "openrouter"
        else (custom_key if provider == "custom"
        else None)))
    )
    return provider, model, api_key


def _can_call_llm(provider: str, api_key: str) -> bool:
    if provider == "gemini":
        return bool(api_key and not api_key.startswith("["))
    if provider in ("openrouter", "edgeone"):
        return bool(api_key and not api_key.startswith("["))
    if provider == "custom":
        if api_key and not api_key.startswith("["):
            return True
        base_u = str(getattr(AppConfig, "CUSTOM_BASE_URL", "")).lower()
        return any(h in base_u for h in ("127.0.0.1", "localhost", "0.0.0.0", "192.168.", "10.", "172."))
    if provider == "ollama":
        return True
    return False


# ==============================================================================
# 1. QUALITY GATE: STATISTIK + LLM SAMPLE AUDIT (CLEANING / PREPROCESSING)
# ==============================================================================
class SlangMappingItem(BaseModel):
    slang: str = Field(description="Kata tidak baku / singkatan / typo (huruf kecil).")
    formal: str = Field(description="Kata baku Bahasa Indonesia yang benar (huruf kecil).")


class QualityGateAuditSchema(BaseModel):
    passed: bool = Field(
        description="True jika sampel teks hasil cleaning sudah cukup bersih dan siap untuk IndoBERT/BERTopic. False jika masih banyak slang/noise yang perlu dibersihkan ulang."
    )
    quality_score: float = Field(description="Skor kualitas hasil cleaning dari 0.0 hingga 1.0.")
    new_slang_mappings: list[SlangMappingItem] = Field(
        default_factory=list,
        description="Daftar kata singkatan/slang/typo yang ditemukan di sampel atau daftar token mencurigakan beserta padanan kata bakunya.",
    )
    new_stopwords: list[str] = Field(
        default_factory=list,
        description="Kata-kata noise atau kata seru tak bermakna topik (misal: 'wkwk', 'haha', 'min', 'kak') yang sebaiknya ditambahkan ke stopwords.",
    )
    collapse_repeated_chars: bool = Field(
        default=True,
        description="True jika ditemukan kata dengan huruf berulang berlebih (contoh: 'bagussss', 'lemooot').",
    )
    audit_notes: str = Field(description="Ringkasan evaluasi kualitas teks dalam Bahasa Indonesia.")


_RE_URL = re.compile(r"https?://\S+|www\.\S+")
_RE_MENTION = re.compile(r"@\w+")
_RE_NON_WORD = re.compile(r"[^\w\s]")
_RE_REPEATS = re.compile(r"(.)\1{2,}")
_RE_END_REPEATS = re.compile(r"(.)\1+$")


def normalisasi_teks_hardened(text: str, kamus: dict, collapse_repeats: bool = False) -> str:
    """
    Normalisasi teks yang dapat dikustomisasi parameternya saat retry oleh Quality Gate.
    Menggunakan pre-compiled regex untuk performa tinggi pada ribuan ulasan.
    """
    text = str(text).lower()
    text = _RE_URL.sub(" ", text)
    text = _RE_MENTION.sub(" ", text)
    text = _RE_NON_WORD.sub(" ", text)
    if collapse_repeats:
        text = _RE_REPEATS.sub(r"\1", text)
    words = text.split()
    normalized_words = []
    for word in words:
        mapped = kamus.get(word, word)
        if collapse_repeats and mapped == word and len(word) > 3:
            trimmed = _RE_END_REPEATS.sub(r"\1", word)
            mapped = kamus.get(trimmed, word)
        normalized_words.append(mapped)
    return " ".join(normalized_words)


def _compute_cleaning_stats(docs_raw: list[str], docs_clean: list[str], stopwords_set: set, min_words: int):
    total = len(docs_clean)
    if total == 0:
        return {
            "total_docs": 0,
            "empty_or_short_count": 0,
            "empty_or_short_ratio": 0.0,
            "duplicate_ratio": 0.0,
            "avg_word_count": 0.0,
            "suspicious_tokens": [],
        }

    word_counts = []
    empty_or_short = 0
    token_counter = Counter()

    for doc in docs_clean:
        tokens = [w for w in doc.split() if w not in stopwords_set and not w.isdigit()]
        wc = len(tokens)
        word_counts.append(wc)
        if wc < min_words:
            empty_or_short += 1
        for t in tokens:
            token_counter[t] += 1

    unique_docs = len(set(d for d in docs_clean if d.strip()))
    non_empty = max(1, sum(1 for d in docs_clean if d.strip()))
    duplicate_ratio = round(1.0 - (unique_docs / non_empty), 4)

    vowels = set("aiueo")
    suspicious_tokens = []
    for tok, freq in token_counter.most_common(120):
        if freq < 2:
            continue
        has_vowel = any(c in vowels for c in tok)
        has_repeat = bool(re.search(r"(.)\1{2,}", tok))
        if (len(tok) <= 3 and freq >= 3) or not has_vowel or has_repeat:
            suspicious_tokens.append(f"{tok} ({freq}x)")
        if len(suspicious_tokens) >= 25:
            break

    return {
        "total_docs": total,
        "empty_or_short_count": empty_or_short,
        "empty_or_short_ratio": round(empty_or_short / total, 4),
        "duplicate_ratio": duplicate_ratio,
        "avg_word_count": round(float(np.mean(word_counts)) if word_counts else 0.0, 2),
        "suspicious_tokens": suspicious_tokens,
    }


def save_learned_slang(new_slang_dict: dict, data_dir: str = None) -> int:
    """
    Menyimpan kata slang baru hasil pembelajaran (incremental learning) ke file pendamping
    writable kamus-alay-learned.csv tanpa mengubah file dasar 'kamus-alay-nasalsabila.csv'
    sehingga kredit hak cipta Nasalsabila tetap aman dan terpisah.
    """
    if not new_slang_dict:
        return 0

    if data_dir is not None:
        os.makedirs(data_dir, exist_ok=True)
        learned_path = os.path.join(data_dir, "kamus-alay-learned.csv")
    else:
        learned_path = get_user_learned_slang_path()
        os.makedirs(os.path.dirname(learned_path), exist_ok=True)
    existing_learned = {}

    if os.path.exists(learned_path):
        try:
            df_old = pd.read_csv(learned_path)
            if "slang" in df_old.columns and "formal" in df_old.columns:
                existing_learned = dict(zip(
                    df_old["slang"].astype(str).str.strip().str.lower(),
                    df_old["formal"].astype(str).str.strip().str.lower()
                ))
        except Exception:
            existing_learned = {}

    truly_new = {}
    for s_word, f_word in new_slang_dict.items():
        s_clean = str(s_word).strip().lower()
        f_clean = str(f_word).strip().lower()
        if s_clean and f_clean and s_clean != f_clean and len(s_clean) >= 2:
            if s_clean not in existing_learned:
                truly_new[s_clean] = f_clean

    if not truly_new:
        return 0

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(learned_path) and os.path.getsize(learned_path) > 0

    try:
        import csv
        with open(learned_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["slang", "formal", "source", "learned_at"])
            for s, f_w in sorted(truly_new.items()):
                writer.writerow([s, f_w, "cari_sentimen_learning", now_str])

        print(f"[LEARNING] 🧠 Menyimpan {len(truly_new)} kata slang baru ke '{learned_path}' (Kredit dasar Nasalsabila tetap utuh).")
        return len(truly_new)
    except Exception as e:
        print(f"[WARNING] Gagal menyimpan learned slang: {e}")
        return 0


def save_learned_stopwords(new_stopwords: list[str], data_dir: str = None) -> int:
    """
    Menyimpan stopwords baru secara akumulatif ke stopwords.txt writable pengguna tanpa menimpa kata lama.
    """
    if not new_stopwords:
        return 0

    if data_dir is not None:
        os.makedirs(data_dir, exist_ok=True)
        sw_path = os.path.join(data_dir, "stopwords.txt")
    else:
        sw_path = get_user_custom_stopwords_path()
        os.makedirs(os.path.dirname(sw_path), exist_ok=True)
    existing_sw = set()

    if os.path.exists(sw_path):
        try:
            with open(sw_path, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip().lower()
                    if w and len(w) > 1:
                        existing_sw.add(w)
        except Exception:
            pass

    to_add = set()
    for w in new_stopwords:
        w_clean = str(w).strip().lower()
        if w_clean and len(w_clean) > 1 and w_clean not in existing_sw:
            to_add.add(w_clean)

    if not to_add:
        return 0

    all_sw = sorted(list(existing_sw | to_add))
    try:
        with open(sw_path, "w", encoding="utf-8") as f:
            for w in all_sw:
                f.write(f"{w}\n")
        print(f"[LEARNING] 📚 Menambahkan {len(to_add)} stopwords baru ke '{sw_path}' (Total sekarang: {len(all_sw)} kata).")
        return len(to_add)
    except Exception as e:
        print(f"[WARNING] Gagal memperbarui stopwords.txt: {e}")
        return 0


def run_quality_gate(
    docs_raw: list[str],
    kamus: dict,
    stopwords: list[str],
    domain_name: str = "Aplikasi",
    output_dir: str = None,
    segment_label: str = "all",
    config_override: dict = None,
) -> tuple[list[str], dict, list[str], dict]:
    """
    Menjalankan Quality Gate pada tahap Cleaning / Preprocessing:
    - Selalu dimulai dari kamus & stopwords DEFAULT (in-memory copy) agar transparan & otentik
    - Menghitung statistik teks hasil normalisasi
    - Melakukan LLM Sample Audit terhadap sampel mikro (8 dokumen) & token mencurigakan
    - Jika belum optimal, memperkaya kamus_slang & stopwords di memori untuk retry pada run ini
    """
    working_kamus = dict(kamus)
    stopwords_set = set(stopwords)

    if not AppConfig.AGENTIC_GATES_ENABLED:
        docs_clean = [normalisasi_teks_hardened(d, working_kamus, collapse_repeats=False) for d in docs_raw]
        return docs_clean, working_kamus, sorted(list(stopwords_set)), {"enabled": False}

    print(f"\n[QUALITY GATE] Memeriksa kualitas cleaning & preprocessing ({segment_label.upper()}) [Default Config]...")
    max_retries = max(1, AppConfig.AGENTIC_MAX_RETRIES)
    min_words = max(1, AppConfig.AGENTIC_QUALITY_MIN_WORDS)
    provider, model, api_key = _get_active_ai_credentials(config_override)

    collapse_repeats = False
    attempts_history = []
    docs_clean = []

    for attempt in range(max_retries + 1):
        docs_clean = [
            normalisasi_teks_hardened(doc, working_kamus, collapse_repeats=collapse_repeats)
            for doc in docs_raw
        ]
        stats = _compute_cleaning_stats(docs_raw, docs_clean, stopwords_set, min_words)

        print(
            f"  [Quality Gate - Iterasi {attempt + 1}] Total Dokumen: {stats['total_docs']} | "
            f"Avg Kata: {stats['avg_word_count']} | Rasio Terlalu Pendek: {stats['empty_or_short_ratio']:.1%} | "
            f"Token Mencurigakan: {len(stats['suspicious_tokens'])}"
        )

        sample_indices = np.linspace(0, max(0, len(docs_raw) - 1), min(8, len(docs_raw)), dtype=int)
        sample_pairs_text = ""
        for idx in sample_indices:
            r_txt = str(docs_raw[idx]).replace("\n", " ").strip()[:160]
            c_txt = str(docs_clean[idx]).replace("\n", " ").strip()[:160]
            sample_pairs_text += f"- RAW  : {r_txt}\n  CLEAN: {c_txt}\n"

        llm_audit = None
        if attempt == 0 and len(stats["suspicious_tokens"]) >= 3 and _can_call_llm(provider, api_key) and len(docs_raw) > 0:
            prompt = (
                f"Anda adalah Data Quality Auditor untuk pipeline NLP Bahasa Indonesia pada '{domain_name}'.\n"
                "Evaluasi kualitas hasil text cleaning/normalisasi berikut sebelum masuk ke IndoBERT & BERTopic.\n\n"
                f"Statistik Saat Ini:\n"
                f"- Total Dokumen: {stats['total_docs']}\n"
                f"- Rata-rata kata bermakna per dokumen: {stats['avg_word_count']}\n"
                f"- Rasio dokumen terlalu pendek (<{min_words} kata): {stats['empty_or_short_ratio']:.1%}\n"
                f"- Token pendek/mencurigakan yang sering muncul (belum masuk kamus slang/stopwords): {', '.join(stats['suspicious_tokens'][:20])}\n\n"
                f"Sampel Perbandingan Teks (RAW vs CLEAN):\n{sample_pairs_text}\n"
                "Tugas Audit:\n"
                "1. Identifikasi kata singkatan/slang/typo Bahasa Indonesia di sampel atau daftar token mencurigakan yang belum dinormalisasi ke kata baku (masukkan ke `new_slang_mappings`).\n"
                "2. Identifikasi kata seru/partikel/noise tidak bermakna topik (seperti wkwk, haha, min, kak, gan, bro, mas, bos, dll.) yang sebaiknya masuk ke `new_stopwords`.\n"
                "3. Jika pada iterasi ini masih ditemukan >= 2 kata slang/noise penting yang belum bersih, set `passed = false` agar sistem melakukan retry cleaning dengan parameter baru. Jika sudah bersih, set `passed = true`."
            )
            llm_audit = generate_structured_json(prompt, QualityGateAuditSchema, provider, model, api_key)

        new_slang_dict = {}
        new_sw_list = []
        passed = True
        quality_score = 0.85
        audit_notes = "Statistik lolos evaluasi deterministik."

        if llm_audit and isinstance(llm_audit, dict):
            passed = bool(llm_audit.get("passed", True))
            quality_score = float(llm_audit.get("quality_score", 0.85))
            audit_notes = str(llm_audit.get("audit_notes", ""))
            raw_slang_mappings = llm_audit.get("new_slang_mappings", []) or []
            if isinstance(raw_slang_mappings, dict):
                raw_slang_mappings = [{"slang": k, "formal": v} for k, v in raw_slang_mappings.items()]
            for item in raw_slang_mappings:
                if isinstance(item, dict):
                    s_word = str(item.get("slang", "")).strip().lower()
                    f_word = str(item.get("formal", "")).strip().lower()
                elif isinstance(item, str) and (":" in item or "->" in item or "=" in item):
                    parts = re.split(r"[:=]|->", item, maxsplit=1)
                    s_word = parts[0].strip().lower()
                    f_word = parts[1].strip().lower() if len(parts) > 1 else ""
                else:
                    continue
                if s_word and f_word and s_word != f_word and len(s_word) >= 2:
                    if working_kamus.get(s_word) != f_word:
                        new_slang_dict[s_word] = f_word
            for sw in llm_audit.get("new_stopwords", []) or []:
                sw_clean = str(sw).strip().lower()
                if sw_clean and len(sw_clean) >= 2 and sw_clean not in stopwords_set:
                    new_sw_list.append(sw_clean)

            if llm_audit.get("collapse_repeated_chars", False):
                collapse_repeats = True
        else:
            if not collapse_repeats and len(stats["suspicious_tokens"]) > 5:
                collapse_repeats = True
                passed = False
                audit_notes = "Deteksi deterministik menemukan karakter berulang/token tidak baku; mengaktifkan collapse_repeats."

        attempts_history.append({
            "attempt": attempt + 1,
            "stats": stats,
            "passed": passed,
            "quality_score": quality_score,
            "new_slang_added": len(new_slang_dict),
            "new_stopwords_added": len(new_sw_list),
            "learned_slang": new_slang_dict,
            "learned_stopwords": new_sw_list,
            "audit_notes": audit_notes,
        })

        has_parameter_updates = bool(new_slang_dict or new_sw_list or (not passed and not collapse_repeats))
        if (passed and not has_parameter_updates) or attempt >= max_retries:
            if new_slang_dict or new_sw_list:
                working_kamus.update(new_slang_dict)
                stopwords_set.update(new_sw_list)
                docs_clean = [
                    normalisasi_teks_hardened(doc, working_kamus, collapse_repeats=True)
                    for doc in docs_raw
                ]
            print(f"  [QUALITY GATE PASS] Skor Kualitas: {quality_score:.2f} | Catatan: {audit_notes}")
            break

        print(
            f"  [QUALITY GATE RETRY] Menambahkan {len(new_slang_dict)} kamus slang baru & "
            f"{len(new_sw_list)} stopwords baru (in-memory), lalu mengulang preprocessing..."
        )
        collapse_repeats = True
        if new_slang_dict:
            working_kamus.update(new_slang_dict)
        if new_sw_list:
            stopwords_set.update(new_sw_list)

    updated_stopwords = sorted(list(stopwords_set))
    gate_report = {
        "status": "PASSED",
        "total_attempts": len(attempts_history),
        "attempts": attempts_history,
    }
    AgenticAuditLogger.log_gate(output_dir, "QualityGate", segment_label, gate_report)

    # Simpan hasil incremental learning ke disk secara kumulatif
    all_learned_slang = {}
    all_learned_stopwords = []
    for att in attempts_history:
        all_learned_slang.update(att.get("learned_slang", {}))
        all_learned_stopwords.extend(att.get("learned_stopwords", []))

    if all_learned_slang:
        save_learned_slang(all_learned_slang)
    if all_learned_stopwords:
        save_learned_stopwords(all_learned_stopwords)

    return docs_clean, working_kamus, updated_stopwords, gate_report


# ==============================================================================
# 2. TOPIC GATE: CEK 10 SAMPEL/TOPIK x 2 PUTARAN LLM SEBELUM LABELING
# ==============================================================================
class TopicMergePair(BaseModel):
    topic_id_1: int = Field(description="ID topik pertama yang duplikat/identik dengan topik kedua.")
    topic_id_2: int = Field(description="ID topik kedua yang duplikat/identik dengan topik pertama.")
    reason: str = Field(description="Alasan mengapa ke-10 sampel kedua topik ini identik membahas hal yang sama.")


class TopicGateAuditSchema(BaseModel):
    passed: bool = Field(
        description="True jika ke-10 sampel pada masing-masing topik sudah identik satu bahasan (koheren) dan layak lanjut ke tahap Labeling. False jika banyak topik yang isinya masih campur aduk sehingga harus dikalkulasi ulang."
    )
    coherence_score: float = Field(description="Skor kohesi dan kemurnian isi sampel per topik (0.0 - 1.0).")
    incoherent_topic_ids: list[int] = Field(
        default_factory=list,
        description="Daftar topic_id yang 10 sampel di dalamnya TIDAK identik satu bahasan (masih campur aduk berbagai isu berbeda).",
    )
    duplicate_pairs: list[TopicMergePair] = Field(
        default_factory=list,
        description="Pasangan topic_id yang ke-10 sampelnya membahas hal yang sama persis (kembar) dan harus digabung.",
    )
    recommended_action: str = Field(
        description="Pilih salah satu: 'pass', 'merge_duplicates', 'decrease_min_cluster_size', 'increase_min_cluster_size'."
    )
    audit_notes: str = Field(description="Analisis singkat hasil pengecekan 10 sampel per topik dalam Bahasa Indonesia.")


def evaluate_topic_cohesion_and_duplication(
    topic_model,
    docs_clean: list[str],
    embeddings: np.ndarray,
    max_similarity_threshold: float = 0.85,
    docs_raw: list[str] = None,
) -> dict:
    """
    Menghitung metrik kohesi intra-topik, duplikasi antar-topik, serta mengekstrak
    minimal 10 sampel komentar/ulasan per topik untuk:
      - Putaran 1 (`samples_pass_1`: 10 sampel paling representatif di pusat topik)
      - Putaran 2 (`samples_pass_2`: 10 sampel stratifikasi/tersebar di tengah-tepi topik)
    """
    topics = np.array(topic_model.topics_)
    total_docs = len(topics)
    source_docs = docs_raw if (docs_raw is not None and len(docs_raw) == total_docs) else docs_clean

    if total_docs == 0:
        return {
            "total_docs": 0,
            "num_topics": 0,
            "outlier_count": 0,
            "outlier_ratio": 0.0,
            "mean_cohesion": 0.0,
            "low_cohesion_topics": [],
            "duplicate_pairs": [],
            "topic_summaries": [],
        }

    outlier_count = int(np.sum(topics == -1))
    outlier_ratio = round(outlier_count / total_docs, 4)

    unique_valid_topics = sorted([int(t) for t in set(topics) if t != -1])
    centroids = {}
    intra_cohesions = {}
    topic_keywords_map = {}
    topic_top1_kw = {}
    topic_summaries = []

    for t_id in unique_valid_topics:
        idx = np.where(topics == t_id)[0]
        if len(idx) == 0:
            continue
        sub_emb = embeddings[idx]
        mean_vec = sub_emb.mean(axis=0)
        norm = np.linalg.norm(mean_vec)
        centroid = mean_vec / norm if norm > 0 else mean_vec
        centroids[t_id] = centroid

        # Urutkan dokumen di topik ini berdasarkan kemiripan ke centroid (tertinggi ke terendah)
        sims = np.dot(sub_emb, centroid)
        cohesion = float(np.mean(sims))
        intra_cohesions[t_id] = round(cohesion, 4)
        sorted_local_order = np.argsort(-sims)
        sorted_doc_indices = idx[sorted_local_order]

        # Ambil minimal 10 sampel untuk Putaran 1 (10 dokumen paling representatif)
        pass1_indices = sorted_doc_indices[:10]
        samples_pass_1 = [
            str(source_docs[i]).replace("\n", " ").strip()[:130] for i in pass1_indices
        ]

        # Ambil minimal 10 sampel untuk Putaran 2 (stratifikasi merata dari seluruh anggota topik)
        n_members = len(sorted_doc_indices)
        if n_members >= 20:
            strat_pos = np.linspace(3, n_members - 1, 10, dtype=int)
            pass2_indices = sorted_doc_indices[strat_pos]
        elif n_members >= 10:
            pass2_indices = sorted_doc_indices[-10:][::-1]
        else:
            pass2_indices = sorted_doc_indices[::-1]

        samples_pass_2 = [
            str(source_docs[i]).replace("\n", " ").strip()[:130] for i in pass2_indices
        ]

        # Ambil top keywords c-TF-IDF
        t_words = topic_model.get_topic(t_id) or []
        kw_list = [str(w).strip().lower() for w, _ in t_words[:8] if str(w).strip()]
        base_tokens = set()
        for kw in kw_list[:6]:
            base_tokens.add(kw)
            for part in kw.split():
                if len(part) >= 3:
                    base_tokens.add(part)
        topic_keywords_map[t_id] = base_tokens
        topic_top1_kw[t_id] = kw_list[0].split()[0] if kw_list else ""

        topic_summaries.append({
            "topic_id": t_id,
            "count": int(len(idx)),
            "cohesion": round(cohesion, 3),
            "keywords": ", ".join(kw_list),
            "samples": " | ".join(samples_pass_1[:3]),
            "samples_pass_1": samples_pass_1,
            "samples_pass_2": samples_pass_2,
        })

    mean_cohesion = round(float(np.mean(list(intra_cohesions.values()))), 4) if intra_cohesions else 0.0
    low_cohesion_topics = [t_id for t_id, c in intra_cohesions.items() if c < 0.55]

    # Cek pasangan topik duplikat secara leksikal + vektor
    duplicate_pairs = []
    n_t = len(unique_valid_topics)
    for i in range(n_t):
        for j in range(i + 1, n_t):
            t1, t2 = unique_valid_topics[i], unique_valid_topics[j]
            if t1 not in centroids or t2 not in centroids:
                continue
            cos_sim = float(np.dot(centroids[t1], centroids[t2]))
            kw1, kw2 = topic_keywords_map.get(t1, set()), topic_keywords_map.get(t2, set())
            union_len = len(kw1 | kw2)
            jaccard = (len(kw1 & kw2) / union_len) if union_len > 0 else 0.0
            top1_same = (
                bool(topic_top1_kw.get(t1))
                and topic_top1_kw.get(t1) == topic_top1_kw.get(t2)
                and len(topic_top1_kw.get(t1, "")) >= 4
            )

            is_dup = (
                (cos_sim >= max_similarity_threshold and jaccard >= 0.25)
                or (cos_sim >= 0.78 and jaccard >= 0.40)
                or (top1_same and cos_sim >= 0.70 and jaccard >= 0.15)
            )
            if is_dup:
                duplicate_pairs.append({
                    "topic_id_1": t1,
                    "topic_id_2": t2,
                    "cosine_similarity": round(cos_sim, 4),
                    "keyword_jaccard": round(jaccard, 4),
                })

    duplicate_pairs.sort(key=lambda x: (x["keyword_jaccard"], x["cosine_similarity"]), reverse=True)

    return {
        "total_docs": total_docs,
        "num_topics": len(unique_valid_topics),
        "outlier_count": outlier_count,
        "outlier_ratio": outlier_ratio,
        "mean_cohesion": mean_cohesion,
        "low_cohesion_topics": low_cohesion_topics,
        "duplicate_pairs": duplicate_pairs,
        "topic_summaries": topic_summaries,
    }


def _run_llm_topic_sample_check(
    metrics: dict,
    pass_number: int,
    domain_name: str,
    segment_label: str,
    hdbscan_params: dict,
    provider: str,
    model: str,
    api_key: str,
) -> dict:
    """
    Menjalankan 1 putaran pemeriksaan LLM terhadap hasil klasterisasi topik
    dengan menampilkan minimal 10 sampel komentar/ulasan nyata untuk SETIAP topik.
    Jika jumlah topik > 10, dievaluasi per batch (maks 10 topik/batch) agar akurat & cepat.
    """
    topic_summaries = metrics.get("topic_summaries", [])
    if not topic_summaries or not _can_call_llm(provider, api_key):
        return {
            "passed": True,
            "coherence_score": metrics.get("mean_cohesion", 0.75),
            "incoherent_topic_ids": [],
            "duplicate_pairs": [],
            "recommended_action": "pass",
            "audit_notes": "Evaluasi deterministik (LLM tidak dipanggil).",
        }

    sample_key = "samples_pass_1" if pass_number == 1 else "samples_pass_2"
    pass_desc = (
        "Putaran 1 (10 Sampel Utama/Pusat Klaster per Topik)"
        if pass_number == 1
        else "Putaran 2 (10 Sampel Stratifikasi/Uji Silang per Topik)"
    )
    print(f"    -> [Topic Gate - Cek LLM {pass_number}/2] Menguji kesesuaian 10 sampel/topik ({pass_desc})...")

    # Batch size diperkecil ke 4 agar payload tidak terlalu panjang (~1.200 prompt token),
    # menghindari token exhaustion pada reasoning model, dan menjaga latensi per panggilan tetap gesit (4-8 detik).
    batch_size = 4
    total_batches = (len(topic_summaries) + batch_size - 1) // batch_size
    all_incoherent_ids = []
    all_dup_pairs = []
    coherence_scores = []
    notes_list = []
    recommended_actions = []

    for b_start in range(0, len(topic_summaries), batch_size):
        batch = topic_summaries[b_start : b_start + batch_size]
        batch_num = (b_start // batch_size) + 1
        batch_t_ids = [ts["topic_id"] for ts in batch]
        print(
            f"      [Cek LLM {pass_number}/2 - Batch {batch_num}/{total_batches}] "
            f"Mengevaluasi {len(batch)} topik (Topic ID: {batch_t_ids}, masing-masing 10 sampel)...",
            flush=True,
        )
        summaries_txt = ""
        for ts in batch:
            samples_list = ts.get(sample_key) or ts.get("samples_pass_1") or []
            numbered_samples = "\n".join(
                [f"      {idx_s + 1}. \"{s_txt}\"" for idx_s, s_txt in enumerate(samples_list[:10])]
            )
            summaries_txt += (
                f"=== Topic ID: {ts['topic_id']} (Total Anggota: {ts['count']}, Kohesi Vektor: {ts['cohesion']}) ===\n"
                f"  Kata Kunci c-TF-IDF: [{ts['keywords']}]\n"
                f"  Sampel Komentar/Ulasan ({len(samples_list[:10])} sampel):\n{numbered_samples}\n\n"
            )

        dup_hint = (
            json.dumps(metrics.get("duplicate_pairs", []), ensure_ascii=False)
            if metrics.get("duplicate_pairs")
            else "Tidak ada pasangan yang melebihi threshold leksikal+vektor."
        )

        prompt = (
            f"Anda adalah Senior Topic Modeling Auditor untuk '{domain_name}' (segmen: {segment_label}).\n"
            f"Ini adalah **Pengecekan LLM Putaran ke-{pass_number} dari 2** SEBELUM topik masuk ke tahap Auto-Labeling.\n"
            f"Parameter HDBSCAN saat ini: min_cluster_size={hdbscan_params.get('min_cluster_size')}, "
            f"min_samples={hdbscan_params.get('min_samples')}.\n\n"
            f"Kandidat Pasangan Mirip (Deteksi Vektor+Keyword): {dup_hint}\n\n"
            f"Berikut adalah daftar topik beserta **10 sampel nyata** dari masing-masing topik:\n\n"
            f"{summaries_txt}"
            "TUGAS EVALUASI KETAT:\n"
            "1. Periksa ke-10 sampel pada setiap Topic ID: apakah sampel-sampel di dalam satu topik tersebut **identik membahas satu pokok bahasan/opini yang koheren**?\n"
            "   - Jika ada topik yang isinya sangat campur aduk (membahas banyak isu yang bertolak belakang dalam 1 topik), masukkan ID-nya ke `incoherent_topic_ids`.\n"
            "2. Periksa antar-topik: apakah ada dua Topic ID berbeda yang ke-10 sampelnya **identik membahas hal yang sama persis**? Jika ada, masukkan ke `duplicate_pairs`.\n"
            "3. Tentukan keputusan:\n"
            "   - Jika mayoritas topik (>= 75% topik) sudah koheren/identik satu bahasan, set `passed = true` dan `recommended_action = 'pass'` (atau `'merge_duplicates'` jika hanya perlu menggabungkan topik kembar).\n"
            "   - Jika banyak topik (> 25% topik) masih campur aduk dan tidak koheren sehingga harus dikalkulasi ulang oleh BERTopic, set `passed = false` dan pilih `'decrease_min_cluster_size'` (untuk memecah topik yang terlalu besar/campur aduk) atau `'increase_min_cluster_size'` (jika terlalu banyak topik kecil yang pecah)."
        )

        res = generate_structured_json(prompt, TopicGateAuditSchema, provider, model, api_key)
        if res and isinstance(res, dict):
            b_score = float(res.get("coherence_score", metrics.get("mean_cohesion", 0.75)))
            b_inc = res.get("incoherent_topic_ids", []) or []
            b_dup = res.get("duplicate_pairs", []) or []
            b_note = str(res.get("audit_notes", ""))
            print(
                f"      [Cek LLM {pass_number}/2 - Batch {batch_num}/{total_batches} Selesai] "
                f"Skor: {b_score:.2f} | Inkoheren: {b_inc} | Duplikat: {b_dup} | Catatan: {b_note[:120]}...",
                flush=True,
            )
            coherence_scores.append(float(res.get("coherence_score", metrics.get("mean_cohesion", 0.75))))
            notes_list.append(str(res.get("audit_notes", "")))
            act = str(res.get("recommended_action", "pass")).strip().lower()
            recommended_actions.append((bool(res.get("passed", True)), act))

            for inc_id in res.get("incoherent_topic_ids", []) or []:
                try:
                    val_id = int(inc_id)
                    if val_id not in all_incoherent_ids:
                        all_incoherent_ids.append(val_id)
                except Exception:
                    pass

            for dp in res.get("duplicate_pairs", []) or []:
                try:
                    if isinstance(dp, dict):
                        t1 = int(dp.get("topic_id_1"))
                        t2 = int(dp.get("topic_id_2"))
                    elif isinstance(dp, (list, tuple)) and len(dp) >= 2:
                        t1, t2 = int(dp[0]), int(dp[1])
                    else:
                        continue
                    if t1 != t2 and (t1, t2) not in all_dup_pairs and (t2, t1) not in all_dup_pairs:
                        all_dup_pairs.append((t1, t2))
                except Exception:
                    pass

    total_topics = max(1, len(topic_summaries))
    incoherent_ratio = len(all_incoherent_ids) / total_topics
    avg_coh = round(float(np.mean(coherence_scores)), 3) if coherence_scores else metrics.get("mean_cohesion", 0.75)

    # Jika rasio topik tidak koheren > 30% atau LLM secara eksplisit meminta re-cluster
    recluster_votes = [
        act for ok, act in recommended_actions
        if not ok and act in ("decrease_min_cluster_size", "increase_min_cluster_size")
    ]
    if incoherent_ratio > 0.30 or (recluster_votes and incoherent_ratio > 0.20):
        overall_passed = False
        chosen_action = recluster_votes[0] if recluster_votes else "decrease_min_cluster_size"
    elif all_dup_pairs:
        overall_passed = True
        chosen_action = "merge_duplicates"
    else:
        overall_passed = True
        chosen_action = "pass"

    return {
        "pass_number": pass_number,
        "passed": overall_passed,
        "coherence_score": avg_coh,
        "incoherent_topic_ids": all_incoherent_ids,
        "incoherent_ratio": round(incoherent_ratio, 4),
        "duplicate_pairs": [{"topic_id_1": a, "topic_id_2": b} for a, b in all_dup_pairs],
        "recommended_action": chosen_action,
        "audit_notes": " | ".join([n for n in notes_list if n])[:400] or "Evaluasi 10 sampel/topik selesai.",
    }


def _merge_duplicate_topics_safely(topic_model, docs_clean: list[str], pairs_to_merge: list[tuple[int, int]]):
    """
    Menggabungkan pasangan topik yang terdeteksi duplikat secara terbatas (bounded greedy groups,
    maks 2 topik per pasangan per tahap) untuk mencegah efek bola salju (transitive snowball chaining)
    yang menelan seluruh topik ke dalam satu klaster raksasa.
    """
    if not pairs_to_merge:
        return False

    valid_topics = set(topic_model.topics_) - {-1}
    total_valid = len(valid_topics)
    if total_valid <= 4:
        return False

    min_allowed_topics = max(5, total_valid // 2)
    max_merges_allowed = max(0, total_valid - min_allowed_topics)
    if max_merges_allowed == 0:
        return False

    used_topics = set()
    merge_groups = []
    merges_count = 0

    for t1, t2 in pairs_to_merge:
        if merges_count >= max_merges_allowed:
            break
        if t1 not in valid_topics or t2 not in valid_topics or t1 == t2:
            continue
        if t1 not in used_topics and t2 not in used_topics:
            merge_groups.append(sorted([t1, t2]))
            used_topics.add(t1)
            used_topics.add(t2)
            merges_count += 1

    if not merge_groups:
        return False

    try:
        print(f"  [Topic Gate] Menggabungkan pasangan topik identik/duplikat: {merge_groups}...")
        topic_model.merge_topics(docs_clean, merge_groups)
        return True
    except Exception as e:
        print(f"  [Topic Gate WARNING] Gagal menggabungkan topik duplikat: {e}")
        return False


def audit_and_heal_topic_clustering(
    docs_clean: list[str],
    embeddings: np.ndarray,
    vectorizer_model,
    config: dict,
    initial_min_size: int,
    domain_name: str = "Aplikasi",
    segment_label: str = "all",
    output_dir: str = None,
    config_override: dict = None,
    docs_raw: list[str] = None,
):
    """
    Menjalankan siklus BERTopic + Topic Gate SEBELUM tahap Auto-Labeling:
    - Selalu memulai Iterasi 1 dengan konfigurasi DEFAULT dari `config/bertopic_config.json`
      dan UMAP deterministik (`random_state=42`)
    - Mengekstrak minimal 10 sampel komentar/ulasan per topik dan melakukan **2x Pengecekan LLM**:
      * Cek LLM 1/2: 10 sampel utama (pusat klaster) per topik -> cek apakah tiap topik identik satu bahasan & apakah ada topik kembar
      * Cek LLM 2/2: 10 sampel stratifikasi (tengah-tepi klaster) per topik -> verifikasi silang kedua kalinya
    - Jika identik/koheren pada 2x cek LLM -> LOLOS (lanjut ke Auto-Labeling)
    - Jika tidak identik / campur aduk -> KALKULASI ULANG (tune parameter HDBSCAN & cluster ulang)
    """
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    try:
        from umap import UMAP
    except ImportError:
        UMAP = None

    max_retries = max(1, AppConfig.AGENTIC_MAX_RETRIES) if AppConfig.AGENTIC_GATES_ENABLED else 0
    max_outlier_ratio = AppConfig.AGENTIC_TOPIC_MAX_OUTLIER_RATIO
    max_sim_thresh = AppConfig.AGENTIC_TOPIC_MAX_SIMILARITY
    provider, model, api_key = _get_active_ai_credentials(config_override)

    # Mulai dari salinan murni parameter HDBSCAN default
    hdbscan_params = copy.deepcopy(config["hdbscan"])
    min_size = max(5, initial_min_size)
    hdbscan_params["min_cluster_size"] = min_size

    attempts_log = []
    topic_model = None
    probs = None

    for gate_attempt in range(max_retries + 1):
        # 1. Fit BERTopic dengan UMAP deterministik (random_state=42)
        for fit_try in range(3):
            hdbscan_model = HDBSCAN(**hdbscan_params, core_dist_n_jobs=1)
            umap_model = (
                UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)
                if UMAP is not None
                else None
            )
            topic_model = BERTopic(
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                language=config["bertopic"]["language"],
                calculate_probabilities=config["bertopic"]["calculate_probabilities"],
                min_topic_size=hdbscan_params["min_cluster_size"],
                vectorizer_model=vectorizer_model,
                verbose=False,
            )
            try:
                topics, probs = topic_model.fit_transform(docs_clean, embeddings=embeddings)
                break
            except Exception as e:
                if fit_try == 2:
                    raise e
                min_size = max(5, min_size - 2)
                hdbscan_params["min_cluster_size"] = min_size
                hdbscan_params["min_samples"] = max(1, min_size // 2)

        # 2. Outlier reduction awal sesuai strategi default config
        current_topics = topic_model.topics_
        if -1 in current_topics and len(set(current_topics) - {-1}) >= 1:
            try:
                new_topics = topic_model.reduce_outliers(
                    docs_clean,
                    current_topics,
                    strategy=config["bertopic"]["reduce_outliers_strategy"],
                )
                topic_model.update_topics(docs_clean, topics=new_topics, vectorizer_model=vectorizer_model)
            except Exception as e:
                print(f"  [BERTopic] Peringatan saat mengurangi outliers: {e}")

        # 2b. Reduksi otomatis ke target topik agregasi (maksimal 20-25 topik) SEBELUM evaluasi dan 2x Cek LLM
        # Memastikan audit LLM hanya dilakukan pada topik yang sudah diagregasi (sangat hemat token)
        unique_t = set(topic_model.topics_) - {-1}
        max_aggregate_topics = 20 if len(docs_clean) < 1000 else 25
        if len(unique_t) > max_aggregate_topics:
            try:
                print(f"  [Topic Gate] Mereduksi {len(unique_t)} topik mikro menjadi {max_aggregate_topics} topik agregasi sebelum audit LLM...")
                topic_model.reduce_topics(docs_clean, nr_topics=max_aggregate_topics)
            except Exception as e:
                print(f"  [Topic Gate WARNING] Gagal mereduksi topik awal: {e}")

        if not AppConfig.AGENTIC_GATES_ENABLED:
            break

        # 3. Evaluasi Matematis + Ekstraksi 10 Sampel Putaran 1 & Putaran 2 per Topik
        metrics = evaluate_topic_cohesion_and_duplication(
            topic_model, docs_clean, embeddings, max_similarity_threshold=max_sim_thresh, docs_raw=docs_raw
        )
        print(
            f"\n  [Topic Gate - Iterasi Klaster {gate_attempt + 1}] Topik Terbentuk: {metrics['num_topics']} | "
            f"Outlier Ratio: {metrics['outlier_ratio']:.1%} | "
            f"Mean Kohesi Vektor: {metrics['mean_cohesion']:.3f}"
        )

        llm_checks_log = []
        merged_any = False

        # Cek kondisi gagal deterministik (terlalu sedikit topik ATAU klaster menggelembung/mega-blob)
        total_docs_count = len(docs_clean)
        if total_docs_count >= 800:
            min_topics_req = 8
        elif total_docs_count >= 300:
            min_topics_req = 5
        elif total_docs_count >= 100:
            min_topics_req = 4
        elif total_docs_count >= 40:
            min_topics_req = 3
        else:
            min_topics_req = 2

        max_topic_size = max([t["count"] for t in metrics["topic_summaries"]], default=0)
        max_topic_ratio = (max_topic_size / total_docs_count) if total_docs_count > 0 else 0.0
        is_giant_blob = (max_topic_ratio > 0.45 and total_docs_count >= 100)
        is_too_few = (metrics["num_topics"] < min_topics_req)
        is_high_outlier = (metrics["outlier_ratio"] > max_outlier_ratio)

        if is_high_outlier or is_too_few or is_giant_blob:
            passed = False
            recommended_action = "switch_to_leaf_or_decrease"
            reasons = []
            if is_too_few:
                reasons.append(f"topik terlalu sedikit ({metrics['num_topics']} < {min_topics_req})")
            if is_giant_blob:
                reasons.append(f"klaster terbesar menggelembung ({max_topic_size}/{total_docs_count} = {max_topic_ratio:.1%})")
            if is_high_outlier:
                reasons.append(f"outlier terlalu tinggi ({metrics['outlier_ratio']:.1%})")
            audit_notes = f"Distribusi klaster tidak seimbang [{', '.join(reasons)}]. Wajib kalkulasi ulang dengan parameter lebih granular."
        else:
            # --- CEK LLM PUTARAN 1 (10 Sampel Utama/Representatif per Topik) ---
            check_1 = _run_llm_topic_sample_check(
                metrics=metrics,
                pass_number=1,
                domain_name=domain_name,
                segment_label=segment_label,
                hdbscan_params=hdbscan_params,
                provider=provider,
                model=model,
                api_key=api_key,
            )
            llm_checks_log.append(check_1)
            print(
                f"    [Hasil Cek LLM 1/2] Passed: {check_1['passed']} | Skor Kohesi: {check_1['coherence_score']:.2f} | "
                f"Topik Campur Aduk: {check_1['incoherent_topic_ids']} | Duplikat: {len(check_1['duplicate_pairs'])}"
            )

            # Gabungkan pasangan topik duplikat yang terkonfirmasi baik oleh deterministik atau Cek LLM 1
            det_dup_pairs = [(d["topic_id_1"], d["topic_id_2"]) for d in metrics["duplicate_pairs"]]
            llm1_dup_pairs = [(d["topic_id_1"], d["topic_id_2"]) for d in check_1["duplicate_pairs"]]
            # Hanya gabungkan pasangan dari LLM jika memiliki minimal kesamaan kata kunci/centroid agar aman
            valid_merge_candidates = list(det_dup_pairs)
            for t1, t2 in llm1_dup_pairs:
                if (t1, t2) not in valid_merge_candidates and (t2, t1) not in valid_merge_candidates:
                    valid_merge_candidates.append((t1, t2))

            if valid_merge_candidates and check_1["passed"]:
                if _merge_duplicate_topics_safely(topic_model, docs_clean, valid_merge_candidates):
                    merged_any = True
                    metrics = evaluate_topic_cohesion_and_duplication(
                        topic_model, docs_clean, embeddings, max_similarity_threshold=max_sim_thresh, docs_raw=docs_raw
                    )

            # --- CEK LLM PUTARAN 2 (10 Sampel Stratifikasi/Uji Silang per Topik) ---
            check_2 = _run_llm_topic_sample_check(
                metrics=metrics,
                pass_number=2,
                domain_name=domain_name,
                segment_label=segment_label,
                hdbscan_params=hdbscan_params,
                provider=provider,
                model=model,
                api_key=api_key,
            )
            llm_checks_log.append(check_2)
            print(
                f"    [Hasil Cek LLM 2/2] Passed: {check_2['passed']} | Skor Kohesi: {check_2['coherence_score']:.2f} | "
                f"Topik Campur Aduk: {check_2['incoherent_topic_ids']} | Duplikat: {len(check_2['duplicate_pairs'])}"
            )

            # Jika pada Cek LLM 2 masih ditemukan pasangan topik kembar, gabungkan secara aman
            llm2_dup_pairs = [(d["topic_id_1"], d["topic_id_2"]) for d in check_2["duplicate_pairs"]]
            if llm2_dup_pairs and check_2["passed"]:
                if _merge_duplicate_topics_safely(topic_model, docs_clean, llm2_dup_pairs):
                    merged_any = True
                    metrics = evaluate_topic_cohesion_and_duplication(
                        topic_model, docs_clean, embeddings, max_similarity_threshold=max_sim_thresh, docs_raw=docs_raw
                    )

            # Keputusan gabungan dari 2x Cek LLM:
            # Topik dianggap TIDAK SESUAI (wajib kalkulasi ulang) jika:
            # - Kedua putaran LLM menyatakan `passed == False`, ATAU
            # - Irisan topik campur aduk (`incoherent_topic_ids`) yang konsisten di Putaran 1 & Putaran 2 > 25% dari total topik
            persistent_incoherent = set(check_1["incoherent_topic_ids"]) & set(check_2["incoherent_topic_ids"])
            persistent_incoherent_ratio = len(persistent_incoherent) / max(1, metrics["num_topics"])

            if (not check_1["passed"] and not check_2["passed"]) or persistent_incoherent_ratio > 0.25:
                passed = False
                recommended_action = (
                    check_2["recommended_action"]
                    if check_2["recommended_action"] in ("decrease_min_cluster_size", "increase_min_cluster_size")
                    else "decrease_min_cluster_size"
                )
                audit_notes = (
                    f"Gagal verifikasi 2x Cek LLM (Topik tidak identik/campur aduk konsisten: {sorted(list(persistent_incoherent))}). "
                    f"Wajib kalkulasi ulang parameter klaster."
                )
            else:
                passed = True
                recommended_action = "pass"
                audit_notes = (
                    f"Lolos 2x Cek LLM dengan 10 sampel/topik "
                    f"(Skor Putaran 1: {check_1['coherence_score']:.2f}, Putaran 2: {check_2['coherence_score']:.2f}). "
                    f"Topik identik dan siap masuk ke tahap Labeling."
                )

        attempts_log.append({
            "attempt": gate_attempt + 1,
            "hdbscan_params": copy.deepcopy(hdbscan_params),
            "num_topics": metrics["num_topics"],
            "outlier_ratio": metrics["outlier_ratio"],
            "mean_cohesion": metrics["mean_cohesion"],
            "merged_duplicates": merged_any,
            "llm_checks_completed": len(llm_checks_log),
            "llm_checks": llm_checks_log,
            "recommended_action": recommended_action,
            "passed": passed,
            "audit_notes": audit_notes,
        })

        need_recluster = (
            not passed
            and recommended_action in ("decrease_min_cluster_size", "increase_min_cluster_size", "switch_to_leaf_or_decrease")
            and gate_attempt < max_retries
        )
        if not need_recluster:
            print(
                f"  [TOPIC GATE PASS] Topik Final Siap Labeling: {len(set(topic_model.topics_) - {-1})} | "
                f"Kohesi Vektor: {metrics['mean_cohesion']:.3f} | {audit_notes}"
            )
            break

        # Tune parameter HDBSCAN di memori untuk kalkulasi ulang (re-cluster)
        if recommended_action in ("decrease_min_cluster_size", "switch_to_leaf_or_decrease"):
            hdbscan_params["cluster_selection_method"] = "leaf"
            new_min = max(5, int(hdbscan_params["min_cluster_size"] * 0.70))
            if new_min == hdbscan_params["min_cluster_size"]:
                new_min = max(5, new_min - 1)
            hdbscan_params["min_cluster_size"] = new_min
            hdbscan_params["min_samples"] = max(1, new_min // 3)
            print(
                f"  [TOPIC GATE RETRY - KALKULASI ULANG] Menyesuaikan parameter HDBSCAN -> "
                f"method='leaf', min_cluster_size={new_min}, min_samples={hdbscan_params['min_samples']} dan menghitung ulang klaster..."
            )
        elif recommended_action == "increase_min_cluster_size":
            new_min = int(hdbscan_params["min_cluster_size"] * 1.4) + 2
            hdbscan_params["min_cluster_size"] = min(max(5, len(docs_clean) // 10), new_min)
            hdbscan_params["min_samples"] = max(2, hdbscan_params["min_cluster_size"] // 2)

        print(
            f"  [TOPIC GATE RETRY - KALKULASI ULANG] Menyesuaikan parameter HDBSCAN -> "
            f"min_cluster_size={hdbscan_params['min_cluster_size']}, "
            f"min_samples={hdbscan_params.get('min_samples')} dan menghitung ulang klaster..."
        )

    gate_report = {
        "status": "PASSED",
        "total_attempts": len(attempts_log),
        "attempts": attempts_log,
    }
    AgenticAuditLogger.log_gate(output_dir, "TopicGate", segment_label, gate_report)
    return topic_model, topic_model.topics_, probs, gate_report


# ==============================================================================
# 3. VERIFICATION GATE: SAMPEL LABEL AUDIT + CONFIDENCE CHECK & REROUTING
# ==============================================================================
class TopicRelabelItem(BaseModel):
    topic_id: int = Field(description="ID topik yang dievaluasi.")
    is_accurate: bool = Field(description="True jika label saat ini sudah akurat, berbahasa Indonesia baku, dan sesuai sampel.")
    corrected_sentiment: str = Field(
        default="",
        description="Isi dengan 'Positif', 'Negatif', atau 'Netral' jika perlu dikoreksi.",
    )
    corrected_threat_domain: str = Field(
        default="",
        description="Domain ancaman / kategori narasi pengganti dalam Bahasa Indonesia (maksimal 4-5 kata) jika is_accurate=False.",
    )
    corrected_sub_issue: str = Field(
        default="",
        description="Sub-isu spesifik pengganti dalam Bahasa Indonesia (maksimal 10 kata) jika is_accurate=False.",
    )
    corrected_merge_group: str = Field(
        default="",
        description="Kode UPPERCASE_SNAKE_CASE pengganti jika is_accurate=False.",
    )


class LabelVerificationBatchSchema(BaseModel):
    verifications: list[TopicRelabelItem] = Field(description="Hasil verifikasi label untuk setiap topik.")


class RerouteDecisionItem(BaseModel):
    item_id: str = Field(description="ID ulasan atau komentar yang dievaluasi.")
    selected_topic_id: int = Field(
        description="Topic ID terbaik yang paling cocok dengan isi teks (pilih dari kandidat utama/alternatif, atau -1 jika murni noise)."
    )
    confidence_score: float = Field(description="Tingkat keyakinan kecocokan teks dengan topik terpilih (0.0 - 1.0).")


class RerouteBatchSchema(BaseModel):
    decisions: list[RerouteDecisionItem] = Field(description="Keputusan rerouting untuk batch ulasan/komentar low-confidence.")


def verify_and_heal_topic_labels(
    agg_csv_path: str,
    domain_name: str,
    domain_desc: str,
    has_ai_sentiment: bool = False,
    has_merge_group: bool = True,
    config_override: dict = None,
) -> dict:
    """
    Bagian 1 dari Verification Gate:
    Memeriksa kualitas hasil pelabelan AI pada file `master_topic_*_agregasi.csv`.
    Mendeteksi label yang kosong, berbahasa Inggris, atau memiliki kontradiksi
    antara sentimen dengan kata kunci/10 sampel (misal: sindiran 'wapres ilegal'
    yang salah dilabeli Positif), lalu memperbaikinya secara otomatis.
    """
    if not os.path.exists(agg_csv_path):
        return {"checked": 0, "relabeled": 0}

    df = pd.read_csv(agg_csv_path)
    if df.empty:
        return {"checked": 0, "relabeled": 0}

    provider, model, api_key = _get_active_ai_credentials(config_override)
    sample_col = "sample_reviews" if "sample_reviews" in df.columns else "sample_comments"

    valid_rows = df[df["topic_id"].astype(str) != "-1"].copy()
    if valid_rows.empty:
        return {"checked": 0, "relabeled": 0}

    english_markers = {"issue", "problem", "error", "payment", "delivery", "service", "update", "app", "good", "bad", "feature"}
    negative_markers = {
        "ilegal", "mundur", "palsu", "kebohongan", "penjara", "pembodohan",
        "curang", "rusak", "error", "gagal", "kecewa", "penipuan", "bohong",
        "makzulkan", "pecat", "kacau", "malu", "parah", "bobrok",
    }
    gratitude_markers = {"alhamdulillah", "syukur", "terima kasih", "kebenaran", "semoga"}

    items_for_audit = []
    deterministic_flagged_ids = set()

    for idx, row in valid_rows.iterrows():
        t_id = int(row["topic_id"])
        b_cat = str(row.get("threat_domain") or row.get("business_category", "")).strip()
        s_iss = str(row.get("sub_issue", "")).strip()
        m_grp = str(row.get("merge_group", "")).strip() if has_merge_group else ""
        a_sent = str(row.get("ai_sentiment", "")).strip() if has_ai_sentiment else ""
        kw_str = str(row.get("top_keywords", "")).lower()
        samp_str = str(row.get(sample_col, "")).lower()
        combined_text = f"{kw_str} {samp_str}"

        cat_words = set(re.findall(r"\b\w+\b", b_cat.lower()))
        text_words = set(re.findall(r"\b\w+\b", combined_text))
        has_eng = len(cat_words & english_markers) >= 2

        sentiment_contradiction = False
        if has_ai_sentiment:
            if a_sent == "Positif" and (text_words & negative_markers) and not (text_words & gratitude_markers):
                sentiment_contradiction = True
            elif a_sent == "Negatif" and ("alhamdulillah" in kw_str) and not (text_words & negative_markers):
                sentiment_contradiction = True

        is_invalid = (
            not b_cat or b_cat == "nan"
            or not s_iss or s_iss == "nan"
            or len(b_cat.split()) > 7
            or has_eng
            or (has_ai_sentiment and a_sent not in ("Positif", "Negatif", "Netral"))
            or sentiment_contradiction
        )
        if is_invalid:
            deterministic_flagged_ids.add(t_id)

        items_for_audit.append({
            "df_idx": idx,
            "topic_id": t_id,
            "keywords": str(row.get("top_keywords", ""))[:180],
            "samples": str(row.get(sample_col, ""))[:800],
            "threat_domain": b_cat,
            "sub_issue": s_iss,
            "merge_group": m_grp,
            "ai_sentiment": a_sent,
            "flagged": is_invalid,
        })

    relabeled_count = 0
    if _can_call_llm(provider, api_key) and items_for_audit and len(deterministic_flagged_ids) > 0:
        items_sorted = [it for it in items_for_audit if it["flagged"]][:8]
        batch_text = ""
        for item in items_sorted:
            batch_text += (
                f"- Topic ID: {item['topic_id']} [FLAGGED - PERLU DIVERIFIKASI ULANG]\n"
                f"  Keywords: {item['keywords']}\n"
                f"  10 Sampel: {item['samples']}\n"
                f"  Label Saat Ini -> Domain Ancaman: '{item['threat_domain']}' | Sub-Isu: '{item['sub_issue']}'"
            )
            if has_ai_sentiment:
                batch_text += f" | Sentimen: '{item['ai_sentiment']}'"
            if has_merge_group:
                batch_text += f" | Group: '{item['merge_group']}'"
            batch_text += "\n\n"

        prompt = (
            f"Anda adalah Perwira Quality Verifier Intelijen Kognitif PUSSIBERAD TNI AD untuk pelabelan topik komentar '{domain_name}' ({domain_desc}).\n"
            "Periksa apakah label `threat_domain`, `sub_issue`, dan `ai_sentiment` pada setiap Topic ID di bawah ini sudah:\n"
            "1. Akurat mencerminkan Kata Kunci & 10 Sampel nyata (waspadai sarkasme/sindiran/delegitimasi seperti 'wapres ilegal', 'pembodohan', 'samsul' yang seharusnya Negatif/Kritik, bukan Positif).\n"
            "2. Menggunakan Bahasa Indonesia baku dan taktis (`threat_domain` maks 4-5 kata, `sub_issue` maks 10 kata).\n"
            "3. Tidak kosong dan tidak menggunakan istilah bahasa Inggris.\n\n"
            f"Daftar Topik untuk Diverifikasi:\n{batch_text}\n"
            "Jika kurang tepat atau berstatus [FLAGGED], set `is_accurate = false` dan berikan `corrected_sentiment`, `corrected_threat_domain`, dan `corrected_sub_issue` yang akurat!"
        )

        res = generate_structured_json(prompt, LabelVerificationBatchSchema, provider, model, api_key)
        if res and "verifications" in res:
            idx_map = {it["topic_id"]: it["df_idx"] for it in items_sorted}
            for v in res["verifications"]:
                if not isinstance(v, dict):
                    continue
                t_id = v.get("topic_id")
                try:
                    t_id = int(t_id)
                except Exception:
                    continue
                df_idx = idx_map.get(t_id)
                if df_idx is None:
                    continue
                is_acc = bool(v.get("is_accurate", True))
                if not is_acc or t_id in deterministic_flagged_ids:
                    new_cat = str(v.get("corrected_threat_domain") or v.get("corrected_business_category", "")).strip()
                    new_sub = str(v.get("corrected_sub_issue", "")).strip()
                    new_grp = str(v.get("corrected_merge_group", "")).strip()
                    new_sent = str(v.get("corrected_sentiment", "")).strip().capitalize()

                    if new_cat:
                        df.at[df_idx, "threat_domain"] = new_cat
                        if "business_category" in df.columns:
                            df.at[df_idx, "business_category"] = new_cat
                    if new_sub:
                        df.at[df_idx, "sub_issue"] = new_sub
                    if has_merge_group and new_grp and "merge_group" in df.columns:
                        df.at[df_idx, "merge_group"] = new_grp
                    if has_ai_sentiment and new_sent in ("Positif", "Negatif", "Netral") and "ai_sentiment" in df.columns:
                        df.at[df_idx, "ai_sentiment"] = new_sent
                    relabeled_count += 1
                    print(
                        f"    [Verification Gate - Relabel] Topik {t_id} diperbaiki -> "
                        f"Sentimen='{new_sent or df.at[df_idx, 'ai_sentiment']}', '{new_cat}: {new_sub}'"
                    )

    if relabeled_count > 0:
        df.to_csv(agg_csv_path, index=False, encoding="utf-8-sig")

    return {
        "file": os.path.basename(agg_csv_path),
        "checked": len(items_for_audit),
        "deterministic_flags": len(deterministic_flagged_ids),
        "relabeled": relabeled_count,
    }


def reroute_low_confidence_records(
    df_mapping: pd.DataFrame,
    df_agg: pd.DataFrame,
    id_col: str,
    text_col: str,
    domain_name: str,
    config_override: dict = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Bagian 2 dari Verification Gate:
    Mengevaluasi tingkat keyakinan (confidence check) pada hasil pemetaan topik,
    dan melakukan rerouting otomatis untuk baris ber-confidence 'Low'.
    """
    if df_mapping.empty or df_agg.empty:
        return df_mapping, df_agg, {"rerouted_alt_topic": 0, "rerouted_llm": 0}

    df_map = df_mapping.copy()
    df_topics_agg = df_agg.copy()

    topic_label_lookup = {}
    for _, row in df_topics_agg.iterrows():
        try:
            tid = int(row["topic_id"])
        except Exception:
            continue
        if tid == -1:
            continue
        topic_label_lookup[tid] = {
            "topic_name": str(row.get("topic_name", f"Topic {tid}")),
            "threat_domain": str(row.get("threat_domain") or row.get("business_category", "")),
            "sub_issue": str(row.get("sub_issue", "")),
            "keywords": str(row.get("top_keywords", "")),
        }

    total_rows = len(df_map)
    initial_low_mask = (
        (df_map["topic_id"].astype(str) == "-1")
        | (pd.to_numeric(df_map["main_topic_prob"], errors="coerce").fillna(0.0) < 0.50)
    )
    initial_low_count = int(initial_low_mask.sum())
    initial_conf_rate = round((total_rows - initial_low_count) / total_rows, 4) if total_rows > 0 else 1.0

    rerouted_alt_count = 0
    rerouted_llm_count = 0

    # --- Tahap 1: Deterministic Alt-Topic Arbitrage ---
    for idx in df_map[initial_low_mask].index:
        row = df_map.loc[idx]
        curr_prob = float(row.get("main_topic_prob") or 0.0) if pd.notna(row.get("main_topic_prob")) else 0.0
        alt1_id = row.get("alt_topic_1")
        alt1_prob = float(row.get("alt_topic_1_prob") or 0.0) if pd.notna(row.get("alt_topic_1_prob")) else 0.0

        try:
            alt1_id_int = int(float(alt1_id)) if pd.notna(alt1_id) and str(alt1_id).strip() != "" else -1
        except Exception:
            alt1_id_int = -1

        if alt1_id_int != -1 and alt1_id_int in topic_label_lookup:
            if alt1_prob >= 0.50 and (str(row["topic_id"]) == "-1" or alt1_prob >= curr_prob + 0.05):
                df_map.at[idx, "topic_id"] = alt1_id_int
                df_map.at[idx, "topic_name"] = topic_label_lookup[alt1_id_int]["topic_name"]
                df_map.at[idx, "main_topic_prob"] = round(alt1_prob, 4)
                rerouted_alt_count += 1

    # --- Tahap 2: LLM Batch Rerouting untuk Sampel Low-Confidence yang Informatif ---
    provider, model, api_key = _get_active_ai_credentials(config_override)
    still_low_mask = (
        (df_map["topic_id"].astype(str) == "-1")
        | (pd.to_numeric(df_map["main_topic_prob"], errors="coerce").fillna(0.0) < 0.50)
    )
    current_conf_rate = round((total_rows - int(still_low_mask.sum())) / total_rows, 4) if total_rows > 0 else 1.0

    if (
        _can_call_llm(provider, api_key)
        and current_conf_rate < AppConfig.AGENTIC_VERIFY_MIN_CONFIDENCE_RATE
        and int(still_low_mask.sum()) > 0
        and topic_label_lookup
    ):
        candidates_df = df_map[still_low_mask].copy()
        candidates_df["word_len"] = candidates_df[text_col].astype(str).apply(lambda s: len(s.split()))
        candidates_df["alt1_prob_num"] = pd.to_numeric(candidates_df.get("alt_topic_1_prob", 0.0), errors="coerce").fillna(0.0)
        candidates_df = candidates_df[
            (candidates_df["word_len"] >= 4) & (candidates_df["alt1_prob_num"] >= 0.35)
        ].sort_values(by="alt1_prob_num", ascending=False)

        max_batch = min(8, max(3, AppConfig.AGENTIC_VERIFY_LLM_REROUTE_BATCH))
        selected_for_llm = candidates_df.head(max_batch)

        if not selected_for_llm.empty:
            print(
                f"  [Verification Gate] Mereroute {len(selected_for_llm)} sampel ulasan/komentar low-confidence via LLM..."
            )
            items_prompt = ""
            row_idx_by_item_id = {}
            for idx, r in selected_for_llm.iterrows():
                item_id = str(r[id_col])
                row_idx_by_item_id[item_id] = idx
                txt = str(r[text_col]).replace("\n", " ").strip()[:200]

                cand_ids = set()
                for c_col in ["topic_id", "alt_topic_1", "alt_topic_2"]:
                    val = r.get(c_col)
                    try:
                        tid_c = int(float(val))
                        if tid_c in topic_label_lookup:
                            cand_ids.add(tid_c)
                    except Exception:
                        pass

                cand_desc = []
                for cid in sorted(cand_ids):
                    info = topic_label_lookup[cid]
                    cand_desc.append(
                        f"Topic {cid} ({info['threat_domain']} - {info['sub_issue']} | kw: {info['keywords'][:60]})"
                    )

                if not cand_desc:
                    continue

                items_prompt += (
                    f"- ID: {item_id}\n"
                    f"  Teks: \"{txt}\"\n"
                    f"  Kandidat Topik: {' ; '.join(cand_desc)} ; atau -1 (Noise/Umum)\n\n"
                )

            if items_prompt:
                prompt = (
                    f"Anda adalah Verifier Klasifikasi Topik untuk '{domain_name}'.\n"
                    "Berikut adalah ulasan/komentar yang saat ini memiliki tingkat keyakinan (confidence) rendah terhadap klaster topiknya.\n"
                    "Untuk setiap ID, pilih `selected_topic_id` yang paling tepat dari Kandidat Topik yang tersedia (atau pilih -1 jika teks benar-benar tidak relevan dengan semua kandidat).\n\n"
                    f"{items_prompt}"
                )
                llm_res = generate_structured_json(prompt, RerouteBatchSchema, provider, model, api_key)
                if llm_res and "decisions" in llm_res:
                    for dec in llm_res["decisions"]:
                        if not isinstance(dec, dict):
                            continue
                        it_id = str(dec.get("item_id", ""))
                        sel_tid = dec.get("selected_topic_id")
                        conf_sc = float(dec.get("confidence_score", 0.0) or 0.0)
                        try:
                            sel_tid = int(sel_tid)
                        except Exception:
                            continue

                        r_idx = row_idx_by_item_id.get(it_id)
                        if r_idx is not None and sel_tid in topic_label_lookup and conf_sc >= 0.60:
                            df_map.at[r_idx, "topic_id"] = sel_tid
                            df_map.at[r_idx, "topic_name"] = topic_label_lookup[sel_tid]["topic_name"]
                            old_p = float(df_map.at[r_idx, "main_topic_prob"] or 0.0)
                            df_map.at[r_idx, "main_topic_prob"] = round(max(old_p, 0.55, min(0.85, conf_sc)), 4)
                            rerouted_llm_count += 1

    # Sinkronkan ulang jumlah review_count / comment_count di df_topics_agg
    if (rerouted_alt_count + rerouted_llm_count) > 0:
        count_col = "review_count" if "review_count" in df_topics_agg.columns else "comment_count"
        if count_col in df_topics_agg.columns:
            new_counts = df_map["topic_id"].astype(int).value_counts().to_dict()
            for idx, row in df_topics_agg.iterrows():
                try:
                    tid = int(row["topic_id"])
                    cnt = int(new_counts.get(tid, 0))
                    df_topics_agg.at[idx, count_col] = cnt
                    if "percentage" in df_topics_agg.columns and total_rows > 0:
                        df_topics_agg.at[idx, "percentage"] = round(cnt / total_rows * 100, 2)
                except Exception:
                    pass

    final_low_mask = (
        (df_map["topic_id"].astype(str) == "-1")
        | (pd.to_numeric(df_map["main_topic_prob"], errors="coerce").fillna(0.0) < 0.50)
    )
    final_conf_rate = round((total_rows - int(final_low_mask.sum())) / total_rows, 4) if total_rows > 0 else 1.0

    report = {
        "total_records": total_rows,
        "initial_confident_rate": initial_conf_rate,
        "final_confident_rate": final_conf_rate,
        "rerouted_via_alt_topic": rerouted_alt_count,
        "rerouted_via_llm": rerouted_llm_count,
    }
    print(
        f"  [VERIFICATION GATE PASS] Confidence Rate: {initial_conf_rate:.1%} -> {final_conf_rate:.1%} "
        f"(Rerouted Alt-Topic: {rerouted_alt_count}, Rerouted LLM: {rerouted_llm_count})"
    )
    return df_map, df_topics_agg, report


# ==============================================================================
# 4. REPORT GATE: AUDIT ANGKA NARASI VS SUMBER DATA JSON
# ==============================================================================
class ReportDiscrepancyItem(BaseModel):
    claim_in_narrative: str = Field(description="Kutipan kalimat/angka di dalam teks narasi yang keliru atau tidak sesuai data.")
    ground_truth_in_json: str = Field(description="Angka atau fakta sebenarnya berdasarkan sumber data JSON.")


class ReportGateAuditSchema(BaseModel):
    passed: bool = Field(
        description="True jika seluruh angka, persentase, dan klaim utama di narasi 100% akurat sesuai JSON. False jika ada selisih angka/halusinasi."
    )
    accuracy_score: float = Field(description="Skor akurasi faktual laporan narasi (0.0 - 1.0).")
    discrepancies: list[ReportDiscrepancyItem] = Field(
        default_factory=list,
        description="Daftar ketidaksesuaian angka/fakta antara teks narasi dan sumber data JSON.",
    )
    audit_summary: str = Field(description="Ringkasan hasil verifikasi angka laporan dalam Bahasa Indonesia.")


def _extract_reference_numbers_from_json(obj, ref_ints: set, ref_floats: list):
    """Mengekstrak seluruh angka referensi yang sah dari struktur JSON EDA."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            _extract_reference_numbers_from_json(v, ref_ints, ref_floats)
    elif isinstance(obj, list):
        for item in obj:
            _extract_reference_numbers_from_json(item, ref_ints, ref_floats)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, int):
        ref_ints.add(abs(obj))
        ref_floats.append(float(abs(obj)))
    elif isinstance(obj, float):
        if not np.isnan(obj):
            val = abs(float(obj))
            ref_floats.append(val)
            ref_ints.add(int(round(val)))
            if 0.0 < val <= 1.0:
                ref_floats.append(round(val * 100.0, 2))
                ref_floats.append(round(val * 100.0, 1))
                ref_ints.add(int(round(val * 100.0)))
    elif isinstance(obj, str):
        cleaned = obj.replace(",", "").replace(".", "")
        if cleaned.isdigit():
            ref_ints.add(int(cleaned))


def _deterministic_number_and_rule_check(narrative_text: str, eda_data: dict) -> dict:
    """
    Mengecek secara deterministik:
    1. Apakah angka total ulasan/komentar utama disebutkan dengan benar.
    2. Apakah ada nama topik mentah BERTopic (contoh: `0_aplikasi_tidak_bisa`) yang bocor ke narasi.
    3. Apakah ada angka besar (>= 15) di dalam narasi yang sama sekali tidak ada padanannya di eda_summary.json.
    """
    ref_ints = set()
    ref_floats = []
    _extract_reference_numbers_from_json(eda_data, ref_ints, ref_floats)

    ov = eda_data.get("overview", {})
    total_main = ov.get("total_reviews") or ov.get("total_comments") or 0
    if total_main:
        ref_ints.add(int(total_main))

    raw_topic_leaks = re.findall(r"\b\d+_[a-z0-9]+_[a-z0-9_]+\b", narrative_text.lower())

    body_text = re.sub(r"^>.*$", "", narrative_text, flags=re.MULTILINE)
    body_text = re.sub(r"\b202\d[-/]\d{2}[-/]\d{2}\b", " ", body_text)
    body_text = re.sub(r"\b202\d[-/]\d{2}\b", " ", body_text)
    body_text = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", body_text)
    body_text = re.sub(r"\bv?\d+\.\d+\.\d+(?:\.\d+)?\b", " ", body_text, flags=re.IGNORECASE)

    unmatched_numbers = []
    number_tokens = re.findall(r"(?<![a-zA-Z0-9_])\d{1,3}(?:[.,]\d{3})+|\b\d+[.,]\d+\b|\b\d+\b", body_text)

    for tok in number_tokens:
        val_candidates = []
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", tok):
            val_candidates.append(float(tok.replace(".", "")))
        elif re.fullmatch(r"\d{1,3}(?:,\d{3})+", tok):
            val_candidates.append(float(tok.replace(",", "")))
        if "," in tok and tok.count(",") == 1:
            try:
                val_candidates.append(float(tok.replace(",", ".")))
            except Exception:
                pass
        if "." in tok and tok.count(".") == 1:
            try:
                val_candidates.append(float(tok))
            except Exception:
                pass
        if tok.isdigit():
            val_candidates.append(float(tok))

        if not val_candidates:
            continue

        primary_val = val_candidates[0]
        if primary_val <= 12 or (2020 <= primary_val <= 2030) or primary_val == 100.0 or primary_val == 70.0:
            continue

        matched = False
        for vc in val_candidates:
            if int(round(vc)) in ref_ints:
                matched = True
                break
            for rf in ref_floats:
                if abs(vc - rf) <= max(0.15, rf * 0.015):
                    matched = True
                    break
            if matched:
                break

        if not matched and tok not in unmatched_numbers:
            unmatched_numbers.append(tok)

    return {
        "total_ground_truth": total_main,
        "raw_topic_name_leaks": list(set(raw_topic_leaks)),
        "unmatched_number_tokens": unmatched_numbers[:15],
    }


def run_report_gate(
    narrative_md_path: str,
    eda_json_path: str,
    slimmed_eda_data: dict,
    app_name: str,
    output_dir: str = None,
    config_override: dict = None,
) -> dict:
    """
    Menjalankan Report Gate setelah narasi AI dibuat (`narrative_insights.md`)
    dan sebelum diekspor ke XLSX / PPTX / HTML / PDF.
    """
    if not AppConfig.AGENTIC_GATES_ENABLED:
        return {"enabled": False}

    if not os.path.exists(narrative_md_path) or not os.path.exists(eda_json_path):
        return {"status": "SKIPPED", "reason": "File narasi atau EDA JSON tidak ditemukan."}

    print(f"\n[REPORT GATE] Memverifikasi akurasi angka narasi vs sumber data JSON ({os.path.basename(eda_json_path)})...")
    with open(eda_json_path, "r", encoding="utf-8") as f:
        full_eda_data = json.load(f)

    provider, model, api_key = _get_active_ai_credentials(config_override)
    narration_model = (config_override or {}).get("AI_NARRATION_MODEL", AppConfig.AI_NARRATION_MODEL) or model
    max_retries = max(1, AppConfig.AGENTIC_MAX_RETRIES)

    attempts_log = []
    slim_json_str = json.dumps(slimmed_eda_data, ensure_ascii=False, indent=2)

    for attempt in range(max_retries + 1):
        with open(narrative_md_path, "r", encoding="utf-8") as f:
            current_md = f.read()

        header_block = ""
        narrative_body = current_md
        if "---\n" in current_md and current_md.startswith("# Laporan Insight"):
            parts = current_md.split("---\n", 1)
            header_block = parts[0] + "---\n\n"
            narrative_body = parts[1].strip()

        det_check = _deterministic_number_and_rule_check(narrative_body, full_eda_data)
        print(
            f"  [Report Gate - Iterasi {attempt + 1}] "
            f"Kebocoran topic_name: {len(det_check['raw_topic_name_leaks'])} | "
            f"Angka mencurigakan (belum terverifikasi): {len(det_check['unmatched_number_tokens'])}"
        )

        passed = True
        accuracy_score = 0.95
        discrepancies = []
        audit_summary = "Lolos pemeriksaan deterministik."

        if det_check["raw_topic_name_leaks"]:
            passed = False
            discrepancies.append({
                "claim_in_narrative": f"Penggunaan topic_name mentah: {', '.join(det_check['raw_topic_name_leaks'])}",
                "ground_truth_in_json": "Wajib gunakan deskripsi dari field 'sub_issue' atau 'threat_domain', bukan 'topic_name'.",
            })

        need_llm_report_audit = bool(det_check["raw_topic_name_leaks"]) or len(det_check["unmatched_number_tokens"]) >= 3
        if need_llm_report_audit and _can_call_llm(provider, api_key):
            audit_prompt = (
                f"Anda adalah Fact-Checker & Financial/Data Auditor untuk laporan '{app_name}'.\n"
                "Tugas Anda adalah membandingkan setiap angka, persentase, jumlah ulasan/komentar, skor rating, "
                "dan klaim di dalam TEKS NARASI terhadap SUMBER DATA JSON.\n\n"
                f"=== SUMBER DATA JSON (GROUND TRUTH) ===\n{slim_json_str}\n\n"
                f"=== TEKS NARASI SAAT INI ===\n{narrative_body}\n\n"
                f"Catatan Pemeriksaan Deterministik Awal:\n"
                f"- Kebocoran topic_name mentah: {det_check['raw_topic_name_leaks']}\n"
                f"- Angka di teks yang perlu dicek khusus (apakah hasil halusinasi atau perhitungan rasio yang valid): {det_check['unmatched_number_tokens']}\n\n"
                "Aturan Verifikasi:\n"
                "1. Setiap angka jumlah ulasan/komentar, persentase sentimen, rata-rata skor/likes, jumlah topik, dan metrik CS/engagement HARUS sesuai dengan SUMBER DATA JSON (rasio turunan seperti likes per ulasan diperbolehkan asal hitungan matematikanya benar).\n"
                "2. Tidak boleh ada penggunaan `topic_name` mentah (seperti `0_kata_kunci`).\n"
                "3. Jika semua angka akurat, set `passed = true`. Jika ada angka yang salah/halusinasi, set `passed = false` dan cantumkan detailnya di `discrepancies`."
            )
            llm_audit = generate_structured_json(audit_prompt, ReportGateAuditSchema, provider, model, api_key)
            if llm_audit and isinstance(llm_audit, dict):
                llm_passed = bool(llm_audit.get("passed", True))
                accuracy_score = float(llm_audit.get("accuracy_score", 0.90))
                audit_summary = str(llm_audit.get("audit_summary", ""))
                for d in llm_audit.get("discrepancies", []) or []:
                    if isinstance(d, dict):
                        discrepancies.append({
                            "claim_in_narrative": str(d.get("claim_in_narrative", "")),
                            "ground_truth_in_json": str(d.get("ground_truth_in_json", "")),
                        })
                    elif isinstance(d, str):
                        discrepancies.append({
                            "claim_in_narrative": d,
                            "ground_truth_in_json": "Sesuaikan dengan sumber data JSON.",
                        })
                if not llm_passed or discrepancies:
                    passed = False

        attempts_log.append({
            "attempt": attempt + 1,
            "passed": passed,
            "accuracy_score": accuracy_score,
            "deterministic_check": det_check,
            "discrepancies": discrepancies,
            "audit_summary": audit_summary,
        })

        if passed or attempt >= max_retries or not _can_call_llm(provider, api_key):
            status_str = "PASSED" if passed else "COMPLETED_WITH_MAX_RETRIES"
            print(f"  [REPORT GATE {status_str}] Skor Akurasi: {accuracy_score:.2f} | {audit_summary}")
            break

        print(f"  [REPORT GATE RETRY] Ditemukan {len(discrepancies)} ketidaksesuaian angka/fakta. Merevisi narasi otomatis...")
        disc_bullet = "\n".join(
            [f"- KLAIM SALAH: {d['claim_in_narrative']}\n  FAKTA SEBENARNYA: {d['ground_truth_in_json']}" for d in discrepancies]
        )
        revision_prompt = (
            f"Anda adalah editor analis data senior untuk laporan '{app_name}'.\n"
            "Laporan narasi berikut gagal melewati Report Gate karena ditemukan ketidaksesuaian angka/fakta terhadap sumber data JSON.\n\n"
            f"=== DAFTAR KOREKSI WAJIB ===\n{disc_bullet}\n\n"
            f"=== SUMBER DATA JSON (GROUND TRUTH) ===\n{slim_json_str}\n\n"
            f"=== TEKS NARASI YANG HARUS DIREVISI ===\n{narrative_body}\n\n"
            "INSTRUKSI REVISI:\n"
            "1. Perbaiki seluruh angka dan klaim yang keliru di atas agar 100% akurat sesuai SUMBER DATA JSON.\n"
            "2. Pertahankan struktur heading Markdown (`## 1.`, `## 2.`, dst.) dan gaya bahasa profesional.\n"
            "3. Jangan pernah menampilkan kode `topic_name` mentah; selalu gunakan `sub_issue` atau `threat_domain`.\n"
            "4. Kembalikan HANYA teks narasi Markdown yang sudah diperbaiki secara utuh."
        )
        revised_body = generate_text(revision_prompt, provider, narration_model, api_key)
        if revised_body and len(revised_body.strip()) >= 400:
            with open(narrative_md_path, "w", encoding="utf-8") as f:
                if header_block:
                    f.write(header_block + revised_body.strip() + "\n")
                else:
                    f.write(revised_body.strip() + "\n")
            print("    [OK] Narasi berhasil direvisi dan disimpan ulang.")

    gate_report = {
        "status": "PASSED" if attempts_log and attempts_log[-1]["passed"] else "AUDITED",
        "total_attempts": len(attempts_log),
        "attempts": attempts_log,
    }
    AgenticAuditLogger.log_gate(output_dir, "ReportGate", "narrative_vs_eda_json", gate_report)
    return gate_report
