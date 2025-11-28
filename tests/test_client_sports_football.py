"""
Tests for FootballClient with mocked HTTP responses.
"""

from datetime import datetime, timedelta

import pytest
import responses

from src.clients.sports.football import FootballClient
from src.config import Config


@pytest.fixture
def mock_team_response():
    """Sample football-data.org team response."""
    return {
        "id": 57,
        "name": "Arsenal FC",
        "shortName": "Arsenal",
        "tla": "ARS",
        "crest": "https://crests.football-data.org/57.png",
    }


@pytest.fixture
def mock_matches_finished():
    """Sample finished match response."""
    return {
        "matches": [
            {
                "utcDate": "2025-11-20T15:00:00Z",
                "homeTeam": {"shortName": "Arsenal"},
                "awayTeam": {"shortName": "Chelsea"},
                "score": {
                    "fullTime": {"home": 3, "away": 1},
                },
                "competition": {"name": "Premier League"},
            }
        ]
    }


@pytest.fixture
def mock_matches_scheduled():
    """Sample scheduled match response."""
    future_date = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
    return {
        "matches": [
            {
                "utcDate": future_date,
                "homeTeam": {"shortName": "Man Utd"},
                "awayTeam": {"shortName": "Arsenal"},
                "competition": {"name": "Premier League"},
            }
        ]
    }


@pytest.fixture
def mock_standings():
    """Sample league standings response."""
    return {
        "standings": [
            {
                "type": "TOTAL",
                "table": [
                    {
                        "position": 1,
                        "team": {"shortName": "Liverpool"},
                        "playedGames": 12,
                        "won": 10,
                        "draw": 1,
                        "lost": 1,
                        "points": 31,
                        "goalDifference": 15,
                    },
                    {
                        "position": 2,
                        "team": {"shortName": "Arsenal"},
                        "playedGames": 12,
                        "won": 9,
                        "draw": 2,
                        "lost": 1,
                        "points": 29,
                        "goalDifference": 12,
                    },
                ],
            }
        ]
    }


class TestFootballClient:
    """Test FootballClient with mocked API responses."""

    @responses.activate
    def test_get_team_data_success(
        self,
        monkeypatch,
        mock_team_response,
        mock_matches_finished,
        mock_matches_scheduled,
        mock_standings,
    ):
        """Test successful team data fetch."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        team_id = "57"

        # Mock team request
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}",
            json=mock_team_response,
            status=200,
        )

        # Mock finished matches
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=1",
            json=mock_matches_finished,
            status=200,
        )

        # Mock scheduled matches
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED&limit=3",
            json=mock_matches_scheduled,
            status=200,
        )

        # Mock standings
        responses.add(
            responses.GET,
            "https://api.football-data.org/v4/competitions/2021/standings",
            json=mock_standings,
            status=200,
        )

        # Mock live check (empty)
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=IN_PLAY",
            json={"matches": []},
            status=200,
        )

        client = FootballClient()
        data = client.get_team_data(team_id)

        assert data is not None
        assert data.team_name == "Arsenal"
        assert data.sport == "football"
        assert data.last_result is not None
        assert data.last_result.home_team == "Arsenal"
        assert data.last_result.home_score == "3"
        assert len(data.next_fixtures) == 1
        assert len(data.league_table) == 2
        assert data.is_live is False

    @responses.activate
    def test_no_api_key(self, monkeypatch):
        """Test client without API key."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", None)

        client = FootballClient()
        data = client.get_team_data("57")

        assert data is None

    @responses.activate
    def test_api_error_handling(self, monkeypatch):
        """Test API error handling."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        # Mock 404 error
        responses.add(
            responses.GET,
            "https://api.football-data.org/v4/teams/57",
            json={"error": "not_found"},
            status=404,
        )

        client = FootballClient()
        data = client.get_team_data("57")

        assert data is None

    @responses.activate
    def test_is_game_today(self, monkeypatch):
        """Test checking if game is today."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Mock today's match
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/57/matches?dateFrom={today}&dateTo={tomorrow}",
            json={"matches": [{"id": 12345}]},
            status=200,
        )

        client = FootballClient()
        has_game = client.is_game_today("57")

        assert has_game is True

    @responses.activate
    def test_is_game_today_no_match(self, monkeypatch):
        """Test checking when no game today."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        # Mock no matches
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/57/matches?dateFrom={today}&dateTo={tomorrow}",
            json={"matches": []},
            status=200,
        )

        client = FootballClient()
        has_game = client.is_game_today("57")

        assert has_game is False

    @responses.activate
    def test_is_game_live(self, monkeypatch):
        """Test checking if game is live."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        # Mock live match
        responses.add(
            responses.GET,
            "https://api.football-data.org/v4/teams/57/matches?status=IN_PLAY",
            json={
                "matches": [
                    {
                        "homeTeam": {"shortName": "Arsenal"},
                        "awayTeam": {"shortName": "Spurs"},
                        "score": {"fullTime": {"home": 2, "away": 0}},
                    }
                ]
            },
            status=200,
        )

        client = FootballClient()
        is_live = client.is_game_live("57")

        assert is_live is True

    @responses.activate
    def test_live_match_in_team_data(
        self, monkeypatch, mock_team_response, mock_matches_finished, mock_standings
    ):
        """Test team data includes live match score."""
        monkeypatch.setattr(Config, "FOOTBALL_API_KEY", "test_api_key")

        team_id = "57"

        # Mock team request
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}",
            json=mock_team_response,
            status=200,
        )

        # Mock finished matches
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=1",
            json=mock_matches_finished,
            status=200,
        )

        # Mock scheduled matches (empty)
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED&limit=3",
            json={"matches": []},
            status=200,
        )

        # Mock standings
        responses.add(
            responses.GET,
            "https://api.football-data.org/v4/competitions/2021/standings",
            json=mock_standings,
            status=200,
        )

        # Mock live match
        responses.add(
            responses.GET,
            f"https://api.football-data.org/v4/teams/{team_id}/matches?status=IN_PLAY",
            json={
                "matches": [
                    {
                        "homeTeam": {"shortName": "Arsenal"},
                        "awayTeam": {"shortName": "Spurs"},
                        "score": {"fullTime": {"home": 3, "away": 1}},
                    }
                ]
            },
            status=200,
        )

        client = FootballClient()
        data = client.get_team_data(team_id)

        assert data is not None
        assert data.is_live is True
        assert "Arsenal" in data.live_score
        assert "3 - 1" in data.live_score
