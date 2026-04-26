STYLE_ANALYSIS_PROMPT = """根据用户的风格偏好，从以下可用模板中选择最合适的一个。

## 用户偏好
{user_preference}

## 可用模板
{template_list}

请返回模板名称（name 字段的值），只返回名称字符串，不要其他内容。"""
