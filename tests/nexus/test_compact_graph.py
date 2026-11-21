from nexus_ui.widgets.compact_graph import graph_scale


def test_empty_scale():
    assert graph_scale([]) == 1


def test_low_utilization():
    assert graph_scale([0.1, 0.3, 0.6]) == 1


def test_memory_utilization():
    assert graph_scale([4.1, 4.2, 4.5]) == 5


def test_medium_utilization():
    assert graph_scale([12, 20, 24]) == 25


def test_high_utilization():
    assert graph_scale([80, 95, 100]) == 100


def test_invalid_samples():
    assert graph_scale([
        float("nan"),
        float("inf"),
        -5,
        1,
    ]) == 1


def test_out_of_range():
    assert graph_scale([120]) == 100
