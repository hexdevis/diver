#include <iostream>

// Simple singly linked list of integers with basic operations.
struct Node {
  int val;
  Node* next;
  Node(int v) : val(v), next(nullptr) {}
};

struct LinkedList {
  Node* head;
  LinkedList() : head(nullptr) {}
  ~LinkedList() {
    while (head) {
      Node* tmp = head;
      head = head->next;
      delete tmp;
    }
  }

  void push_front(int v) {
    Node* n = new Node(v);
    n->next = head;
    head = n;
  }

  bool pop_front(int &out) {
    if (!head) return false;
    Node* n = head;
    out = n->val;
    head = head->next;
    delete n;
    return true;
  }

  void print() const {
    Node* cur = head;
    std::cout << "List:";
    while (cur) {
      std::cout << ' ' << cur->val;
      cur = cur->next;
    }
    std::cout << '\n';
  }
};

int main() {
  LinkedList l;
  l.push_front(10);
  l.push_front(20);
  l.push_front(50);
  l.print(); // expected: List: 30 20 10

  int v;
  if (l.pop_front(v)) {
    std::cout << "Popped: " << v << '\n';
  }
  l.print(); // expected: List: 20 10

  // Confirm remaining elements
  while (l.pop_front(v)) {
    std::cout << "Removed: " << v << '\n';
  }
  l.print(); // expected: List:

  return 0;
}
