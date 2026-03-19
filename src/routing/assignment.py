"""Team assignment logic."""

from typing import Optional, Dict, List
from dataclasses import dataclass
import yaml


@dataclass
class TeamConfig:
    """Team configuration."""
    name: str
    description: str
    categories: List[str]
    channels: List[str]
    max_queue: Optional[int] = None
    escalation_threshold: Optional[int] = None


class TeamAssignmentManager:
    """Manages team assignments for feedback."""

    DEFAULT_TEAM_CONFIG = {
        "sales": TeamConfig(
            name="Sales",
            description="Sales team for prospects and lost customers",
            categories=["lost", "suggestion"],
            channels=["email", "slack"]
        ),
        "support": TeamConfig(
            name="Support",
            description="Support team for questions and bugs",
            categories=["bug", "question"],
            channels=["email", "slack", "intercom"]
        ),
        "product": TeamConfig(
            name="Product",
            description="Product team for features and requests",
            categories=["feature", "suggestion"],
            channels=["slack", "email"]
        ),
        "customer_success": TeamConfig(
            name="Customer Success",
            description="CS team for complaints and concerns",
            categories=["complaint", "escalation"],
            channels=["email", "slack"]
        ),
    }

    # Map categories to default teams
    CATEGORY_TEAM_MAP = {
        "bug": "support",
        "feature": "product",
        "question": "support",
        "complaint": "customer_success",
        "praise": "customer_success",
        "suggestion": "product",
        "lost": "sales",
        "escalation": "management",
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize team assignment manager.

        Args:
            config_path: Optional path to YAML config file
        """
        self.teams = self.DEFAULT_TEAM_CONFIG.copy()
        if config_path:
            self.load_from_yaml(config_path)

    def get_team_for_category(self, category: str) -> str:
        """Get team assignment for category.

        Args:
            category: Feedback category

        Returns:
            Team name
        """
        return self.CATEGORY_TEAM_MAP.get(category, "support")

    def get_team_for_urgency(self, urgency: str) -> Optional[str]:
        """Get team for specific urgency level.

        Args:
            urgency: Urgency level

        Returns:
            Team name if applicable
        """
        if urgency == "critical":
            return "management"
        return None

    def load_from_yaml(self, yaml_path: str) -> None:
        """Load team configuration from YAML.

        Args:
            yaml_path: Path to YAML configuration file
        """
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)

        if not config or 'teams' not in config:
            return

        for team_name, team_data in config['teams'].items():
            self.teams[team_name] = TeamConfig(
                name=team_data.get('name', team_name),
                description=team_data.get('description', ''),
                categories=team_data.get('categories', []),
                channels=team_data.get('channels', []),
                max_queue=team_data.get('max_queue'),
                escalation_threshold=team_data.get('escalation_threshold')
            )

        # Update category map if provided
        if 'category_mappings' in config:
            self.CATEGORY_TEAM_MAP.update(config['category_mappings'])

    def get_team_config(self, team_name: str) -> Optional[TeamConfig]:
        """Get team configuration.

        Args:
            team_name: Team name

        Returns:
            TeamConfig if found
        """
        return self.teams.get(team_name)

    def get_all_teams(self) -> Dict[str, TeamConfig]:
        """Get all team configurations.

        Returns:
            Dictionary of all teams
        """
        return self.teams.copy()

    def is_team_available(self, team_name: str) -> bool:
        """Check if team is configured and available.

        Args:
            team_name: Team name

        Returns:
            True if team is available
        """
        return team_name in self.teams

    def get_team_for_channel(self, channel: str) -> Optional[str]:
        """Get best team for specific channel.

        Args:
            channel: Feedback channel

        Returns:
            Team name if applicable
        """
        for team_name, config in self.teams.items():
            if channel in config.channels:
                return team_name
        return None

    def get_backup_team(self, primary_team: str) -> Optional[str]:
        """Get backup team if primary is unavailable.

        Args:
            primary_team: Primary team name

        Returns:
            Backup team name
        """
        # Define backup routing
        backup_map = {
            "sales": "customer_success",
            "support": "customer_success",
            "product": "support",
            "customer_success": "support",
        }
        return backup_map.get(primary_team)
