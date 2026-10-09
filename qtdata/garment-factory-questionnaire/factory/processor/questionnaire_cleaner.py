# questionnaire_cleaner.py

import pandas as pd
import numpy as np
from typing import Dict, Optional

class QuestionnaireCleaner:
    """
    问卷数据清洗处理器（Processor）
    输入：原始 DataFrame（含中文列名）
    输出：标准化清洗后的 DataFrame（符合 DataContract 规范）

    符合 DataContract: tests/fixtures/workspace/catelog/contract/output-contract.yaml
    """

    # 配置：性别标准化映射
    GENDER_MAPPING = {
        "男": "male",
        "女": "female",
        "其他": "other",
        "未知": "unknown"
    }

    # 配置：教育程度映射
    EDU_MAPPING = {
        "初中": "初中",
        "高中": "高中",
        "大专": "大专",
        "本科": "本科",
        "硕士": "硕士",
        "MBA": "硕士",  # MBA映射为硕士
        "博士": "博士",
        "其他": "其他",
        "未知": "未知"
    }

    # 配置：雇佣状态映射
    EMP_STATUS_MAPPING = {
        "在职": "在职",
        "实习生": "实习生",
        "返聘": "返聘",
        "退休": "非员工",
        "学生": "非员工",
        "其他": "其他",
        "未知": "未知"
    }

    # 配置：城市标准化映射
    CITY_MAPPING = {
        "北京": "北京",
        "上海": "上海",
        "广州": "广州",
        "深圳": "深圳",
        "杭州": "杭州",
        "成都": "成都",
        "重庆": "重庆",
        "其他城市": "其他城市",
        "未知城市": "未知城市"
    }

    def __init__(self):
        self.raw_df: Optional[pd.DataFrame] = None
        self.cleaned_df: Optional[pd.DataFrame] = None

    def process(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """主入口：执行完整清洗流程"""
        self.raw_df = raw_df.copy()
        df = self.raw_df.copy()

        # 阶段1：元数据标准化
        df = self._standardize_datetime(df)
        df = self._standardize_id(df)

        # 阶段2：数值字段处理
        df = self._process_age(df)
        df = self._process_total_exp(df)
        df = self._process_satisfaction(df)
        df = self._process_workload(df)
        df = self._process_tenure(df)
        df = self._process_monthly_income(df)

        # 阶段3：分类字段标准化
        df = self._standardize_dept(df)
        df = self._standardize_gender(df)
        df = self._standardize_education(df)
        df = self._standardize_emp_status(df)
        df = self._standardize_city(df)

        # 阶段4：福利字段处理
        df = self._process_benefits(df)

        # 阶段5：备注字段处理
        df = self._process_other_notes(df)

        # 阶段6：重复检测与标记
        df = self._detect_duplicates(df)

        # 阶段7：数据质量标记
        df = self._add_data_quality_flags(df)

        # 阶段8：字段选择与排序
        df = self._select_and_order_columns(df)

        self.cleaned_df = df
        return self.cleaned_df

    def _standardize_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一提交时间格式为 YYYY-MM-DD HH:MM:SS"""
        df["submit_time"] = pd.to_datetime(
            df["提交时间"] if "提交时间" in df.columns else df["submit_time"],
            format="mixed",
            errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")
        return df

    def _standardize_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化ID字段为整数"""
        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)
        df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
        return df

    def _process_age(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理年龄字段，约束：16-200，允许NULL"""
        # 尝试从现有列中提取年龄值
        age_col = None
        for col in ["年龄", "age"]:
            if col in df.columns:
                age_col = col
                break

        if age_col:
            # 清理年龄数据（去除"岁"、中文字符等）
            if "age" in df.columns:
                df["age"] = df["age"].astype(str).str.replace("岁", "").replace("NULL", "").replace("未知", "").replace("二十八", "28")
            elif "年龄" in df.columns:
                df["age"] = df["年龄"].astype(str).str.replace("岁", "").replace("NULL", "").replace("未知", "")
            df["age"] = pd.to_numeric(df["age"], errors="coerce")
        # 不强制限制范围，允许极端值，通过data_quality_flag标记
        return df

    def _process_total_exp(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理工作年限字段，约束：0-50，允许NULL"""
        # 清理工作年限数据
        if "total_exp" in df.columns:
            df["total_exp"] = df["total_exp"].astype(str).str.replace("年", "").replace("刚入职", "0")
            df["total_exp"] = pd.to_numeric(df["total_exp"], errors="coerce")
        elif "工作年限" in df.columns:
            df["total_exp"] = df["工作年限"].astype(str).str.replace("年", "").replace("刚入职", "0")
            df["total_exp"] = pd.to_numeric(df["total_exp"], errors="coerce")
            df = df.drop(columns=["工作年限"])
        return df

    def _process_satisfaction(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理整体满意度字段，约束：0-6分，允许NULL"""
        # 清理满意度数据
        if "overall_satis" in df.columns:
            df["overall_satis"] = df["overall_satis"].astype(str).str.replace("满意", "").replace("分", "")
            df["overall_satis"] = pd.to_numeric(df["overall_satis"], errors="coerce")
        elif "满意度" in df.columns:
            df["overall_satis"] = df["满意度"].astype(str).str.replace("满意", "").replace("分", "")
            df["overall_satis"] = pd.to_numeric(df["overall_satis"], errors="coerce")
            df = df.drop(columns=["满意度"])
        return df

    def _process_workload(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理工作负荷字段，约束：1-10分，允许NULL"""
        workload_col = "工作负荷" if "工作负荷" in df.columns else "workload"
        df["workload"] = pd.to_numeric(df[workload_col], errors="coerce")
        return df

    def _process_tenure(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理任期/司龄字段，约束：0-50，支持小数，允许NULL"""
        # 清理任期数据
        if "tenure" in df.columns:
            df["tenure"] = df["tenure"].astype(str).str.replace("年", "").replace("刚入职", "0")
            df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")
        elif "任期" in df.columns:
            df["tenure"] = df["任期"].astype(str).str.replace("年", "").replace("刚入职", "0")
            df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")
            df = df.drop(columns=["任期"])
        return df

    def _process_monthly_income(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理月收入字段，约束：0-35000，负数转为NULL，允许NULL"""
        # 清理月收入数据
        if "monthly_income" in df.columns:
            df["monthly_income"] = df["monthly_income"].astype(str).str.replace("元", "").replace("K", "000").replace("保密", "").replace("-", "")
            df["monthly_income"] = pd.to_numeric(df["monthly_income"], errors="coerce")
        elif "月收入" in df.columns:
            df["monthly_income"] = df["月收入"].astype(str).str.replace("元", "").replace("K", "000").replace("保密", "").replace("-", "")
            df["monthly_income"] = pd.to_numeric(df["monthly_income"], errors="coerce")
            df = df.drop(columns=["月收入"])
        # 负数转为NULL
        df.loc[df["monthly_income"] < 0, "monthly_income"] = None
        return df

    def _standardize_dept(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化部门字段"""
        # 部门映射：标准化部门名称
        dept_mapping = {
            "研发部": "研发",
            "R&D": "研发",
            "销售部": "销售",
            "生产": "生产",
            "生产部": "生产",
            "职能": "职能",
            "职能部": "职能",
            "管理": "管理",
            "管理部": "管理",
            "顾问": "其他",
            "测试部门": "测试部门"
        }

        if "dept" in df.columns:
            df["dept"] = df["dept"].map(dept_mapping).fillna(df["dept"])
            df["dept"] = df["dept"].fillna("其他")
        elif "所属部门" in df.columns:
            df["dept"] = df["所属部门"].map(dept_mapping).fillna(df["所属部门"])
            df["dept"] = df["dept"].fillna("其他")
            df = df.drop(columns=["所属部门"])
        return df

    def _standardize_gender(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化性别字段为 male/female/unknown"""
        # 扩展性别映射
        gender_mapping = {
            "男": "male",
            "male": "male",
            "M": "male",
            "1": "male",
            "女": "female",
            "female": "female",
            "F": "female",
            "2": "female",
            "其他": "other",
            "other": "other",
            "未知": "unknown",
            "unknown": "unknown"
        }

        if "gender" in df.columns:
            df["gender"] = df["gender"].fillna("unknown").map(gender_mapping).fillna("unknown")
        elif "性别" in df.columns:
            df["gender"] = df["性别"].fillna("unknown").map(gender_mapping).fillna("unknown")
            df = df.drop(columns=["性别"])
        return df

    def _standardize_education(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化教育程度字段，MBA映射为硕士"""
        if "edu" in df.columns:
            df["edu"] = df["edu"].fillna("未知").map(self.EDU_MAPPING).fillna("其他")
        elif "教育程度" in df.columns:
            df["edu"] = df["教育程度"].fillna("未知").map(self.EDU_MAPPING).fillna("其他")
            df = df.drop(columns=["教育程度"])
        return df

    def _standardize_emp_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化雇佣状态字段"""
        if "emp_status" in df.columns:
            df["emp_status"] = df["emp_status"].fillna("未知").map(self.EMP_STATUS_MAPPING).fillna("其他")
        elif "雇佣状态" in df.columns:
            df["emp_status"] = df["雇佣状态"].fillna("未知").map(self.EMP_STATUS_MAPPING).fillna("其他")
            df = df.drop(columns=["雇佣状态"])
        return df

    def _standardize_city(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化城市字段为中文"""
        # 城市名称标准化映射（处理大小写、空格等）
        city_mapping = {
            "北京": "北京",
            "Beijing": "北京",
            "上海": "上海",
            "Shanghai": "上海",
            "shang hai": "上海",
            "广州": "广州",
            "深圳": "深圳",
            "杭州": "杭州",
            "成都": "成都",
            "重庆": "重庆",
            "其他城市": "其他城市",
            "未知城市": "未知城市"
        }

        if "city" in df.columns:
            # 先进行基本映射
            df["city"] = df["city"].map(city_mapping)
            # 再使用 CITY_MAPPING 进行标准化
            df["city"] = df["city"].fillna("未知城市").map(self.CITY_MAPPING).fillna("未知城市")
        elif "城市" in df.columns:
            df["city"] = df["城市"].map(city_mapping)
            df["city"] = df["city"].fillna("未知城市").map(self.CITY_MAPPING).fillna("未知城市")
            df = df.drop(columns=["城市"])
        return df

    def _process_benefits(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理福利字段，转换为boolean类型"""
        benefit_cols = {
            "benefit_pension": ["养老金", "养老"],
            "benefit_annual_leave": ["年假", "带薪年假"],
            "benefit_health_ins": ["医疗", "医保", "医疗保险"],
            "benefit_other": ["其他", "其他福利"]
        }

        for col_name, keywords in benefit_cols.items():
            # 查找对应的中文列名
            source_col = None
            for keyword in keywords:
                if keyword in df.columns:
                    source_col = keyword
                    break

            if source_col is not None:
                df[col_name] = df[source_col].fillna(False).astype(bool)
            else:
                # 如果没有原始列，初始化为False
                df[col_name] = False

        return df

    def _process_other_notes(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理备注字段，从性别列或其他字段提取备注信息"""
        # 处理备注中的特殊标记
        if "other_notes" in df.columns:
            df["other_notes"] = df["other_notes"].astype(str).str.replace("—", "").replace("nan", "").replace("其他〖", "").replace("〗", "").replace("测试", "测试")
            df["other_notes"] = df["other_notes"].fillna("")
        elif "备注" in df.columns:
            df["other_notes"] = df["备注"].astype(str).str.replace("—", "").replace("nan", "").replace("其他〖", "").replace("〗", "").replace("测试", "测试")
            df["other_notes"] = df["other_notes"].fillna("")
            df = df.drop(columns=["备注"])
        else:
            df["other_notes"] = ""
        return df

    def _detect_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测重复记录并标记"""
        df["is_duplicate"] = False
        if df.duplicated(subset=["submit_time", "age", "total_exp", "dept"]).any():
            df["is_duplicate"] = df.duplicated(subset=["submit_time", "age", "total_exp", "dept"], keep="first")
        return df

    def _add_data_quality_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加数据质量标记"""
        df["data_quality_flag"] = "正常"

        # 收入缺失
        df.loc[df["monthly_income"].isna() & (df["data_quality_flag"] == "正常"), "data_quality_flag"] = "收入缺失"

        # 关键字段缺失
        df.loc[(df["overall_satis"].isna() | df["workload"].isna()) & (df["data_quality_flag"] == "正常"), "data_quality_flag"] = "关键字段缺失"

        # 逻辑校验：学生
        df.loc[(df["emp_status"] == "非员工") & (df["age"] < 18) & (df["emp_status"].shift(1) != "非员工") & (df["data_quality_flag"] == "正常"), "data_quality_flag"] = "逻辑校验_学生"

        # 逻辑校验：退休
        df.loc[(df["emp_status"] == "非员工") & (df["age"] >= 60) & (df["emp_status"].shift(1) != "非员工") & (df["data_quality_flag"] == "正常"), "data_quality_flag"] = "逻辑校验_退休"

        # 异常值：年龄 > 70 或工作负荷 > 10
        df.loc[(df["age"] > 70) | (df["workload"] > 10), "data_quality_flag"] = "异常值_收入负数_工作负荷越界"

        # 测试数据（优先级最高）
        df.loc[df["dept"] == "测试部门", "data_quality_flag"] = "测试数据"

        # 重复记录（优先级最高）
        df.loc[df["is_duplicate"], "data_quality_flag"] = "重复记录"

        return df

    def _select_and_order_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """选择并排序输出列"""
        output_columns = [
            "id",
            "submit_time",
            "age",
            "total_exp",
            "dept",
            "overall_satis",
            "workload",
            "benefit_pension",
            "benefit_annual_leave",
            "benefit_health_ins",
            "benefit_other",
            "other_notes",
            "gender",
            "edu",
            "emp_status",
            "tenure",
            "monthly_income",
            "city",
            "is_duplicate",
            "data_quality_flag"
        ]

        # 只保留存在的列
        existing_columns = [col for col in output_columns if col in df.columns]
        return df[existing_columns]
