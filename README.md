# phdkit - Scripting Utilities for PhD Students

## Overview

TODO

## Features

### Algorithms

#### Interval Tree

A high-performance Red-Black tree based interval tree implementation for efficiently managing and querying overlapping intervals.

**Key Features:**

- O(log n) insertion and deletion
- O(log n + k) overlap queries (where k is the number of results)
- Half-open interval semantics [start, end)
- Support for point queries and range queries
- Generic data payload support

**Example Usage:**

```python
from phdkit.alg import IntervalTree, Interval

# Create intervals
tree = IntervalTree()
tree.insert(Interval(1, 5, "Task A"))
tree.insert(Interval(3, 8, "Task B"))

# Find overlapping intervals
overlaps = tree.search(2, 6)  # Returns intervals overlapping [2, 6)

# Find intervals containing a point
containing = tree.query_point(4)  # Returns intervals containing point 4
```

### Logging and email notification

TODO

### Configuration management

TODO

### Task batching

TODO

### Declaratively plotting

TODO

### Other utilities

TODO

## Development

TODO
