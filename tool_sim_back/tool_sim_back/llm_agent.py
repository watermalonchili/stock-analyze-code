import re
from openai import OpenAI

# 初始化 DeepSeek 客户端
# 注意：在生产环境中建议将 API Key 放在环境变量中
DEEPSEEK_API_KEY = "sk-1b1877dcd19d47b4b355d662fe0e95bd"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"  # DeepSeek 的官方接口地址
)


def generate_ai_filter(tags, custom_prompt):
    """
    调用 DeepSeek-Coder 将前端标签翻译为 Pandas 滑窗过滤代码
    关键：生成宽松的过滤规则，避免全量过滤
    """
    if not tags and not custom_prompt:
        return lambda df: True  # 如果没传标签，默认全部放行

    # 【极其严谨的 Prompt 架构】
    prompt = f"""
       你是一个精通Python和Pandas的量化交易工程师。
       请编写一个Python函数 `def ai_filter(df):`。
       输入参数 df 是一个包含大约20行数据的Pandas DataFrame，按时间正序排列。
       包含的列有：'trade_date', 'open', 'close', 'high', 'low', 'MA4', 'MA8', 'MA12', 'MA16', 'MA20', 'MA47'。

       请将以下用户的形态描述转化为Pandas逻辑：
       【用户勾选标签】: {tags}
       【用户补充要求】: {custom_prompt}

       【逻辑编写指南 - 务必严格遵守】：
       1. ⚠️ 极度宽松：这是粗筛阶段，目标是通过率15-40%。宁可多放行也不能漏掉！
       2. ⚠️ 关键修改：数值范围用中心值×0.30 ~ ×1.70：
          - 用户说"波动幅度13.7%"，代码应写 0.04 <= range <= 0.23（即 13.7%×0.30≈4%, 13.7%×1.70≈23%）
          - 用户说"回撤15.9%"，代码应写 0.05 <= dd <= 0.27
          - 用户说"振幅比22%"，代码应写 0.07 <= amp <= 0.37
          - 用户说"8个拐点"，代码应写 peaks >= 3（只设很低的下限）
       3. ⚠️ 最多只保留2-3个最重要的条件！不要堆砌！有数值的条件挑最重要的2个即可。
       4. ⚠️ 数值条件之间的关系用 OR 逻辑！只要满足其中任意一个数值条件即可通过。
       5. ⚠️ 方向性判断极度宽松：
          - 下降趋势：close[-1] < close[0] * 1.01（仅要求收盘不涨超1%）
          - 上升趋势：close[-1] > close[0] * 0.99（仅要求收盘不跌超1%）
       6. 时间分段：如果提及"前段"，使用 df.iloc[:len(df)//3]；"中段"使用 df.iloc[len(df)//3 : 2*len(df)//3]；"后段"使用 df.iloc[2*len(df)//3:]。
       7. 上穿/下穿：只需对比局部的起点和终点即可。
       8. ⚠️ 容错处理：计算距离时，必须用基于价格均值的百分比差值，不要用绝对数值！
       9. ⚠️ 自检：估算你的条件组合通过率，如果明显低于15%，进一步放宽数值范围或减少条件！
       10. 只输出纯净的 Python 代码，不要任何中文解释！不要输出 ```python 标记！
       """

    try:
        # 调用 deepseek-coder 模型
        response = client.chat.completions.create(
            model="deepseek-coder",  # 专门用于写代码的模型
            messages=[
                {"role": "system", "content": "你是一个只输出合法Python代码的机器，不输出任何Markdown格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # 完全确定性，相同输入永远相同输出
            max_tokens=4096
        )

        # 1. 提取生成的代码
        code_str = response.choices[0].message.content.strip()

        # 2. 提取并打印 Token 消耗情况
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        print("\n" + "💰" * 20)
        print(
            f"💸 [DeepSeek 消耗] 提示词: {prompt_tokens} tokens | 生成代码: {completion_tokens} tokens | 总计消耗: {total_tokens} tokens")
        print("💰" * 20 + "\n")

        # 3. 清理可能残留的 markdown 标记
        code_str = re.sub(r'^```python\n|^```\n|```$', '', code_str, flags=re.MULTILINE).strip()

        print(f"📝 [DeepSeek 实时生成的过滤代码]:\n{code_str}\n" + "-" * 40)

        # 4. 动态编译为 Python 函数
        local_env = {}
        exec(code_str, globals(), local_env)
        return local_env['ai_filter']

    except Exception as e:
        print(f"❌ [DeepSeek] 代码生成或编译失败: {e}")
        return lambda df: True  # 兜底逻辑：如果 AI 写错代码报错了，直接返回 True 保证程序不崩溃