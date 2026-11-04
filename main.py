"""程序入口：接收用户目标并输出 Agent 的最终结果。"""

import argparse
import json

from agents.ads_learning_agent import run_ads_learning_agent


def main():
    # --image-path 只传文件路径，程序不会自动点击广告后台。
    parser = argparse.ArgumentParser(description="Google Ads + Meta Ads 学习 Agent")
    parser.add_argument("user_goal", nargs="*", help="学习问题")
    parser.add_argument("--image-path", help="本地广告后台截图路径")
    args = parser.parse_args()
    user_goal = " ".join(args.user_goal) if args.user_goal else input("请输入目标：")
    result = run_ads_learning_agent(user_goal, image_path=args.image_path)
    # 入口只负责展示结构化结果，不决定调用哪个能力。
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
