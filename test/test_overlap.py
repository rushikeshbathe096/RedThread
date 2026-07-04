import pytest
from backend.memory import find_overlap

def test_find_overlap_exact_match():
    nodes_a = [
        {"id": "node_1", "label": "Julian Barnes"},
        {"id": "node_2", "label": "0x9A4bC3F8D"}
    ]
    nodes_b = [
        {"id": "node_3", "label": "Arthur Pendelton"},
        {"id": "node_4", "label": "0x9a4bc3f8d "} # Differently cased and with a space
    ]
    
    overlap = find_overlap(nodes_a, nodes_b)
    
    assert len(overlap) == 1
    assert overlap[0]["id"] == "node_2"

def test_find_overlap_no_match():
    nodes_a = [
        {"id": "node_1", "label": "Julian Barnes"}
    ]
    nodes_b = [
        {"id": "node_3", "label": "Arthur Pendelton"}
    ]
    
    overlap = find_overlap(nodes_a, nodes_b)
    
    assert len(overlap) == 0
