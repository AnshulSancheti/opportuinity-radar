import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from sqlalchemy import select
from app.models import Hackathon
from app.scrapers.hackathons.mlh import parse_mlh_page
from app.scrapers.hackathons.devpost import DevpostScraper, parse_devpost_event, submission_dates
from app.services.hackathon_service import discoverable_hackathons, reconcile_hackathon_source, upsert_hackathon
from tests.test_accounts import clients, register, action


def test_mlh_reads_provider_dates_and_location_without_guessing():
    event = {"id": "event-1", "name": "Example Hack", "startsAt": "2027-01-09T10:00:00Z", "endsAt": "2027-01-10T20:00:00Z", "websiteUrl": "https://example.com/hack", "formatType": "physical", "venueAddress": {"city": "Delhi", "state": "Delhi", "country": "IN"}}
    html = '<script data-page="app" type="application/json">' + json.dumps({"props": {"upcomingEvents": [event]}}) + '</script>'
    result = parse_mlh_page(html)[0]
    assert result["name"] == "Example Hack" and result["source_event_id"] == "event-1"
    assert result["start_date"].year == 2027 and result["end_date"].day == 10
    assert result["location"] == "Delhi, IN" and result["mode"] == "offline"
    assert "registration_deadline" not in result and "organizer" not in result


def test_mlh_layout_failure_never_becomes_fake_or_empty_success():
    with pytest.raises(ValueError): parse_mlh_page('<article>Random page content</article>')
    with pytest.raises(ValueError): parse_mlh_page('<script data-page="app" type="application/json">{"props":{"upcomingEvents":[]}}</script>')


@pytest.mark.parametrize("value,start,end", [("Aug 26 - Oct 30, 2026",(2026,8,26),(2026,10,30)), ("Oct 27 - 30, 2026",(2026,10,27),(2026,10,30)), ("Dec 20 - Jan 5, 2027",(2026,12,20),(2027,1,5)), ("Dec 20, 2026 - Jan 5, 2027",(2026,12,20),(2027,1,5)), ("Nov 02, 2026",None,(2026,11,2))])
def test_submission_date_formats(value,start,end):
    actual_start, actual_end = submission_dates(value)
    assert (actual_start.date().timetuple()[:3] if actual_start else None) == start
    assert actual_end.date().timetuple()[:3] == end
    assert actual_end.hour == 23


def test_devpost_retains_source_fields_without_inventing_registration_deadline():
    item = parse_devpost_event({"id":123,"title":"Test AI Hack", "url":"https://test.devpost.com/", "submission_period_dates":"Oct 27 - Nov 3, 2026", "open_state":"open", "displayed_location":{"location":"Online"}, "themes":[{"name":"AI"}], "prize_amount":"$<span>5,000</span>", "organization_name":"Example"})
    assert item["prize_text"] == "$5,000" and item["themes"] == ["AI"]
    assert item["mode"] == "online" and item["application_status"] == "open"
    assert "registration_deadline" not in item
    with pytest.raises(ValueError): submission_dates("Dates to be announced")


def test_devpost_checks_all_pages_and_rejects_partial_results(monkeypatch):
    scraper = DevpostScraper(None)
    item = {"id":123,"title":"Test Hack", "url":"https://test.devpost.com/", "submission_period_dates":"Nov 02, 2026", "open_state":"open"}
    pages = [{"hackathons":[item],"meta":{"total_count":2,"per_page":1}}, {"hackathons":[dict(item,id=124)],"meta":{"total_count":2,"per_page":1}}]
    monkeypatch.setattr(scraper,"fetch_url",lambda url: SimpleNamespace(json=lambda: pages[int(url.split('page=')[1].split('&')[0])-1]))
    assert len(scraper.fetch()) == 2
    pages[1] = {"hackathons":[],"meta":{"total_count":2,"per_page":1}}
    with pytest.raises(ValueError): scraper.fetch()


def live_item(identity, end, **extra):
    return {"source_event_id":identity, "name":"Verified example", "source_name":"mlh", "url":"https://example.com/annual", "start_date":end-timedelta(days=1), "end_date":end, **extra}


def test_upsert_corrects_fields_and_preserves_distinct_editions(clients):
    _, _, db, _, _ = clients
    end = datetime.now(timezone.utc)+timedelta(days=30)
    assert upsert_hackathon(db,live_item("test-edition-a",end)) == "inserted"
    assert upsert_hackathon(db,live_item("test-edition-a",end, name="Corrected title", location="Delhi", prize_text="$100")) == "updated"
    assert upsert_hackathon(db,live_item("test-edition-b",end+timedelta(days=365))) == "inserted"
    rows = db.scalars(select(Hackathon).where(Hackathon.url=="https://example.com/annual")).all()
    assert len(rows)==2 and any(r.name=="Corrected title" and r.location=="Delhi" for r in rows)
    assert upsert_hackathon(db,{"source_name":"static_list", "name":"Unverified", "url":"https://example.com"}) == "skipped"


def test_expiration_staleness_and_seed_filtering_keep_saved_records(clients):
    a, _, db, _, _ = clients
    register(a)
    now = datetime.now(timezone.utc)
    for identity, end in [("test-future",now+timedelta(days=5)),("test-past",now-timedelta(days=1))]: upsert_hackathon(db,live_item(identity,end))
    rows = db.scalars(select(Hackathon).where(Hackathon.url=="https://example.com/annual")).all()
    future = next(r for r in rows if r.status=="active")
    past = next(r for r in rows if r.status=="expired")
    action(a,"hackathon",past.id); action(a,"hackathon",past.id,"applied")
    assert db.scalar(select(Hackathon.id).where(discoverable_hackathons(),Hackathon.id==past.id)) is None
    assert any(r["item_id"]==past.id for r in a.get('/api/v1/actions/saved').json())
    assert any(r["item_id"]==past.id for r in a.get('/api/v1/actions/saved?action=applied').json())
    assert db.scalar(select(Hackathon.id).where(discoverable_hackathons(now+timedelta(days=6)),Hackathon.id==future.id)) is None
    future.last_seen_at=now-timedelta(hours=49); db.commit()
    assert db.scalar(select(Hackathon.id).where(discoverable_hackathons(),Hackathon.id==future.id)) is None
    future.last_seen_at=now; future.source_name="static_list"; db.commit()
    assert db.scalar(select(Hackathon.id).where(discoverable_hackathons(),Hackathon.id==future.id)) is None


def test_reconcile_missing_listing_preserves_its_saved_record(clients):
    a, _, db, _, _ = clients
    register(a)
    end=datetime.now(timezone.utc)+timedelta(days=5)
    upsert_hackathon(db,live_item("test-disappeared",end))
    row=db.scalar(select(Hackathon).where(Hackathon.url=="https://example.com/annual"))
    action(a,"hackathon",row.id)
    reconcile_hackathon_source(db,"mlh",datetime.now(timezone.utc)+timedelta(seconds=1))
    db.refresh(row)
    assert row.status=="unavailable"
    assert any(r["item_id"]==row.id for r in a.get('/api/v1/actions/saved').json())


@pytest.mark.parametrize("state,age_minutes,expected", [("success",30,False),("success",361,True),("failed",10,False),("failed",16,True),("running",5,False),("running",31,True)])
def test_refresh_interval_and_failure_backoff(monkeypatch,state,age_minutes,expected):
    from contextlib import nullcontext
    from app.services import hackathon_refresh
    now=datetime.now(timezone.utc)
    checked=now-timedelta(minutes=age_minutes)
    row=SimpleNamespace(status=state, started_at=checked, finished_at=None if state=="running" else checked)
    monkeypatch.setattr(hackathon_refresh,"SessionLocal",lambda: nullcontext(SimpleNamespace(scalar=lambda query: row)))
    monkeypatch.setattr(hackathon_refresh,"load_sources",lambda: {"hackathons":{"mlh":{"enabled":True},"devpost":{"enabled":True}}})
    assert hackathon_refresh.refresh_due(now)==expected


def test_closed_registration_excluded_even_if_event_is_in_future(clients):
    _, _, db, _, _=clients
    now=datetime.now(timezone.utc)
    upsert_hackathon(db,live_item("test-registration-closed",now+timedelta(days=10),registration_deadline=now-timedelta(days=1)))
    row=db.scalar(select(Hackathon).where(Hackathon.url=="https://example.com/annual"))
    assert db.scalar(select(Hackathon.id).where(discoverable_hackathons(),Hackathon.id==row.id)) is None
