# Chinese Postman Problem

## Strategy

If all nodes in the graph have an even degree, the graph has an Eulerian circuit, which is easy to find.

If not, there will be an even number of nodes with an odd degree. We match up these nodes into pairs, and
connect each pair with the shortest path between them. We add this shortest path to the graph again as additional
edges (each of its segments will be traversed another time). Doing this for each pair will make all the nodes have
an odd degree, giving it an Eulerian circuit.

The challenge is finding the best matching of pairs, which is a standard maximum matching problem.

Once the matching is found and the pairs joined, the problem is reduced to finding an Eulerian circuit.

## Algorithm

1. Start with a bidirectional graph with a single component.
2. Construct a new graph that:
    a. Contains all the odd nodes in the original graph.
    b. Every node is connected to every other node.
    c. The weight of each edge is equal to the shortest distance between the two nodes in the original graph.
3. Find the maximum matching of the above graph, using the [Blossom algorithm][1]
4. For each matched pair, double up the shortest path between them in the original graph, creating an Eulerian graph.
5. With the Eulerian graph, find an Eulerian Circuit.

## Complexity

We assume the number of odd nodes is at least some constant percentage of the total number of nodes, say 10%. Then the
total complexity is `O(V^3)`.


 [1]: http://en.wikipedia.org/wiki/Blossom_algorithm
