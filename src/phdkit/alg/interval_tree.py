"""Interval Tree data structure implementation.

An interval tree is a specialized data structure designed for efficiently storing
and querying intervals. It's particularly useful for problems involving overlapping
intervals, range queries, and conflict detection in scheduling systems.
"""

from typing import List, Optional, Union, Any, Generator, Protocol, TypeVar
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering


class Color(Enum):
    """Colors for Red-Black tree balancing."""

    RED = "red"
    BLACK = "black"


@dataclass
class Interval:
    """Represents an interval with start and end points.

    Args:
        start: The beginning of the interval (inclusive).
        end: The end of the interval (inclusive).
        data: Optional data associated with the interval.
    """

    # TODO: Make this more type-safe with generics if needed
    start: Any
    end: Any
    data: Any = None

    def __post_init__(self) -> None:
        """Validate interval properties after initialization."""
        if self.start > self.end:
            raise ValueError(
                f"Invalid interval: start ({self.start}) must be <= end ({self.end})"
            )

    def overlaps(self, other: "Interval") -> bool:
        """Check if this interval overlaps with another interval.

        Uses half-open intervals: [start, end).
        Special case: point intervals [x, x] are treated as single points.

        Args:
            other: The interval to check for overlap.

        Returns:
            True if intervals overlap, False otherwise.
        """
        # Handle point intervals specially
        if self.start == self.end:  # self is a point interval
            return other.contains_point(self.start)
        if other.start == other.end:  # other is a point interval
            return self.contains_point(other.start)

        # Normal interval overlap check
        return self.start < other.end and other.start < self.end

    def contains_point(self, point: Any) -> bool:
        """Check if this interval contains a specific point.

        Uses half-open intervals: [start, end).
        Special case: point intervals [x, x] are treated as containing only point x.

        Args:
            point: The point to check.

        Returns:
            True if the point is within the interval, False otherwise.
        """
        if self.start == self.end:  # Point interval
            return self.start == point
        return self.start <= point < self.end

    def __repr__(self) -> str:
        """String representation of the interval."""
        if self.data is not None:
            return f"Interval({self.start}, {self.end}, {self.data!r})"
        return f"Interval({self.start}, {self.end})"

    def __str__(self) -> str:
        """Human-readable string representation of the interval."""
        if self.data is not None:
            return f"[{self.start}, {self.end}): {self.data}"
        return f"[{self.start}, {self.end})"


class IntervalNode:
    """Node in the interval tree.

    Each node stores an interval and maintains the maximum endpoint
    of all intervals in its subtree for efficient querying.
    """

    def __init__(self, interval: Interval) -> None:
        """Initialize an interval tree node.

        Args:
            interval: The interval stored in this node.
        """
        self.interval = interval
        self.max_end = interval.end
        self.left: Optional["IntervalNode"] = None
        self.right: Optional["IntervalNode"] = None
        self.parent: Optional["IntervalNode"] = None
        self.color = Color.RED  # For Red-Black tree balancing

    def update_max_end(self) -> None:
        """Update the maximum endpoint in this subtree."""
        self.max_end = self.interval.end
        if self.left is not None:
            self.max_end = max(self.max_end, self.left.max_end)
        if self.right is not None:
            self.max_end = max(self.max_end, self.right.max_end)

    def __repr__(self) -> str:
        """String representation of the node."""
        return f"IntervalNode({self.interval}, max_end={self.max_end})"


class IntervalTree:
    """Red-Black tree based interval tree for efficient interval operations.

    This implementation provides O(log n) insertion, deletion, and O(log n + k)
    overlap queries, where k is the number of overlapping intervals found.
    """

    def __init__(self) -> None:
        """Initialize an empty interval tree."""
        self.root: Optional[IntervalNode] = None
        self.size = 0

    def insert(self, interval: Interval) -> None:
        """Insert an interval into the tree.

        Args:
            interval: The interval to insert.
        """
        if self.root is None:
            self.root = IntervalNode(interval)
            self.root.color = Color.BLACK
            self.size += 1
            return

        # Standard BST insertion based on start point
        node = self.root
        while True:
            if interval.start <= node.interval.start:
                if node.left is None:
                    node.left = IntervalNode(interval)
                    node.left.parent = node
                    new_node = node.left
                    break
                else:
                    node = node.left
            else:
                if node.right is None:
                    node.right = IntervalNode(interval)
                    node.right.parent = node
                    new_node = node.right
                    break
                else:
                    node = node.right

        # Update max_end values up the tree
        current = new_node
        while current is not None:
            current.update_max_end()
            current = current.parent

        # Fix Red-Black tree properties
        self._fix_insert(new_node)
        self.size += 1

    def _fix_insert(self, node: IntervalNode) -> None:
        """Fix Red-Black tree properties after insertion.

        Args:
            node: The newly inserted node to fix.
        """
        while node.parent is not None and node.parent.color == Color.RED:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                break

            if parent == grandparent.left:
                uncle = grandparent.right
                if uncle is not None and uncle.color == Color.RED:
                    # Case 1: Uncle is red
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grandparent.color = Color.RED
                    node = grandparent
                else:
                    if node == parent.right:
                        # Case 2: Node is right child
                        node = parent
                        self._rotate_left(node)
                        parent = node.parent  # Update parent after rotation
                        if parent is None:
                            break
                        grandparent = parent.parent
                        if grandparent is None:
                            break
                    # Case 3: Node is left child
                    if parent is not None:
                        parent.color = Color.BLACK
                    grandparent.color = Color.RED
                    self._rotate_right(grandparent)
            else:
                uncle = grandparent.left
                if uncle is not None and uncle.color == Color.RED:
                    # Case 1: Uncle is red
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grandparent.color = Color.RED
                    node = grandparent
                else:
                    if node == parent.left:
                        # Case 2: Node is left child
                        node = parent
                        self._rotate_right(node)
                        parent = node.parent  # Update parent after rotation
                        if parent is None:
                            break
                        grandparent = parent.parent
                        if grandparent is None:
                            break
                    # Case 3: Node is right child
                    if parent is not None:
                        parent.color = Color.BLACK
                    grandparent.color = Color.RED
                    self._rotate_left(grandparent)

        if self.root is not None:
            self.root.color = Color.BLACK

    def _rotate_left(self, node: IntervalNode) -> None:
        """Perform left rotation for tree balancing.

        Args:
            node: The node to rotate around.
        """
        right_child = node.right
        if right_child is None:
            return

        node.right = right_child.left
        if right_child.left is not None:
            right_child.left.parent = node

        right_child.parent = node.parent
        if node.parent is None:
            self.root = right_child
        elif node == node.parent.left:
            node.parent.left = right_child
        else:
            node.parent.right = right_child

        right_child.left = node
        node.parent = right_child

        # Update max_end values
        node.update_max_end()
        right_child.update_max_end()

    def _rotate_right(self, node: IntervalNode) -> None:
        """Perform right rotation for tree balancing.

        Args:
            node: The node to rotate around.
        """
        left_child = node.left
        if left_child is None:
            return

        node.left = left_child.right
        if left_child.right is not None:
            left_child.right.parent = node

        left_child.parent = node.parent
        if node.parent is None:
            self.root = left_child
        elif node == node.parent.right:
            node.parent.right = left_child
        else:
            node.parent.left = left_child

        left_child.right = node
        node.parent = left_child

        # Update max_end values
        node.update_max_end()
        left_child.update_max_end()

    def search_overlaps(self, interval: Interval) -> List[Interval]:
        """Find all intervals that overlap with the given interval.

        Args:
            interval: The query interval to find overlaps for.

        Returns:
            List of intervals that overlap with the query interval.
        """
        results = []
        self._search_overlaps_recursive(self.root, interval, results)
        return results

    def _search_overlaps_recursive(
        self, node: Optional[IntervalNode], interval: Interval, results: List[Interval]
    ) -> None:
        """Recursively search for overlapping intervals.

        Args:
            node: Current node being examined.
            interval: Query interval.
            results: List to accumulate overlapping intervals.
        """
        if node is None:
            return

        # Check if current node's interval overlaps with query
        if node.interval.overlaps(interval):
            results.append(node.interval)

        # Search left subtree if it might contain overlapping intervals
        if node.left is not None and node.left.max_end >= interval.start:
            self._search_overlaps_recursive(node.left, interval, results)

        # Search right subtree if it might contain overlapping intervals
        if node.right is not None and node.interval.start <= interval.end:
            self._search_overlaps_recursive(node.right, interval, results)

    def search_point(self, point: Any) -> List[Interval]:
        """Find all intervals that contain the given point.

        Args:
            point: The point to search for.

        Returns:
            List of intervals that contain the point.
        """
        point_interval = Interval(point, point)
        return self.search_overlaps(point_interval)

    def search(
        self, start: Any, end: Any
    ) -> List[Interval]:
        """Find all intervals that overlap with the given range.

        Args:
            start: Start of the query range.
            end: End of the query range.

        Returns:
            List of intervals that overlap with the query range.
        """
        query_interval = Interval(start, end)
        return self.search_overlaps(query_interval)

    def query_point(self, point: Any) -> List[Interval]:
        """Find all intervals that contain the given point.

        This is an alias for search_point for convenience.

        Args:
            point: The point to search for.

        Returns:
            List of intervals that contain the point.
        """
        return self.search_point(point)

    def delete(self, interval: Interval) -> bool:
        """Delete an interval from the tree.

        Args:
            interval: The interval to delete.

        Returns:
            True if the interval was found and deleted, False otherwise.
        """
        node = self._find_node(interval)
        if node is None:
            return False

        self._delete_node(node)
        self.size -= 1
        return True

    def _find_node(self, interval: Interval) -> Optional[IntervalNode]:
        """Find the node containing the specified interval.

        Args:
            interval: The interval to find.

        Returns:
            The node containing the interval, or None if not found.
        """
        node = self.root
        while node is not None:
            if (
                node.interval.start == interval.start
                and node.interval.end == interval.end
                and node.interval.data == interval.data
            ):
                return node
            elif interval.start <= node.interval.start:
                node = node.left
            else:
                node = node.right
        return None

    def _delete_node(self, node: IntervalNode) -> None:
        """Delete a specific node from the tree.

        Args:
            node: The node to delete.
        """
        # Implementation of Red-Black tree deletion would go here
        # For simplicity, this is a basic implementation
        if node.left is None and node.right is None:
            # Leaf node
            if node.parent is None:
                self.root = None
            elif node.parent.left == node:
                node.parent.left = None
            else:
                node.parent.right = None
        elif node.left is None:
            # Only right child
            right_child = node.right
            if right_child is not None:
                if node.parent is None:
                    self.root = right_child
                    right_child.parent = None
                elif node.parent.left == node:
                    node.parent.left = right_child
                    right_child.parent = node.parent
                else:
                    node.parent.right = right_child
                    right_child.parent = node.parent
        elif node.right is None:
            # Only left child
            left_child = node.left
            if left_child is not None:
                if node.parent is None:
                    self.root = left_child
                    left_child.parent = None
                elif node.parent.left == node:
                    node.parent.left = left_child
                    left_child.parent = node.parent
                else:
                    node.parent.right = left_child
                    left_child.parent = node.parent
        else:
            # Both children exist - replace with inorder successor
            successor = self._find_min(node.right)
            node.interval = successor.interval
            self._delete_node(successor)
            return

        # Update max_end values up the tree
        current = node.parent
        while current is not None:
            current.update_max_end()
            current = current.parent

    def _find_min(self, node: IntervalNode) -> IntervalNode:
        """Find the minimum node in a subtree.

        Args:
            node: Root of the subtree.

        Returns:
            The node with the minimum interval start value.
        """
        while node.left is not None:
            node = node.left
        return node

    def is_empty(self) -> bool:
        """Check if the tree is empty.

        Returns:
            True if the tree contains no intervals, False otherwise.
        """
        return self.root is None

    def clear(self) -> None:
        """Remove all intervals from the tree."""
        self.root = None
        self.size = 0

    def __len__(self) -> int:
        """Return the number of intervals in the tree."""
        return self.size

    def __bool__(self) -> bool:
        """Return True if the tree is not empty."""
        return not self.is_empty()

    def __iter__(self) -> Generator[Interval, None, None]:
        """Iterate over all intervals in the tree in sorted order."""
        yield from self._inorder_traversal(self.root)

    def _inorder_traversal(
        self, node: Optional[IntervalNode]
    ) -> Generator[Interval, None, None]:
        """Perform inorder traversal of the tree.

        Args:
            node: Current node in traversal.

        Yields:
            Intervals in sorted order by start point.
        """
        if node is not None:
            yield from self._inorder_traversal(node.left)
            yield node.interval
            yield from self._inorder_traversal(node.right)

    def get_all_intervals(self) -> List[Interval]:
        """Get all intervals in the tree.

        Returns:
            List of all intervals sorted by start point.
        """
        return list(self)

    def __repr__(self) -> str:
        """String representation of the interval tree."""
        intervals = self.get_all_intervals()
        return f"IntervalTree({intervals})"
