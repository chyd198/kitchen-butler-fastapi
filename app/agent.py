"""Agent singleton for the FastAPI service — same definition as butler_agent.py,
created once at import time so concurrent requests share the same MemorySaver state.
"""
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from tavily import TavilyClient

load_dotenv()

_tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web. Returns results (title/link/snippet) plus related image URLs.
    Use "<ingredients> 食谱 做法" for recipes and "<dish name> 图片" for dish photos."""
    r = _tavily.search(query, max_results=3, include_images=True)
    lines = []
    for i, item in enumerate(r.get("results", []), 1):
        lines.append(f"{i}. {item['title']}\n   Link: {item['url']}\n   Snippet: {item['content'][:150]}")
    images = r.get("images", [])
    if images:
        lines.append("Related image URLs: " + ", ".join(images[:3]))
    return "\n\n".join(lines) if lines else "No results found"


SYSTEM_PROMPT = """你是 AI 私厨管家。用户会发来食材照片或文字描述自己有哪些食材，你帮他推荐食谱。

工作要求：
1. 用户发图片时，仔细识别图中所有食材，并判断每种食材是否新鲜可用于烹饪；
   不新鲜的食材不纳入推荐，但要在报告中列出并说明跳过原因
2. 用 web_search 搜索可用食材的相关食谱（查询词用「食材 食谱 做法」）
3. 对每道食谱从三个维度打分：
   - 营养价值（1-10 分）：蔬菜多、蛋白质丰富、少油少盐得高分
   - 制作难度（1-5 分）：步骤少、时间短、工具简单得高分（越容易分越高）
   - 美味程度（1-15 分）：口感、风味丰富度、大众接受度综合评估，越好吃分越高
   总分 = 三项之和（满分 30 分），按总分从高到低排序
4. 对排名前几的菜，用 web_search 搜「菜名 图片」获取菜品照片，
   从返回的「相关图片 URL」里选一个
5. 最终输出 Markdown 格式的推荐报告，必须包含：
   - ## 📋 食材清单：可用食材；跳过的食材及原因（如有）
   - ## 🏆 食谱推荐排名：每道菜包含——
     菜名和总分、三项分数、推荐理由（1-2句）、
     做法简述（3-4 步，用①②③④分隔，凭常识写即可）、
     参考食谱链接、菜品图片
   - 菜品图片必须用 ![菜名](图片URL) 语法内嵌，URL 必须来自搜索结果的
     「相关图片 URL」（图片文件），绝不能用网页链接冒充图片
6. 搜不到合适食谱时，给出 3 个创意搭配建议（含菜名和做法思路）
7. 用中文回复；用户追问时正常对话，不用每次都重新生成完整报告
"""

agent = create_react_agent(
    model=ChatOpenAI(model="kimi-k2.6"),
    tools=[web_search],
    prompt=SYSTEM_PROMPT,
    checkpointer=MemorySaver(),
)
