import asyncio
import os
import cognee
from cognee.infrastructure.databases.graph.get_graph_engine import get_graph_engine

async def main():
    engine = await get_graph_engine()
    data = await engine.get_graph_data()
    print("Type of data:", type(data))
    if isinstance(data, tuple):
        nodes, edges = data
        print("Nodes count:", len(nodes))
        print("Edges count:", len(edges))
        if len(nodes) > 0:
            print("Node 0:", nodes[0])
        if len(edges) > 0:
            print("Edge 0:", edges[0])
    elif hasattr(data, "nodes") and hasattr(data, "edges"):
        print("Nodes count:", len(data.nodes))
        print("Edges count:", len(data.edges))
        if len(data.nodes) > 0:
            print("Node 0:", data.nodes[0])
        if len(data.edges) > 0:
            print("Edge 0:", data.edges[0])
    else:
        print("Data representation:", data)

if __name__ == "__main__":
    asyncio.run(main())
