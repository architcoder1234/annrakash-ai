"""
Demand Prediction Engine for AnnRakshak AI.
Implements a transparent, deterministic mathematical baseline estimation model.
Includes:
- P80 prediction interval (mean + 1.28 * std of historical waste/consumption ratio)
- Historical sample backtesting with MAPE (Mean Absolute Percentage Error) metric
- Edge case handling (0/negative attendees, clamped 0-50% buffer, cold-start fallback ratios)
- Complete formula documentation for UI rendering
"""

from typing import Dict, Any, List, Optional, Tuple
import math

# Baseline catering consumption ratios based on institutional hospitality benchmarks
CATEGORY_BASELINE_RATIOS = {
    "wedding": 0.82,
    "birthday party": 0.88,
    "restaurant": 0.90,
    "conference": 0.85,
    "corporate": 0.85,
    "canteen": 0.88,
    "default": 0.85
}

def calculate_demand_estimate(
    event_type: str,
    meal_type: str,
    expected_attendees: int,
    cost_per_meal: float,
    safety_buffer_pct: float = 10.0,
    historical_records: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes baseline food preparation recommendations with edge-case validation
    and P80 risk-averse prediction intervals.
    
    Formula:
    Recommended = ceil( Attendees * Consumption_Factor * (1 + Clamped_Buffer / 100) )
    where Clamped_Buffer in [0.0, 50.0].
    
    P80 Prediction Interval:
    P80 Factor = min(1.0, mean_consumption + 1.28 * std_consumption)
    P80 Recommended = ceil( Attendees * P80_Factor )
    """
    if expected_attendees <= 0:
        raise ValueError("Expected attendees must be a positive integer greater than 0.")
    if cost_per_meal < 0:
        raise ValueError("Cost per meal cannot be negative.")

    # Clamp buffer strictly between 0% and 50%
    clamped_buffer = max(0.0, min(50.0, float(safety_buffer_pct)))

    relevant_history = []
    if historical_records:
        for r in historical_records:
            m_type = str(r.get("meal_type", "")).lower()
            p_name = str(r.get("provider_name", "")).lower()
            if meal_type.lower() in m_type or event_type.lower() in p_name:
                prep = r.get("portions_prepared", 0)
                cons = r.get("portions_consumed", 0)
                if prep > 0 and cons > 0:
                    relevant_history.append(r)

    has_history = len(relevant_history) >= 2

    if has_history:
        total_prep = sum(r["portions_prepared"] for r in relevant_history)
        total_cons = sum(r["portions_consumed"] for r in relevant_history)
        consumption_efficiency = total_cons / total_prep if total_prep > 0 else 0.85
        # Conservative arrival factor clamped between 0.75 and 1.0
        arrival_factor = min(1.0, max(0.75, consumption_efficiency + 0.03))

        estimated_net_demand = int(round(expected_attendees * arrival_factor))
        recommended_prep = int(math.ceil(estimated_net_demand * (1.0 + (clamped_buffer / 100.0))))

        # Calculate P80 prediction interval using standard deviation
        cons_ratios = [float(r["portions_consumed"]) / float(r["portions_prepared"]) for r in relevant_history]
        waste_ratios = [(float(r.get("discarded_waste", 0)) + float(r.get("edible_surplus", 0))) / float(r["portions_prepared"]) for r in relevant_history]

        mean_cons = sum(cons_ratios) / len(cons_ratios)
        variance_cons = sum((x - mean_cons) ** 2 for x in cons_ratios) / (len(cons_ratios) - 1 if len(cons_ratios) > 1 else 1)
        std_cons = math.sqrt(variance_cons)

        mean_waste = sum(waste_ratios) / len(waste_ratios)
        variance_waste = sum((x - mean_waste) ** 2 for x in waste_ratios) / (len(waste_ratios) - 1 if len(waste_ratios) > 1 else 1)
        std_waste = math.sqrt(variance_waste)

        # Z = 1.28 for 80th percentile (P80)
        p80_cons_factor = min(1.0, max(0.80, mean_cons + (1.28 * std_cons)))
        p80_portions = int(math.ceil(expected_attendees * p80_cons_factor))
        p80_waste_ratio = min(0.50, max(0.02, mean_waste + (1.28 * std_waste)))

        is_fallback = False
        methodology_note = (
            f"Calculated from {len(relevant_history)} historical audit records. "
            f"Observed consumption rate: {consumption_efficiency*100:.1f}%. "
            f"Applied arrival factor: {arrival_factor*100:.1f}% with a {clamped_buffer:.1f}% safety buffer. "
            f"P80 risk-averse bound: {p80_portions} portions (Z=1.28, σ={std_cons:.3f})."
        )
    else:
        # Fallback default ratio per event type
        ev_key = event_type.lower().strip()
        fallback_ratio = CATEGORY_BASELINE_RATIOS.get(ev_key, CATEGORY_BASELINE_RATIOS["default"])
        estimated_net_demand = int(round(expected_attendees * fallback_ratio))
        recommended_prep = int(math.ceil(estimated_net_demand * (1.0 + (clamped_buffer / 100.0))))

        # Fallback P80 estimate assuming standard hospitality σ=0.04
        mean_cons = fallback_ratio
        std_cons = 0.04
        mean_waste = 1.0 - fallback_ratio
        std_waste = 0.04
        p80_cons_factor = min(1.0, fallback_ratio + (1.28 * 0.04))
        p80_portions = int(math.ceil(expected_attendees * p80_cons_factor))
        p80_waste_ratio = min(0.30, mean_waste + (1.28 * 0.04))

        is_fallback = True
        methodology_note = (
            f"Standard hospitality baseline ratio ({fallback_ratio*100:.0f}%) applied for '{event_type}'. "
            f"No prior kitchen audit records found for this specific event type. "
            f"Safety buffer clamped to {clamped_buffer:.1f}%. "
            f"Fallback P80 bound: {p80_portions} portions."
        )

    expected_total_cost = recommended_prep * cost_per_meal
    estimated_buffer_cost = (recommended_prep - estimated_net_demand) * cost_per_meal

    formula_latex = r"\text{Recommended Portions} = \left\lceil \text{Attendees} \times \text{Factor} \times \left(1 + \frac{\text{Buffer}\%}{100}\right) \right\rceil"
    formula_text = f"Recommended = ceil({expected_attendees} attendees * {estimated_net_demand/expected_attendees:.2f} factor * (1 + {clamped_buffer/100:.2f} buffer)) = {recommended_prep} portions"

    return {
        "expected_attendees": expected_attendees,
        "estimated_net_demand": estimated_net_demand,
        "recommended_preparation": recommended_prep,
        "safety_buffer_portions": recommended_prep - estimated_net_demand,
        "safety_buffer_pct": clamped_buffer,
        "p80_portions": p80_portions,
        "p80_waste_ratio": round(p80_waste_ratio, 4),
        "mean_waste_ratio": round(mean_waste, 4),
        "std_waste_ratio": round(std_waste, 4),
        "cost_per_meal": cost_per_meal,
        "expected_total_cost": expected_total_cost,
        "estimated_buffer_cost": estimated_buffer_cost,
        "methodology": methodology_note,
        "historical_records_used": len(relevant_history),
        "is_fallback": is_fallback,
        "formula_latex": formula_latex,
        "formula_text": formula_text
    }

def backtest_model(historical_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Backtests the deterministic demand prediction engine against historical kitchen waste records.
    Calculates Mean Absolute Percentage Error (MAPE) to quantify model accuracy.
    
    Formula:
    MAPE = (1 / n) * sum( |Actual_Consumed - Predicted_Demand| / Actual_Consumed ) * 100%
    """
    valid_samples = [
        r for r in historical_records
        if r.get("portions_prepared", 0) > 0 and r.get("portions_consumed", 0) > 0
    ]

    if not valid_samples:
        return {
            "mape_pct": 0.0,
            "sample_count": 0,
            "accuracy_pct": 100.0,
            "details": []
        }

    ape_list = []
    details = []

    for r in valid_samples:
        actual_cons = float(r["portions_consumed"])
        prepared = int(r["portions_prepared"])
        m_type = str(r.get("meal_type", "Lunch"))
        p_name = str(r.get("provider_name", "General"))

        # Predict based on attendees = portions_prepared
        try:
            prediction = calculate_demand_estimate(
                event_type=p_name,
                meal_type=m_type,
                expected_attendees=prepared,
                cost_per_meal=float(r.get("cost_per_meal", 100.0)),
                safety_buffer_pct=5.0,
                historical_records=[x for x in valid_samples if x["id"] != r.get("id")]
            )
            pred_demand = float(prediction["estimated_net_demand"])
        except Exception:
            pred_demand = prepared * 0.85

        ape = abs(actual_cons - pred_demand) / actual_cons * 100.0
        ape_list.append(ape)

        details.append({
            "id": r.get("id", "HIST"),
            "provider_name": p_name,
            "date": r.get("date", ""),
            "portions_prepared": prepared,
            "actual_consumed": int(actual_cons),
            "predicted_demand": int(pred_demand),
            "abs_error_portions": int(abs(actual_cons - pred_demand)),
            "ape_pct": round(ape, 2)
        })

    mape = sum(ape_list) / len(ape_list) if ape_list else 0.0
    accuracy = max(0.0, 100.0 - mape)

    return {
        "mape_pct": round(mape, 2),
        "accuracy_pct": round(accuracy, 2),
        "sample_count": len(valid_samples),
        "details": details
    }
