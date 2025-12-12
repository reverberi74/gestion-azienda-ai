from app.core.config import get_settings


def test_settings_basic_attributes():
    settings = get_settings()

    # Controlliamo che i campi principali esistano e abbiano il tipo giusto
    assert isinstance(settings.MODEL_NAME, str)
    assert isinstance(settings.DEVICE, str)
    assert isinstance(settings.MAX_TOKENS, int)

    assert isinstance(settings.HOST, str)
    assert isinstance(settings.PORT, int)
    assert isinstance(settings.DEBUG, bool)


def test_allowed_origins_list_parsing():
    settings = get_settings()
    origins_list = settings.allowed_origins_list

    # Deve essere una lista (anche se vuota)
    assert isinstance(origins_list, list)
    # Se in .env hai settato ALLOWED_ORIGINS, ogni voce deve essere stringa
    for origin in origins_list:
        assert isinstance(origin, str)
