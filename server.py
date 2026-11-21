import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
try:
    from backend import HospitalSystem
except ImportError:
    from backend_2 import HospitalSystem
hs = HospitalSystem()
patient_meta: dict[int, dict[str, str]] = {}
active_admissions = 0
DOCTORS_DIRECTORY = [
    {"name": "Dr. Ibrahim Ashraf", "field": "General Medicine", "status": "Available"},
    {"name": "Dr. Shawal Nadeem", "field": "Cardiology", "status": "Available"},
    {"name": "Dr. Abubakar Naveed", "field": "Orthopedics", "status": "On Duty"},
    {"name": "Dr. Bisma Iqbal", "field": "Pediatrics", "status": "Available"},
    {"name": "Dr. Aibtasam Ali", "field": "Neurology", "status": "On Duty"},
    {"name": "Dr. Ibrahim Ali", "field": "ENT & Dermatology", "status": "Available"},
]
def _collect_patients() -> list[dict]:
    items = []
    curr = getattr(hs, "head", None)
    while curr:
        meta = patient_meta.get(
            curr.id,
            {
                "doctor": "Dr. Ibrahim Ashraf",
                "field": "General Medicine",
                "rate": "",
                "status": "Waiting",
                "prescription": "",
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
                "rate": meta["rate"],
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
def _snapshot(status_msg: str | None = None) -> dict:
    patients = _collect_patients()
    queue_list = list(getattr(hs, "queue", []))
    queue_items = [
        {"name": name, "wait": "Next Up" if idx == 1 else f"#{idx} in line"}
        for idx, name in enumerate(queue_list, start=1)
    ]
    available_count = sum(1 for d in DOCTORS_DIRECTORY if d["status"] == "Available")
    payload = {
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
class HospitalHandler(SimpleHTTPRequestHandler):
    def _send_json(self, code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        clean_path = self.path.split("?", 1)[0]
        if clean_path == "/api/state":
            self._send_json(200, _snapshot())
            return
        if clean_path == "/":
            self.path = "/index.html"
        return super().do_GET()
    def do_POST(self):
        global active_admissions
        clean_path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return
        if clean_path == "/api/add-patient":
            try:
                pid = int(str(data.get("id", "")).strip())
                age = int(str(data.get("age", "")).strip())
            except ValueError:
                self._send_json(400, {"error": "Invalid ID or Age"})
                return
            name = str(data.get("name", "")).strip()
            disease = str(data.get("disease", "")).strip()
            rate = str(data.get("rate", "")).strip()
            doctor_choice = str(data.get("doctor", "")).strip()
            if not name or not disease:
                self._send_json(400, {"error": "Missing Name or Disease"})
                return
            if _find_patient(pid) is None:
                hs.add_patient(pid, name, age, disease)
                active_admissions += 1
            doc_obj = next(
                (d for d in DOCTORS_DIRECTORY if f"{d['name']} ({d['field']})" == doctor_choice or d["name"] == doctor_choice),
                DOCTORS_DIRECTORY[(pid - 1) % len(DOCTORS_DIRECTORY)],
            )
            patient_meta[pid] = {
                "doctor": doc_obj["name"],
                "field": doc_obj["field"],
                "rate": rate,
                "status": "In Progress",
                "prescription": f"{doc_obj['field']} Care",
            }
            self._send_json(
                200,
                _snapshot(
                    f"Add Patient: Patient ID {pid} | Name: {name} | Age: {age} | Disease: {disease} | {doc_obj['name']} ({doc_obj['field']})"
                ),
            )
            return
        if clean_path == "/api/book-appointment":
            name = str(data.get("name", "")).strip()
            doctor_choice = str(data.get("doctor", "")).strip()
            if not name:
                self._send_json(400, {"error": "Missing name"})
                return
            hs.book_appointment(name)
            self._send_json(
                200,
                _snapshot(
                    f"Book Appt: Booked appointment for {name} ({doctor_choice}) | Waiting Queue: {len(hs.queue)}"
                ),
            )
            return
        if clean_path == "/api/call-next":
            if not hs.queue:
                self._send_json(200, _snapshot("Call Next Patient: No pending appointments in queue."))
                return
            next_patient = hs.queue[0]
            hs.call_next()
            curr = getattr(hs, "head", None)
            while curr:
                if curr.name.lower() == next_patient.lower() and curr.id in patient_meta:
                    patient_meta[curr.id]["status"] = "Completed"
                curr = curr.next
            self._send_json(
                200,
                _snapshot(
                    f"Call Next Patient: Now attending {next_patient} | Remaining in queue: {len(hs.queue)}"
                ),
            )
            return
        if clean_path == "/api/cancel-appointment":
            idx = data.get("index", -1)
            if isinstance(idx, int) and 0 <= idx < len(hs.queue):
                removed = hs.queue[idx]
                del hs.queue[idx]
                self._send_json(200, _snapshot(f"Cancel Appointment: Cancelled appointment for {removed}."))
            else:
                self._send_json(200, _snapshot("Cancel Appointment: No appointment removed."))
            return
        if clean_path == "/api/search-patient":
            try:
                pid = int(str(data.get("id", "")).strip())
            except ValueError:
                self._send_json(400, {"error": "Invalid ID"})
                return
            hs.search_patient(pid)
            node = _find_patient(pid)
            if node:
                meta = patient_meta.get(pid, {"doctor": "Dr. Ibrahim Ashraf", "field": "General Medicine"})
                info = (
                    f"Patient ID {node.id} | Name: {node.name} | Age: {node.age} | "
                    f"Disease: {node.disease} | {meta['doctor']} ({meta['field']})"
                )
                self._send_json(200, _snapshot(f"Search Patient: Found -> {info}"))
            else:
                self._send_json(200, _snapshot(f"Search Patient: Patient with ID {pid} not found."))
            return
        self._send_json(404, {"error": "Not found"})
def main():
    import uvicorn
    from llm_server import app

    print("Server running at http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)
if __name__ == "__main__":
    main()