"""
问卷数据清洗流水线

使用 catalog/record 中的 dirty.csv 作为输入，
通过 factory/processor 中的 QuestionnaireCleaner 进行处理，
结果与 catalog/record 中的 clean.csv 进行对比验证
"""

import sys
from pathlib import Path
import pandas as pd

# 添加处理器目录到路径
processor_dir = Path(__file__).parent.parent / "processor"
sys.path.insert(0, str(processor_dir))

from questionnaire_cleaner import QuestionnaireCleaner


class QuestionnairePipeline:
    """
    问卷数据清洗流水线

    流程：
    1. 加载 dirty.csv 原始数据
    2. 使用 QuestionnaireCleaner 进行清洗
    3. 返回清洗后的数据（暂不保存）
    """

    def __init__(self, dirty_csv_path: Path):
        """
        初始化流水线

        Args:
            dirty_csv_path: 脏数据 CSV 文件路径
        """
        self.dirty_csv_path = Path(dirty_csv_path)
        self.cleaner = QuestionnaireCleaner()
        self.raw_df = None
        self.cleaned_df = None

    def load_data(self) -> pd.DataFrame:
        """加载原始数据"""
        self.raw_df = pd.read_csv(self.dirty_csv_path)
        return self.raw_df

    def process(self) -> pd.DataFrame:
        """
        执行完整清洗流程

        Returns:
            清洗后的 DataFrame
        """
        if self.raw_df is None:
            self.load_data()

        self.cleaned_df = self.cleaner.process(self.raw_df)
        return self.cleaned_df

    def run(self) -> pd.DataFrame:
        """
        运行完整流水线

        Returns:
            清洗后的 DataFrame
        """
        return self.process()


def main():
    """主函数：运行流水线并输出结果"""
    # 获取路径
    pipeline_dir = Path(__file__).parent
    record_dir = pipeline_dir.parent.parent / "catelog" / "record"
    dirty_csv_path = record_dir / "dirty.csv"
    clean_csv_path = record_dir / "clean.csv"

    print(f"加载原始数据: {dirty_csv_path}")
    pipeline = QuestionnairePipeline(dirty_csv_path)

    print("执行清洗流程...")
    cleaned_df = pipeline.run()

    print(f"\n清洗完成！")
    print(f"原始记录数: {len(pipeline.raw_df)}")
    print(f"清洗后记录数: {len(cleaned_df)}")
    print(f"列数: {len(cleaned_df.columns)}")
    print(f"\n列名: {list(cleaned_df.columns)}")

    # 显示前几条记录
    print(f"\n前5条清洗后数据:")
    print(cleaned_df.head().to_string())

    return cleaned_df


if __name__ == "__main__":
    main()
