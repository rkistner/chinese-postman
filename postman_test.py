#!/usr/bin/env python3
"""
Unit tests for the Chinese Postman Problem solver.
"""

import unittest
import networkx as nx
import postman


class TestPostman(unittest.TestCase):
    """
    Test cases for the postman module.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        pass

    def test_import_csv_graph(self):
        """
        Test importing a graph from CSV.
        """
        with open('test_graph.csv', 'r') as csv_file:
            graph = postman.import_csv_graph(csv_file)
        
        # Check that the graph has nodes and edges
        self.assertGreater(len(graph.nodes()), 0)
        self.assertGreater(len(graph.edges()), 0)

    def test_graph_components(self):
        """
        Test finding connected components.
        """
        with open('test_graph.csv', 'r') as csv_file:
            graph = postman.import_csv_graph(csv_file)
        
        components = postman.graph_components(graph)
        self.assertGreater(len(components), 0)
        # The largest component should have the most edges
        if len(components) > 1:
            for i in range(len(components) - 1):
                self.assertGreaterEqual(
                    components[i].size(),
                    components[i + 1].size()
                )

    def test_odd_graph(self):
        """
        Test constructing the odd-degree graph.
        """
        with open('test_graph.csv', 'r') as csv_file:
            graph = postman.import_csv_graph(csv_file)
        
        components = postman.graph_components(graph)
        component = components[0]
        
        odd = postman.odd_graph(component)
        # All nodes in odd should have odd degree in component
        for node in odd.nodes():
            self.assertEqual(component.degree(node) % 2, 1)

    def test_single_chinese_postman_path(self):
        """
        Test the end-to-end Chinese Postman solution.
        """
        with open('test_graph.csv', 'r') as csv_file:
            graph = postman.import_csv_graph(csv_file)
        
        components = postman.graph_components(graph)
        component = components[0]

        eulerian_graph, nodes = postman.single_chinese_postman_path(component)

        in_length = postman.edge_sum(component) / 1000.0
        path_length = postman.edge_sum(eulerian_graph) / 1000.0
        duplicate_length = path_length - in_length

        # Check that the path is valid
        self.assertGreater(len(nodes), 0)
        self.assertEqual(nodes[0], nodes[-1])  # Circuit should be closed
        
        # Check expected values (from original test)
        self.assertAlmostEqual(in_length, 14.889, places=3)
        self.assertAlmostEqual(path_length, 20.316, places=3)
        self.assertAlmostEqual(duplicate_length, 5.427, places=3)

    def test_eulerian_circuit(self):
        """
        Test that the Eulerian circuit is valid.
        """
        # Create a simple Eulerian graph (all nodes have even degree)
        graph = nx.Graph()
        graph.add_edge(1, 2, weight=1)
        graph.add_edge(2, 3, weight=1)
        graph.add_edge(3, 1, weight=1)
        
        circuit = postman.eulerian_circuit(graph)
        # Circuit should start and end at the same node
        self.assertEqual(circuit[0], circuit[-1])
        # Circuit should visit all edges
        self.assertGreaterEqual(len(circuit), 4)

    def test_pairs(self):
        """
        Test the pairs helper function.
        """
        # Test linear pairs
        self.assertEqual(
            list(postman.pairs([1, 2, 3, 4])),
            [(1, 2), (2, 3), (3, 4)]
        )
        # Test circular pairs
        self.assertEqual(
            list(postman.pairs([1, 2, 3, 4], circular=True)),
            [(1, 2), (2, 3), (3, 4), (4, 1)]
        )


if __name__ == '__main__':
    unittest.main()
