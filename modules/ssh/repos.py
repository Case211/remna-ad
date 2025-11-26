from dataclasses import dataclass
from typing import List, Dict
from uuid import uuid4


@dataclass
class Repo:
    id: str
    name: str
    description: str
    command: str  # command to run in shell for installation


_FAVORITES: Dict[int, List[Repo]] = {}


def get_repositories() -> List[Repo]:
    """Return configured repositories. Edit this list to suit your environment."""
    return [
        # Examples. Replace with your actual repos and install commands.
        Repo(
            id="example_node_a",
            name="Example Node A",
            description="Установка ноды A (пример). Скрипт задаёт вопросы.",
            command="bash -lc 'git clone https://example.com/node-a.git && cd node-a && ./install.sh'",
        ),
        Repo(
            id="example_node_b",
            name="Example Node B",
            description="Установка ноды B (пример)",
            command="bash -lc 'git clone https://example.com/node-b.git && cd node-b && ./setup.sh'",
        ),
    ]


def get_favorite_repositories(user_id: int) -> List[Repo]:
    return list(_FAVORITES.get(int(user_id), []))


def add_favorite_repository(user_id: int, name: str, description: str, command: str) -> Repo:
    repo = Repo(
        id=f"fav_{uuid4().hex[:10]}",
        name=name.strip(),
        description=description.strip(),
        command=command.strip(),
    )
    favs = _FAVORITES.setdefault(int(user_id), [])
    favs.append(repo)
    return repo


def get_all_repositories_for_user(user_id: int) -> List[Repo]:
    # Favorites first, then defaults
    return get_favorite_repositories(user_id) + get_repositories()
