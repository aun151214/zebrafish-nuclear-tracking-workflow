from zebrafish_tracking.io.tracking_csv import parse_parent_ids


def test_parse_parent_ids():
    assert parse_parent_ids("") == ()
    assert parse_parent_ids("NaN") == ()
    assert parse_parent_ids("12") == (12,)
    assert parse_parent_ids("[12, 15]") == (12, 15)
    assert parse_parent_ids("15.0;12.0;15.0") == (12, 15)
