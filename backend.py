from collections import deque
import heapq
class PatientNode:
    def __init__(self, id, name, age, disease): self.id, self.name, self.age, self.disease, self.next = id, name, age, disease, None
class DoublyPatientList:
    def __init__(self): self.head = self.tail = None
    def _n(self, id, name, age, disease): return {"id": id, "name": name, "age": age, "disease": disease, "prev": None, "next": None}
    def add_to_tail(self, id, name, age, disease):
        n = self._n(id, name, age, disease)
        if not self.tail: self.head = self.tail = n
        else: n["prev"], self.tail["next"], self.tail = self.tail, n, n
    def add_to_head(self, id, name, age, disease):
        n = self._n(id, name, age, disease)
        if not self.head: self.head = self.tail = n
        else: n["next"], self.head["prev"], self.head = self.head, n, n
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
    def _trav(self, step):
        out, c = [], self.head if step == "next" else self.tail
        while c: out.append({k: c[k] for k in ("id", "name", "age", "disease")}); c = c[step]
        return out
    def traverse_forward(self): return self._trav("next")
    def traverse_backward(self): return self._trav("prev")
class ActionStack:
    def __init__(self, capacity=100): self._items, self.capacity = [], capacity
    def push(self, element):
        if self.is_full(): self._items.pop(0)
        self._items.append(element)
    def pop(self): return None if self.is_empty() else self._items.pop()
    def top_value(self): return None if self.is_empty() else self._items[-1]
    def is_empty(self): return len(self._items) == 0
    def is_full(self): return len(self._items) >= self.capacity
class CircularAppointmentQueue:
    def __init__(self, capacity=50):
        self.capacity, self._arr = capacity, [None] * capacity
        self._front = self._size = 0; self._rear = -1
    def is_empty(self): return self._size == 0
    def is_full(self): return self._size == self.capacity
    def enqueue(self, element):
        if self.is_full(): return False
        self._rear = (self._rear + 1) % self.capacity; self._arr[self._rear] = element; self._size += 1; return True
    def dequeue(self):
        if self.is_empty(): return None
        item, self._arr[self._front] = self._arr[self._front], None
        self._front = (self._front + 1) % self.capacity; self._size -= 1; return item
    def items(self): return [self._arr[(self._front + i) % self.capacity] for i in range(self._size)]
class PriorityAppointmentQueue:
    def __init__(self): self._heap, self._counter = [], 0
    def enqueue_priority(self, name, priority=5, doctor=""):
        heapq.heappush(self._heap, (priority, self._counter, name, doctor)); self._counter += 1
    def _fmt(self, row): return {"name": row[2], "priority": row[0], "doctor": row[3]} if row else None
    def dequeue_priority(self): return self._fmt(heapq.heappop(self._heap)) if self._heap else None
    def peek(self): return self._fmt(self._heap[0]) if self._heap else None
class PatientBinaryTree:
    def __init__(self): self.root, self.array_view = None, []
    def insert_level_order(self, value):
        self.array_view.append(value)
        node = {"val": value, "left": None, "right": None}
        if not self.root: self.root = node; return
        q = deque([self.root])
        while q:
            c = q.popleft()
            for side in ("left", "right"):
                if not c[side]: c[side] = node; return
                q.append(c[side])
class PatientBST:
    def __init__(self): self.root = None
    def insert(self, pid, name, disease):
        def _ins(n, pid, name, disease):
            if not n: return {"pid": pid, "name": name, "disease": disease, "left": None, "right": None}
            if pid != n["pid"]: side = "left" if pid < n["pid"] else "right"; n[side] = _ins(n[side], pid, name, disease)
            else: n["name"], n["disease"] = name, disease
            return n
        self.root = _ins(self.root, pid, name, disease)
    def search(self, pid):
        c = self.root
        while c:
            if pid == c["pid"]: return type("BSTHit", (), c)()
            c = c["left" if pid < c["pid"] else "right"]
        return None
    def delete(self, pid):
        def _del(n, pid):
            if not n: return None, False
            if pid != n["pid"]: side = "left" if pid < n["pid"] else "right"; n[side], d = _del(n[side], pid); return n, d
            if not n["left"] or not n["right"]: return (n["right"] or n["left"]), True
            s = n["right"]
            while s["left"]: s = s["left"]
            n["pid"], n["name"], n["disease"] = s["pid"], s["name"], s["disease"]
            n["right"], _ = _del(n["right"], s["pid"]); return n, True
        self.root, deleted = _del(self.root, pid); return deleted
    def inorder(self):
        out = []
        def _in(n):
            if n: _in(n["left"]); out.append({"id": n["pid"], "name": n["name"], "disease": n["disease"]}); _in(n["right"])
        _in(self.root); return out
class _HeapBase:
    def __init__(self, is_min=True): self.data, self._s = [], (1 if is_min else -1)
    def insert(self, key, value=None): self.data.append((key, value)); self._up(len(self.data) - 1)
    def delete(self):
        if not self.data: return None
        top, last = self.data[0], self.data.pop()
        if self.data: self.data[0] = last; self._down(0)
        return {"key": top[0], "value": top[1]}
    def _cmp(self, a, b): return (a - b) * self._s < 0
    def _up(self, i):
        while i > 0 and self._cmp(self.data[i][0], self.data[(i - 1) // 2][0]):
            p = (i - 1) // 2; self.data[i], self.data[p] = self.data[p], self.data[i]; i = p
    def _down(self, i):
        n, best, l, r = len(self.data), i, 2 * i + 1, 2 * i + 2
        for ch in (l, r):
            if ch < n and self._cmp(self.data[ch][0], self.data[best][0]): best = ch
        if best != i: self.data[i], self.data[best] = self.data[best], self.data[i]; self._down(best)
class PatientMinHeap(_HeapBase):
    def __init__(self): super().__init__(True)
class PatientMaxHeap(_HeapBase):
    def __init__(self): super().__init__(False)
class PatientAVLTree:
    def __init__(self): self.root = None
    def _h(self, n): return n["h"] if n else 0
    def _bf(self, n): return (self._h(n["left"]) - self._h(n["right"])) if n else 0
    def _upd(self, n): n["h"] = 1 + max(self._h(n["left"]), self._h(n["right"])); return n
    def _rot(self, n, d):
        a, b = ("left", "right") if d == "r" else ("right", "left")
        piv, mid = n[a], n[a][b]; piv[b], n[a] = n, mid; self._upd(n); self._upd(piv); return piv
    def _bal(self, n):
        self._upd(n); bf = self._bf(n)
        if bf > 1:
            if self._bf(n["left"]) < 0: n["left"] = self._rot(n["left"], "l")
            return self._rot(n, "r")
        if bf < -1:
            if self._bf(n["right"]) > 0: n["right"] = self._rot(n["right"], "r")
            return self._rot(n, "l")
        return n
    def insert(self, pid, name):
        def _i(n, pid, name):
            if not n: return {"pid": pid, "name": name, "left": None, "right": None, "h": 1}
            if pid != n["pid"]: side = "left" if pid < n["pid"] else "right"; n[side] = _i(n[side], pid, name)
            else: n["name"] = name; return n
            return self._bal(n)
        self.root = _i(self.root, pid, name)
    def delete(self, pid):
        def _d(n, pid):
            if not n: return None, False
            if pid != n["pid"]: side = "left" if pid < n["pid"] else "right"; n[side], ok = _d(n[side], pid)
            else:
                ok = True
                if not n["left"] or not n["right"]: return (n["right"] or n["left"]), True
                s = n["right"]
                while s["left"]: s = s["left"]
                n["pid"], n["name"] = s["pid"], s["name"]; n["right"], _ = _d(n["right"], s["pid"])
            return (None, ok) if not n else (self._bal(n), ok)
        self.root, deleted = _d(self.root, pid); return deleted
class PatientHashTable:
    def __init__(self, size=31):
        self.size, self.buckets = size, [[] for _ in range(size)]
        self.linear_table, self.quad_table = [None] * size, [None] * size
    def _hash(self, key): return int(key) % self.size
    def _probe(self, table, idx, pid, record, step_fn):
        for step in range(self.size):
            pos = (idx + step_fn(step)) % self.size
            if table[pos] is None or table[pos][0] == pid: table[pos] = (pid, record); return
    def insert(self, pid, record):
        idx = self._hash(pid)
        for item in self.buckets[idx]:
            if item[0] == pid: item[1] = record; break
        else: self.buckets[idx].append([pid, record])
        self._probe(self.linear_table, idx, pid, record, lambda s: s)
        self._probe(self.quad_table, idx, pid, record, lambda s: s * s)
    def get(self, pid):
        for k, v in self.buckets[self._hash(pid)]:
            if k == pid: return v
        return None
class HospitalWardGraph:
    def __init__(self): self.adj, self.weighted_adj, self.edges = {}, {}, []
    def add_edge(self, u, v, weight=1):
        for x, y in ((u, v), (v, u)):
            self.adj.setdefault(x, [])
            if y not in self.adj[x]: self.adj[x].append(y)
            self.weighted_adj.setdefault(x, []).append((y, weight))
        self.edges.append((weight, u, v))
    def bfs(self, start):
        if start not in self.adj: return []
        vis, q, out = {start}, deque([start]), []
        while q:
            c = q.popleft(); out.append(c)
            for n in self.adj[c]:
                if n not in vis: vis.add(n); q.append(n)
        return out
    def dfs(self, start):
        if start not in self.adj: return []
        vis, out = set(), []
        def _f(u):
            vis.add(u); out.append(u)
            for n in self.adj[u]:
                if n not in vis: _f(n)
        _f(start); return out
class HospitalSystem:
    def __init__(self):
        self.head, self.queue = None, deque()
        self.doubly_patients, self.action_stack = DoublyPatientList(), ActionStack()
        self.circular_queue, self.priority_queue = CircularAppointmentQueue(), PriorityAppointmentQueue()
        self.binary_tree, self.bst = PatientBinaryTree(), PatientBST()
        self.min_heap, self.max_heap = PatientMinHeap(), PatientMaxHeap()
        self.avl, self.hash_index = PatientAVLTree(), PatientHashTable()
        self.ward_graph = HospitalWardGraph()
        for a, b, w in [("Reception", "OPD", 2), ("OPD", "Cardiology", 4), ("OPD", "General Medicine", 3), ("Emergency", "Cardiology", 5), ("Emergency", "Pharmacy", 2)]:
            self.ward_graph.add_edge(a, b, weight=w)
    def add_patient(self, id, name, age, disease):
        node = PatientNode(id, name, age, disease)
        if not self.head: self.head = node
        else:
            c = self.head
            while c.next: c = c.next
            c.next = node
        self.doubly_patients.add_to_tail(id, name, age, disease); self.binary_tree.insert_level_order({"id": id, "name": name})
        self.bst.insert(id, name, disease); self.min_heap.insert(id, name); self.max_heap.insert(age, name)
        self.avl.insert(id, name); self.hash_index.insert(id, {"id": id, "name": name, "age": age, "disease": disease})
        self.action_stack.push(f"ADD_PATIENT:{id}:{name}")
    def remove_patient(self, id):
        c, prev = self.head, None
        while c:
            if c.id == id:
                if prev is None: self.head = c.next
                else: prev.next = c.next
                self.doubly_patients.remove_by_id(id); self.bst.delete(id); self.avl.delete(id)
                self.action_stack.push(f"REMOVE_PATIENT:{id}"); return True
            prev, c = c, c.next
        return False
    def _find_node(self, id):
        c = self.head
        while c:
            if c.id == id: return c
            c = c.next
        return None
    def search_patient(self, id):
        c = self._find_node(id)
        print(f"ID: {c.id} | Name: {c.name} | Age: {c.age} | Disease: {c.disease}" if c else "Patient not found.")
    def book_appointment(self, name): self.queue.append(name); self.circular_queue.enqueue(name); self.action_stack.push(f"BOOK_APPT:{name}")
    def call_next(self):
        if not self.queue: print("No pending appointments."); return
        attended = self.queue.popleft(); self.circular_queue.dequeue(); self.action_stack.push(f"CALL_NEXT:{attended}")
    def display_patients(self):
        if not self.head: print("No patient records found."); return
        c = self.head
        while c: print(f"ID: {c.id} | Name: {c.name} | Age: {c.age} | Disease: {c.disease}"); c = c.next
    def get_sorted_patients_by_age(self):
        arr, c = [], self.head
        while c: arr.append({"id": c.id, "name": c.name, "age": c.age, "disease": c.disease}); c = c.next
        for i in range(1, len(arr)):
            key, j = arr[i], i - 1
            while j >= 0 and arr[j]["age"] > key["age"]: arr[j + 1] = arr[j]; j -= 1
            arr[j + 1] = key
        return arr
def main():
    hs = HospitalSystem()
    while True:
        print("\n--- Hospital Management System ---\n 1.Add Patient\n 2.Search Patient\n 3.Book Appointment\n 4.Call Next Patient\n 5.Display All\n 6.Exit")
        ch = input("Enter choice: ")
        if ch == "1": hs.add_patient(int(input("ID: ")), input("Name: "), int(input("Age: ")), input("Disease: "))
        elif ch == "2": hs.search_patient(int(input("ID:")))
        elif ch == "3": hs.book_appointment(input("Name:"))
        elif ch == "4": hs.call_next()
        elif ch == "5": hs.display_patients()
        elif ch == "6": break
        else: print("Invalid choice.")
if __name__ == "__main__": main()