import extract_tagged_text


def test_empty():
    tag = '3'
    text = ''
    result = extract_tagged_text.TaggedFile.get_text_for_tag_from_string(tag, text)
    assert result == []


def test_no_tag():
    tag = '3'
    text = 'jkfadyie k=ew 3098023ljld 3f3f'
    result = extract_tagged_text.TaggedFile.get_text_for_tag_from_string(tag, text)
    assert result == []


def test_tag():
    tag = '3'
    text = r'jkfadyie k=ew <3>tagged stuff</3>3098023ljld 3f3f'
    result = extract_tagged_text.TaggedFile.get_text_for_tag_from_string(tag, text)
    assert result == ['tagged stuff']


def test_nested_tags():
    result = extract_tagged_text.TaggedFile('tests/test_file_1.txt')
    assert len(result.tagged_chunks) == 3
    tags = [t.tags for t in result.tagged_chunks]
    assert set('1') in tags
    assert {'1', '2'} in tags
    assert set('2') in tags
    assert extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'1', '2'}) == ['less stuff']


def test_overlapped_tags():
    result = extract_tagged_text.TaggedFile('tests/test_file_2.txt')
    assert len(result.tagged_chunks) == 4
    tags = [t.tags for t in result.tagged_chunks]
    assert set('1') in tags
    assert {'1', '2'} in tags
    assert set('2') in tags
    assert 'less stuff' in extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'1', '2'})


def test_complex_tags():
    result = extract_tagged_text.TaggedFile('tests/test_file_3.txt')
    # <a>sad<b> dasdas</b> sadsad<b>asda</a>das</b>
    assert len(result.tagged_chunks) == 6
    tags = [t.tags for t in result.tagged_chunks]
    assert set('a') in tags
    assert {'a', 'b'} in tags
    assert set('b') in tags
    assert 'asda' in extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'a', 'b'})
    assert ' dasdas' in extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'a', 'b'})
    assert 'asdadas' in extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'b'})
    assert 'sad' not in extract_tagged_text.find_text_with_tag_set(result.tagged_chunks, {'b'})

