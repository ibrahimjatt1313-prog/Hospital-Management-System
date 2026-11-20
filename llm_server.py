import math
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    from backend import HospitalSystem
except ImportError:
    from backend_2 import HospitalSystem

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Hospital Management System — AI & LLM Backend", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

default_db = "/tmp/hms_records.db" if os.getenv("VERCEL") else (BASE_DIR / "hms_records.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{default_db}"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class PatientDB(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=False)
    disease = Column(String(180), nullable=False)
    doctor = Column(String(160), nullable=False)
    field = Column(String(120), nullable=False)
    address = Column(String(200), default="")
    status = Column(String(50), default="In Progress")
    prescription = Column(Text, default="")
    visits_summary = Column(Text, default="")


Base.metadata.create_all(bind=engine)

hs = HospitalSystem()
patient_meta: dict[int, dict[str, str]] = {}
active_admissions = 0

DOCTORS_DIRECTORY = [
    {"name": "Dr. Ibrahim Ashraf", "field": "General Medicine", "status": "Available", "slots": ["10:00 AM", "11:30 AM", "02:00 PM"]},
    {"name": "Dr. Shawal Nadeem", "field": "Cardiology", "status": "Available", "slots": ["09:30 AM", "01:00 PM", "04:00 PM"]},
    {"name": "Dr. Abubakar Naveed", "field": "Orthopedics", "status": "Available", "slots": ["11:00 AM", "03:00 PM"]},
    {"name": "Dr. Aibtasam Ali", "field": "Pediatrics", "status": "Available", "slots": ["10:30 AM", "02:30 PM"]},
    {"name": "Dr. Bisma Iqbal", "field": "Neurology", "status": "On Duty", "slots": ["01:30 PM", "04:30 PM"]},
    {"name": "Dr. Ibrahim Ali", "field": "ENT & Dermatology", "status": "On Duty", "slots": ["12:00 PM", "03:30 PM"]},
]

HOSPITAL_DOCS: list[dict[str, str]] = [
    {
        "title": "OPD & Visiting Hours Policy",
        "text": "General OPD runs Monday to Saturday from 9:00 AM to 6:00 PM. Emergency department operates 24/7. Patient visitor hours are 4:00 PM to 7:00 PM daily.",
    },
    {
        "title": "Appointment Booking & Queue Rules",
        "text": "Patients can book appointments by name and medical field or doctor. The waiting queue follows FIFO order with Live Info status and Call Next Patient.",
    },
    {
        "title": "Cardiology & Chest Pain Triage",
        "text": "Patients reporting chest pain, palpitations, or shortness of breath should be prioritized for Cardiology evaluation and baseline ECG.",
    },
    {
        "title": "General Medicine & Fever Protocol",
        "text": "For fever, viral symptoms, or general checkups, General Medicine advises temperature monitoring, hydration, and physician prescription review.",
    },
    {
        "title": "Discharge & Prescription Guidelines",
        "text": "Before discharge, verify prescription clarity, follow-up schedule, and update patient status so active admissions remain accurate.",
    },
]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _search_docs(query: str, top_k: int = 3) -> list[dict[str, str]]:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return HOSPITAL_DOCS[:top_k]

    q_tf: dict[str, int] = {}
    for tok in q_tokens:
        q_tf[tok] = q_tf.get(tok, 0) + 1

    scored: list[tuple[float, dict[str, str]]] = []
    for doc in HOSPITAL_DOCS:
        d_tokens = _tokenize(f"{doc['title']} {doc['text']}")
        d_tf: dict[str, int] = {}
        for tok in d_tokens:
            d_tf[tok] = d_tf.get(tok, 0) + 1

        common = set(q_tf.keys()) & set(d_tf.keys())
        dot = sum(q_tf[k] * d_tf[k] for k in common)
        q_norm = math.sqrt(sum(v * v for v in q_tf.values()))
        d_norm = math.sqrt(sum(v * v for v in d_tf.values()))
        sim = (dot / (q_norm * d_norm)) if (q_norm and d_norm) else 0.0
        scored.append((sim, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def _run_llm(system_prompt: str, user_prompt: str, fallback_text: str) -> tuple[str, str]:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                ),
            )
            content = (getattr(response, "text", None) or "").strip()
            if content:
                return content, f"Gemini ({model_name})"
        except Exception as exc:
            return f"{fallback_text}\n\n(Gemini note: {exc})", "Local AI Fallback"

    return fallback_text, "Local AI + HMS Fallback"


def _persist_patient_to_sql(
    pid: int,
    name: str,
    age: int,
    disease: str,
    doctor: str,
    field: str,
    address: str,
    status: str,
    prescription: str,
):
    try:
        with SessionLocal() as db:
            existing = db.scalar(select(PatientDB).where(PatientDB.id == pid))
            visit_line = f"Visit: {disease} under {doctor} ({status})"
            if existing:
                existing.name = name
                existing.age = age
                existing.disease = disease
                existing.doctor = doctor
                existing.field = field
                existing.address = address
                existing.status = status
                existing.prescription = prescription
                prev = existing.visits_summary or ""
                if visit_line not in prev:
                    existing.visits_summary = f"{prev} | {visit_line}".strip(" |")
            else:
                db.add(
                    PatientDB(
                        id=pid,
                        name=name,
                        age=age,
                        disease=disease,
                        doctor=doctor,
                        field=field,
                        address=address,
                        status=status,
                        prescription=prescription,
                        visits_summary=visit_line,
                    )
                )
            db.commit()
    except Exception:
        pass


def _collect_patients() -> list[dict[str, Any]]:
    items = []
    curr = getattr(hs, "head", None)
    while curr:
        meta = patient_meta.get(
            curr.id,
            {
                "doctor": "Dr. Ibrahim Ashraf",
                "field": "General Medicine",
                "address": "",
                "status": "In Progress",
                "prescription": "General Medicine Care",
            },
        )
        items.append(
            {
                "id": curr.id,
                "name": curr.name,
                "age": curr.age,
                "disease": curr.disease,
                "doctor": meta["doctor"],
                "field": meta["field"],
                "address": meta.get("address", ""),
                "rate": meta.get("address", ""),
                "status": meta["status"],
                "prescription": meta["prescription"],
            }
        )
        curr = curr.next
    return items


def _find_patient(pid: int):
    curr = getattr(hs, "head", None)
    while curr:
        if curr.id == pid:
            return curr
        curr = curr.next
    return None


def _snapshot(status_msg: str | None = None) -> dict[str, Any]:
    patients = _collect_patients()
    queue_list = list(getattr(hs, "queue", []))
    queue_items = [
        {"name": name, "wait": "Next Up" if idx == 1 else f"#{idx} in line"}
        for idx, name in enumerate(queue_list, start=1)
    ]
    available_count = sum(1 for d in DOCTORS_DIRECTORY if d["status"] == "Available")
    payload: dict[str, Any] = {
        "kpis": {
            "totalPatients": len(patients),
            "waitingQueue": len(queue_list),
            "activeAdmissions": active_admissions,
            "availableDoctors": available_count,
        },
        "doctors": DOCTORS_DIRECTORY,
        "queue": queue_items,
        "patients": patients,
    }
    if status_msg is not None:
        payload["status"] = status_msg
    return payload


class AddPatientReq(BaseModel):
    id: int
    name: str
    age: int
    disease: str
    address: str = ""
    rate: str = ""
    doctor: str = "Dr. Ibrahim Ashraf — General Medicine"


class BookApptReq(BaseModel):
    name: str
    doctor: str = "Dr. Ibrahim Ashraf — General Medicine"


class CancelApptReq(BaseModel):
    index: int = -1


class SearchPatientReq(BaseModel):
    id: int


class PriorityAppointmentReq(BaseModel):
    name: str = Field(..., min_length=1)
    priority: int = Field(default=5, ge=1, le=10)
    doctor: str = "Dr. Ibrahim Ashraf — General Medicine"


class ChatbotReq(BaseModel):
    question: str = Field(..., min_length=1)


class AiAppointmentReq(BaseModel):
    query: str = Field(..., min_length=1)
    patient_name: str = ""
    auto_book: bool = False


class ReportSummaryReq(BaseModel):
    report_text: str = Field(..., min_length=1)
    patient_name: str = ""


class DoctorAssistantReq(BaseModel):
    patient_id: int | None = None
    patient_name: str = ""
    question: str = ""


class AnalyticsReq(BaseModel):
    focus: str = "Overall hospital statistics and management summary"


@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/{file_name}")
def serve_static_file(file_name: str):
    allowed = {"style.css", "app.js", "app_2.js", "backend.py", "backend_2.py"}
    target = BASE_DIR / file_name
    if file_name in allowed and target.exists():
        return FileResponse(target)
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/api/state")
def api_state():
    return _snapshot()


@app.post("/api/add-patient")
def api_add_patient(req: AddPatientReq):
    global active_admissions
    pid = int(req.id)
    age = int(req.age)
    name = req.name.strip()
    disease = req.disease.strip()
    address = (req.address or req.rate or "").strip()
    doc_choice = req.doctor.strip()

    doc_obj = next(
        (
            d
            for d in DOCTORS_DIRECTORY
            if doc_choice.startswith(d["name"]) or f"{d['name']} — {d['field']}" == doc_choice
        ),
        DOCTORS_DIRECTORY[(pid - 1) % len(DOCTORS_DIRECTORY)],
    )
    rx = f"{doc_obj['field']} Care"
    if _find_patient(pid) is None:
        hs.add_patient(pid, name, age, disease)
        active_admissions += 1
    patient_meta[pid] = {
        "doctor": doc_obj["name"],
        "field": doc_obj["field"],
        "address": address,
        "status": "In Progress",
        "prescription": rx,
    }
    _persist_patient_to_sql(pid, name, age, disease, doc_obj["name"], doc_obj["field"], address, "In Progress", rx)
    return _snapshot(
        f"Add Patient: Patient ID {pid} | Name: {name} | Age: {age} | Disease: {disease} | {doc_obj['name']} ({doc_obj['field']})"
    )


@app.post("/api/book-appointment")
def api_book_appointment(req: BookApptReq):
    name = req.name.strip()
    hs.book_appointment(name)
    return _snapshot(f"Book Appt: Booked appointment for {name} ({req.doctor}) | Waiting Queue: {len(hs.queue)}")


@app.post("/api/call-next")
def api_call_next():
    if not hs.queue:
        return _snapshot("Call Next Patient: No pending appointments in queue.")
    next_patient = hs.queue[0]
    hs.call_next()
    curr = getattr(hs, "head", None)
    while curr:
        if curr.name.lower() == next_patient.lower() and curr.id in patient_meta:
            patient_meta[curr.id]["status"] = "Completed"
        curr = curr.next
    return _snapshot(f"Call Next Patient: Now attending {next_patient} | Remaining in queue: {len(hs.queue)}")


@app.post("/api/cancel-appointment")
def api_cancel_appointment(req: CancelApptReq):
    idx = req.index
    if 0 <= idx < len(hs.queue):
        removed = hs.queue[idx]
        del hs.queue[idx]
        return _snapshot(f"Cancel Appointment: Cancelled appointment for {removed}.")
    return _snapshot("Cancel Appointment: No appointment removed.")


@app.post("/api/search-patient")
def api_search_patient(req: SearchPatientReq):
    pid = int(req.id)
    hs.search_patient(pid)
    node = _find_patient(pid)
    if node:
        meta = patient_meta.get(pid, {"doctor": "Dr. Ibrahim Ashraf", "field": "General Medicine"})
        info = f"Patient ID {node.id} | Name: {node.name} | Age: {node.age} | Disease: {node.disease} | {meta['doctor']} ({meta['field']})"
        return _snapshot(f"Search Patient: Found -> {info}")
    return _snapshot(f"Search Patient: Patient with ID {pid} not found.")


@app.post("/api/ds/priority-book")
def api_ds_priority_book(req: PriorityAppointmentReq):
    pq = getattr(hs, "priority_queue", None)
    if pq is None:
        return JSONResponse({"error": "Priority queue not initialized"}, status_code=400)
    clean_name = req.name.strip()
    pq.enqueue_priority(clean_name, priority=req.priority, doctor=req.doctor.strip())
    if hasattr(hs, "action_stack"):
        hs.action_stack.push(f"API_PRIORITY_BOOK:{clean_name}:P{req.priority}")
    return {
        "status": "Priority appointment queued",
        "patient": clean_name,
        "priority": req.priority,
        "next_highest_priority": pq.peek(),
    }


@app.post("/api/ds/priority-call-next")
def api_ds_priority_call_next():
    pq = getattr(hs, "priority_queue", None)
    if pq is None:
        return JSONResponse({"error": "Priority queue not initialized"}, status_code=400)
    attended = pq.dequeue_priority()
    if not attended:
        return {"status": "No priority appointments in queue", "attended": None}
    if hasattr(hs, "action_stack"):
        hs.action_stack.push(f"API_PRIORITY_CALL:{attended['name']}")
    return {
        "status": "Attending highest-priority patient",
        "attended": attended,
        "next_in_line": pq.peek(),
    }


@app.get("/api/ds/bst-lookup/{patient_id}")
def api_ds_bst_lookup(patient_id: int):
    bst = getattr(hs, "bst", None)
    if bst is None:
        return JSONResponse({"error": "BST not initialized"}, status_code=400)
    found = bst.search(patient_id)
    return {
        "found": found is not None,
        "patient": {"id": found.pid, "name": found.name, "disease": found.disease} if found else None,
        "inorder_records": bst.inorder(),
    }


@app.get("/api/ds/sorted-by-age")
def api_ds_sorted_by_age():
    if not hasattr(hs, "get_sorted_patients_by_age"):
        return JSONResponse({"error": "Sorting helper not available"}, status_code=400)
    sorted_list = hs.get_sorted_patients_by_age()
    return {"count": len(sorted_list), "sorted_by": "age (insertion sort)", "patients": sorted_list}


@app.get("/api/ds/stack-top")
def api_ds_stack_top():
    stack = getattr(hs, "action_stack", None)
    if stack is None:
        return JSONResponse({"error": "Action stack not initialized"}, status_code=400)
    return {"is_empty": stack.is_empty(), "top_action": stack.top_value()}
@app.get("/api/ds/hash-lookup/{patient_id}")
def api_ds_hash_lookup(patient_id: int):
    ht = getattr(hs, "hash_index", None)
    if ht is None:
        return JSONResponse({"error": "Hash index not initialized"}, status_code=400)
    record = ht.get(patient_id)
    return {
        "found": record is not None,
        "bucket": patient_id % ht.size if getattr(ht, "size", 0) else None,
        "record": record,
    }


@app.get("/api/ds/ward-route/{start_ward}")
def api_ds_ward_route(start_ward: str):
    wg = getattr(hs, "ward_graph", None)
    if wg is None:
        return JSONResponse({"error": "Ward graph not initialized"}, status_code=400)
    return {
        "start": start_ward,
        "bfs_order": wg.bfs(start_ward),
        "dfs_order": wg.dfs(start_ward),
    }

@app.post("/api/ai/chatbot")
def ai_chatbot(req: ChatbotReq):
    retrieved = _search_docs(req.question, top_k=3)
    docs_context = "\n".join([f"- [{d['title']}] {d['text']}" for d in retrieved])
    fallback = (
        f"Hospital Guide Answer:\n"
        f"{retrieved[0]['text']}\n\n"
        f"Related Policy ({retrieved[1]['title']}): {retrieved[1]['text']}"
    )
    answer, engine_used = _run_llm(
        "You are a helpful hospital front-desk AI assistant. Answer clearly using the provided hospital policies and recommend physician review when needed.",
        f"Hospital Policies:\n{docs_context}\n\nQuestion: {req.question}",
        fallback,
    )
    return {
        "module": "01 AI Hospital Chatbot",
        "engine": engine_used,
        "retrieved_docs": [d["title"] for d in retrieved],
        "answer": answer,
    }


@app.post("/api/ai/appointment")
def ai_appointment(req: AiAppointmentReq):
    q_lower = req.query.lower()
    matched = [
        d
        for d in DOCTORS_DIRECTORY
        if any(word in f"{d['name']} {d['field']} {d['status']}".lower() for word in _tokenize(q_lower))
    ]
    candidates = matched if matched else DOCTORS_DIRECTORY[:3]
    booked_msg = ""
    if req.auto_book and req.patient_name.strip():
        chosen = candidates[0]
        p_label = req.patient_name.strip()
        hs.book_appointment(p_label)
        booked_msg = f"\nBooked '{p_label}' in queue under {chosen['name']} ({chosen['field']}). Current queue size: {len(hs.queue)}."

    lines = [
        f"• {d['name']} — {d['field']} [{d['status']}] | Slots: {', '.join(d['slots'])}"
        for d in candidates
    ]
    fallback = "Matching Doctors & Appointments:\n" + "\n".join(lines) + booked_msg
    answer, engine_used = _run_llm(
        "You are an AI appointment coordinator. Present matching doctors, availability, and slots clearly.",
        f"Query: {req.query}\nPatient: {req.patient_name}\nMatches:\n" + "\n".join(lines) + booked_msg,
        fallback,
    )
    return {
        "module": "02 AI Appointment Booking",
        "engine": engine_used,
        "matches": candidates,
        "booked": bool(booked_msg),
        "queue": _snapshot()["queue"],
        "answer": answer,
    }


@app.post("/api/ai/summarize-report")
def ai_summarize_report(req: ReportSummaryReq):
    snippet = req.report_text.strip()
    sentences = [s.strip() for s in re.split(r"[.\n]+", snippet) if s.strip()]
    key_points = sentences[:4] if sentences else [snippet]
    fallback = (
        f"Simple Medical Report Summary{f' ({req.patient_name})' if req.patient_name.strip() else ''}:\n"
        + "\n".join([f"• {pt}" for pt in key_points])
        + "\n• Next Step: Confirm findings with your assigned physician."
    )
    answer, engine_used = _run_llm(
        "Summarize medical reports into concise, clear bullet points for clinical staff and patients without giving a final diagnosis.",
        f"Patient: {req.patient_name}\nReport Text:\n{snippet}",
        fallback,
    )
    return {
        "module": "03 AI Medical Report Summarizer",
        "engine": engine_used,
        "answer": answer,
    }


@app.post("/api/ai/doctor-assistant")
def ai_doctor_assistant(req: DoctorAssistantReq):
    patients = _collect_patients()
    target = None
    if req.patient_id is not None:
        target = next((p for p in patients if p["id"] == req.patient_id), None)
    if target is None and req.patient_name.strip():
        target = next((p for p in patients if req.patient_name.strip().lower() in p["name"].lower()), None)
    if target is None and patients:
        target = patients[-1]

    sql_history = ""
    if target:
        try:
            with SessionLocal() as db:
                row = db.scalar(select(PatientDB).where(PatientDB.id == target["id"]))
                if row and row.visits_summary:
                    sql_history = row.visits_summary
        except Exception:
            pass

    if not target:
        fallback = "No patient records found in HMS yet. Add a patient first so the AI Doctor Assistant can summarize history and visits."
    else:
        fallback = (
            f"Doctor Brief — {target['name']} (ID: {target['id']}, Age: {target['age']}):\n"
            f"• Current Condition: {target['disease']}\n"
            f"• Assigned Doctor: {target['doctor']} ({target['field']})\n"
            f"• Status & Rx: {target['status']} | {target['prescription']}\n"
            f"• Visit History: {sql_history or 'Initial registration recorded in HMS.'}"
        )

    answer, engine_used = _run_llm(
        "You are an AI Clinical Doctor Assistant. Provide a concise pre-consultation brief covering condition, status, prescription, and visit history.",
        f"Patient Record: {target}\nSQL History: {sql_history}\nDoctor Question: {req.question}",
        fallback,
    )
    return {
        "module": "04 AI Doctor Assistant",
        "engine": engine_used,
        "patient": target,
        "answer": answer,
    }


@app.post("/api/ai/analytics")
def ai_analytics(req: AnalyticsReq):
    snap = _snapshot()
    patients = snap["patients"]
    by_field: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for p in patients:
        fld = p.get("field") or "General Medicine"
        st = p.get("status") or "In Progress"
        by_field[fld] = by_field.get(fld, 0) + 1
        by_status[st] = by_status.get(st, 0) + 1

    field_str = ", ".join([f"{k}: {v}" for k, v in by_field.items()]) or "None yet"
    status_str = ", ".join([f"{k}: {v}" for k, v in by_status.items()]) or "None yet"
    fallback = (
        f"Hospital Analytics Report ({req.focus}):\n"
        f"• Total Patients: {snap['kpis']['totalPatients']} | Waiting Queue: {snap['kpis']['waitingQueue']} | "
        f"Active Admissions: {snap['kpis']['activeAdmissions']} | Available Doctors: {snap['kpis']['availableDoctors']}\n"
        f"• By Status: {status_str}\n"
        f"• By Department: {field_str}"
    )
    answer, engine_used = _run_llm(
        "You are an AI Hospital Operations Analytics Assistant. Turn live hospital KPIs and department counts into clear management insights.",
        f"KPIs: {snap['kpis']}\nBy Status: {by_status}\nBy Department: {by_field}\nFocus: {req.focus}",
        fallback,
    )
    return {
        "module": "05 AI Hospital Analytics Assistant",
        "engine": engine_used,
        "kpis": snap["kpis"],
        "by_department": by_field,
        "by_status": by_status,
        "answer": answer,
    }