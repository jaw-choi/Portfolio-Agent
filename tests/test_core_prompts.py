from app.core.prompts import build_user_message


def test_build_user_message_without_context_instructs_dont_know_fallback():
    result = build_user_message("싱글톤이 뭐야?", [])

    assert result.endswith("질문: 싱글톤이 뭐야?")
    assert "모른다" in result


def test_build_user_message_includes_context_and_question():
    chunks = [
        {
            "document_id": "doc1",
            "text": "싱글톤은 인스턴스를 하나만 생성한다.",
            "filename": "cs_singleton.md",
            "source_url": None,
        },
        {
            "document_id": "doc2",
            "text": "블로그 글 내용",
            "filename": None,
            "source_url": "https://example.tistory.com/1",
        },
    ]

    result = build_user_message("싱글톤이 뭐야?", chunks)

    assert "cs_singleton.md" in result
    assert "싱글톤은 인스턴스를 하나만 생성한다." in result
    assert "https://example.tistory.com/1" in result
    assert "블로그 글 내용" in result
    assert result.endswith("질문: 싱글톤이 뭐야?")


def test_build_user_message_falls_back_to_document_id_when_no_name():
    chunks = [{"document_id": "doc1", "text": "내용", "filename": None, "source_url": None}]

    result = build_user_message("질문", chunks)

    assert "doc1" in result
