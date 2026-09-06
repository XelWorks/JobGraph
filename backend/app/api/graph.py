import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.domain.auth import User

logger = logging.getLogger("app.api.graph")

router = APIRouter()


class GraphNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    epic: int
    wave: int
    developer: str
    files_touched: list[str]
    requires: list[str]
    enables: list[str]


class GraphEdge(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    target: str
    type: str


class DependencyGraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    waves: list[dict[str, Any]]
    epics: list[dict[str, Any]]


def _load_plan() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    plan_path = root / "docs" / "plans" / "dependency-graph.yml"
    with open(plan_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@router.get("", response_model=DependencyGraphResponse)
async def get_dependency_graph(current_user: User = Depends(get_current_user)) -> DependencyGraphResponse:
    plan = _load_plan()

    nodes: list[GraphNode] = []
    for story in plan.get("stories", []):
        nodes.append(
            GraphNode(
                id=story["id"],
                label=story["title"],
                epic=story["epic"],
                wave=story["wave"],
                developer=story["developer"],
                files_touched=story.get("files_touched", []),
                requires=story.get("requires", []),
                enables=story.get("enables", []),
            )
        )

    edges: list[GraphEdge] = []
    for story in plan.get("stories", []):
        for req in story.get("requires", []):
            edge_id = f"{req}-{story['id']}"
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=req,
                    target=story["id"],
                    type="requires",
                )
            )

    waves = plan.get("waves", [])
    epics = []
    seen_epics: set[int] = set()
    for s in plan.get("stories", []):
        epic_num = s["epic"]
        if epic_num not in seen_epics:
            seen_epics.add(epic_num)
            epic_stories = [x for x in plan.get("stories", []) if x["epic"] == epic_num]
            epics.append(
                {
                    "id": f"epic-{epic_num}",
                    "number": epic_num,
                    "title": epic_stories[0].get("title", f"Epic {epic_num}") if epic_stories else f"Epic {epic_num}",
                    "story_count": len(epic_stories),
                }
            )

    return DependencyGraphResponse(nodes=nodes, edges=edges, waves=waves, epics=epics)
