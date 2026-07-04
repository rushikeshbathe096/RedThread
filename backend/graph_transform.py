import asyncio
from cognee.infrastructure.databases.graph.get_graph_engine import get_graph_engine

async def get_flat_graph() -> dict:
    """
    Retrieves the graph data from Cognee and flattens it into the expected format.
    """
    engine = await get_graph_engine()
    data = await engine.get_graph_data()
    
    if isinstance(data, tuple) and len(data) == 2:
        nodes, edges = data
    elif hasattr(data, "nodes") and hasattr(data, "edges"):
        nodes, edges = data.nodes, data.edges
    else:
        nodes, edges = [], []
        
    formatted_nodes = []
    for node in nodes:
        node_dict = node if isinstance(node, dict) else (getattr(node, "__dict__", {}))
        # Handle dict or object attributes
        node_id = str(node_dict.get("id", getattr(node, "id", getattr(node, "node_id", ""))))
        node_label = str(node_dict.get("name", getattr(node, "name", node_id)))
        node_type = str(node_dict.get("type", getattr(node, "type", getattr(node, "label", "Entity"))))
        
        # sometimes node['id'] might be missing, try fallback
        if not node_id:
            node_id = str(hash(str(node_dict)))
            
        formatted_nodes.append({
            "id": node_id,
            "label": node_label,
            "type": node_type
        })
        
    formatted_edges = []
    for edge in edges:
        edge_dict = edge if isinstance(edge, dict) else (getattr(edge, "__dict__", {}))
        source = str(edge_dict.get("source", getattr(edge, "source", getattr(edge, "source_id", getattr(edge, "source_node_id", "")))))
        target = str(edge_dict.get("target", getattr(edge, "target", getattr(edge, "target_id", getattr(edge, "target_node_id", "")))))
        label = str(edge_dict.get("relationship_name", getattr(edge, "relationship_name", getattr(edge, "type", getattr(edge, "label", "RELATED_TO")))))
        
        if source and target:
            formatted_edges.append({
                "source": source,
                "target": target,
                "label": label
            })
            
    return {"nodes": formatted_nodes, "edges": formatted_edges}
