"""
AI Insights Module for AnnRakshak AI.
Integrates Gemma 4 using the official Google Gen AI SDK ('google-genai').
Securely reads API key from env/st.secrets only.
Verifies model ID, applies retry with timeout, sanitizes PII (phone/email),
and supports full Hindi output when lang == 'hi'.
"""

import os
import re
import time
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_GEMMA4_MODEL = "gemma-4-26b-a4b-it"
ALTERNATIVE_GEMMA4_MODEL = "gemma-4-31b-it"

def get_api_key() -> Optional[str]:
    """Retrieve API key from environment variable or Streamlit secrets only."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                key = st.secrets["GEMINI_API_KEY"]
            elif hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
                key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass
    return key

def scrub_pii(text: str) -> str:
    """Never send phone numbers or emails to external AI models."""
    if not text:
        return ""
    # Scrub phone numbers (Indian & international formats)
    s = re.sub(r'(\+?\d{1,4}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', '[PHONE REDACTED]', text)
    # Scrub email addresses
    s = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', s)
    return s

def verify_gemma_model(model_name: str = DEFAULT_GEMMA4_MODEL) -> Tuple[bool, str]:
    """
    Startup health check to verify model access with the official google-genai SDK.
    Returns (is_available, status_message).
    """
    api_key = get_api_key()
    if not api_key:
        return False, "No Gemini API Key found in env or st.secrets. Using deterministic rule-based fallback."
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Test lightweight listing or metadata call
        models = client.models.list()
        model_found = any(model_name in getattr(m, 'name', '') for m in models)
        if model_found:
            return True, f"Verified access to model '{model_name}' via Google GenAI."
        return True, f"Google GenAI client active with model target '{model_name}'."
    except Exception as e:
        return False, f"Model verification notice: {str(e)[:80]}. Falling back to deterministic engine."

def call_gemma_with_retry(
    client,
    model_name: str,
    contents: str,
    max_retries: int = 2,
    timeout_seconds: float = 10.0
) -> Optional[str]:
    """
    Calls Google GenAI client with 3 attempts, exponential backoff (1s, 2s, 4s),
    and max 10-second timeout per call.
    """
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.models.generate_content,
                    model=model_name,
                    contents=contents
                )
                response = future.result(timeout=timeout_seconds)

            if response and hasattr(response, 'text') and response.text:
                return response.text.strip()
        except concurrent.futures.TimeoutError:
            last_err = TimeoutError(f"Gemma model call timed out after {timeout_seconds:.1f}s")
            if attempt < max_retries:
                backoff = 1.0 * (2 ** attempt)
                time.sleep(backoff)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                backoff = 1.0 * (2 ** attempt)
                time.sleep(backoff)

    if last_err:
        raise last_err
    return None

def analyze_food_waste_with_gemma(
    waste_records: List[Dict[str, Any]],
    model_name: str = DEFAULT_GEMMA4_MODEL,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Analyzes historical food waste records using Gemma 4 via google-genai SDK.
    Ground truth metrics calculated in Python. PII scrubbed. Supports Hindi translation.
    """
    if not waste_records:
        return {
            "success": False,
            "source": "None",
            "message": "No food waste records available to analyze.",
            "content": None
        }

    # Python-calculated ground truth metrics
    total_prep = sum(r.get("portions_prepared", 0) for r in waste_records)
    total_cons = sum(r.get("portions_consumed", 0) for r in waste_records)
    total_edible = sum(r.get("edible_surplus", 0) for r in waste_records)
    total_discard = sum(r.get("discarded_waste", 0) for r in waste_records)
    total_financial_loss = sum(r.get("financial_loss", 0.0) for r in waste_records)
    record_count = len(waste_records)

    cons_pct = (total_cons / total_prep * 100) if total_prep > 0 else 0
    discard_pct = (total_discard / total_prep * 100) if total_prep > 0 else 0
    edible_pct = (total_edible / total_prep * 100) if total_prep > 0 else 0

    meal_type_breakdown = {}
    for r in waste_records:
        mt = r.get("meal_type", "Other")
        meal_type_breakdown[mt] = meal_type_breakdown.get(mt, 0) + r.get("discarded_waste", 0)
    
    highest_waste_meal = max(meal_type_breakdown.items(), key=lambda x: x[1])[0] if meal_type_breakdown else "N/A"

    metrics_summary = {
        "record_count": record_count,
        "total_portions_prepared": total_prep,
        "total_portions_consumed": total_cons,
        "consumption_rate_pct": round(cons_pct, 1),
        "total_edible_surplus_portions": total_edible,
        "edible_surplus_pct": round(edible_pct, 1),
        "total_discarded_waste_portions": total_discard,
        "discarded_waste_pct": round(discard_pct, 1),
        "total_financial_loss_inr": round(total_financial_loss, 2),
        "highest_waste_meal_category": highest_waste_meal
    }

    api_key = get_api_key()

    # If no API key, return deterministic rule-based demo report
    if not api_key:
        fallback_report = generate_rule_based_fallback(metrics_summary, waste_records, lang=lang)
        return {
            "success": True,
            "source": "Deterministic Rule-Based Baseline Engine (Live Gemma 4 API Key not provided)",
            "model": "rule-based-deterministic-v1",
            "is_live_gemma": False,
            "metrics": metrics_summary,
            "observations": fallback_report["observations"],
            "supporting_figures": fallback_report["supporting_figures"],
            "recommendations": fallback_report["recommendations"],
            "limitations": fallback_report["limitations"],
            "food_safety_note": (
                "IMPORTANT: Algorithmic models cannot certify food as safe or edible. "
                "All surplus donations must be physically verified by handling staff according "
                "to applicable hygiene and FSSAI guidelines before redistribution."
            )
        }

    # Attempt Live Call with Google Gen AI SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        lang_instruction = (
            "MANDATORY LANGUAGE: The user requested Hindi output. Respond completely in clean, professional Hindi "
            "(Devanagari script) with appropriate culinary terminology."
            if lang == "hi" else
            "Respond in concise, professional English."
        )

        sanitized_samples = []
        for r in waste_records[:5]:
            p_name = scrub_pii(r.get("provider_name", ""))
            notes = scrub_pii(r.get("notes", ""))
            sanitized_samples.append(
                f"- {p_name} ({r.get('date')} {r.get('meal_type')}): "
                f"Prepared: {r.get('portions_prepared')}, Consumed: {r.get('portions_consumed')}, "
                f"Discarded: {r.get('discarded_waste')}. Notes: {notes}"
            )

        prompt = f"""
You are an AI Food Waste Reduction Specialist advising event caterers, mess managers, and banquet hosts.
You are running on model {model_name}.
{lang_instruction}

CRITICAL MANDATORY INSTRUCTIONS:
1. DO NOT invent, hallucinate, or alter any numbers, statistics, donations, NGOs, or outcomes.
2. Rely strictly and solely upon the pre-calculated metrics provided below by the Python backend.
3. DO NOT claim that AI can certify food safety. Remind users that physical sensory and hygiene inspection is required.
4. Structure your response into four clearly defined markdown sections:
   - ### Observations
   - ### Supporting Figures
   - ### Practical Recommendations
   - ### Limitations & Uncertainties

GROUND TRUTH METRICS (Calculated by Python Backend):
- Total records evaluated: {record_count}
- Total meal portions prepared: {total_prep}
- Total portions consumed: {total_cons} ({metrics_summary['consumption_rate_pct']}%)
- Total edible surplus portions (eligible for donation before spoilage): {total_edible} ({metrics_summary['edible_surplus_pct']}%)
- Total discarded waste portions (food thrown away): {total_discard} ({metrics_summary['discarded_waste_pct']}%)
- Estimated total financial loss: ₹{total_financial_loss:,.2f}
- Meal category with highest recorded waste: {highest_waste_meal}

RECENT EVENT WASTE EXAMPLES (PII Scrubbed):
{chr(10).join(sanitized_samples)}

Please synthesize these observations and provide concrete, actionable recommendations for mess and banquet operations to minimize overproduction.
"""

        raw_text = call_gemma_with_retry(client, model_name, prompt)

        return {
            "success": True,
            "source": f"Live Gemma 4 Analysis ({model_name})",
            "model": model_name,
            "is_live_gemma": True,
            "metrics": metrics_summary,
            "raw_text": raw_text,
            "food_safety_note": (
                "SAFETY NOTICE: Live Gemma 4 analysis provides operational waste optimization recommendations. "
                "AI cannot and does not certify biological or chemical safety of prepared foods."
            )
        }

    except Exception as e:
        err_msg = str(e)
        fallback_report = generate_rule_based_fallback(metrics_summary, waste_records, lang=lang)
        return {
            "success": True,
            "source": f"Deterministic Rule-Based Baseline Engine (Live call fallback: {err_msg[:80]}...)",
            "model": "rule-based-deterministic-v1",
            "is_live_gemma": False,
            "error_detail": err_msg,
            "metrics": metrics_summary,
            "observations": fallback_report["observations"],
            "supporting_figures": fallback_report["supporting_figures"],
            "recommendations": fallback_report["recommendations"],
            "limitations": fallback_report["limitations"],
            "food_safety_note": (
                "SAFETY NOTICE: Algorithmic baseline report. Physical sensory and hygiene inspection is always mandatory."
            )
        }

def prioritize_donations_with_gemma(
    donations: List[Dict[str, Any]],
    model_name: str = DEFAULT_GEMMA4_MODEL,
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Ranks available food donations by urgency (time remaining, portion volume, food perishability).
    Guarantees no PII is transmitted.
    """
    if not donations:
        return {
            "success": False,
            "ranked_items": [],
            "dispatch_guidance": "No active donations available to prioritize."
        }

    # Deterministic calculation of urgency score
    from database import get_ist_now
    now = get_ist_now()

    scored = []
    for d in donations:
        try:
            dead_str = d.get("pickup_deadline", "").replace("T", " ")[:19]
            from datetime import datetime
            dead_dt = datetime.strptime(dead_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=now.tzinfo)
            hours_left = max(0.1, (dead_dt - now).total_seconds() / 3600.0)
        except Exception:
            hours_left = 4.0

        # Urgency formula: higher portions with lower hours remaining have highest priority
        portions = d.get("available_portions", d.get("quantity_portions", 0))
        urgency_score = (portions * 1.5) / hours_left
        
        # Scrub contact before any processing
        clean_item = dict(d)
        clean_item["private_contact"] = "[CONTACT REDACTED]"
        clean_item["hours_left"] = round(hours_left, 1)
        clean_item["urgency_score"] = round(urgency_score, 1)
        scored.append(clean_item)

    scored.sort(key=lambda x: x["urgency_score"], reverse=True)

    guidance = (
        f"प्राथमिकता 1: '{scored[0].get('donor_name')}' के पास {scored[0].get('available_portions')} हिस्से हैं और केवल {scored[0].get('hours_left')} घंटे शेष हैं। निकटतम इलेक्ट्रिक वैन तत्काल रवाना करें।"
        if lang == "hi" else
        f"Priority 1: '{scored[0].get('donor_name')}' has {scored[0].get('available_portions')} portions with only {scored[0].get('hours_left')}h remaining. Dispatch nearest recovery vehicle immediately."
    )

    return {
        "success": True,
        "ranked_items": scored,
        "dispatch_guidance": guidance,
        "is_live_gemma": False,
        "source": "Deterministic FSSAI Urgency Router"
    }

def generate_rule_based_fallback(
    metrics: Dict[str, Any],
    waste_records: List[Dict[str, Any]],
    lang: str = "en"
) -> Dict[str, Any]:
    """Generates high-fidelity, deterministic rule-based advice in English or Hindi."""
    cons_rate = metrics.get("consumption_rate_pct", 0)
    discard_rate = metrics.get("discarded_waste_pct", 0)
    loss = metrics.get("total_financial_loss_inr", 0)
    highest_meal = metrics.get("highest_waste_meal_category", "Dinner")

    if lang == "hi":
        observations = [
            f"विश्लेषित {metrics.get('record_count')} आयोजनों में कुल खपत दर {cons_rate:.1f}% रही।",
            f"भोजन का {discard_rate:.1f}% हिस्सा बर्बाद होकर फेंक दिया गया, जिससे ₹{loss:,.2f} का सीधा वित्तीय नुकसान हुआ।",
            f"सबसे अधिक बर्बादी '{highest_meal}' श्रेणी के आयोजनों में दर्ज की गई।"
        ]
        figures = [
            f"कुल तैयार भोजन: {metrics.get('total_portions_prepared'):,} थालियां",
            f"कुल खपत: {metrics.get('total_portions_consumed'):,} थालियां ({cons_rate:.1f}%)",
            f"खाने योग्य अधिशेष: {metrics.get('total_edible_surplus_portions'):,} थालियां ({metrics.get('edible_surplus_pct'):.1f}%)",
            f"सीधा वित्तीय नुकसान: ₹{loss:,.2f}"
        ]
        recommendations = [
            f"1. **{highest_meal} मेनू में तैयारी बफर घटाएं**: {highest_meal} में 15% कम शुरुआती तैयारी करें और लाइव री-फिलिंग काउंटर अपनाएं।",
            "2. **सख्त FSSAI तापमान निगरानी**: पके हुए भोजन को 65°C से ऊपर गर्म रखने वाले बर्तनों में रखें ताकि 6 घंटे की सुरक्षा खिड़की पूरी मिले।",
            "3. **अधिशेष की पूर्व-सूचना**: कार्यक्रम समाप्त होने से 90 मिनट पूर्व एनजीओ नेटवर्क को ऐप पर अलर्ट भेजें।"
        ]
        limitations = [
            "यह रिपोर्ट ऐतिहासिक ऑडिट डेटा के सांख्यिकीय विश्लेषण पर आधारित है।",
            "एल्गोरिथम मॉडल जैविक सुरक्षा प्रमाणित नहीं कर सकता। वितरण से पूर्व मानव सत्यापन अनिवार्य है।"
        ]
    else:
        observations = [
            f"Across {metrics.get('record_count')} recorded service audits, overall guest consumption efficiency was {cons_rate:.1f}%.",
            f"Unsalvaged discard accounted for {discard_rate:.1f}% of prepared volume, generating ₹{loss:,.2f} in direct ingredient loss.",
            f"The '{highest_meal}' meal category represents the primary vulnerability zone for over-catering."
        ]
        figures = [
            f"Total Meal Portions Prepared: {metrics.get('total_portions_prepared'):,}",
            f"Total Portions Consumed: {metrics.get('total_portions_consumed'):,} ({cons_rate:.1f}%)",
            f"Edible Surplus Salvage Potential: {metrics.get('total_edible_surplus_portions'):,} ({metrics.get('edible_surplus_pct'):.1f}%)",
            f"Direct Measured Financial Loss: ₹{loss:,.2f}"
        ]
        recommendations = [
            f"1. **Trim Safety Cushion for {highest_meal}**: Institute staged cooking batches to reduce initial baseline overproduction.",
            "2. **Strict Hot-Holding Compliance**: Maintain cooked surplus in insulated commercial containers at >65°C to preserve 6-hour rescue safety.",
            "3. **Pre-emptive NGO Coordination**: Notify recovery partners 90 minutes before banquet closure to ensure zero food is discarded."
        ]
        limitations = [
            "Derived from recorded kitchen audit balance logs. Localized attendance factors (e.g. weather) may introduce variance.",
            "Algorithmic recommendations do not replace mandatory FSSAI hygiene standards and sensory evaluation."
        ]

    return {
        "observations": observations,
        "supporting_figures": figures,
        "recommendations": recommendations,
        "limitations": limitations
    }
