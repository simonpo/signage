"""
Football (soccer) client using football-data.org API.
Free tier: 10 requests/minute
"""

import logging
from datetime import datetime, timedelta

import pytz

from src.clients.sports.base_sports import BaseSportsClient
from src.config import Config
from src.models.signage_data import LeagueTableRow, SportsData, SportsFixture, SportsResult

logger = logging.getLogger(__name__)


class FootballClient(BaseSportsClient):
    """
    Football (soccer) client for Premier League using football-data.org.

    Free tier: 10 requests/minute, covers major European leagues.
    Get your free API key at: https://www.football-data.org/client/register
    """

    BASE_URL = "https://api.football-data.org/v4"
    PREMIER_LEAGUE_ID = 2021  # Premier League code

    def __init__(self, api_key: str | None = None):
        """Initialize football client with API key."""
        super().__init__()
        self.api_key = api_key or Config.FOOTBALL_API_KEY

        if not self.api_key:
            logger.warning("No FOOTBALL_API_KEY configured - FootballClient will not work")

    def _make_request(self, endpoint: str) -> dict | None:  # type: ignore[override]  # Simplified signature for football API
        """Make API request with authentication."""
        if not self.api_key:
            logger.error("No API key available")
            return None

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"X-Auth-Token": self.api_key}

        response = super()._make_request(url, headers=headers)
        if response and response.status_code == 200:
            return response.json()  # type: ignore[no-any-return]  # JSON from football API

        logger.error(
            f"Football API request failed: {response.status_code if response else 'No response'}"
        )
        return None

    def get_team_data(self, team_id: str) -> SportsData | None:
        """
        Get comprehensive team data including fixtures and standings.

        Args:
            team_id: Team ID (e.g., "57" for Arsenal)

        Returns:
            SportsData object or None on failure
        """
        try:
            # Get team info
            team_data = self._make_request(f"teams/{team_id}")
            if not team_data:
                return None

            team_name = team_data.get("shortName", team_data.get("name", "Unknown"))

            # Get recent matches (last 10)
            matches_data = self._make_request(f"teams/{team_id}/matches?status=FINISHED&limit=1")
            last_result = None
            if matches_data and matches_data.get("matches"):
                match = matches_data["matches"][0]
                last_result = self._parse_result(match)

            # Get upcoming fixtures (next 3)
            upcoming_data = self._make_request(f"teams/{team_id}/matches?status=SCHEDULED&limit=3")
            next_fixtures = []
            if upcoming_data and upcoming_data.get("matches"):
                next_fixtures = [self._parse_fixture(m) for m in upcoming_data["matches"]]

            # Get league standings
            standings_data = self._make_request(f"competitions/{self.PREMIER_LEAGUE_ID}/standings")
            league_table = []
            if standings_data and standings_data.get("standings"):
                # Get the main table (standings[0])
                table = standings_data["standings"][0].get("table", [])
                league_table = [self._parse_table_row(row) for row in table[:10]]  # Top 10

            # Check if there's a live match
            live_data = self._make_request(f"teams/{team_id}/matches?status=IN_PLAY")
            is_live = False
            live_score = None
            if live_data and live_data.get("matches"):
                match = live_data["matches"][0]
                is_live = True
                live_score = f"{match['homeTeam']['shortName']} {match['score']['fullTime']['home']} - {match['score']['fullTime']['away']} {match['awayTeam']['shortName']}"

            return SportsData(
                team_name=team_name,
                sport="football",
                last_result=last_result,
                next_fixtures=next_fixtures,
                league_table=league_table,
                is_live=is_live,
                live_score=live_score,
                primary_color="#EF0107",  # Arsenal red
                secondary_color="#FFFFFF",  # Arsenal white
                league_name="Premier League Standings",
            )

        except Exception as e:
            logger.error(f"Failed to get football data: {e}")
            return None

    def _parse_result(self, match: dict) -> SportsResult:
        """Parse match result from API data."""
        home_team = match["homeTeam"]["shortName"]
        away_team = match["awayTeam"]["shortName"]
        home_score = match["score"]["fullTime"]["home"] or 0
        away_score = match["score"]["fullTime"]["away"] or 0

        # Parse date
        match_date = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
        date_str = match_date.strftime("%b %d")

        competition = match.get("competition", {}).get("name", "Premier League")

        return SportsResult(
            home_team=home_team,
            away_team=away_team,
            home_score=str(home_score),
            away_score=str(away_score),
            date=date_str,
            competition=competition,
        )

    def _parse_fixture(self, match: dict) -> SportsFixture:
        """Parse upcoming fixture from API data."""
        home_team = match["homeTeam"]["shortName"]
        away_team = match["awayTeam"]["shortName"]

        # Parse date and convert to PST
        match_date_utc = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
        pst = pytz.timezone("US/Pacific")
        match_date_pst = match_date_utc.astimezone(pst)
        date_str = match_date_pst.strftime("%b %d, %I:%M %p PST")

        return SportsFixture(
            home_team=home_team,
            away_team=away_team,
            date=date_str,
            competition=match.get("competition", {}).get("name", "Premier League"),
        )

    def _parse_table_row(self, row: dict) -> LeagueTableRow:
        """Parse league table row from API data."""
        return LeagueTableRow(
            position=row["position"],
            team=row["team"]["shortName"],
            played=row["playedGames"],
            won=row["won"],
            drawn=row["draw"],
            lost=row["lost"],
            points=row["points"],
            goal_difference=row["goalDifference"],
        )

    def is_game_today(self, team_id: str) -> bool:
        """Check if team has a game today."""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        matches_data = self._make_request(
            f"teams/{team_id}/matches?dateFrom={today}&dateTo={tomorrow}"
        )

        return bool(matches_data and matches_data.get("matches"))

    def is_game_live(self, team_id: str) -> bool:
        """Check if team has a live game."""
        live_data = self._make_request(f"teams/{team_id}/matches?status=IN_PLAY")
        return bool(live_data and live_data.get("matches"))
