import os
import google.generativeai as genai
from .analytics import metrics

SYSTEM = (
    "You are Credit Assistant, a financial wellness advisor for users in India. "
    "Use CIBIL (300-900), INR amounts, and Indian context (EMIs, RBI norms, credit cards, "
    "personal/home/auto loans). Give specific, actionable, prioritized advice. Be concise, "
    "use short bullet points, and never promise score outcomes. You are not a licensed "
    "financial advisor; remind users to verify major decisions with a professional."
)


def _summary(p) -> str:
    m = metrics(p)
    return (
        f"CIBIL score: {p.cibil_score} ({m['score_band']})\n"
        f"Monthly income: INR {p.monthly_income:,.0f}; expenses: INR {p.monthly_expenses:,.0f}; "
        f"EMIs: INR {p.monthly_debt_payments:,.0f}\n"
        f"Credit limit: INR {p.credit_limit:,.0f}; used: INR {p.credit_used:,.0f} "
        f"(utilization {m['utilization']}%)\n"
        f"DTI: {m['dti_ratio']}%; savings rate: {m['savings_rate']}%; savings: INR {p.savings:,.0f}\n"
        f"Active loans: {p.active_loans}; missed payments: {p.missed_payments}\n"
        f"Goal: {p.financial_goal or 'not specified'}\n"
        f"Health score: {m['health_score']}/100; risks: {'; '.join(m['risks']) or 'none'}"
    )


def _fallback(p) -> str:
    m = metrics(p)
    tips = ["**Rule-based guidance (AI key not configured or unavailable):**"]
    if m["utilization"] > 30:
        tips.append("- Pay down card balances to bring utilization below 30%; consider asking for a limit increase.")
    if p.missed_payments:
        tips.append("- Set up auto-debit for EMIs and card minimums; on-time payment is the biggest score factor.")
    if m["dti_ratio"] > 40:
        tips.append("- Avoid new loans and prepay the highest-interest debt first.")
    if m["savings_rate"] < 20:
        tips.append("- Aim to save at least 20% of income; automate a SIP/RD on salary day.")
    if p.active_loans > 3:
        tips.append("- Avoid multiple hard enquiries; consolidate loans if it lowers your interest rate.")
    if len(tips) == 1:
        tips.append("- Your profile looks healthy. Keep utilization low and check your CIBIL report yearly.")
    return "\n".join(tips)


def _generate(prompt: str) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("no key")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), system_instruction=SYSTEM)
    return model.generate_content(prompt).text


def analyze(p) -> str:
    prompt = (
        f"User financial profile:\n{_summary(p)}\n\nProvide: 1) credit health analysis, "
        "2) top 5 prioritized actions to improve score, 3) debt & utilization plan, "
        "4) savings guidance, 5) a short roadmap toward their goal."
    )
    try:
        return _generate(prompt)
    except Exception:
        return _fallback(p)


def chat(p, message: str) -> str:
    prompt = f"User financial profile:\n{_summary(p)}\n\nUser question: {message}"
    try:
        return _generate(prompt)
    except Exception:
        return _fallback(p)
