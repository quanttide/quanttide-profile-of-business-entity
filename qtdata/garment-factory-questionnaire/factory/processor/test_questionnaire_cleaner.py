"""
QuestionnaireCleaner 集成测试

测试问卷数据清洗处理器的端到端功能
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# 添加父目录到 Python 路径以导入被测试模块
processor_dir = Path(__file__).parent
sys.path.insert(0, str(processor_dir))

from questionnaire_cleaner import QuestionnaireCleaner


class TestQuestionnaireCleanerIntegration:
    """QuestionnaireCleaner 集成测试类"""

    @pytest.fixture
    def cleaner(self):
        """创建 QuestionnaireCleaner 实例"""
        return QuestionnaireCleaner()

    @pytest.fixture
    def sample_raw_data(self):
        """创建样本原始数据 DataFrame"""
        data = {
            "提交时间": [
                "2025-01-15 10:30:00",
                "2025-01-16 14:20:00",
                "2025-01-17 09:15:00",
                "2025/01/18 16:45:00",
                "invalid_datetime"
            ],
            "年龄": [25, 30, 45, None, 150],
            "工作年限": [3, 8, 15, 1.5, None],
            "所属部门": ["研发部", "销售部", "财务部", None, "测试部门"],
            "满意度": [5, 4, 3, None, 2],
            "工作负荷": [7, 8, 5, None, 15],
            "任期": [2.5, 6, 10, 0.5, None],
            "月收入": [15000, 20000, 25000, -5000, None],
            "性别": ["男", "女", None, "其他", "未知"],
            "教育程度": ["本科", "硕士", "MBA", "博士", "其他"],
            "雇佣状态": ["在职", "在职", "实习生", "退休", "学生"],
            "城市": ["北京", "上海", None, "深圳", "成都"],
            "养老金": [True, False, True, False, True],
            "年假": [False, True, True, False, False],
            "医疗": [True, True, False, False, True],
            "其他福利": [False, False, False, True, False],
            "备注": ["正常", "", None, "测试数据", "其他信息"]
        }
        df = pd.DataFrame(data)
        # 添加缺失的福利列（如果原始数据中不包含这些列）
        for col in ["养老金", "年假", "医疗", "其他福利"]:
            if col not in df.columns:
                df[col] = False
        return df

    @pytest.fixture
    def duplicate_data(self):
        """创建包含重复记录的数据"""
        data = {
            "提交时间": ["2025-01-15 10:30:00", "2025-01-15 10:30:00", "2025-01-16 10:30:00"],
            "年龄": [25, 25, 30],
            "工作年限": [3, 3, 5],
            "所属部门": ["研发部", "研发部", "销售部"],
            "满意度": [5, 5, 4],
            "工作负荷": [7, 7, 6],
            "任期": [2.5, 2.5, 3],
            "月收入": [15000, 15000, 18000],
            "性别": ["男", "男", "女"],
            "教育程度": ["本科", "本科", "硕士"],
            "雇佣状态": ["在职", "在职", "在职"],
            "城市": ["北京", "北京", "上海"],
            "养老金": [True, True, False],
            "年假": [False, False, True],
            "医疗": [True, True, True],
            "其他福利": [False, False, False],
            "备注": ["", "", ""]
        }
        return pd.DataFrame(data)

    # ========== 端到端测试 ==========

    def test_end_to_end_processing(self, cleaner, sample_raw_data):
        """测试完整的端到端数据处理流程"""
        result = cleaner.process(sample_raw_data)

        # 验证输出结构
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_raw_data)

        # 验证关键字段存在
        required_columns = [
            "id", "submit_time", "age", "total_exp", "dept",
            "overall_satis", "workload", "gender", "edu",
            "emp_status", "tenure", "monthly_income", "city",
            "is_duplicate", "data_quality_flag"
        ]
        for col in required_columns:
            assert col in result.columns, f"缺少必需列: {col}"

    def test_schema_compliance(self, cleaner, sample_raw_data):
        """测试输出数据符合契约定义的 schema"""
        result = cleaner.process(sample_raw_data)

        # 验证数据类型
        assert pd.api.types.is_integer_dtype(result["id"])
        assert pd.api.types.is_object_dtype(result["submit_time"])  # object类型存储字符串和NaN
        assert pd.api.types.is_numeric_dtype(result["age"])  # float64 允许 NULL
        assert pd.api.types.is_string_dtype(result["dept"])
        assert pd.api.types.is_string_dtype(result["gender"])
        assert pd.api.types.is_bool_dtype(result["benefit_pension"])
        assert pd.api.types.is_bool_dtype(result["is_duplicate"])

    # ========== 阶段1：元数据标准化测试 ==========

    def test_datetime_standardization(self, cleaner, sample_raw_data):
        """测试时间格式标准化"""
        result = cleaner.process(sample_raw_data)

        # 验证时间格式统一（排除无效时间）
        valid_times = result[result["submit_time"] != "NaT"]["submit_time"]
        for time_str in valid_times:
            # 确保time_str是字符串类型
            if pd.notna(time_str) and isinstance(time_str, str):
                assert len(time_str) == 19  # YYYY-MM-DD HH:MM:SS
                assert time_str[4] == "-"
                assert time_str[7] == "-"
                assert time_str[10] == " "
                assert time_str[13] == ":"
                assert time_str[16] == ":"

    def test_id_generation(self, cleaner, sample_raw_data):
        """测试ID字段生成和标准化"""
        result = cleaner.process(sample_raw_data)

        # 验证ID连续且为整数
        assert result["id"].notna().all()
        assert list(result["id"]) == list(range(1, len(result) + 1))

    # ========== 阶段2：数值字段处理测试 ==========

    def test_age_processing(self, cleaner, sample_raw_data):
        """测试年龄字段处理"""
        result = cleaner.process(sample_raw_data)

        # 验证年龄为数值类型（允许NULL）
        assert pd.api.types.is_numeric_dtype(result["age"])
        assert result["age"].iloc[0] == 25
        assert pd.isna(result["age"].iloc[3])

    def test_total_exp_processing(self, cleaner, sample_raw_data):
        """测试工作年限处理"""
        result = cleaner.process(sample_raw_data)

        assert result["total_exp"].iloc[0] == 3.0
        assert result["total_exp"].iloc[3] == 1.5
        assert pd.isna(result["total_exp"].iloc[4])

    def test_satisfaction_processing(self, cleaner, sample_raw_data):
        """测试满意度处理"""
        result = cleaner.process(sample_raw_data)

        assert result["overall_satis"].iloc[0] == 5
        assert pd.isna(result["overall_satis"].iloc[3])

    def test_workload_processing(self, cleaner, sample_raw_data):
        """测试工作负荷处理"""
        result = cleaner.process(sample_raw_data)

        assert result["workload"].iloc[0] == 7
        assert result["workload"].iloc[4] == 15  # 允许越界值，通过质量标记

    def test_tenure_processing(self, cleaner, sample_raw_data):
        """测试任期处理"""
        result = cleaner.process(sample_raw_data)

        assert result["tenure"].iloc[0] == 2.5
        assert result["tenure"].iloc[3] == 0.5

    def test_monthly_income_processing(self, cleaner, sample_raw_data):
        """测试月收入处理（负数转NULL）"""
        result = cleaner.process(sample_raw_data)

        # 验证负数被转为NULL
        assert result["monthly_income"].iloc[0] == 15000
        assert pd.isna(result["monthly_income"].iloc[3])  # 原值为 -5000

    # ========== 阶段3：分类字段标准化测试 ==========

    def test_gender_standardization(self, cleaner, sample_raw_data):
        """测试性别标准化"""
        result = cleaner.process(sample_raw_data)

        assert result["gender"].iloc[0] == "male"
        assert result["gender"].iloc[1] == "female"
        assert result["gender"].iloc[2] == "unknown"  # NULL -> unknown
        assert result["gender"].iloc[3] == "other"
        assert result["gender"].iloc[4] == "unknown"

    def test_education_standardization(self, cleaner, sample_raw_data):
        """测试教育程度标准化（MBA映射为硕士）"""
        result = cleaner.process(sample_raw_data)

        assert result["edu"].iloc[0] == "本科"
        assert result["edu"].iloc[1] == "硕士"
        assert result["edu"].iloc[2] == "硕士"  # MBA -> 硕士
        assert result["edu"].iloc[3] == "博士"

    def test_emp_status_standardization(self, cleaner, sample_raw_data):
        """测试雇佣状态标准化"""
        result = cleaner.process(sample_raw_data)

        assert result["emp_status"].iloc[0] == "在职"
        assert result["emp_status"].iloc[1] == "在职"
        assert result["emp_status"].iloc[2] == "实习生"
        assert result["emp_status"].iloc[3] == "非员工"  # 退休 -> 非员工
        assert result["emp_status"].iloc[4] == "非员工"  # 学生 -> 非员工

    def test_city_standardization(self, cleaner, sample_raw_data):
        """测试城市标准化"""
        result = cleaner.process(sample_raw_data)

        assert result["city"].iloc[0] == "北京"
        assert result["city"].iloc[1] == "上海"
        assert result["city"].iloc[2] == "未知城市"  # NULL -> 未知城市
        assert result["city"].iloc[3] == "深圳"
        assert result["city"].iloc[4] == "成都"

    def test_dept_standardization(self, cleaner, sample_raw_data):
        """测试部门标准化"""
        result = cleaner.process(sample_raw_data)

        assert result["dept"].iloc[0] == "研发部"
        assert result["dept"].iloc[3] == "其他"  # NULL -> 其他

    # ========== 阶段4：福利字段处理测试 ==========

    def test_benefits_boolean_conversion(self, cleaner, sample_raw_data):
        """测试福利字段转换为 boolean"""
        result = cleaner.process(sample_raw_data)

        # 验证所有福利字段都是 boolean 类型
        benefit_cols = ["benefit_pension", "benefit_annual_leave", "benefit_health_ins", "benefit_other"]
        for col in benefit_cols:
            assert pd.api.types.is_bool_dtype(result[col])

        # 验证值
        assert result["benefit_pension"].iloc[0] == True
        assert result["benefit_annual_leave"].iloc[1] == True

    # ========== 阶段5：备注字段处理测试 ==========

    def test_other_notes_processing(self, cleaner, sample_raw_data):
        """测试备注字段处理"""
        result = cleaner.process(sample_raw_data)

        assert result["other_notes"].iloc[0] == "正常"
        assert result["other_notes"].iloc[1] == ""  # 空字符串保持
        assert result["other_notes"].iloc[2] == ""  # NULL -> 空字符串

    # ========== 阶段6：重复检测测试 ==========

    def test_duplicate_detection(self, cleaner, duplicate_data):
        """测试重复记录检测"""
        result = cleaner.process(duplicate_data)

        # 第一条记录应该不标记为重复
        assert result["is_duplicate"].iloc[0] == False
        # 第二条记录是第一条的重复，应该标记
        assert result["is_duplicate"].iloc[1] == True
        # 第三条记录不重复
        assert result["is_duplicate"].iloc[2] == False

    # ========== 阶段7：数据质量标记测试 ==========

    def test_quality_flag_income_missing(self, cleaner, sample_raw_data):
        """测试收入缺失质量标记"""
        # 创建测试数据，收入缺失但其他条件满足
        test_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [25],
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [None],  # 收入缺失
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(test_df)

        # 月收入缺失的记录应该被标记
        assert result["data_quality_flag"].iloc[0] == "收入缺失"

    def test_quality_flag_key_fields_missing(self, cleaner, sample_raw_data):
        """测试关键字段缺失质量标记"""
        # 创建关键字段缺失的测试数据
        test_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [25],
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [None],  # 满意度缺失
            "工作负荷": [None],  # 工作负荷缺失
            "任期": [2.5],
            "月收入": [15000],  # 收入存在
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(test_df)

        # 缺少满意度或工作负荷的记录应该被标记
        assert result["data_quality_flag"].iloc[0] == "关键字段缺失"

    def test_quality_flag_test_data(self, cleaner, sample_raw_data):
        """测试测试数据质量标记"""
        # 创建专门的测试数据
        test_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [25],
            "工作年限": [3],
            "所属部门": ["测试部门"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [15000],
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(test_df)

        # 测试部门应该被标记
        assert result["data_quality_flag"].iloc[0] == "测试数据"

    def test_quality_flag_duplicate_records(self, cleaner, duplicate_data):
        """测试重复记录质量标记"""
        result = cleaner.process(duplicate_data)

        # 重复记录应该被标记
        assert result["data_quality_flag"].iloc[1] == "重复记录"

    def test_quality_flag_anomaly_values(self, cleaner, sample_raw_data):
        """测试异常值质量标记"""
        # 创建异常值记录（年龄 > 70）
        anomaly_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [150],  # 年龄 > 70
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [15000],
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(anomaly_df)

        # 年龄 > 70 或工作负荷 > 10 的记录应该被标记
        assert "异常值" in result["data_quality_flag"].iloc[0]

    def test_quality_flag_normal_records(self, cleaner, sample_raw_data):
        """测试正常记录质量标记"""
        # 创建正常记录
        normal_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [25],
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [15000],
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(normal_df)

        # 第一条记录应该是正常的
        assert result["data_quality_flag"].iloc[0] == "正常"

    # ========== 阶段8：字段选择与排序测试 ==========

    def test_column_selection_and_ordering(self, cleaner, sample_raw_data):
        """测试字段选择和排序"""
        result = cleaner.process(sample_raw_data)

        # 验证列的顺序符合预期
        expected_order = [
            "id", "submit_time", "age", "total_exp", "dept",
            "overall_satis", "workload", "benefit_pension",
            "benefit_annual_leave", "benefit_health_ins", "benefit_other",
            "other_notes", "gender", "edu", "emp_status",
            "tenure", "monthly_income", "city", "is_duplicate",
            "data_quality_flag"
        ]

        # 只验证实际存在的列的顺序
        actual_columns = [col for col in expected_order if col in result.columns]
        assert list(result.columns) == actual_columns

    # ========== 边界条件测试 ==========

    def test_empty_dataframe(self, cleaner):
        """测试空DataFrame处理"""
        empty_df = pd.DataFrame(columns=["提交时间", "年龄", "工作年限", "所属部门", "满意度",
                                         "工作负荷", "任期", "月收入", "性别", "教育程度",
                                         "雇佣状态", "城市"])
        result = cleaner.process(empty_df)

        assert len(result) == 0
        assert "id" in result.columns

    def test_single_record(self, cleaner):
        """测试单条记录处理"""
        single_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [25],
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [15000],
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })

        result = cleaner.process(single_df)

        assert len(result) == 1
        assert result["id"].iloc[0] == 1

    def test_all_null_values(self, cleaner):
        """测试全部为NULL值的记录"""
        null_df = pd.DataFrame({
            "提交时间": [None],
            "年龄": [None],
            "工作年限": [None],
            "所属部门": [None],
            "满意度": [None],
            "工作负荷": [None],
            "任期": [None],
            "月收入": [None],
            "性别": [None],
            "教育程度": [None],
            "雇佣状态": [None],
            "城市": [None]
        })

        result = cleaner.process(null_df)

        assert len(result) == 1
        assert result["gender"].iloc[0] == "unknown"
        assert result["city"].iloc[0] == "未知城市"
        assert result["dept"].iloc[0] == "其他"

    def test_large_dataset(self, cleaner):
        """测试大数据集处理性能"""
        # 创建1000条记录
        large_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"] * 1000,
            "年龄": [25] * 1000,
            "工作年限": [3] * 1000,
            "所属部门": ["研发部"] * 1000,
            "满意度": [5] * 1000,
            "工作负荷": [7] * 1000,
            "任期": [2.5] * 1000,
            "月收入": [15000] * 1000,
            "性别": ["男"] * 1000,
            "教育程度": ["本科"] * 1000,
            "雇佣状态": ["在职"] * 1000,
            "城市": ["北京"] * 1000
        })

        result = cleaner.process(large_df)

        assert len(result) == 1000
        assert result["id"].iloc[-1] == 1000

    # ========== 映射配置测试 ==========

    def test_gender_mapping_completeness(self, cleaner, sample_raw_data):
        """测试性别映射完整性"""
        result = cleaner.process(sample_raw_data)

        # 所有性别值都应该被映射到标准值
        valid_genders = {"male", "female", "other", "unknown"}
        for gender in result["gender"]:
            assert gender in valid_genders

    def test_education_mapping_with_mba(self, cleaner, sample_raw_data):
        """测试教育程度映射包含MBA"""
        result = cleaner.process(sample_raw_data)

        # MBA应该被映射为硕士
        assert result["edu"].iloc[2] == "硕士"

    def test_emp_status_mapping_special_cases(self, cleaner, sample_raw_data):
        """测试雇佣状态映射特殊情况"""
        result = cleaner.process(sample_raw_data)

        # 退休和学生应该映射为非员工
        assert result["emp_status"].iloc[3] == "非员工"
        assert result["emp_status"].iloc[4] == "非员工"

    # ========== 数据完整性测试 ==========

    def test_record_count_preservation(self, cleaner, sample_raw_data):
        """测试记录数量保持不变"""
        original_count = len(sample_raw_data)
        result = cleaner.process(sample_raw_data)

        assert len(result) == original_count

    def test_no_data_loss_in_transformation(self, cleaner, sample_raw_data):
        """测试数据转换过程中无数据丢失"""
        result = cleaner.process(sample_raw_data)

        # 验证原始数据中的关键信息都被保留
        assert sum(result["age"].notna()) == sum(sample_raw_data["年龄"].notna())
        assert sum(result["total_exp"].notna()) == sum(sample_raw_data["工作年限"].notna())

    # ========== 与契约合规性测试 ==========

    def test_contract_id_not_null_constraint(self, cleaner, sample_raw_data):
        """测试ID字段not_null约束"""
        result = cleaner.process(sample_raw_data)

        assert result["id"].notna().all()

    def test_contract_age_range_constraint(self, cleaner, sample_raw_data):
        """测试年龄范围约束（允许极端值）"""
        # 创建极端年龄的记录
        extreme_age_df = pd.DataFrame({
            "提交时间": ["2025-01-15 10:30:00"],
            "年龄": [150],  # 极端年龄
            "工作年限": [3],
            "所属部门": ["研发部"],
            "满意度": [5],
            "工作负荷": [7],
            "任期": [2.5],
            "月收入": [15000],
            "性别": ["男"],
            "教育程度": ["本科"],
            "雇佣状态": ["在职"],
            "城市": ["北京"]
        })
        result = cleaner.process(extreme_age_df)

        # 年龄应该允许极端值（如150），通过质量标记
        assert result["age"].iloc[0] == 150
        assert "异常值" in result["data_quality_flag"].iloc[0]

    def test_contract_monthly_income_negative_handling(self, cleaner, sample_raw_data):
        """测试月收入负数处理"""
        result = cleaner.process(sample_raw_data)

        # 负数应该被转为NULL
        assert pd.isna(result["monthly_income"].iloc[3])
