"""集中登记允许自动运行的学习工作流。"""

from workflows.scheduled_learning_workflow import run_scheduled_learning
from workflows.ads_monitoring_workflow import run_ads_information_collection


WORKFLOWS = {
    "scheduled_ads_learning": {
        "name": "scheduled_ads_learning", "description": "检索官方广告资料并整理学习摘要",
        "trigger_type": ("manual", "schedule", "webhook"),
        "handler": run_scheduled_learning, "risk_level": "low", "enabled": True,
    },
    "ads_information_collection": {
        "name": "ads_information_collection", "description": "公开信息收集和表格生成的未来流程占位",
        "trigger_type": ("manual", "schedule", "webhook"),
        "handler": run_ads_information_collection, "risk_level": "low", "enabled": False,
    },
}


def get_workflow(name):
    return WORKFLOWS.get(name)


def get_available_workflows():
    return [{key: value for key, value in item.items() if key != "handler"}
            for item in WORKFLOWS.values()]
