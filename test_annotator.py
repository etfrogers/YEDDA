from YEDDA_Annotator import pos_to_tk_coords


def test_empty():
    pos = 0
    content = ''
    loc = '1.0'
    result = pos_to_tk_coords(pos, content)
    assert result == loc


def test_zero_pos():
    pos = 0
    content = 'yadda\nyadda'
    loc = '1.0'
    result = pos_to_tk_coords(pos, content)
    assert result == loc
