from memory import append_message, clear_memory, get_memory


def test_session_memory_isolated():
    clear_memory("a")
    clear_memory("b")
    append_message("a", "user", "hello")
    append_message("b", "user", "different")
    assert get_memory("a")[0]["content"] == "hello"
    assert get_memory("b")[0]["content"] == "different"
