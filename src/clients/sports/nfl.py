"""
NFL sports client using ESPN API.
Fetches Seahawks fixtures, results, and NFC West standings.
"""

import logging
from datetime import datetime
from typing import Optional

from src.clients.sports.base_sports import BaseSportsClient
from src.config import Config
from src.models.signage_data import (
    LeagueTableRow,
    SportsData,
    SportsFixture,
    SportsResult,
)

logger = logging.getLogger(__name__)


class NFLClient(BaseSportsClient):
    """
    NFL client using ESPN's public API.
    Optimized for Seattle Seahawks but works for any team.
    """

    ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self):
        """Initialize NFL client."""
        super().__init__()
        self.team_id = Config.SEAHAWKS_TEAM_ID

    def get_team_data(self, team_id: Optional[str] = None) -> Optional[SportsData]:
        """
        Get comprehensive team data: fixtures, results, standings.

        Args:
            team_id: Team ID (defaults to configured Seahawks ID)

        Returns:
            SportsData with NFL information
        """
        if team_id is None:
            team_id = self.team_id

        logger.info(f"Fetching NFL data for team {team_id}")

        # Get schedule for this team
        schedule = self._get_schedule(team_id)

        # Get NFC West standings
        standings = self._get_standings()

        # Get team info (logo, colors)
        team_info = self._get_team_info(team_id)

        # Parse last result and next fixtures
        last_result = None
        next_fixtures = []

        for game in schedule:
            status = game.get("status", {}).get("type", {}).get("name", "")

            if status in ["STATUS_FINAL", "STATUS_FINAL_OVERTIME"]:
                # This is a completed game
                if not last_result:  # Get most recent result
                    last_result = self._parse_result(game, team_id)

            elif status in ["STATUS_SCHEDULED", "STATUS_POSTPONED"]:
                # This is an upcoming game
                if len(next_fixtures) < 3:
                    fixture = self._parse_fixture(game, team_id)
                    if fixture:
                        next_fixtures.append(fixture)

        # Check if game is live
        is_live = self.is_game_live(team_id)
        live_score = self._get_live_score(team_id) if is_live else None

        return SportsData(
            team_name=team_info.get("name", "Seattle Seahawks"),
            sport="nfl",
            last_result=last_result,
            next_fixtures=next_fixtures,
            league_table=standings,
            is_live=is_live,
            live_score=live_score,
            team_logo_url=team_info.get("logo"),
            primary_color=team_info.get("color", "#002244"),
            secondary_color=team_info.get("alt_color", "#69BE28"),
        )

    def _get_schedule(self, team_id: str) -> list[dict]:
        """Fetch team schedule."""
        url = f"{self.ESPN_BASE}/teams/{team_id}/schedule"

        response = self._make_request(url)
        if not response:
            logger.error(f"Failed to fetch schedule for team {team_id}")
            return []

        try:
            data = response.json()
            events = data.get("events", [])
            logger.debug(f"Fetched {len(events)} events for team {team_id}")
            return events
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse schedule: {e}")
            return []

    def _get_standings(self) -> list[LeagueTableRow]:
        """Fetch NFC West standings."""
        url = f"{self.ESPN_BASE}/standings"

        response = self._make_request(url)
        if not response:
            logger.warning("Failed to fetch NFL standings")
            return []

        try:
            data = response.json()

            # Find NFC West division
            for conference in data.get("children", []):
                if conference.get("abbreviation") == "NFC":
                    for division in conference.get("children", []):
                        if "West" in division.get("name", ""):
                            standings = division.get("standings", {}).get("entries", [])

                            rows = []
                            for entry in standings[:5]:  # Top 5
                                team = entry.get("team", {})
                                stats = {s["name"]: s["value"] for s in entry.get("stats", [])}

                                rows.append(
                                    LeagueTableRow(
                                        position=len(rows) + 1,
                                        team=team.get("shortDisplayName", ""),
                                        played=int(stats.get("gamesPlayed", 0)),
                                        won=int(stats.get("wins", 0)),
                                        drawn=0,  # NFL doesn't have draws (pre-overtime)
                                        lost=int(stats.get("losses", 0)),
                                        points=int(stats.get("points", 0)),
                                        goal_difference=int(stats.get("pointDifferential", 0)),
                                    )
                                )

                            return rows

            logger.warning("Could not find NFC West standings")
            return []

        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse standings: {e}")
            return []

    def _get_team_info(self, team_id: str) -> dict:
        """Get team name, logo, colors."""
        url = f"{self.ESPN_BASE}/teams/{team_id}"

        response = self._make_request(url)
        if not response:
            return {}

        try:
            data = response.json()
            team = data.get("team", {})

            return {
                "name": team.get("displayName", ""),
                "logo": team.get("logos", [{}])[0].get("href"),
                "color": f"#{team.get('color', '002244')}",
                "alt_color": f"#{team.get('alternateColor', '69BE28')}",
            }
        except (ValueError, KeyError):
            return {}

    def _parse_result(self, game: dict, team_id: str) -> Optional[SportsResult]:
        """Parse completed game into SportsResult."""
        try:
            competitions = game.get("competitions", [{}])[0]
            competitors = competitions.get("competitors", [])

            home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})

            date_str = game.get("date", "")
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            return SportsResult(
                date=date_obj.strftime("%b %d"),
                home_team=home_team.get("team", {}).get("shortDisplayName", ""),
                away_team=away_team.get("team", {}).get("shortDisplayName", ""),
                home_score=home_team.get("score", "0"),
                away_score=away_team.get("score", "0"),
                competition="NFL",
            )
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse result: {e}")
            return None

    def _parse_fixture(self, game: dict, team_id: str) -> Optional[SportsFixture]:
        """Parse upcoming game into SportsFixture."""
        try:
            competitions = game.get("competitions", [{}])[0]
            competitors = competitions.get("competitors", [])

            home_team = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), {})

            date_str = game.get("date", "")
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            is_home = home_team.get("team", {}).get("id") == team_id

            return SportsFixture(
                date=date_obj.strftime("%b %d %I:%M %p"),
                home_team=home_team.get("team", {}).get("shortDisplayName", ""),
                away_team=away_team.get("team", {}).get("shortDisplayName", ""),
                competition="NFL",
                venue=competitions.get("venue", {}).get("fullName", ""),
                is_home_game=is_home,
            )
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse fixture: {e}")
            return None

    def _get_live_score(self, team_id: str) -> Optional[str]:
        """Get live score if game is in progress."""
        url = f"{self.ESPN_BASE}/scoreboard"

        response = self._make_request(url)
        if not response:
            return None

        try:
            data = response.json()

            for event in data.get("events", []):
                competitions = event.get("competitions", [{}])[0]
                competitors = competitions.get("competitors", [])

                # Check if this game involves our team
                team_ids = [c.get("team", {}).get("id") for c in competitors]
                if team_id not in team_ids:
                    continue

                # Check if game is live
                status = event.get("status", {}).get("type", {}).get("name", "")
                if "IN_PROGRESS" not in status:
                    continue

                # Build score string
                home = next((c for c in competitors if c.get("homeAway") == "home"), {})
                away = next((c for c in competitors if c.get("homeAway") == "away"), {})

                return (
                    f"{home.get('team', {}).get('abbreviation', '')} "
                    f"{home.get('score', '0')} - "
                    f"{away.get('score', '0')} "
                    f"{away.get('team', {}).get('abbreviation', '')}"
                )

        except (ValueError, KeyError) as e:
            logger.error(f"Failed to get live score: {e}")

        return None

    def is_game_today(self, team_id: Optional[str] = None) -> bool:
        """Check if team has a game today."""
        if team_id is None:
            team_id = self.team_id

        schedule = self._get_schedule(team_id)
        today = datetime.now().date()

        for game in schedule:
            try:
                date_str = game.get("date", "")
                game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()

                if game_date == today:
                    return True
            except (ValueError, KeyError):
                continue

        return False

    def is_game_live(self, team_id: Optional[str] = None) -> bool:
        """Check if team is currently playing."""
        if team_id is None:
            team_id = self.team_id

        return self._get_live_score(team_id) is not None
