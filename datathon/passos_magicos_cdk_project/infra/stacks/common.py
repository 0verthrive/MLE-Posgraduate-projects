from dataclasses import dataclass

@dataclass
class ProjectTags:
    project_name: str
    stage: str

    def as_dict(self) -> dict[str, str]:
        return {
            "Project": self.project_name,
            "Stage": self.stage,
            "ManagedBy": "CDK",
        }
