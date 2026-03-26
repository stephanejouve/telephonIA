"""Tests pour le module config."""

from telephonia.config import SVIMessage, get_default_messages


class TestSVIMessage:
    """Tests pour la dataclass SVIMessage."""

    def test_create_message(self):
        msg = SVIMessage(name="test", text="Bonjour", target_duration=10)
        assert msg.name == "test"
        assert msg.text == "Bonjour"
        assert msg.target_duration == 10
        assert msg.background_music is None
        assert msg.music_volume_db == -15.0

    def test_create_message_with_music(self):
        msg = SVIMessage(
            name="test",
            text="Bonjour",
            target_duration=30,
            background_music="/path/to/music.mp3",
            music_volume_db=-20.0,
        )
        assert msg.background_music == "/path/to/music.mp3"
        assert msg.music_volume_db == -20.0


class TestGetDefaultMessages:
    """Tests pour get_default_messages."""

    def test_returns_three_messages(self):
        messages = get_default_messages()
        assert len(messages) == 3

    def test_all_messages_are_svi_message(self):
        messages = get_default_messages()
        for msg in messages:
            assert isinstance(msg, SVIMessage)

    def test_all_messages_have_non_empty_text(self):
        messages = get_default_messages()
        for msg in messages:
            assert msg.text
            assert len(msg.text) > 0

    def test_all_messages_have_positive_duration(self):
        messages = get_default_messages()
        for msg in messages:
            assert msg.target_duration > 0

    def test_message_names(self):
        messages = get_default_messages()
        names = [m.name for m in messages]
        assert names == ["pre_decroche", "attente", "repondeur"]

    def test_pre_decroche_no_music(self):
        messages = get_default_messages()
        pre_decroche = messages[0]
        assert pre_decroche.background_music is None
        assert pre_decroche.target_duration == 10

    def test_attente_with_music(self):
        messages = get_default_messages(music_path="/path/to/music.mp3")
        attente = messages[1]
        assert attente.background_music == "/path/to/music.mp3"
        assert attente.music_volume_db == -15.0
        assert attente.target_duration == 50

    def test_attente_without_music_path(self):
        messages = get_default_messages()
        attente = messages[1]
        assert attente.background_music is None

    def test_repondeur_no_music(self):
        messages = get_default_messages()
        repondeur = messages[2]
        assert repondeur.background_music is None
        assert repondeur.target_duration == 30

    def test_durations_are_coherent(self):
        messages = get_default_messages()
        durations = {m.name: m.target_duration for m in messages}
        assert durations["pre_decroche"] < durations["repondeur"]
        assert durations["repondeur"] < durations["attente"]
