########## 配置文件 ##########
import os


class Config:
    TUSHARE_TOKEN = '025198f4736f5b8f90f99903c08840a57f974daf1b1f78fe135f652e'
    DEBUG = True
    CORS_ORIGINS = ["http://localhost:8080"]
    _BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

    # 训练好的YOLO模型路径 / 检测结果保存目录(相对项目目录,避免硬编码盘符)
    MODEL_PATH = os.path.join(_BACKEND_DIR, "models", "weights", "best.pt")
    OUTPUT_DIR = os.path.join(_BACKEND_DIR, "models", "weights", "yolo_results")

    # 行情数据目录:默认项目内 data/kline-data;可用环境变量 DATA_FOLDER 覆盖(Docker 里设为 /data)
    DATA_FOLDER = os.environ.get("DATA_FOLDER") or os.path.normpath(
        os.path.join(_BACKEND_DIR, "data", "kline-data")
    )
