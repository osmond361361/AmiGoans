from app.villages import wikipedia


def test_clean_name_strips_parenthetical_suffix():
    assert wikipedia.clean_name("Anjuna (Ct)") == "Anjuna"
    assert wikipedia.clean_name("Navelim") == "Navelim"


def test_candidate_titles_include_goa_disambiguation():
    candidates = wikipedia._candidate_titles("Navelim (Ct)")
    assert candidates == ["Navelim", "Navelim, Goa", "Navelim (village)"]


def test_split_sections_extracts_history():
    extract = (
        "Aldona is a village in Bardez.\n\n"
        "== History ==\n"
        "Aldona was founded long ago.\n\n"
        "== Demographics ==\n"
        "Aldona has a small population."
    )
    intro, sections = wikipedia._split_sections(extract)
    assert intro == "Aldona is a village in Bardez."
    assert sections["history"] == "Aldona was founded long ago."
    assert sections["demographics"] == "Aldona has a small population."


def test_split_sections_with_no_sections_returns_whole_extract_as_intro():
    intro, sections = wikipedia._split_sections("Just a short stub article.")
    assert intro == "Just a short stub article."
    assert sections == {}


def test_within_goa_accepts_coordinates_inside_the_state():
    assert wikipedia._within_goa([{"lat": 15.4909, "lon": 73.8278}])  # Aldona


def test_within_goa_rejects_coordinates_outside_the_state():
    assert not wikipedia._within_goa([{"lat": 43.9, "lon": 4.8}])  # Provence, France


def test_within_goa_handles_missing_coordinates():
    assert not wikipedia._within_goa(None)
    assert not wikipedia._within_goa([])


def test_truncate_leaves_short_text_untouched():
    assert wikipedia._truncate("Short text.", 100) == "Short text."


def test_truncate_cuts_at_a_sentence_boundary():
    text = "First sentence. " + ("word " * 100) + "Last sentence."
    truncated = wikipedia._truncate(text, 40)
    assert truncated == "First sentence."


def test_fetch_image_attribution_falls_back_to_local_wikipedia_file(monkeypatch):
    # Commons reports the file missing (it was uploaded directly to Wikipedia,
    # never mirrored to Commons) -- must fall back to Wikipedia's own API.
    def fake_query_imageinfo(api_url, filename):
        if api_url == wikipedia.COMMONS_API:
            return None
        return {
            "Artist": {"value": "Some Photographer"},
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
        }

    monkeypatch.setattr(wikipedia, "_query_imageinfo", fake_query_imageinfo)
    attribution, source_url = wikipedia._fetch_image_attribution("Church.jpg")
    assert attribution == "Some Photographer — CC BY-SA 4.0"
    assert source_url == "https://en.wikipedia.org/wiki/File:Church.jpg"


def test_fetch_image_attribution_returns_none_when_neither_source_has_it(monkeypatch):
    monkeypatch.setattr(wikipedia, "_query_imageinfo", lambda api_url, filename: None)
    assert wikipedia._fetch_image_attribution("Church.jpg") == (None, None)


def test_fetch_village_wikipedia_drops_a_photo_it_cannot_credit(monkeypatch):
    def fake_fetch_page(title):
        return {
            "extract": "Pernem is a village in Goa, India.",
            "coordinates": [{"lat": 15.7, "lon": 73.8}],
            "fullurl": "https://en.wikipedia.org/wiki/Pernem",
            "thumbnail": {"source": "https://upload.wikimedia.org/thumb.jpg"},
            "pageimage": "Church.jpg",
        }

    monkeypatch.setattr(wikipedia, "_fetch_page", fake_fetch_page)
    monkeypatch.setattr(wikipedia, "_fetch_image_attribution", lambda filename: (None, None))

    result = wikipedia.fetch_village_wikipedia(
        "Pernem", images_dir="/tmp/should-not-be-used", slug="pernem"
    )
    assert result is not None
    assert result["wiki_image"] is None
    assert result["wiki_image_attribution"] is None


def test_fetch_village_wikipedia_rejects_disambiguation_pages(monkeypatch):
    # A page like "Chandel" that lists a Manipur town, a Manipur district, AND
    # a Goa village together must never be treated as the village's article,
    # even though its text happens to mention "Goa".
    def fake_fetch_page(title):
        return None  # _fetch_page itself filters these out via pageprops

    monkeypatch.setattr(wikipedia, "_fetch_page", fake_fetch_page)
    assert wikipedia.fetch_village_wikipedia("Chandel", taluka="Pernem") is None


def test_fetch_village_wikipedia_rejects_a_same_named_place_outside_goa(monkeypatch):
    def fake_fetch_page(title):
        return {
            "extract": "Canca is a former urban community in Provence-Alpes-Cote d'Azur, France.",
            "coordinates": [{"lat": 43.9, "lon": 4.8}],
            "fullurl": "https://en.wikipedia.org/wiki/Canca",
            "thumbnail": None,
            "pageimage": None,
        }

    monkeypatch.setattr(wikipedia, "_fetch_page", fake_fetch_page)
    assert wikipedia.fetch_village_wikipedia("Canca") is None


def test_fetch_village_wikipedia_matches_a_confirmed_goa_village(monkeypatch):
    def fake_fetch_page(title):
        return {
            "extract": (
                "Aldona is a village in the Bardez taluka of Goa, India.\n\n"
                "== History ==\nAldona has a long history."
            ),
            "coordinates": [{"lat": 15.4909, "lon": 73.8278}],
            "fullurl": "https://en.wikipedia.org/wiki/Aldona",
            "thumbnail": None,
            "pageimage": None,
        }

    monkeypatch.setattr(wikipedia, "_fetch_page", fake_fetch_page)
    result = wikipedia.fetch_village_wikipedia("Aldona")
    assert result["wiki_url"] == "https://en.wikipedia.org/wiki/Aldona"
    assert "Bardez taluka" in result["wiki_summary"]
    assert result["wiki_history"] == "Aldona has a long history."


def test_fetch_village_wikipedia_rejects_duplicate_named_village_in_wrong_taluka(monkeypatch):
    def fake_fetch_page(title):
        return {
            "extract": "Navelim is a census town in the Salcete taluka of Goa, India.",
            "coordinates": [{"lat": 15.15, "lon": 73.97}],
            "fullurl": "https://en.wikipedia.org/wiki/Navelim",
            "thumbnail": None,
            "pageimage": None,
        }

    monkeypatch.setattr(wikipedia, "_fetch_page", fake_fetch_page)

    matching = wikipedia.fetch_village_wikipedia(
        "Navelim", taluka="Salcete", require_taluka_match=True
    )
    assert matching is not None

    mismatching = wikipedia.fetch_village_wikipedia(
        "Navelim", taluka="Bicholim", require_taluka_match=True
    )
    assert mismatching is None
