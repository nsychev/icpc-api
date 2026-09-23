"""Institutions: the unit's odd wire key, the grid's export path, and the CLI edit."""

from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from icpc.api import common
from icpc.cli import main
from icpc.models.common import Country
from icpc.models.countries import country
from icpc.models.entities import InstitutionUnit
from icpc.models.enums import InstitutionUnitType
from icpc.search import institutions

UNIT: dict[str, Any] = {
    "id": 5695,
    "version": 4,
    "federalTaxId": None,
    "longitude": 69.2833793,
    "latitude": 41.3069797,
    "name": "Westminster International University in Tashkent",
    "abbreviation": None,
    "nativeName": "Toshkent shahridagi Xalqaro Vestminster universiteti",
    "shortName": "Westminster IU Tashkent",
    "homepageUrl": "https://www.wiut.uz/",
    "institution_id": 6187,
    "preserveChanges": None,
    "institutionUnitType": "UNIVERSITY_NO_GRADUATE",
    "mailingAddress": {
        "addressLine1": None,
        "addressLine2": None,
        "addressLine3": None,
        "city": None,
        "state": None,
        "zip": None,
        "country": {
            "id": 230,
            "version": 0,
            "name": "Uzbekistan",
            "a2": "UZ",
            "a3": "UZB",
            "number": 860,
            "currency": "UZS",
            "available": True,
        },
    },
    "socialInfo": {
        "id": 5733,
        "version": 4,
        "twitterName": None,
        "twitterHash": None,
        "facebookPage": None,
        "socialInfo": "",
    },
}


def test_a_unit_round_trips_to_the_exact_wire_shape():
    """``institution_id`` is snake_case on the wire; camelCasing it would drop the link."""
    unit = InstitutionUnit.model_validate(UNIT)
    assert unit.institution_id == 6187
    assert unit.institution_unit_type is InstitutionUnitType.UNIVERSITY_NO_GRADUATE
    assert unit.model_dump(by_alias=True) == UNIT


def test_the_grid_exports_from_a_sibling_path():
    endpoint = institutions()
    q = endpoint.query(filters=[endpoint.fields.inst_name.contains("west")])
    assert endpoint.rows(q).request.path == "/common/institution/search"
    assert endpoint.count(q).request.path == "/common/institution/search/count"
    assert endpoint.export(q).request.path == "/common/institution/export"


class _Fake:
    def __init__(self) -> None:
        self.sent: list[Any] = []

    def __enter__(self) -> _Fake:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def send(self, op: Any) -> Any:
        if op.request.method == "POST":
            self.sent.append(op.request.json)
            return None
        return InstitutionUnit.model_validate(UNIT)


def test_set_unit_edits_nested_keys_and_sends_the_whole_object(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(main, "_client", lambda _ctx: fake)
    result = CliRunner().invoke(
        main.app,
        [
            "-o",
            "json",
            "institution",
            "set-unit",
            "5695",
            "mailingAddress.city=Tashkent",
            "latitude=41.5",
        ],
    )
    assert result.exit_code == 0, result.output
    assert fake.sent == [
        {**UNIT, "latitude": 41.5, "mailingAddress": {**UNIT["mailingAddress"], "city": "Tashkent"}}
    ]
    assert common.update_institution_unit({}).request.path == "/common/institutionunit"


def test_set_unit_refuses_an_unknown_nested_key(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(main, "_client", lambda _ctx: fake)
    result = CliRunner().invoke(
        main.app, ["institution", "set-unit", "5695", "mailingAddress.town=Tashkent"]
    )
    assert result.exit_code == 1
    assert fake.sent == []


def test_password_in_the_environment_skips_the_store(monkeypatch):
    monkeypatch.setenv("ICPC_PASSWORD", "secret")
    seen: list[Any] = []
    monkeypatch.setattr(main.Icpc, "from_password", classmethod(lambda _cls, u: seen.append(u)))
    monkeypatch.setattr(main.Icpc, "from_store", classmethod(lambda *_: 1 / 0))
    CliRunner().invoke(main.app, ["-u", "me@example.com", "whoami"], env={"ICPC_PASSWORD": "x"})
    assert seen == ["me@example.com"]


def test_create_sends_what_the_web_form_sends(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(main, "_client", lambda _ctx: fake)
    result = CliRunner().invoke(
        main.app,
        [
            "institution",
            "create",
            "name=Karshi State Technical University",
            "shortName=Karshi STU",
            "homepageUrl=https://kstu.uz/en",
            "institutionUnitType=UNIVERSITY_NO_GRADUATE",
            "addressLine1=225 Mustaqillik Avenue",
            "city=Karshi",
            "state=Qashqadaryo Region",
            "zip=180100",
            "country=uzbekistan",
        ],
    )
    assert result.exit_code == 0, result.output
    assert fake.sent == [
        {
            "name": "Karshi State Technical University",
            "shortName": "Karshi STU",
            "homepageUrl": "https://kstu.uz/en",
            "institutionUnitType": "UNIVERSITY_NO_GRADUATE",
            "mailingAddress": {
                "addressLine1": "225 Mustaqillik Avenue",
                "city": "Karshi",
                "state": "Qashqadaryo Region",
                "zip": "180100",
                "country": {
                    "available": True,
                    "number": 860,
                    "name": "Uzbekistan",
                    "currency": "UZS",
                    "a2": "UZ",
                    "a3": "UZB",
                    "version": 0,
                    "id": 230,
                    "uuid": "b582bc55-6f01-45c7-b901-e0c39e36279e",
                },
            },
        }
    ]
    assert common.create_suggested_institution({}).request.path == "/common/suggestedinstitution/"


def test_create_refuses_an_unknown_country(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(main, "_client", lambda _ctx: fake)
    args = ["name=Some University", "shortName=SU", "homepageUrl=https://su.example"]
    result = CliRunner().invoke(
        main.app,
        ["institution", "create", *args, "institutionUnitType=HIGH_SCHOOL", "country=Atlantis"],
    )
    assert result.exit_code == 2
    assert fake.sent == []


def test_approve_is_a_put_that_is_never_retried():
    request = common.approve_suggested_institution(69362).request
    assert (request.method, request.path) == ("PUT", "/common/suggestedinstitution/approve/69362")
    assert request.idempotent is False


def test_a_country_sends_uuid_only_when_it_has_one():
    assert country("UZ").uuid == "b582bc55-6f01-45c7-b901-e0c39e36279e"
    from_server = Country.model_validate(UNIT["mailingAddress"]["country"])
    assert from_server.model_dump(by_alias=True) == UNIT["mailingAddress"]["country"]


def test_a_logo_goes_up_as_one_multipart_file_with_its_image_type():
    mime = common.logo_mime("mit.svg", 6)
    request = common.set_institution_logo(1145, "mit.svg", b"<svg/>", mime).request
    assert (request.method, request.path) == ("POST", "/common/logo/institution/1145")
    assert request.files == {"file": ("mit.svg", b"<svg/>", "image/svg+xml")}


@pytest.mark.parametrize(
    ("name", "size"), [("logo.pdf", 10), ("logo.webp", 10), ("logo.png", 3_000_001)]
)
def test_a_logo_the_form_would_refuse_is_refused(name: str, size: int):
    with pytest.raises(ValueError):
        common.logo_mime(name, size)
