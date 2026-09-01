"""项目状态枚举单一真源测试：API 契约 Literal 与 ORM 常量强制同步。"""
from typing import get_args

from api.projects.schemas import StatusLiteral
from infrastructure.models.project import PROJECT_STATUSES


def test_status_literal_matches_model_constants():
    # 防止前后端/两层各自漂移：任何一侧改动都必须同步另一侧
    assert set(get_args(StatusLiteral)) == set(PROJECT_STATUSES)


def test_status_lifecycle_order():
    assert PROJECT_STATUSES == ("created", "topic", "literature",
                                "writing", "review", "finalize")
