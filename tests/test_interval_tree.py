"""Tests for the Interval Tree implementation."""

import pytest
from phdkit.alg.interval_tree import IntervalTree, Interval


class TestInterval:
    """Test cases for the Interval class."""

    def test_interval_creation(self) -> None:
        """Test creating an interval."""
        interval = Interval(1, 5, "data")
        assert interval.start == 1
        assert interval.end == 5
        assert interval.data == "data"

    def test_interval_overlaps(self) -> None:
        """Test interval overlap detection."""
        interval1 = Interval(1, 5)
        interval2 = Interval(3, 7)
        interval3 = Interval(6, 10)

        assert interval1.overlaps(interval2)
        assert interval2.overlaps(interval1)
        assert interval2.overlaps(interval3)
        assert not interval1.overlaps(interval3)

    def test_interval_equality(self) -> None:
        """Test interval equality."""
        interval1 = Interval(1, 5, "data")
        interval2 = Interval(1, 5, "data")
        interval3 = Interval(1, 5, "other")

        assert interval1 == interval2
        assert interval1 != interval3

    def test_interval_string_representation(self) -> None:
        """Test interval string representation."""
        interval = Interval(1, 5, "test")
        assert str(interval) == "[1, 5): test"


class TestIntervalTree:
    """Test cases for the IntervalTree class."""

    def test_empty_tree(self) -> None:
        """Test operations on an empty tree."""
        tree = IntervalTree()
        assert tree.search(1, 5) == []
        assert tree.query_point(3) == []
        assert not tree.delete(Interval(1, 5))

    def test_single_interval(self) -> None:
        """Test tree with a single interval."""
        tree = IntervalTree()
        interval = Interval(1, 5, "test")

        tree.insert(interval)

        # Test search
        results = tree.search(3, 4)
        assert len(results) == 1
        assert results[0] == interval

        # Test point query
        point_results = tree.query_point(3)
        assert len(point_results) == 1
        assert point_results[0] == interval

        # Test no overlap
        assert tree.search(6, 10) == []
        assert tree.query_point(6) == []

    def test_multiple_intervals(self) -> None:
        """Test tree with multiple intervals."""
        tree = IntervalTree()
        intervals = [
            Interval(1, 3, "A"),
            Interval(2, 5, "B"),
            Interval(4, 7, "C"),
            Interval(6, 9, "D"),
            Interval(8, 10, "E"),
        ]

        for interval in intervals:
            tree.insert(interval)

        # Test overlapping search
        results = tree.search(2, 6)
        expected_data = {"A", "B", "C"}  # D [6,9) doesn't overlap with [2,6)
        result_data = {interval.data for interval in results}
        assert result_data == expected_data

        # Test point query
        point_results = tree.query_point(5)
        expected_point_data = {"B"}  # Only B [2,5) contains point 5? No, 5 is not < 5
        # Actually, point 5 is not contained in [2,5) since it's half-open
        # Let's test point 4 instead which should be in B and C
        point_results = tree.query_point(4)
        expected_point_data = {"B", "C"}  # B [2,5) and C [4,7) contain point 4
        point_result_data = {interval.data for interval in point_results}
        assert point_result_data == expected_point_data

    def test_deletion(self) -> None:
        """Test interval deletion."""
        tree = IntervalTree()
        intervals = [Interval(1, 3, "A"), Interval(2, 5, "B"), Interval(4, 7, "C")]

        for interval in intervals:
            tree.insert(interval)

        # Delete an interval
        assert tree.delete(intervals[1])  # Delete B

        # Verify deletion
        results = tree.search(1, 10)
        result_data = {interval.data for interval in results}
        assert result_data == {"A", "C"}

        # Try to delete non-existent interval
        assert not tree.delete(Interval(10, 15))

    def test_edge_cases(self) -> None:
        """Test edge cases."""
        tree = IntervalTree()

        # Test point intervals - in half-open intervals, we use [x, x+1) for a single point
        point_interval = Interval(5, 6, "point")  # Represents point 5
        tree.insert(point_interval)

        results = tree.query_point(5)
        assert len(results) == 1
        assert results[0] == point_interval

        # Test that point 6 is not included (half-open interval)
        results = tree.query_point(6)
        assert len(results) == 0

        # Test adjacent intervals (should not overlap)
        tree = IntervalTree()
        interval1 = Interval(1, 3)
        interval2 = Interval(3, 5)
        tree.insert(interval1)
        tree.insert(interval2)

        # Point 3 should only match interval2 (intervals are [start, end))
        results = tree.query_point(3)
        assert len(results) == 1
        assert results[0] == interval2

    def test_duplicate_intervals(self) -> None:
        """Test handling of duplicate intervals."""
        tree = IntervalTree()
        interval1 = Interval(1, 5, "first")
        interval2 = Interval(1, 5, "second")

        tree.insert(interval1)
        tree.insert(interval2)

        results = tree.search(1, 5)
        assert len(results) == 2
        result_data = {interval.data for interval in results}
        assert result_data == {"first", "second"}

    def test_large_dataset(self) -> None:
        """Test with a larger dataset to verify performance and correctness."""
        tree = IntervalTree()
        intervals = []

        # Create intervals with various overlaps
        for i in range(0, 100, 5):
            interval = Interval(i, i + 10, f"interval_{i}")
            intervals.append(interval)
            tree.insert(interval)

        # Test search in the middle
        results = tree.search(45, 55)
        # Should find intervals that overlap with [45, 55)
        expected_count = 0
        for interval in intervals:
            if interval.start < 55 and interval.end > 45:
                expected_count += 1

        assert len(results) == expected_count

        # Test point query
        point_results = tree.query_point(50)
        expected_point_count = 0
        for interval in intervals:
            if interval.start <= 50 < interval.end:
                expected_point_count += 1

        assert len(point_results) == expected_point_count

    def test_stress_operations(self) -> None:
        """Test various operations in sequence."""
        tree = IntervalTree()

        # Insert intervals
        intervals = [
            Interval(1, 10, "A"),
            Interval(5, 15, "B"),
            Interval(12, 20, "C"),
            Interval(18, 25, "D"),
        ]

        for interval in intervals:
            tree.insert(interval)

        # Perform various searches
        assert len(tree.search(0, 1)) == 0
        assert len(tree.search(1, 2)) == 1
        assert len(tree.search(8, 12)) == 2
        assert len(tree.search(15, 18)) == 1
        assert len(tree.search(22, 30)) == 1

        # Delete and verify
        tree.delete(intervals[1])  # Remove B
        assert len(tree.search(8, 12)) == 1  # Should only find A now

        # Point queries
        assert len(tree.query_point(5)) == 1  # Only A
        assert len(tree.query_point(15)) == 1  # Only C
        assert len(tree.query_point(20)) == 1  # Only D


if __name__ == "__main__":
    pytest.main([__file__])
