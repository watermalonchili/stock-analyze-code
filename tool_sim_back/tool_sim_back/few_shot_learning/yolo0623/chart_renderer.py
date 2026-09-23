"""Lightweight RGB K-line chart rendering for YOLO."""
from PIL import Image, ImageDraw
import numpy as np


RENDERER_VERSION = "pillow-kline-v1"

# 均线颜色配置（与 few_shot_utils.MA_COLORS 保持一致）
MA_COLORS = {
    'MA4': '#000000', 'MA8': '#FF9800', 'MA12': '#E91E63',
    'MA16': '#9C27B0', 'MA20': '#4CAF50', 'MA47': '#2196F3'
}


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def render_kline_image(df, img_size=640):
    """Render an OHLC DataFrame as an axis-free RGB candlestick image."""
    image = Image.new("RGB", (img_size, img_size), "white")
    if df is None or df.empty:
        return image

    required_columns = {"open", "close", "high", "low"}
    if not required_columns.issubset(df.columns):
        return image

    values = df[["open", "close", "high", "low"]].astype(float)
    price_min = float(values[["low", "open", "close"]].min().min())
    price_max = float(values[["high", "open", "close"]].max().max())
    price_range = price_max - price_min
    if price_range <= 0:
        price_range = max(abs(price_max) * 0.01, 1.0)
        price_min -= price_range / 2
        price_max += price_range / 2
    else:
        padding = price_range * 0.05
        price_min -= padding
        price_max += padding
        price_range = price_max - price_min

    count = len(values)
    x_step = img_size / count
    body_width = max(1, round(x_step * 0.7))
    wick_width = max(1, round(x_step * 0.15))
    draw = ImageDraw.Draw(image)

    def y(value):
        return max(0, min(img_size - 1, round((price_max - value) / price_range * (img_size - 1))))

    for index, candle in enumerate(values.itertuples(index=False)):
        open_price, close_price, high_price, low_price = candle
        x_center = round((index + 0.5) * x_step)
        up = close_price >= open_price
        color = (255, 0, 0) if up else (0, 128, 0)
        top = y(max(open_price, close_price))
        bottom = y(min(open_price, close_price))
        high_y = y(high_price)
        low_y = y(low_price)

        draw.rectangle(
            (x_center - wick_width // 2, high_y, x_center + wick_width // 2, low_y),
            fill=color,
        )
        draw.rectangle(
            (x_center - body_width // 2, top, x_center + body_width // 2, max(top, bottom)),
            fill=color,
        )

    return image


def render_ma_image(df, img_size=416):
    """Render MA lines as an axis-free RGB line chart (6 colors on white)."""
    image = Image.new("RGB", (img_size, img_size), "white")
    if df is None or df.empty:
        return image

    ma_columns = [c for c in df.columns if c in MA_COLORS]
    if not ma_columns:
        return image

    # 统一 y 轴缩放：基于所有可见均线值
    all_vals = []
    for col in ma_columns:
        vals = df[col].astype(float).values
        valid = vals[~np.isnan(vals)]
        if len(valid):
            all_vals.extend(valid.tolist())
    if not all_vals:
        return image

    y_min = min(all_vals)
    y_max = max(all_vals)
    y_range = y_max - y_min
    if y_range <= 0:
        y_range = max(abs(y_max) * 0.01, 1.0)
        y_min -= y_range / 2
        y_max += y_range / 2
        y_range = y_max - y_min
    else:
        padding = y_range * 0.05
        y_min -= padding
        y_max += padding
        y_range = y_max - y_min

    count = len(df)
    draw = ImageDraw.Draw(image)

    def coord(i, value):
        x = img_size * (i + 0.5) / count
        y = (y_max - value) / y_range * img_size
        return x, y

    for col in ma_columns:
        vals = df[col].astype(float).values
        color = _hex_to_rgb(MA_COLORS[col])
        # 将 NaN 断开为多段连续折线
        segments = []
        current = []
        for i, v in enumerate(vals):
            if np.isnan(v):
                if len(current) >= 2:
                    segments.append(current)
                current = []
            else:
                current.append(coord(i, v))
        if len(current) >= 2:
            segments.append(current)
        for seg in segments:
            draw.line(seg, fill=color, width=2)

    return image
