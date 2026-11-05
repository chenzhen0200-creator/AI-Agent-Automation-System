"""公开资料收集流程占位；目前没有抓取、去重或写表实现。"""

from errors import make_error


PLANNED_STEPS = ("input_urls", "fetch_or_browser", "extract_fields", "clean_data",
                 "deduplicate", "write_table", "return_result")


def run_ads_information_collection(_context, _run_tool):
    return make_error("Workflow Not Implemented", "公开信息收集与写表流程尚未实现")
