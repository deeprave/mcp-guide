"""Profile model for composable project configuration."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from mcp_guide.models import ProfileCategory, ProfileCollection

if TYPE_CHECKING:
    from mcp_guide.models import Project


async def get_profiles_dir() -> Path:
    """Get the path to the profiles directory.

    Returns:
        Path to _profiles directory within templates
    """
    from mcp_guide.installer.core import get_templates_path

    templates_path = await get_templates_path()
    return templates_path / "_profiles"


async def discover_profiles() -> list[str]:
    """Discover available profile names.

    Returns:
        List of profile names (without .yaml extension)
    """
    profiles_dir = await get_profiles_dir()
    if not profiles_dir.exists():
        return []

    profile_files = profiles_dir.glob("*.yaml")
    return sorted([p.stem for p in profile_files if not p.stem.startswith("_")])


@dataclass
class Profile:
    """Profile containing categories and collections to apply to a project."""

    name: str
    categories: list[ProfileCategory]
    collections: list[ProfileCollection]

    @classmethod
    def from_yaml(cls, profile_name: str, yaml_content: str) -> "Profile":
        """Load profile from YAML content.

        Args:
            profile_name: Name of the profile
            yaml_content: YAML content string

        Returns:
            Profile instance

        Raises:
            ValueError: If YAML is invalid or contains unsupported fields
        """
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            raise ValueError(f"Profile {profile_name} must be a YAML dictionary")

        # Validate only categories and collections are present
        allowed_keys = {"categories", "collections"}
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            raise ValueError(
                f"Profile {profile_name} contains unsupported fields: {extra_keys}. "
                f"Only 'categories' and 'collections' are allowed."
            )

        # Parse categories
        categories = []
        for cat_data in data.get("categories", []):
            categories.append(ProfileCategory(**cat_data))

        # Parse collections
        collections = []
        for coll_data in data.get("collections", []):
            collections.append(ProfileCollection(**coll_data))

        return cls(name=profile_name, categories=categories, collections=collections)

    @classmethod
    async def load(cls, profile_name: str) -> "Profile":
        """Load profile from file.

        Args:
            profile_name: Name of the profile (without .yaml extension)

        Returns:
            Profile instance

        Raises:
            FileNotFoundError: If profile file doesn't exist
            ValueError: If profile YAML is invalid
        """
        profiles_dir = await get_profiles_dir()
        profile_path = profiles_dir / f"{profile_name}.yaml"

        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{profile_name}' not found at {profile_path}")

        yaml_content = profile_path.read_text()
        return cls.from_yaml(profile_name, yaml_content)

    def apply_to_project(self, project: "Project") -> "Project":
        """Apply this profile to a project.

        Args:
            project: Project to apply profile to

        Returns:
            Updated project with profile categories and collections
        """
        from mcp_guide.models import Category, Collection

        # Add categories from profile
        for cat_config in self.categories:
            if cat_config.name not in project.categories:
                category = Category(
                    dir=cat_config.dir or f"{cat_config.name}/",
                    patterns=cat_config.patterns,
                    description=cat_config.description,
                )
                project = project.with_category(cat_config.name, category)
            else:
                # Merge patterns into existing category
                existing = project.categories[cat_config.name]
                new_patterns = [p for p in cat_config.patterns if p not in existing.patterns]
                if new_patterns:
                    merged_category = Category(
                        dir=existing.dir,
                        patterns=existing.patterns + new_patterns,
                        description=existing.description,
                    )
                    project = project.with_category(cat_config.name, merged_category)

        # Add collections from profile
        for coll_config in self.collections:
            if coll_config.name not in project.collections:
                collection = Collection(
                    categories=coll_config.categories,
                    description=coll_config.description,
                )
                project = project.with_collection(coll_config.name, collection)

        # Track applied profile in metadata
        applied_profiles = list(project.metadata.get("applied_profiles", []))
        if self.name not in applied_profiles:
            applied_profiles.append(self.name)
            from dataclasses import replace

            new_metadata = dict(project.metadata)
            new_metadata["applied_profiles"] = applied_profiles
            project = replace(project, metadata=new_metadata)

        return project
