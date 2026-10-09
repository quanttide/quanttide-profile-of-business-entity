import argparse
import csv
import os
import sqlite3
import time

import pandas as pd


# -------------------------------- 配置区域 --------------------------------
UID_FILE = "uid.csv"
HISTORY_FILE = "pull_request_history.csv"
PULL_REQUESTS_FILE = "pull_requests.csv"
PROJECTS_FILE = "projects.csv"
USERS_FILE = "users.csv"
CACHE_FILE = "pr_authored_merged_cache.sqlite"
OUTPUT_FILE = "daily_pr_authored_merged.csv"
REPORT_FILE = "pr_reconciliation_report.txt"

START_DATE = "2011-01-01"
END_DATE = "2021-03-06"
CHUNK_SIZE = 500_000
# 二期模块旧面板的 external 总数，用于在核对报告中展示可比口径。
OLD_EXTERNAL_BASELINE = 66_614

HISTORY_COLUMNS = ["id", "pull_request_id", "created_at", "action", "actor_id"]
PR_COLUMNS = [
    "id", "head_repo_id", "base_repo_id", "head_commit_id", "base_commit_id",
    "pullreq_id", "intra_branch",
]
PROJECT_COLUMNS = [
    "id", "url", "owner_id", "name", "description", "language", "created_at",
    "forked_from", "deleted", "updated_at", "forked_commit_id",
]
USER_COLUMNS = [
    "id", "login", "company", "created_at", "type", "fake", "deleted", "long",
    "lat", "country_code", "state", "city", "location",
]


def require_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")


def has_header(path, expected_first_column):
    first = pd.read_csv(path, header=None, nrows=1, dtype="string", na_values=["\\N"])
    return not first.empty and str(first.iloc[0, 0]).strip().lower() == expected_first_column


def csv_reader(path, columns, **kwargs):
    """读取可能有或没有表头的 GHTorrent CSV 文件。"""
    return pd.read_csv(
        path,
        header=0 if has_header(path, columns[0]) else None,
        names=columns,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        encoding="utf-8",
        on_bad_lines="skip",
        na_values=["\\N"],
        **kwargs,
    )


def setup_database(reset_cache):
    if reset_cache and os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    conn = sqlite3.connect(CACHE_FILE)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = FILE")
    conn.execute("CREATE TABLE IF NOT EXISTS pipeline_state (step TEXT PRIMARY KEY)")
    return conn


def step_done(conn, step):
    return conn.execute("SELECT 1 FROM pipeline_state WHERE step = ?", (step,)).fetchone() is not None


def mark_done(conn, step):
    conn.execute("INSERT OR IGNORE INTO pipeline_state(step) VALUES (?)", (step,))
    conn.commit()


def reset_tables(conn, *tables):
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()


def dataframe_to_table(frame, table, conn):
    """将已向量化筛选的 DataFrame 结果批量写入 SQLite。"""
    if not frame.empty:
        # 每次 INSERT 的绑定变量数保持在 SQLite 的保守上限以内。
        frame.to_sql(table, conn, if_exists="append", index=False, method="multi", chunksize=200)


def load_targets(conn):
    if step_done(conn, "targets"):
        return
    reset_tables(conn, "target_users")
    users = pd.read_csv(UID_FILE, dtype="string", na_values=["\\N"])
    if "uid" not in users.columns:
        raise ValueError(f"{UID_FILE} must contain a 'uid' column")
    users = users[["uid"]].dropna().drop_duplicates().rename(columns={"uid": "user_id"})
    dataframe_to_table(users, "target_users", conn)
    conn.execute("CREATE UNIQUE INDEX idx_target_users ON target_users(user_id)")
    mark_done(conn, "targets")


def extract_primary_history(conn):
    """对每个数据块向量化筛选，并持久化相关的原始事件。"""
    if step_done(conn, "primary_history"):
        print("Step 1/5 already complete; reusing cached history events.")
        return
    reset_tables(conn, "raw_authored_opens", "raw_merged_events", "authored_opens", "merged_events")
    target_users = set(pd.read_sql_query("SELECT user_id FROM target_users", conn)["user_id"])
    total_rows = 0
    for chunk in csv_reader(
        HISTORY_FILE,
        HISTORY_COLUMNS,
        dtype={"pull_request_id": "string", "actor_id": "string", "action": "string", "created_at": "string"},
    ):
        total_rows += len(chunk)
        chunk = chunk.dropna(subset=["pull_request_id", "action", "created_at"]).copy()
        chunk["event_date"] = chunk["created_at"].astype("string").str.slice(0, 10)

        opens = chunk.loc[
            (chunk["action"] == "opened")
            & chunk["actor_id"].notna()
            & chunk["actor_id"].isin(target_users)
            & chunk["event_date"].between(START_DATE, END_DATE),
            ["pull_request_id", "actor_id", "event_date"],
        ].rename(columns={"pull_request_id": "pr_id", "actor_id": "author_id", "event_date": "open_date"})
        merges = chunk.loc[
            chunk["action"] == "merged", ["pull_request_id", "event_date"]
        ].rename(columns={"pull_request_id": "pr_id", "event_date": "merge_date"})
        dataframe_to_table(opens, "raw_authored_opens", conn)
        dataframe_to_table(merges, "raw_merged_events", conn)
        if total_rows % 1_000_000 == 0:
            conn.commit()
            print(f"  history scan: {total_rows:,} rows")

    # 窗口函数保留与最早日期对应的 actor。
    conn.executescript("""
        CREATE TABLE authored_opens AS
        SELECT pr_id, author_id, open_date
        FROM (
            SELECT pr_id, author_id, open_date,
                   ROW_NUMBER() OVER (PARTITION BY pr_id ORDER BY open_date, author_id) AS rn
            FROM raw_authored_opens
        ) WHERE rn = 1;
        CREATE UNIQUE INDEX idx_authored_opens_pr ON authored_opens(pr_id);

        CREATE TABLE merged_events AS
        SELECT pr_id, MIN(merge_date) AS merge_date
        FROM raw_merged_events
        GROUP BY pr_id;
        CREATE UNIQUE INDEX idx_merged_events_pr ON merged_events(pr_id);
    """)
    conn.commit()
    mark_done(conn, "primary_history")


def extract_fallback_authors(conn):
    """仅重新扫描逻辑上未匹配的 PR，不将其 ID 全部保存在内存中。"""
    if step_done(conn, "fallback_history"):
        print("Step 2/5 already complete; reusing cached fallback authors.")
        return
    reset_tables(conn, "fallback_candidates", "raw_fallback_events", "fallback_authors", "authored_prs", "stage_history")
    conn.executescript("""
        CREATE TABLE fallback_candidates AS
        SELECT m.pr_id
        FROM merged_events AS m
        LEFT JOIN authored_opens AS o ON o.pr_id = m.pr_id
        WHERE o.pr_id IS NULL;
        CREATE UNIQUE INDEX idx_fallback_candidates_pr ON fallback_candidates(pr_id);
        CREATE TABLE raw_fallback_events (pr_id TEXT, actor_id TEXT, event_date TEXT);
        CREATE TABLE stage_history (pr_id TEXT, actor_id TEXT, event_date TEXT);
    """)
    candidate_count = conn.execute("SELECT COUNT(*) FROM fallback_candidates").fetchone()[0]
    total_rows = 0
    for chunk in csv_reader(
        HISTORY_FILE,
        HISTORY_COLUMNS,
        dtype={"pull_request_id": "string", "actor_id": "string", "created_at": "string"},
    ):
        total_rows += len(chunk)
        # 兜底规则使用最早有效历史记录而不是最早 merged 记录，因此无需 action 字段。
        stage = chunk.dropna(subset=["pull_request_id", "actor_id", "created_at"])[
            ["pull_request_id", "actor_id", "created_at"]
        ].copy()
        stage["event_date"] = stage["created_at"].astype("string").str.slice(0, 10)
        stage = stage[["pull_request_id", "actor_id", "event_date"]].rename(
            columns={"pull_request_id": "pr_id"}
        )
        conn.execute("DELETE FROM stage_history")
        dataframe_to_table(stage, "stage_history", conn)
        conn.execute("""
            INSERT INTO raw_fallback_events(pr_id, actor_id, event_date)
            SELECT s.pr_id, s.actor_id, s.event_date
            FROM stage_history AS s
            INNER JOIN fallback_candidates AS f ON f.pr_id = s.pr_id
        """)
        if total_rows % 1_000_000 == 0:
            conn.commit()
            print(f"  fallback scan: {total_rows:,} rows")

    conn.executescript("""
        CREATE TABLE fallback_authors AS
        SELECT pr_id, actor_id AS author_id, event_date AS open_date
        FROM (
            SELECT e.pr_id, e.actor_id, e.event_date,
                   ROW_NUMBER() OVER (PARTITION BY e.pr_id ORDER BY e.event_date, e.actor_id) AS rn
            FROM raw_fallback_events AS e
        ) AS earliest
        INNER JOIN target_users AS t ON t.user_id = earliest.actor_id
        WHERE rn = 1
          AND event_date >= '2011-01-01'
          AND event_date <= '2021-03-06';
        CREATE UNIQUE INDEX idx_fallback_authors_pr ON fallback_authors(pr_id);

        CREATE TABLE authored_prs AS
        SELECT pr_id, author_id, open_date, 'opened' AS author_source FROM authored_opens
        UNION ALL
        SELECT pr_id, author_id, open_date, 'fallback' AS author_source FROM fallback_authors;
        CREATE UNIQUE INDEX idx_authored_prs_pr ON authored_prs(pr_id);
    """)
    conn.commit()
    mark_done(conn, "fallback_history")
    print(f"  fallback candidates: {candidate_count:,}")


def attach_pr_metadata(conn):
    if step_done(conn, "pr_metadata"):
        print("Step 3/5 already complete; reusing cached PR metadata.")
        return
    reset_tables(conn, "pr_metadata", "stage_prs")
    conn.execute("CREATE TABLE pr_metadata (pr_id TEXT PRIMARY KEY, base_repo_id TEXT, intra_branch INTEGER)")
    conn.execute("CREATE TABLE stage_prs (pr_id TEXT, base_repo_id TEXT, intra_branch TEXT)")
    total_rows = 0
    for chunk in csv_reader(
        PULL_REQUESTS_FILE,
        PR_COLUMNS,
        usecols=["id", "base_repo_id", "intra_branch"],
        dtype={"id": "string", "base_repo_id": "string", "intra_branch": "string"},
    ):
        total_rows += len(chunk)
        stage = chunk.rename(columns={"id": "pr_id"})
        conn.execute("DELETE FROM stage_prs")
        dataframe_to_table(stage, "stage_prs", conn)
        conn.execute("""
            INSERT OR REPLACE INTO pr_metadata(pr_id, base_repo_id, intra_branch)
            SELECT s.pr_id, s.base_repo_id, CASE WHEN TRIM(s.intra_branch) = '1' THEN 1 ELSE 0 END
            FROM stage_prs AS s
            INNER JOIN authored_prs AS a ON a.pr_id = s.pr_id
            INNER JOIN merged_events AS m ON m.pr_id = s.pr_id
        """)
        if total_rows % 5_000_000 == 0:
            conn.commit()
            print(f"  pull_requests scan: {total_rows:,} rows")
    conn.commit()
    mark_done(conn, "pr_metadata")


def attach_ownership_metadata(conn):
    if step_done(conn, "ownership"):
        print("Step 4/5 already complete; reusing cached ownership metadata.")
        return
    reset_tables(conn, "repo_owners", "owner_types", "stage_projects", "stage_users")
    conn.execute("CREATE TABLE repo_owners (base_repo_id TEXT PRIMARY KEY, owner_id TEXT)")
    conn.execute("CREATE TABLE stage_projects (base_repo_id TEXT, owner_id TEXT)")
    total_rows = 0
    for chunk in csv_reader(
        PROJECTS_FILE,
        PROJECT_COLUMNS,
        usecols=["id", "owner_id"],
        dtype={"id": "string", "owner_id": "string"},
    ):
        total_rows += len(chunk)
        stage = chunk.dropna(subset=["owner_id"]).rename(columns={"id": "base_repo_id"})
        conn.execute("DELETE FROM stage_projects")
        dataframe_to_table(stage, "stage_projects", conn)
        conn.execute("""
            INSERT OR REPLACE INTO repo_owners(base_repo_id, owner_id)
            SELECT s.base_repo_id, s.owner_id
            FROM stage_projects AS s
            INNER JOIN pr_metadata AS p ON p.base_repo_id = s.base_repo_id
            WHERE p.intra_branch = 0
        """)
        if total_rows % 10_000_000 == 0:
            conn.commit()
            print(f"  projects scan: {total_rows:,} rows")

    conn.execute("CREATE TABLE owner_types (owner_id TEXT PRIMARY KEY, owner_type TEXT)")
    conn.execute("CREATE TABLE stage_users (owner_id TEXT, owner_type TEXT)")
    total_rows = 0
    for chunk in csv_reader(
        USERS_FILE,
        USER_COLUMNS,
        usecols=["id", "type"],
        dtype={"id": "string", "type": "string"},
    ):
        total_rows += len(chunk)
        stage = chunk.dropna(subset=["type"]).rename(columns={"id": "owner_id", "type": "owner_type"})
        conn.execute("DELETE FROM stage_users")
        dataframe_to_table(stage, "stage_users", conn)
        conn.execute("""
            INSERT OR REPLACE INTO owner_types(owner_id, owner_type)
            SELECT s.owner_id, UPPER(TRIM(s.owner_type))
            FROM stage_users AS s
            INNER JOIN repo_owners AS r ON r.owner_id = s.owner_id
        """)
        if total_rows % 10_000_000 == 0:
            conn.commit()
            print(f"  users scan: {total_rows:,} rows")
    conn.commit()
    mark_done(conn, "ownership")


def export_panel_and_report(conn, elapsed_seconds):
    print("Step 5/5: classifying PRs and writing output files...")
    classified_sql = """
        WITH merged_authored AS (
            SELECT a.pr_id, a.author_id, a.open_date, a.author_source, m.merge_date,
                   p.base_repo_id, p.intra_branch, r.owner_id, u.owner_type
            FROM authored_prs AS a
            INNER JOIN merged_events AS m ON m.pr_id = a.pr_id
            LEFT JOIN pr_metadata AS p ON p.pr_id = a.pr_id
            LEFT JOIN repo_owners AS r ON r.base_repo_id = p.base_repo_id
            LEFT JOIN owner_types AS u ON u.owner_id = r.owner_id
        ), classified AS (
            SELECT *,
                CASE
                    WHEN base_repo_id IS NULL THEN 'unknown'
                    WHEN intra_branch = 1 THEN 'self'
                    WHEN owner_id IS NULL THEN 'unknown'
                    WHEN owner_id = author_id THEN 'self'
                    WHEN owner_type IS NULL THEN 'unknown'
                    WHEN owner_type = 'ORG' THEN 'org'
                    ELSE 'external'
                END AS category,
                CAST(julianday(merge_date) - julianday(open_date) AS INTEGER) AS merge_lag_days
            FROM merged_authored
        ), authored_counts AS (
            SELECT author_id, open_date, COUNT(*) AS authored_pr_opened_count
            FROM authored_prs
            GROUP BY author_id, open_date
        ), merged_counts AS (
            SELECT author_id, open_date,
                COUNT(*) AS merged_pr_count,
                SUM(category = 'self') AS self_pr_merged_count,
                SUM(category = 'org') AS org_pr_merged_count,
                SUM(category = 'external') AS external_pr_merged_count,
                SUM(category = 'unknown') AS unknown_pr_merged_count,
                AVG(merge_lag_days) AS merge_lag_mean
            FROM classified
            GROUP BY author_id, open_date
        )
        SELECT a.author_id, a.open_date, a.authored_pr_opened_count,
               COALESCE(m.merged_pr_count, 0) AS merged_pr_count,
               COALESCE(m.self_pr_merged_count, 0) AS self_pr_merged_count,
               COALESCE(m.org_pr_merged_count, 0) AS org_pr_merged_count,
               COALESCE(m.external_pr_merged_count, 0) AS external_pr_merged_count,
               COALESCE(m.unknown_pr_merged_count, 0) AS unknown_pr_merged_count,
               m.merge_lag_mean
        FROM authored_counts AS a
        LEFT JOIN merged_counts AS m ON m.author_id = a.author_id AND m.open_date = a.open_date
        ORDER BY a.author_id, a.open_date
    """
    panel = pd.read_sql_query(classified_sql, conn)
    count_columns = [
        "self_pr_merged_count", "org_pr_merged_count", "external_pr_merged_count",
        "unknown_pr_merged_count",
    ]
    assert (panel[count_columns].sum(axis=1) == panel["merged_pr_count"]).all(), "Panel reconciliation failed"
    panel.to_csv(OUTPUT_FILE, index=False, encoding="utf-8", float_format="%.6f")

    counts = {
        name: conn.execute(query).fetchone()[0]
        for name, query in {
            "target_users": "SELECT COUNT(*) FROM target_users",
            "observed_opens": "SELECT COUNT(*) FROM authored_opens",
            "all_merged": "SELECT COUNT(*) FROM merged_events",
            "merged_authored": "SELECT COUNT(*) FROM authored_prs a INNER JOIN merged_events m ON m.pr_id = a.pr_id",
            "fallback_merged": "SELECT COUNT(*) FROM fallback_authors f INNER JOIN merged_events m ON m.pr_id = f.pr_id",
            "fallback_candidates": "SELECT COUNT(*) FROM fallback_candidates",
            "missing_pr_metadata": "SELECT COUNT(*) FROM authored_prs a INNER JOIN merged_events m ON m.pr_id=a.pr_id LEFT JOIN pr_metadata p ON p.pr_id=a.pr_id WHERE p.pr_id IS NULL",
            "unresolved_repos": "SELECT COUNT(DISTINCT p.base_repo_id) FROM pr_metadata p LEFT JOIN repo_owners r ON r.base_repo_id=p.base_repo_id WHERE p.intra_branch=0 AND r.base_repo_id IS NULL",
            "missing_owner_types": "SELECT COUNT(DISTINCT r.owner_id) FROM repo_owners r LEFT JOIN owner_types u ON u.owner_id=r.owner_id WHERE u.owner_id IS NULL",
            "negative_lags": "SELECT COUNT(*) FROM authored_prs a INNER JOIN merged_events m ON m.pr_id=a.pr_id WHERE julianday(m.merge_date) < julianday(a.open_date)",
        }.items()
    }
    category_counts = pd.read_sql_query("""
        WITH x AS (
            SELECT CASE
                WHEN p.base_repo_id IS NULL THEN 'unknown'
                WHEN p.intra_branch = 1 THEN 'self'
                WHEN r.owner_id IS NULL THEN 'unknown'
                WHEN r.owner_id = a.author_id THEN 'self'
                WHEN u.owner_type IS NULL THEN 'unknown'
                WHEN u.owner_type = 'ORG' THEN 'org'
                ELSE 'external' END AS category
            FROM authored_prs a INNER JOIN merged_events m ON m.pr_id=a.pr_id
            LEFT JOIN pr_metadata p ON p.pr_id=a.pr_id
            LEFT JOIN repo_owners r ON r.base_repo_id=p.base_repo_id
            LEFT JOIN owner_types u ON u.owner_id=r.owner_id
        ) SELECT category, COUNT(*) AS n FROM x GROUP BY category
    """, conn).set_index("category")["n"].to_dict()
    fallback_share = 0 if not counts["merged_authored"] else counts["fallback_merged"] / counts["merged_authored"] * 100
    third_party_total = (
        category_counts.get("org", 0)
        + category_counts.get("external", 0)
        + category_counts.get("unknown", 0)
    )
    third_party_delta = third_party_total - OLD_EXTERNAL_BASELINE
    third_party_change = 0 if not OLD_EXTERNAL_BASELINE else third_party_delta / OLD_EXTERNAL_BASELINE * 100
    comparison_note = (
        "核验通过：新版可比第三方采纳总量高于二期模块旧 external 基准。"
        if third_party_total >= OLD_EXTERNAL_BASELINE
        else "警告：新版可比第三方采纳总量低于二期模块旧 external 基准，请在交付前复核。"
    )
    report = [
        "=" * 72,
        "PR 作者归属与采纳指标核对报告",
        "=" * 72,
        f"样本窗口（open_date）：{START_DATE} 至 {END_DATE}",
        f"目标用户数：{counts['target_users']:,}",
        f"窗口内目标用户 opened PR 数：{counts['observed_opens']:,}",
        f"全量存在 merged 事件的 PR 数：{counts['all_merged']:,}",
        f"最终纳入面板的“作者提交且被合并”PR 数：{counts['merged_authored']:,}",
        "-" * 72,
        "【opened 缺失兜底】",
        f"有 merged 但未匹配到目标用户 opened 的候选 PR 数：{counts['fallback_candidates']:,}",
        f"经最早有效历史记录兜底后纳入的已合并 PR 数：{counts['fallback_merged']:,}（占最终样本 {fallback_share:.2f}%）",
        "-" * 72,
        "【合并 PR 分类】",
        f"本人仓库合并（self）：{category_counts.get('self', 0):,}",
        f"组织仓库合并（org）：{category_counts.get('org', 0):,}",
        f"其他个人仓库合并（external）：{category_counts.get('external', 0):,}",
        f"无法确权（unknown）：{category_counts.get('unknown', 0):,}",
        f"可比第三方采纳（org + external + unknown）：{third_party_total:,}",
        "-" * 72,
        "【与二期模块旧口径的可比核验】",
        f"二期模块旧 external 总数：{OLD_EXTERNAL_BASELINE:,}",
        f"新版可比第三方采纳总数：{third_party_total:,}",
        f"差异：{third_party_delta:+,}（{third_party_change:+.2f}%）",
        comparison_note,
        "说明：旧 external 未单列组织仓库，故不得直接与新版纯个人 external 比较。",
        "-" * 72,
        "【数据质量与约束】",
        f"缺失 pull_requests 元数据的已合并 PR 数：{counts['missing_pr_metadata']:,}",
        f"无法确权的目标仓库数：{counts['unresolved_repos']:,}",
        f"已确权但缺失 users.type 的 owner 数：{counts['missing_owner_types']:,}",
        f"merge_date 早于 open_date 的异常 PR 数：{counts['negative_lags']:,}",
        "逐行校验通过：self + org + external + unknown = merged_pr_count。",
        "测度边界：GHTorrent 的 merged 事件仅代表可观测采纳，实际采纳数量可能更高。",
        "=" * 72,
    ]
    with open(REPORT_FILE, "w", encoding="utf-8") as handle:
        handle.write("\n".join(report) + "\n")


def run(reset_cache=False):
    for path in [UID_FILE, HISTORY_FILE, PULL_REQUESTS_FILE, PROJECTS_FILE, USERS_FILE]:
        require_file(path)
    started = time.time()
    conn = setup_database(reset_cache)
    try:
        load_targets(conn)
        extract_primary_history(conn)
        extract_fallback_authors(conn)
        attach_pr_metadata(conn)
        attach_ownership_metadata(conn)
        export_panel_and_report(conn, time.time() - started)
    finally:
        conn.close()
    print(f"Completed. Outputs: {OUTPUT_FILE}, {REPORT_FILE}")
    print(f"Cache retained for resume: {CACHE_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a resumable authored-and-merged PR panel.")
    parser.add_argument(
        "--reset-cache", action="store_true",
        help="Delete the SQLite cache and recompute all stages from source CSV files.",
    )
    run(reset_cache=parser.parse_args().reset_cache)
