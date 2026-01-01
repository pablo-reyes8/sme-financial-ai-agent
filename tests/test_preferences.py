from sme_agent.services.preferences import is_show_preferences, parse_save_command


def test_parse_save_command():
    assert parse_save_command("guardar: sector=retail") == ("sector", "retail")


def test_parse_save_command_with_recordar():
    assert parse_save_command("recordar ciudad: Bogota") == ("ciudad", "Bogota")


def test_show_preferences():
    assert is_show_preferences("mis datos") is True
    assert is_show_preferences("ver preferencias") is True
