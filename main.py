import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, analytics, ai
from .database import Base, engine, get_db
from .security import hash_password, verify_password, create_token, current_user

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Credit Assistant API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- Auth ----------
@app.post("/api/auth/register", response_model=schemas.TokenOut, status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(email=data.email).first():
        raise HTTPException(409, "Email already registered")
    user = models.User(name=data.name.strip(), email=data.email, password_hash=hash_password(data.password))
    user.profile = models.CreditProfile()
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id), "name": user.name}


@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=data.email.strip().lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "name": user.name}


@app.post("/api/auth/logout")
def logout(user: models.User = Depends(current_user)):
    # Stateless JWT: the client discards the token.
    return {"message": "Logged out"}


# ---------- Profile ----------
def _profile_dict(p):
    return {c.name: getattr(p, c.name) for c in p.__table__.columns if c.name not in ("id", "user_id")}


@app.get("/api/profile")
def get_profile(user: models.User = Depends(current_user)):
    return {"name": user.name, "email": user.email, **_profile_dict(user.profile)}


@app.put("/api/profile")
def update_profile(data: schemas.ProfileIn, user: models.User = Depends(current_user),
                   db: Session = Depends(get_db)):
    p = user.profile
    last = db.query(models.ScoreHistory).filter_by(user_id=user.id).order_by(models.ScoreHistory.id.desc()).first()
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    if not last or last.score != data.cibil_score:
        db.add(models.ScoreHistory(user_id=user.id, score=data.cibil_score))
    db.commit(); db.refresh(p)
    return {"name": user.name, "email": user.email, **_profile_dict(p)}


# ---------- Score history ----------
@app.post("/api/scores", status_code=201)
def add_score(data: schemas.ScoreIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    user.profile.cibil_score = data.score
    db.add(models.ScoreHistory(user_id=user.id, score=data.score))
    db.commit()
    return {"message": "Score recorded"}


@app.get("/api/scores")
def list_scores(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(models.ScoreHistory).filter_by(user_id=user.id).order_by(models.ScoreHistory.recorded_at).all()
    return [{"score": r.score, "date": r.recorded_at.strftime("%d %b %Y")} for r in rows]


# ---------- Dashboard ----------
@app.get("/api/dashboard")
def dashboard(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    p = user.profile
    rows = db.query(models.ScoreHistory).filter_by(user_id=user.id).order_by(models.ScoreHistory.recorded_at).all()
    history = [{"score": r.score, "date": r.recorded_at.strftime("%d %b %Y")} for r in rows]
    latest = db.query(models.Recommendation).filter_by(user_id=user.id, kind="analysis") \
        .order_by(models.Recommendation.id.desc()).first()
    return {
        "name": user.name,
        "cibil_score": p.cibil_score,
        "metrics": analytics.metrics(p),
        "improvement": analytics.improvement([h["score"] for h in history]),
        "utilization_chart": [
            {"name": "Used", "value": p.credit_used},
            {"name": "Available", "value": max(p.credit_limit - p.credit_used, 0)},
        ],
        "score_history": history,
        "active_loans": p.active_loans,
        "missed_payments": p.missed_payments,
        "latest_recommendation": latest.content if latest else None,
    }


# ---------- AI advisor ----------
@app.post("/api/advisor/analyze", response_model=schemas.RecOut)
def advisor_analyze(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    rec = models.Recommendation(user_id=user.id, kind="analysis", prompt="Full analysis",
                                content=ai.analyze(user.profile))
    db.add(rec); db.commit(); db.refresh(rec)
    return rec


@app.post("/api/advisor/chat", response_model=schemas.RecOut)
def advisor_chat(data: schemas.ChatIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    rec = models.Recommendation(user_id=user.id, kind="chat", prompt=data.message,
                                content=ai.chat(user.profile, data.message))
    db.add(rec); db.commit(); db.refresh(rec)
    return rec


@app.get("/api/advisor/history", response_model=list[schemas.RecOut])
def advisor_history(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(models.Recommendation).filter_by(user_id=user.id) \
        .order_by(models.Recommendation.id.desc()).limit(30).all()
