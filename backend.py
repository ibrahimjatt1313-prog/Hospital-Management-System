from collections import deque
class PatientNode:
    def __init__(self,id,name,age,disease):
        self.id = id
        self.name = name
        self.age = age
        self.disease = disease
        self.next = None
class HospitalSystem:
    def __init__(self):
        self.head = None
        self.queue = deque()
    def add_patient(self,id,name,age,disease):
        node = PatientNode(id,name,age,disease)
        if not self.head:
            self.head = node
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = node
        print("Patient added successfully.")
    def search_patient(self,id):
        curr = self.head
        while curr:
            if curr.id == id:
                print(f"ID: {curr.id} | Name: {curr.name} | Age: {curr.age} | Disease: {curr.disease}")
                return
            curr = curr.next
        print("Patient not found.")
    def book_appointment(self,name):
        self.queue.append(name)
        print(f"Appointment booked for {name}.")
    def call_next(self):
        if not self.queue:
            print("No pending appointments.")
            return
        print(f"Now attending: {self.queue.popleft()}")
    def display_patients(self):
        if not self.head:
            print("No patient records found.")
            return
        curr = self.head
        while curr:
            print(f"ID: {curr.id} | Name: {curr.name} | Age: {curr.age} | Disease: {curr.disease}")
            curr = curr.next
def main():
    hs = HospitalSystem()
    while True:
        print("\n--- Hospital Management System ---")
        print(" 1.Add Patient\n 2.Search Patient\n 3.Book Appointment\n 4.Call Next Patient\n 5.Display All\n 6.Exit")
        choice = input("Enter choice: ")
        if choice == '1':
            hs.add_patient(int(input("ID: ")),input("Name: "),int(input("Age: ")),input("Disease: "))
        elif choice == '2':
            hs.search_patient(int(input("ID:")))
        elif choice == '3':
            hs.book_appointment(input("Name:"))
        elif choice == '4':
            hs.call_next()
        elif choice == '5':
            hs.display_patients()
        elif choice == '6':
            break
        else:
            print("Invalid choice.")
if __name__ == "__main__":
    main()