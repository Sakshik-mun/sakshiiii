"""Financial indicator calculations (CIBIL range 300-900)."""


def score_band(score: int) -> str:
    if score >= 750: return "Excellent"
    if score >= 700: return "Good"
    if score >= 650: return "Fair"
    if score >= 550: return "Poor"
    return "Very Poor"


def dti_ratio(income: float, debt: float) -> float:
    return round(debt / income * 100, 1) if income > 0 else 0.0


def utilization(limit: float, used: float) -> float:
    return round(used / limit * 100, 1) if limit > 0 else 0.0


def savings_rate(income: float, expenses: float, debt: float) -> float:
    return round((income - expenses - debt) / income * 100, 1) if income > 0 else 0.0


def improvement(history: list[int]) -> dict:
    if len(history) < 2:
        return {"change": 0, "since_first": 0}
    return {"change": history[-1] - history[-2], "since_first": history[-1] - history[0]}


def health_assessment(p) -> dict:
    """Weighted 0-100 health score + risk flags."""
    dti, util = dti_ratio(p.monthly_income, p.monthly_debt_payments), utilization(p.credit_limit, p.credit_used)
    sav = savings_rate(p.monthly_income, p.monthly_expenses, p.monthly_debt_payments)
    pts = (p.cibil_score - 300) / 600 * 40                       # 40 pts: CIBIL
    pts += max(0, 20 - max(0, util - 30) * 0.4)                  # 20 pts: utilization (<30% ideal)
    pts += max(0, 20 - max(0, dti - 20) * 0.5)                   # 20 pts: DTI (<20% ideal)
    pts += min(10, max(0, sav) / 2)                              # 10 pts: savings rate
    pts += max(0, 10 - p.missed_payments * 3)                    # 10 pts: payment record
    pts = round(max(0, min(100, pts)))
    risks = []
    if util > 30: risks.append(f"High credit utilization ({util}%) - keep it under 30%")
    if dti > 40: risks.append(f"Debt-to-income is high ({dti}%) - lenders prefer under 40%")
    elif dti > 30: risks.append(f"Debt-to-income is elevated ({dti}%)")
    if p.missed_payments > 0: risks.append(f"{p.missed_payments} missed payment(s) are hurting your score")
    if sav < 10: risks.append("Low monthly savings rate (<10% of income)")
    if p.monthly_expenses and p.savings < p.monthly_expenses * 3:
        risks.append("Emergency fund covers less than 3 months of expenses")
    label = "Excellent" if pts >= 80 else "Good" if pts >= 60 else "Needs Attention" if pts >= 40 else "Critical"
    return {"health_score": pts, "label": label, "risks": risks}


def metrics(p) -> dict:
    return {
        "dti_ratio": dti_ratio(p.monthly_income, p.monthly_debt_payments),
        "utilization": utilization(p.credit_limit, p.credit_used),
        "savings_rate": savings_rate(p.monthly_income, p.monthly_expenses, p.monthly_debt_payments),
        "score_band": score_band(p.cibil_score),
        **health_assessment(p),
    }
