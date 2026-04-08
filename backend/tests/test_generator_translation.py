import app.generator as generator


def test_split_for_translation_respects_max_chunk_size():
    long_text = " ".join(["public-safety"] * 120)

    chunks = generator._split_for_translation(long_text, max_chars=80)

    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)


def test_translate_email_mode_preserves_line_breaks(monkeypatch):
    def fake_translate_chunk(text: str, _google_code: str):
        return f"[HI]{text}"

    monkeypatch.setattr(generator, "_translate_chunk", fake_translate_chunk)

    source = (
        "Subject: Urgent Civic Grievance\n\n"
        "Dear Department,\n"
        "A hazardous condition has been observed in a public area.\n"
    )

    translated = generator._translate(source, "hi")

    assert "\n\n" in translated
    lines = translated.splitlines()
    assert lines[0].startswith("[HI]")
    assert lines[2].startswith("[HI]")
    assert lines[3].startswith("[HI]")


def test_translate_returns_original_when_translation_fails(monkeypatch):
    def fake_translate_chunk(_text: str, _google_code: str):
        return None

    monkeypatch.setattr(generator, "_translate_chunk", fake_translate_chunk)

    source = "Subject: Civic issue\n\nDear Department,\nPlease resolve urgently."
    translated = generator._translate(source, "hi")

    assert translated == source


def test_translate_normalizes_target_language(monkeypatch):
    def fake_translate_chunk(text: str, _google_code: str):
        return f"[HI]{text}"

    monkeypatch.setattr(generator, "_translate_chunk", fake_translate_chunk)

    translated = generator._translate("Please act immediately.", " HI ")
    assert translated == "[HI]Please act immediately."
