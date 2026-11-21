from collections import deque
import heapq
class PatientNode:
    def __init__(self, pid, name, age, disease):
        self.id, self.name, self.age, self.disease, self.next = pid, name, age, disease, None
class DoublyPatientList:
    def __init__(self): self.head = self.tail = None
    def _node(self, pid, name, age, disease, prev=None, nxt=None):
        return {"id": pid, "name": name, "age": age, "disease": disease, "prev": prev, "next": nxt}
    def add_to_tail(self, pid, name, age, disease):
        n = self._node(pid, name, age, disease, prev=self.tail)
        self.head = self.tail = n if not self.tail else (self.tail.update({"next": n}) or self.head)
        if self.tail is not n: self.tail["next"] = n; self.tail = n
    def add_to_head(self, pid, name, age, disease):
        n = self._node(pid, name, age, disease, nxt=self.head)
        if not self.head: self.head = self.tail = n
        else: self.head["prev"] = self.head = n
    def remove_by_id(self, pid):
        c = self.head
        while c:
            if c["id"] == pid:
                if c["prev"]: c["prev"]["next"] = c["next"]
                else: self.head = c["next"]
                if c["next"]: c["next"]["prev"] = c["prev"]
                else: self.tail = c["prev"]
                return True
            c = c["next"]
        return False
    def traverse(self, step="next"):
        out, c = [], self.head if step == "next" else self.tail
        while c: out.append({k: c[k] for k in ("id", "name", "age", "disease")}); c = c[step]
        return out
class ActionStack:
    def __init__(self, cap=100): self.items, self.cap = [], cap
    def push(self, el):
        if len(self.items) >= self.cap: self.items.pop(0)
        self.items.append(el)
    def pop(self): return self.items.pop() if self.items else None
    def top(self): return self.items[-1] if self.items else None
class CircularAppointmentQueue:
    def __init__(self, cap=50):
        self.cap, self.arr, self.front, self.rear, self.size = cap, [None] * cap, 0, -1, 0
    def enqueue(self, el):
        if self.size == self.cap: return False
        self.rear = (self.rear + 1) % self.cap; self.arr[self.rear] = el; self.size += 1; return True
    def dequeue(self):
        if not self.size: return None
        item, self.arr[self.front] = self.arr[self.front], None
        self.front = (self.front + 1) % self.cap; self.size -= 1; return item
class PriorityAppointmentQueue:
    def __init__(self): self.heap, self.c = [], 0
    def enqueue_priority(self, name, priority=5, doctor=""):
        heapq.heappush(self.heap, (priority, self.c, name, doctor)); self.c += 1
    def dequeue_priority(self):
        r = heapq.heappop(self.heap) if self.heap else None
        return {"name": r[2], "priority": r[0], "doctor": r[3]} if r else None
class PatientBinaryTree:
    def __init__(self): self.root, self.array_view = None, []
    def insert_level_order(self, val):
        self.array_view.append(val); node = {"val": val, "left": None, "right": None}
        if not self.root: self.root = node; return
        q = deque([self.root])
        while q:
            c = q.popleft()
            for s in ("left", "right"):
                if not c[s]: c[s] = node; return
                q.append(c[s])
class PatientBST:
    def __init__(self): self.root = None
    def insert(self, pid, name, disease):
        def _ins(n):
            if not n: return {"pid": pid, "name": name, "disease": disease, "left": None, "right": None}
            if pid != n["pid"]: s = "left" if pid < n["pid"] else "right"; n[s] = _ins(n[s])
            else: n["name"], n["disease"] = name, disease
            return n
        self.root = _ins(self.root)
    def search(self, pid):
        c = self.root
        while c and c["pid"] != pid: c = c["left" if pid < c["pid"] else "right"]
        return c
class PatientHeap:
    def __init__(self, is_min=True): self.data, self.s = [], (1 if is_min else -1)
    def insert(self, key, val=None):
        self.data.append((self.s * key, key, val)); i = len(self.data) - 1
        while i > 0 and self.data[i][0] < self.data[(i - 1) // 2][0]:
            p = (i - 1) // 2; self.data[i], self.data[p] = self.data[p], self.data[i]; i = p
    def delete(self):
        if not self.data: return None
        top, last = self.data[0], self.data.pop()
        if self.data:
            self.data[0] = last; i, n = 0, len(self.data)
            while True:
                b, l, r = i, 2 * i + 1, 2 * i + 2
                if l < n and self.data[l][0] < self.data[b][0]: b = l
                if r < n and self.data[r][0] < self.data[b][0]: b = r
                if b == i: break
                self.data[i], self.data[b] = self.data[b], self.data[i]; i = b
        return {"key": top[1], "value": top[2]}
class PatientAVLTree:
    def __init__(self): self.root = None
    def _h(self, n): return n["h"] if n else 0
    def _rot(self, n, d):
        a, b = ("left", "right") if d == "r" else ("right", "left")
        piv, mid = n[a], n[a][b]; piv[b], n[a] = n, mid
        for x in (n, piv): x["h"] = 1 + max(self._h(x["left"]), self._h(x["right"]))
        return piv
    def insert(self, pid, name):
        def _i(n):
            if not n: return {"pid": pid, "name": name, "left": None, "right": None, "h": 1}
            if pid != n["pid"]: s = "left" if pid < n["pid"] else "right"; n[s] = _i(n[s])
            else: n["name"] = name; return n
            n["h"] = 1 + max(self._h(n["left"]), self._h(n["right"])); bf = self._h(n["left"]) - self._h(n["right"])
            if bf > 1: return self._rot(n, "r") if self._h(n["left"]["left"]) >= self._h(n["left"]["right"]) else (n.update({"left": self._rot(n["left"], "l")}) or self._rot(n, "r"))
            if bf < -1: return self._rot(n, "l") if self._h(n["right"]["right"]) >= self._h(n["right"]["left"]) else (n.update({"right": self._rot(n["right"], "r")}) or self._rot(n, "l"))
            return n
        self.root = _i(self.root)
class PatientHashTable:
    def __init__(self, size=31):
        self.size, self.buckets, self.lin, self.quad = size, [[] for _ in range(size)], [None] * size, [None] * size
    def _probe(self, tbl, idx, pid, rec, fn):
        for s in range(self.size):
            pos = (idx + fn(s)) % self.size
            if tbl[pos] is None or tbl[pos][0] == pid: tbl[pos] = (pid, rec); return
    def insert(self, pid, rec):
        idx = int(pid) % self.size
        for item in self.buckets[idx]:
            if item[0] == pid: item[1] = rec; break
        else: self.buckets[idx].append([pid, rec])
        self._probe(self.lin, idx, pid, rec, lambda s: s); self._probe(self.quad, idx, pid, rec, lambda s: s * s)
    def get(self, pid): return next((v for k, v in self.buckets[int(pid) % self.size] if k == pid), None)
class HospitalWardGraph:
    def __init__(self): self.adj, self.edges = {}, []
    def add_edge(self, u, v, w=1):
        for x, y in ((u, v), (v, u)): self.adj.setdefault(x, []); self.adj[x].append(y) if y not in self.adj[x] else None
        self.edges.append((w, u, v))
    def bfs(self, start):
        if start not in self.adj: return []
        vis, q, out = {start}, deque([start]), []
        while q:
            c = q.popleft(); out.append(c)
            for n in self.adj[c]:
                if n not in vis: vis.add(n); q.append(n)
        return out
    def dfs(self, start, vis=None, out=None):
        if start not in self.adj: return []
        vis, out = vis if vis is not None else set(), out if out is not None else []
        vis.add(start); out.append(start)
        for n in self.adj[start]:
            if n not in vis: self.dfs(n, vis, out)
        return out
class HospitalSystem:
    def __init__(self):
        self.head, self.q, self.dll, self.stack = None, deque(), DoublyPatientList(), ActionStack()
        self.cq, self.pq, self.bt, self.bst = CircularAppointmentQueue(), PriorityAppointmentQueue(), PatientBinaryTree(), PatientBST()
        self.min_h, self.max_h, self.avl, self.ht, self.graph = PatientHeap(True), PatientHeap(False), PatientAVLTree(), PatientHashTable(), HospitalWardGraph()
        for a, b, w in [("Reception", "OPD", 2), ("OPD", "Cardiology", 4), ("OPD", "General Medicine", 3), ("Emergency", "Cardiology", 5), ("Emergency", "Pharmacy", 2)]:
            self.graph.add_edge(a, b, w)
    def add_patient(self, pid, name, age, disease):
        node = PatientNode(pid, name, age, disease)
        if not self.head: self.head = node
        else:
            c = self.head
            while c.next: c = c.next
            c.next = node
        self.dll.add_to_tail(pid, name, age, disease); self.bt.insert_level_order({"id": pid, "name": name})
        self.bst.insert(pid, name, disease); self.min_h.insert(pid, name); self.max_h.insert(age, name)
        self.avl.insert(pid, name); self.ht.insert(pid, {"id": pid, "name": name, "age": age, "disease": disease})
        self.stack.push(f"ADD:{pid}:{name}")
    def search_patient(self, pid):
        c = self.head
        while c and c.id != pid: c = c.next
        print(f"ID: {c.id} | Name: {c.name} | Age: {c.age} | Disease: {c.disease}" if c else "Not found.")
    def book_appointment(self, name): self.q.append(name); self.cq.enqueue(name); self.stack.push(f"BOOK:{name}")
    def call_next(self): print(f"Calling: {self.cq.dequeue()}" if self.q and self.q.popleft() else "No pending appointments.")
    def display_patients(self):
        c = self.head
        while c: print(f"ID: {c.id} | Name: {c.name} | Age: {c.age} | Disease: {c.disease}"); c = c.next
        if not self.head: print("No patient records found.")
def main():
    hs = HospitalSystem()
    while (ch := input("\n--- Hospital Management System ---\n1.Add Patient \n2.Search Patient \n3.Book Appointement \n4.Next Call Patient \n5.Display All Patient \n6.Exit\nChoice: ")) != "6":
        if ch == "1": hs.add_patient(int(input("ID: ")), input("Name: "), int(input("Age: ")), input("Disease: "))
        elif ch == "2": hs.search_patient(int(input("ID: ")))
        elif ch == "3": hs.book_appointment(input("Name: "))
        elif ch == "4": hs.call_next()
        elif ch == "5": hs.display_patients()
        else: print("Invalid choice.")
if __name__ == "__main__": main()