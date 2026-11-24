from collections import deque
import heapq
class PatientNode:
    def __init__(self, pid, name, age, disease):
        self.id, self.name, self.age, self.disease = pid, name, age, disease
        self.next = self.prev = None
class DoublyPatientList:
    def __init__(self): self.head = self.tail = None
    def add_to_tail(self, pid, name, age, disease):
        n = PatientNode(pid, name, age, disease)
        if not self.head: self.head = self.tail = n
        else: n.prev, self.tail.next, self.tail = self.tail, n, n
    def traverse_rev(self):
        c, out = self.tail, []
        while c: out.append((c.id, c.name)); c = c.prev
        return out
class ActionStack:
    def __init__(self, cap=100): self.items, self.cap = [], cap
    def push(self, el):
        if len(self.items) >= self.cap: self.items.pop(0)
        self.items.append(el)
    def pop(self): return self.items.pop() if self.items else None
class CircularAppointmentQueue:
    def __init__(self, cap=50): self.cap, self.arr, self.f, self.r, self.size = cap, [None]*cap, 0, -1, 0
    def enqueue(self, el):
        if self.size == self.cap: return False
        self.r = (self.r + 1) % self.cap; self.arr[self.r] = el; self.size += 1; return True
    def dequeue(self):
        if not self.size: return None
        x, self.arr[self.f] = self.arr[self.f], None; self.f = (self.f + 1) % self.cap; self.size -= 1; return x
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
        self.array_view.append(val); n = {"val": val, "left": None, "right": None}
        if not self.root: self.root = n; return
        q = deque([self.root])
        while q:
            c = q.popleft()
            for s in ("left", "right"):
                if not c[s]: c[s] = n; return
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
        heapq.heappush(self.data, (self.s * key, key, val))
    def delete(self):
        r = heapq.heappop(self.data) if self.data else None
        return {"key": r[1], "value": r[2]} if r else None
class PatientAVLTree:
    def __init__(self): self.root = None
    h = lambda self, n: n["h"] if n else 0
    def _rot(self, n, d):
        a, b = ("left", "right") if d == "r" else ("right", "left")
        p, m = n[a], n[a][b]; p[b], n[a] = n, m
        for x in (n, p): x["h"] = 1 + max(self.h(x["left"]), self.h(x["right"]))
        return p
    def insert(self, pid, name):
        def _i(n):
            if not n: return {"pid": pid, "name": name, "left": None, "right": None, "h": 1}
            if pid != n["pid"]: s = "left" if pid < n["pid"] else "right"; n[s] = _i(n[s])
            else: n["name"] = name; return n
            n["h"] = 1 + max(self.h(n["left"]), self.h(n["right"])); bf = self.h(n["left"]) - self.h(n["right"])
            if bf > 1: return self._rot(n, "r") if self.h(n["left"]["left"]) >= self.h(n["left"]["right"]) else (n.update({"left": self._rot(n["left"], "l")}) or self._rot(n, "r"))
            if bf < -1: return self._rot(n, "l") if self.h(n["right"]["right"]) >= self.h(n["right"]["left"]) else (n.update({"right": self._rot(n["right"], "r")}) or self._rot(n, "l"))
            return n
        self.root = _i(self.root)
    def search(self, pid):
        c = self.root
        while c and c["pid"] != pid: c = c["left" if pid < c["pid"] else "right"]
        return c
class PatientHashTable:
    def __init__(self, size=31): self.size, self.buckets, self.lin = size, [[] for _ in range(size)], [None]*size
    def insert(self, pid, rec):
        idx = int(pid) % self.size
        for it in self.buckets[idx]:
            if it[0] == pid: it[1] = rec; break
        else: self.buckets[idx].append([pid, rec])
        for s in range(self.size):
            pos = (idx + s) % self.size
            if self.lin[pos] is None or self.lin[pos][0] == pid: self.lin[pos] = (pid, rec); break
    get = lambda self, pid: next((v for k, v in self.buckets[int(pid) % self.size] if k == pid), None)
class HospitalWardGraph:
    def __init__(self): self.adj = {}
    def add_edge(self, u, v):
        for x, y in ((u, v), (v, u)): self.adj.setdefault(x, []); y in self.adj[x] or self.adj[x].append(y)
    def bfs(self, s):
        if s not in self.adj: return []
        vis, q, out = {s}, deque([s]), []
        while q:
            c = q.popleft(); out.append(c)
            for n in self.adj[c]:
                if n not in vis: vis.add(n); q.append(n)
        return out
    def dfs(self, s, vis=None, out=None):
        if s not in self.adj: return []
        vis, out = vis or set(), out or []; vis.add(s); out.append(s)
        for n in self.adj[s]:
            if n not in vis: self.dfs(n, vis, out)
        return out
class HospitalSystem:
    def __init__(self):
        self.head = None; self.dll, self.stack, self.cq = DoublyPatientList(), ActionStack(), CircularAppointmentQueue()
        self.pq, self.bt, self.bst = PriorityAppointmentQueue(), PatientBinaryTree(), PatientBST()
        self.min_h, self.max_h, self.avl, self.ht, self.graph = PatientHeap(True), PatientHeap(False), PatientAVLTree(), PatientHashTable(), HospitalWardGraph()
        for a, b in [("Reception", "OPD"), ("OPD", "Cardiology"), ("Emergency", "Pharmacy")]: self.graph.add_edge(a, b)
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
        r = self.ht.get(pid)
        b = self.bst.search(pid)
        a = self.avl.search(pid)
        print(f"HT: {r} | BST: {b['name'] if b else None} | AVL: {a['name'] if a else None}" if r else "Not found.")
    def book_appointment(self, name, priority=5):
        self.cq.enqueue(name); self.pq.enqueue_priority(name, priority); self.stack.push(f"BOOK:{name}")

    def call_next(self, urgent=False):
        print(f"Calling: {self.pq.dequeue_priority()['name']}" if urgent and self.pq.heap else f"Calling: {self.cq.dequeue() or 'None'}")
    def display_patients(self):
        c = self.head
        while c: print(f"ID: {c.id} | Name: {c.name} | Age: {c.age} | Disease: {c.disease}"); c = c.next
        if not self.head: print("No patient records found.")
    def ds_ops(self):
        print("DLL Rev:", self.dll.traverse_rev())
        print("Stack Pop:", self.stack.pop())
        print("Binary Tree:", self.bt.array_view)
        print("MinHeap Pop:", self.min_h.delete(), "| MaxHeap Pop:", self.max_h.delete())
        print("BFS:", self.graph.bfs("Reception"), "| DFS:", self.graph.dfs("Emergency"))
def main():
    hs = HospitalSystem()
    while (ch := input("\n--- Hospital Management System ---\n1.Add Patient \n2.Search Patient \n3.Book Appointement \n4.Next Call Patient \n5.Display All Patient \n6.All DS Operation \n7.Exit \nChoice: ")) != "7":
        if ch == "1": hs.add_patient(int(input("ID: ")), input("Name: "), int(input("Age: ")), input("Disease: "))
        elif ch == "2": hs.search_patient(int(input("ID: ")))
        elif ch == "3": hs.book_appointment(input("Name: "), int(input("Priority(1-5): ") or 5))
        elif ch == "4": hs.call_next(input("Urgent(1/0): ") == "1")
        elif ch == "5": hs.display_patients()
        elif ch == "6": hs.ds_ops()
        else: print("Invalid choice.")
if __name__ == "__main__": main()