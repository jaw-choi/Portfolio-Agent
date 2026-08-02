from app.core import conversation


def test_get_history_returns_empty_list_when_no_conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation, "CONVERSATIONS_DIR", tmp_path / "conversations")

    assert conversation.get_history("unknown-id") == []


def test_append_turn_then_get_history_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation, "CONVERSATIONS_DIR", tmp_path / "conversations")

    conversation.append_turn("conv1", "user", "질문1")
    conversation.append_turn("conv1", "assistant", "답변1")
    conversation.append_turn("conv1", "user", "질문2")

    assert conversation.get_history("conv1") == [
        {"role": "user", "content": "질문1"},
        {"role": "assistant", "content": "답변1"},
        {"role": "user", "content": "질문2"},
    ]


def test_conversations_are_isolated_by_id(tmp_path, monkeypatch):
    monkeypatch.setattr(conversation, "CONVERSATIONS_DIR", tmp_path / "conversations")

    conversation.append_turn("conv1", "user", "conv1 질문")
    conversation.append_turn("conv2", "user", "conv2 질문")

    assert conversation.get_history("conv1") == [{"role": "user", "content": "conv1 질문"}]
    assert conversation.get_history("conv2") == [{"role": "user", "content": "conv2 질문"}]
