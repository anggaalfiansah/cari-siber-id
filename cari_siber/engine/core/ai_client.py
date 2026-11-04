"""
==============================================================================
CORE AI CLIENT (UNIVERSAL)
==============================================================================
HTTP client universal untuk memanggil berbagai provider AI (Gemini, OpenRouter,
EdgeOne, Ollama). Fungsi-fungsi di sini tidak mengetahui skema data pipeline
apapun — hanya menerima prompt string dan mengembalikan teks atau dict JSON.

Dapat digunakan dari konteks apapun: pipeline Play Store, data TikTok,
YouTube, script analisis mandiri, dsb.
==============================================================================
"""

import os
from datetime import datetime
import json
import re
import sys
import time
try:
    import requests
except ImportError:
    requests = None
from cari_siber.engine.core.config import AppConfig
from cari_siber.engine.core.exceptions import PipelineError

GEMINI_FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def _log_api_traffic(
    provider: str,
    model: str,
    call_type: str,
    endpoint: str,
    status: str,
    duration_sec: float,
    request_payload: dict,
    response_payload = None,
    error: str = "",
):
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_lines = [
            "=" * 80,
            f"[{now_str}] [API TRAFFIC] PROVIDER: {provider} | MODEL: {model} | TYPE: {call_type}",
            f"ENDPOINT: {endpoint} | STATUS: {status} | LATENCY: {duration_sec:.2f}s",
            "-" * 32 + " [REQUEST BODY] " + "-" * 32,
            json.dumps(request_payload, indent=2, ensure_ascii=False, default=str),
        ]
        if response_payload is not None:
            log_lines.extend([
                "-" * 32 + " [RESPONSE BODY] " + "-" * 31,
                json.dumps(response_payload, indent=2, ensure_ascii=False, default=str)
                if isinstance(response_payload, (dict, list))
                else str(response_payload),
            ])
        if error:
            log_lines.extend([
                "-" * 32 + " [ERROR DETAILS] " + "-" * 31,
                str(error),
            ])
        log_lines.append("=" * 80 + "\n")
        log_text = "\n".join(log_lines)

        try:
            from cari_siber.paths import get_logs_dir
            global_log = os.path.join(get_logs_dir(), "api_traffic.log")
            # Rotasi log jika melebihi 5 MB agar kapasitas disk tidak membengkak
            if os.path.exists(global_log) and os.path.getsize(global_log) > 5 * 1024 * 1024:
                try:
                    bak_log = global_log + ".1"
                    if os.path.exists(bak_log):
                        os.remove(bak_log)
                    os.rename(global_log, bak_log)
                except Exception:
                    pass
            with open(global_log, "a", encoding="utf-8") as gf:
                gf.write(log_text)
        except Exception:
            pass

        try:
            if getattr(AppConfig, "OUTPUT_DIR", None) and os.path.exists(AppConfig.OUTPUT_DIR):
                run_logs_dir = os.path.join(AppConfig.OUTPUT_DIR, "logs")
                os.makedirs(run_logs_dir, exist_ok=True)
                with open(os.path.join(run_logs_dir, "api_traffic.log"), "a", encoding="utf-8") as rf:
                    rf.write(log_text)
        except Exception:
            pass
    except Exception:
        pass

TOKEN_USAGE_TRACKER = {
    "calls": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}


def reset_token_tracker():
    TOKEN_USAGE_TRACKER["calls"] = 0
    TOKEN_USAGE_TRACKER["prompt_tokens"] = 0
    TOKEN_USAGE_TRACKER["completion_tokens"] = 0
    TOKEN_USAGE_TRACKER["total_tokens"] = 0


def _record_usage(usage_obj, prompt_fallback: str = "", completion_fallback: str = "") -> tuple[int, int, int]:
    p_tok, c_tok, t_tok = 0, 0, 0
    if usage_obj is not None:
        p_tok = int(getattr(usage_obj, "prompt_tokens", 0) or getattr(usage_obj, "prompt_token_count", 0) or 0)
        c_tok = int(getattr(usage_obj, "completion_tokens", 0) or getattr(usage_obj, "candidates_token_count", 0) or 0)
        t_tok = int(getattr(usage_obj, "total_tokens", 0) or getattr(usage_obj, "total_token_count", 0) or (p_tok + c_tok))
    if t_tok == 0:
        p_tok = max(1, len(prompt_fallback or "") // 4)
        c_tok = max(1, len(completion_fallback or "") // 4)
        t_tok = p_tok + c_tok
    TOKEN_USAGE_TRACKER["calls"] += 1
    TOKEN_USAGE_TRACKER["prompt_tokens"] += p_tok
    TOKEN_USAGE_TRACKER["completion_tokens"] += c_tok
    TOKEN_USAGE_TRACKER["total_tokens"] += t_tok
    return p_tok, c_tok, t_tok


def _get_gemini_candidate_models(primary_model: str) -> list[str]:
    candidates = [primary_model] if primary_model and not primary_model.startswith("openrouter") else []
    for fb in GEMINI_FALLBACK_MODELS:
        if fb not in candidates:
            candidates.append(fb)
    return candidates


def _repair_inner_quotes_state_machine(text: str) -> str:
    """
    Memperbaiki tanda kutip ganda yang tidak di-escape di dalam nilai string JSON.
    Contoh: {"quote": "Dia bilang "bagus" kemarin", "status": "ok"}
    Menjadi: {"quote": "Dia bilang \"bagus\" kemarin", "status": "ok"}
    """
    result = []
    i = 0
    n = len(text)
    in_string = False
    escape = False

    while i < n:
        c = text[i]

        if escape:
            result.append(c)
            escape = False
            i += 1
            continue

        if c == '\\':
            result.append(c)
            escape = True
            i += 1
            continue

        if c == '"':
            if not in_string:
                in_string = True
                result.append(c)
            else:
                j = i + 1
                while j < n and text[j] in ' \t\r\n':
                    j += 1
                next_c = text[j] if j < n else ''
                if next_c in (',', ':', '}', ']') or j == n:
                    in_string = False
                    result.append(c)
                else:
                    result.append('\\"')
            i += 1
            continue

        result.append(c)
        i += 1

    return "".join(result)


def _clean_json_text(raw_text: str) -> str:
    """Membersihkan pembungkus markdown code block (```json ... ```) dari respons LLM."""
    if not raw_text:
        return ""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]
    return cleaned.strip()


def _robust_json_repair_and_load(raw_text: str) -> dict:
    """
    Self-healing JSON parser multi-tahap untuk model LLM (terutama model free OpenRouter).
    Memperbaiki unescaped newlines/tabs, trailing commas, smart quotes, inner unescaped quotes,
    dan bracket yang belum tertutup akibat batas max_tokens tanpa memicu retry loop.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Respons JSON kosong dari model AI.")

    raw = raw_text.strip()

    # 1. Buang tag <think>...</think> dari model reasoning (DeepSeek R1/Nemotron)
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()

    # 2. Buang code block markdown ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # 3. Ekstrak substring terluar ({...} atau [...])
    fb = cleaned.find("{")
    fbk = cleaned.find("[")
    s_idx = -1
    if fb != -1 and fbk != -1:
        s_idx = min(fb, fbk)
    elif fb != -1:
        s_idx = fb
    elif fbk != -1:
        s_idx = fbk

    if s_idx != -1:
        cleaned = cleaned[s_idx:]

    lb = cleaned.rfind("}")
    lbk = cleaned.rfind("]")
    e_idx = max(lb, lbk)
    if e_idx != -1 and e_idx > 0:
        cleaned = cleaned[: e_idx + 1]

    # Level 1: Parsing langsung dengan strict=False (mengizinkan newline/tab literal di string)
    try:
        return json.loads(cleaned, strict=False)
    except Exception:
        pass

    # Level 2: Buang trailing commas (koma sebelum '}' atau ']')
    no_trailing = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(no_trailing, strict=False)
    except Exception:
        pass

    # Level 3: Normalisasi smart quotes
    normalized_quotes = (
        no_trailing.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )
    try:
        return json.loads(normalized_quotes, strict=False)
    except Exception:
        pass

    # Level 4: Perbaiki unescaped inner double quotes
    fixed_inner = _repair_inner_quotes_state_machine(normalized_quotes)
    try:
        return json.loads(fixed_inner, strict=False)
    except Exception:
        pass

    # Level 5: Auto-close kurung kurawal/siku jika JSON terpotong (max_tokens habis)
    open_brackets = []
    in_string = False
    escape = False
    for char in fixed_inner:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in '{[':
                open_brackets.append(char)
            elif char in '}]':
                if open_brackets:
                    last = open_brackets[-1]
                    if (last == '{' and char == '}') or (last == '[' and char == ']'):
                        open_brackets.pop()

    patched = fixed_inner.rstrip()
    if in_string:
        patched += '"'
    patched = re.sub(r",\s*$", "", patched)
    while open_brackets:
        b = open_brackets.pop()
        patched += "}" if b == "{" else "]"

    try:
        return json.loads(patched, strict=False)
    except Exception:
        pass

    # Level 6: Opsional library json_repair jika terpasang
    try:
        import json_repair
        return json_repair.repair_json(cleaned, return_objects=True)
    except Exception:
        pass

    # Jika semua langkah perbaikan gagal, panggil json.loads asli agar error tersampaikan
    return json.loads(cleaned)


# ==============================================================================
# 1. TEXT GENERATION CALLS
# ==============================================================================
def generate_text(prompt: str, provider: str, model: str, api_key: str = None, min_length: int = 1, max_retries: int = 3, timeout: float = 45.0) -> str:
    """
    Menghasilkan teks narasi bebas berdasarkan prompt menggunakan provider AI terpilih.
    Jika max_retries=1, hanya 1 kali percobaan (cocok untuk uji koneksi cepat).
    """
    provider = provider.lower().strip()

    if provider == "gemini":
        try:
            from google import genai
        except ImportError:
            raise PipelineError("SDK 'google-genai' belum terpasang.")

        if not api_key:
            api_key = AppConfig.GEMINI_API_KEY
        if not api_key:
            raise PipelineError("GEMINI_API_KEY tidak diset di konfigurasi / Pengaturan.")

        client = genai.Client(api_key=api_key)
        target_candidates = [model] if max_retries == 1 else _get_gemini_candidate_models(model)

        for cand_idx, cand_model in enumerate(target_candidates):
            curr_retries = max_retries if max_retries == 1 else (3 if cand_idx == 0 else 2)
            for attempt in range(curr_retries):
                try:
                    print(f"[INFO] Menghubungi Gemini (model: {cand_model})...")
                    response = client.models.generate_content(
                        model=cand_model,
                        contents=prompt,
                    )
                    _record_usage(getattr(response, "usage_metadata", None), prompt, response.text or "")
                    return response.text
                except Exception as e:
                    err_msg = str(e)
                    if max_retries == 1:
                        raise PipelineError(f"Gemini ({cand_model}) Error: {err_msg}")

                    is_overload = "503" in err_msg or "UNAVAILABLE" in err_msg or "404" in err_msg
                    is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower()

                    if is_overload and cand_idx < len(target_candidates) - 1 and attempt >= 1:
                        print(f"    [GEMINI 503/404] Model '{cand_model}' sedang sibuk/tidak tersedia. Beralih ke model fallback '{target_candidates[cand_idx + 1]}'...")
                        break

                    if attempt < curr_retries - 1:
                        wait_time = (12 if is_rate_limit else 4) + (attempt * 3)
                        print(f"    [GEMINI ERROR] Terjadi kesalahan ({err_msg[:140]}). Menunggu {wait_time} detik (Percobaan {attempt+1}/{curr_retries})...")
                        time.sleep(wait_time)
                    else:
                        print(f"[GEMINI ERROR] Gagal memanggil model '{cand_model}': {err_msg[:180]}")
        return ""

    elif provider in ("openrouter", "edgeone", "custom"):
        try:
            from openai import OpenAI
        except ImportError:
            raise PipelineError("SDK 'openai' belum terpasang.")

        is_custom = provider == "custom"
        is_edgeone = provider == "edgeone"
        provider_label = "Custom" if is_custom else ("EdgeOne" if is_edgeone else "OpenRouter")
        base_url = (
            AppConfig.CUSTOM_BASE_URL
            if is_custom
            else ("https://ai-gateway.edgeone.link/v1" if is_edgeone else "https://openrouter.ai/api/v1")
        )

        if not api_key:
            api_key = (
                AppConfig.CUSTOM_API_KEY
                if is_custom
                else (AppConfig.EDGEONE_API_KEY if is_edgeone else AppConfig.OPENROUTER_API_KEY)
            )
        if not api_key:
            key_name = "CUSTOM_API_KEY" if is_custom else ("EDGEONE_API_KEY" if is_edgeone else "OPENROUTER_API_KEY")
            raise PipelineError(f"{key_name} tidak ditemukan di Pengaturan.")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,
        )
        num_retries = max_retries
        for attempt in range(num_retries):
            try:
                _t0 = time.time()
                print(f"[INFO] Menghubungi {provider_label} (model: {model}) [Percobaan {attempt+1}/{num_retries}]...", flush=True)
                kwargs = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 8192,
                }
                if not is_edgeone and not is_custom:
                    kwargs["extra_headers"] = {
                        "HTTP-Referer": "https://github.com/pengikut-raja-capybara/cari-siber-id",
                        "X-Title": "CaRI Siber ID",
                    }
                content = ""
                response_usage = None
                try:
                    # Coba mode streaming terlebih dahulu agar koneksi TCP tidak idle dan tidak terputus timeout proxy
                    kwargs_stream = kwargs.copy()
                    kwargs_stream["stream"] = True
                    stream_resp = client.chat.completions.create(**kwargs_stream)
                    collected = []
                    for chunk in stream_resp:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            collected.append(chunk.choices[0].delta.content)
                        if hasattr(chunk, "usage") and chunk.usage:
                            response_usage = chunk.usage
                    content = "".join(collected)
                    dur = time.time() - _t0
                    u_dict = {
                        "prompt_tokens": getattr(response_usage, "prompt_tokens", len(prompt) // 4) if response_usage else len(prompt) // 4,
                        "completion_tokens": getattr(response_usage, "completion_tokens", len(content) // 4) if response_usage else len(content) // 4,
                        "total_tokens": getattr(response_usage, "total_tokens", (len(prompt) + len(content)) // 4) if response_usage else (len(prompt) + len(content)) // 4,
                    }
                    _log_api_traffic(provider, model, "text_stream", f"{base_url}/chat/completions", "200 OK", dur, kwargs, {"content": content, "usage": u_dict})
                except Exception as stream_err:
                    # Fallback non-streaming jika provider tidak mendukung server-sent events (SSE)
                    try:
                        print(f"      [AI Client] Streaming beralih ke standar non-streaming ({str(stream_err)[:80]})...", flush=True)
                        response = client.chat.completions.create(**kwargs)
                        dur = time.time() - _t0
                        content = response.choices[0].message.content
                        response_usage = getattr(response, "usage", None)
                        u_dict = {"prompt_tokens": getattr(response_usage, "prompt_tokens", None), "completion_tokens": getattr(response_usage, "completion_tokens", None), "total_tokens": getattr(response_usage, "total_tokens", None)} if response_usage else {}
                        _log_api_traffic(provider, model, "text", f"{base_url}/chat/completions", "200 OK", dur, kwargs, {"content": content, "usage": u_dict})
                    except Exception as non_stream_err:
                        dur = time.time() - _t0
                        _log_api_traffic(provider, model, "text", f"{base_url}/chat/completions", "FAILED", dur, kwargs, error=str(non_stream_err))
                        raise non_stream_err
                if content and len(content.strip()) >= min_length:
                    p_t, c_t, tot_t = _record_usage(response_usage, prompt, content)
                    print(f"      [AI Client] Narasi diterima dalam {time.time() - _t0:.1f} dtk (Token: {p_t:,} in + {c_t:,} out = {tot_t:,} total | Akumulasi: {TOKEN_USAGE_TRACKER['total_tokens']:,}).", flush=True)
                    return content
                if max_retries == 1:
                    return content or ""
                if min_length > 1:
                    print(f"    [{provider_label.upper()} WARNING] Respons terlalu pendek ({len(content or '')} karakter, min {min_length}). Mencoba ulang (Percobaan {attempt+1}/{num_retries})...", flush=True)
                else:
                    return content or ""
                time.sleep(3)
            except Exception as e:
                err_msg = str(e)
                if max_retries == 1:
                    raise PipelineError(f"{provider_label} ({model}) Error: {err_msg}")
                print(f"    [{provider_label.upper()} ERROR] ({err_msg[:160]}) (Percobaan {attempt+1}/{num_retries})", flush=True)
                if attempt < num_retries - 1:
                    time.sleep(4 + attempt * 2)

        if max_retries == 1 or is_custom:
            return ""

        if is_edgeone and AppConfig.OPENROUTER_API_KEY:
            print("[INFO] EdgeOne gagal merespons. Beralih otomatis ke fallback OpenRouter...")
            return generate_text(prompt, "openrouter", "openrouter/free", AppConfig.OPENROUTER_API_KEY)
        if not is_edgeone and AppConfig.EDGEONE_API_KEY:
            print("[INFO] OpenRouter gagal merespons. Beralih otomatis ke fallback EdgeOne...")
            return generate_text(prompt, "edgeone", "@makers/deepseek-v4-flash", AppConfig.EDGEONE_API_KEY)
        if AppConfig.GEMINI_API_KEY :
            print(f"[INFO] {provider_label} gagal merespons. Beralih otomatis ke fallback Gemini...")
            return generate_text(prompt, "gemini", "gemini-2.5-flash", AppConfig.GEMINI_API_KEY)
        return ""

    elif provider == "ollama":
        print(f"[INFO] Menghubungi Ollama (model: {model})...")
        url = "http://localhost:11434/api/generate"
        response = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]

    else:
        raise PipelineError(f"Provider AI '{provider}' belum didukung untuk pembuatan teks.")


# ==============================================================================
# 2. STRUCTURED JSON GENERATION CALLS
# ==============================================================================
def generate_structured_json(prompt: str, response_schema, provider: str, model: str, api_key: str = None) -> dict:
    """
    Menghasilkan output JSON terstruktur sesuai skema Pydantic menggunakan provider AI terpilih.
    """
    provider = provider.lower().strip()

    if provider == "gemini":
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise PipelineError("SDK 'google-genai' belum terpasang.")

        if not api_key:
            api_key = AppConfig.GEMINI_API_KEY
        if not api_key:
            raise PipelineError("GEMINI_API_KEY tidak diset di konfigurasi / Pengaturan.")

        client = genai.Client(api_key=api_key)
        candidates = _get_gemini_candidate_models(model)

        for cand_idx, cand_model in enumerate(candidates):
            max_retries = 3 if cand_idx == 0 else 2
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=cand_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=response_schema,
                            temperature=0.2,
                        ),
                    )
                    _record_usage(getattr(response, "usage_metadata", None), prompt, response.text or "")
                    return _robust_json_repair_and_load(response.text)
                except Exception as e:
                    err_msg = str(e)
                    is_overload = "503" in err_msg or "UNAVAILABLE" in err_msg or "404" in err_msg
                    is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower()

                    if is_overload and cand_idx < len(candidates) - 1 and attempt >= 1:
                        print(f"    [GEMINI 503/404] Model '{cand_model}' sedang mengalami lonjakan trafik. Beralih otomatis ke '{candidates[cand_idx + 1]}'...")
                        break

                    if attempt < max_retries - 1:
                        if is_rate_limit:
                            wait_time = 15 + (attempt * 5)
                            print(f"    [GEMINI 429] Batas kuota terlampaui. Menunggu {wait_time} detik sebelum mencoba kembali (Percobaan {attempt+1}/{max_retries})...")
                        else:
                            wait_time = 4 + (attempt * 2)
                            print(f"    [GEMINI ERROR] Terjadi kesalahan ({err_msg[:140]}). Menunggu {wait_time} detik (Percobaan {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        print(f"[GEMINI ERROR] Gagal memanggil model '{cand_model}' setelah {max_retries} percobaan: {err_msg[:180]}")
        return None

    elif provider in ("openrouter", "edgeone", "custom"):
        try:
            from openai import OpenAI
        except ImportError:
            raise PipelineError("SDK 'openai' belum terpasang.")

        is_custom = provider == "custom"
        is_edgeone = provider == "edgeone"
        provider_label = "Custom" if is_custom else ("EdgeOne" if is_edgeone else "OpenRouter")
        base_url = (
            AppConfig.CUSTOM_BASE_URL
            if is_custom
            else ("https://ai-gateway.edgeone.link/v1" if is_edgeone else "https://openrouter.ai/api/v1")
        )

        if not api_key:
            api_key = (
                AppConfig.CUSTOM_API_KEY
                if is_custom
                else (AppConfig.EDGEONE_API_KEY if is_edgeone else AppConfig.OPENROUTER_API_KEY)
            )
        if not api_key:
            key_name = "CUSTOM_API_KEY" if is_custom else ("EDGEONE_API_KEY" if is_edgeone else "OPENROUTER_API_KEY")
            raise PipelineError(f"{key_name} tidak ditemukan di Pengaturan.")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=90.0,
            max_retries=0,
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Anda adalah asisten JSON terstruktur. Jawab langsung dan ringkas tanpa penalaran bertele-tele. DILARANG menggunakan trailing comma (koma sebelum '}' atau ']'). Pastikan semua tanda kutip dua di dalam teks sudah di-escape (\\\"). Kembalikan HANYA objek JSON valid sesuai skema berikut: "
                                + (json.dumps(response_schema.model_json_schema(), ensure_ascii=False) if hasattr(response_schema, "model_json_schema") else "JSON object")
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 4096,
                    "temperature": 0.1,
                }
                if not is_edgeone and not is_custom:
                    kwargs["extra_headers"] = {
                        "HTTP-Referer": "https://github.com/pengikut-raja-capybara/cari-sentimen-id",
                        "X-Title": "CaRI Sentimen ID",
                    }
                if attempt == 0 and "free" not in model.lower():
                    kwargs["response_format"] = {"type": "json_object"}

                _t0 = time.time()
                print(f"      [AI Client] Mengirim request JSON ke {provider_label} ({model}) [Percobaan {attempt+1}/{max_retries}]...", flush=True)
                try:
                    response = client.chat.completions.create(**kwargs)
                except Exception as req_err:
                    if "response_format" in kwargs and ("response_format" in str(req_err).lower() or "400" in str(req_err)):
                        kwargs.pop("response_format", None)
                        response = client.chat.completions.create(**kwargs)
                    else:
                        dur = time.time() - _t0
                        _log_api_traffic(provider, model, "structured_json", f"{base_url}/chat/completions", "FAILED", dur, kwargs, error=str(req_err))
                        raise req_err

                dur = time.time() - _t0
                raw_text = response.choices[0].message.content
                u = getattr(response, "usage", None)
                u_dict = {"prompt_tokens": getattr(u, "prompt_tokens", None), "completion_tokens": getattr(u, "completion_tokens", None), "total_tokens": getattr(u, "total_tokens", None)} if u else {}
                _log_api_traffic(provider, model, "structured_json", f"{base_url}/chat/completions", "200 OK", dur, kwargs, {"raw_text": raw_text, "usage": u_dict})
                p_t, c_t, tot_t = _record_usage(getattr(response, "usage", None), prompt, raw_text or "")
                print(f"      [AI Client] Respons diterima dalam {time.time() - _t0:.1f} dtk (Token: {p_t:,} in + {c_t:,} out = {tot_t:,} total | Akumulasi: {TOKEN_USAGE_TRACKER['total_tokens']:,}).", flush=True)
                return _robust_json_repair_and_load(raw_text)
            except Exception as e:
                err_msg = str(e)
                is_rate_limit = "429" in err_msg or "quota" in err_msg.lower()

                if attempt < max_retries - 1:
                    wait_time = (12 if is_rate_limit else 4) + (attempt * 2)
                    print(f"    [{provider_label.upper()} ERROR] Terjadi kesalahan ({err_msg[:160]}). Menunggu {wait_time} detik (Percobaan {attempt+1}/{max_retries})...", flush=True)
                    time.sleep(wait_time)
                else:
                    print(f"[{provider_label.upper()} ERROR] Gagal memanggil API {provider_label} setelah {max_retries} percobaan: {err_msg[:180]}", flush=True)

        if is_custom:
            return None

        if is_edgeone and AppConfig.OPENROUTER_API_KEY:
            print("[INFO] EdgeOne gagal merespons JSON. Beralih otomatis ke fallback OpenRouter...")
            return generate_structured_json(prompt, response_schema, "openrouter", "openrouter/free", AppConfig.OPENROUTER_API_KEY)
        if not is_edgeone and AppConfig.EDGEONE_API_KEY:
            print("[INFO] OpenRouter gagal merespons JSON. Beralih otomatis ke fallback EdgeOne...")
            return generate_structured_json(prompt, response_schema, "edgeone", "@makers/deepseek-v4-flash", AppConfig.EDGEONE_API_KEY)
        if AppConfig.GEMINI_API_KEY  and not AppConfig.GEMINI_API_KEY.startswith("["):
            print(f"[INFO] {provider_label} gagal merespons JSON. Beralih otomatis ke fallback Gemini...")
            return generate_structured_json(prompt, response_schema, "gemini", "gemini-2.5-flash", AppConfig.GEMINI_API_KEY)
        return None

    elif provider == "ollama":
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                res_data = response.json()
                raw_text = res_data.get("response", "")
                try:
                    return _robust_json_repair_and_load(raw_text)
                except json.JSONDecodeError as je:
                    print(f"[OLLAMA JSON ERROR] Output dari model bukan format JSON valid: {je}")
                    print(f"    Raw Output: {raw_text[:200]}...")
                    return None
            else:
                print(f"[OLLAMA ERROR] Status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"[OLLAMA ERROR] Gagal menghubungi Ollama: {e}")
            return None

    else:
        raise PipelineError(f"Provider AI '{provider}' belum didukung untuk pembuatan JSON terstruktur.")
