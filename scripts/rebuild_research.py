#!/usr/bin/env python3
"""Rebuild source backlog, launch-platform watchlist, and alert candidates."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATE = DATA / "state"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def source_score(row: dict[str, str]) -> int:
    source_type = row.get("source_type_guess", "")
    tag = row.get("narrative_tag", "")
    status = row.get("source_status", "")
    score = 0
    if "company" in source_type or "project" in source_type:
        score += 18
    if "person" in source_type or "founder" in tag:
        score += 16
    if "ai_agent" in tag:
        score += 8
    if "binance" in tag:
        score += 10
    if "chinese_social_meme" in tag or "unmapped_chinese_meme" in tag:
        score += 8
    if status in {"已验证", "verified", "partial"}:
        score += 8
    if row.get("earliest_source_url"):
        score += 8
    return min(score, 25)


def time_advantage_score(row: dict[str, str]) -> int:
    bucket = row.get("first_buy_bucket", "")
    minutes_to_sell = to_float(row.get("minutes_to_first_sell"))
    score = 0
    if bucket == "0-50k":
        score += 14
    elif bucket in {"50k-100k", "100k-200k"}:
        score += 8
    if minutes_to_sell <= 5:
        score += 3
    if row.get("buy_vs_source_window") in {"同日", "source before buy", "pre-amplification"}:
        score += 4
    return min(score, 20)


def onchain_score(row: dict[str, str]) -> int:
    fdv = to_float(row.get("first_buy_fdv_usd"))
    liq = to_float(row.get("first_buy_approx_liquidity_usd_after"))
    buy_bnb = to_float(row.get("buy_bnb"))
    score = 0
    if 0 < fdv <= 50_000:
        score += 8
    elif fdv <= 100_000:
        score += 4
    if 1_000 <= liq <= 30_000:
        score += 5
    if 0 < buy_bnb <= 1.5:
        score += 4
    if to_float(row.get("realized_pnl_bnb")) > 0:
        score += 3
    return min(score, 20)


def risk_penalty(row: dict[str, str]) -> int:
    penalty = 0
    tag = row.get("narrative_tag", "")
    source_type = row.get("source_type_guess", "")
    if tag == "unknown" or source_type == "unknown":
        penalty -= 12
    if "person_name_only" in source_type:
        penalty -= 20
    if to_float(row.get("first_buy_fdv_usd")) > 100_000:
        penalty -= 8
    if not row.get("earliest_source_url"):
        penalty -= 5
    return max(penalty, -50)


def build_source_backlog(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sorted(candidates, key=lambda r: to_float(r.get("research_priority")), reverse=True):
        s_score = source_score(row)
        t_score = time_advantage_score(row)
        c_score = onchain_score(row)
        novelty = 12 if row.get("narrative_tag") not in {"unknown", "pure_meme"} else 5
        penalty = risk_penalty(row)
        total = max(0, s_score + t_score + c_score + novelty + penalty)
        status = row.get("source_status") or "待追踪"
        if row.get("earliest_source_url"):
            next_step = "复核原始发布时间、截图和放大账号"
        elif "chinese" in row.get("narrative_tag", "") or "meme" in row.get("source_type_guess", ""):
            next_step = "补 Douyin/B站/微博首发、热榜和音频复用量"
        elif "binance" in row.get("narrative_tag", ""):
            next_step = "补 Binance/CZ/BNB Chain 官方原帖与 Four.meme 开池时间"
        elif "ai_agent" in row.get("narrative_tag", ""):
            next_step = "补项目官网、模型/agent 发布页、GitHub/产品库收录时间"
        else:
            next_step = "用 token 名称、部署时间和早期传播账号做源头检索"
        rows.append(
            {
                "priority_score": total,
                "research_priority": row.get("research_priority", ""),
                "token_label": row.get("token_label", ""),
                "token_address": row.get("token", ""),
                "first_buy_time_utc": row.get("first_buy_time_utc", ""),
                "first_buy_bucket": row.get("first_buy_bucket", ""),
                "realized_pnl_bnb": row.get("realized_pnl_bnb", ""),
                "narrative_tag": row.get("narrative_tag", ""),
                "source_type_guess": row.get("source_type_guess", ""),
                "source_status": status,
                "source_score": s_score,
                "time_advantage_score": t_score,
                "onchain_score": c_score,
                "risk_penalty": penalty,
                "next_research_step": next_step,
            }
        )
    return rows


def build_alert_candidates(backlog: list[dict[str, Any]], platforms: list[dict[str, str]], min_score: int) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for row in backlog:
        score = int(to_float(row.get("priority_score")))
        if score < min_score:
            continue
        if row.get("source_type_guess") == "unknown" and row.get("risk_penalty", 0) <= -12:
            action = "watchlist_only"
        elif score >= 70:
            action = "email_review"
        else:
            action = "email_watch"
        alerts.append(
            {
                "alert_id": f"SRC-{len(alerts)+1:04d}",
                "score": score,
                "action": action,
                "token_label": row.get("token_label", ""),
                "token_address": row.get("token_address", ""),
                "source_type": row.get("source_type_guess", ""),
                "narrative_tag": row.get("narrative_tag", ""),
                "first_buy_time_utc": row.get("first_buy_time_utc", ""),
                "reason": row.get("next_research_step", ""),
            }
        )
    for platform in platforms:
        score = int(to_float(platform.get("watch_priority")))
        if score >= min_score:
            alerts.append(
                {
                    "alert_id": f"PLAT-{platform.get('platform_id')}",
                    "score": score,
                    "action": "platform_watch",
                    "token_label": platform.get("platform_name", ""),
                    "token_address": "",
                    "source_type": platform.get("platform_type", ""),
                    "narrative_tag": "launch_platform",
                    "first_buy_time_utc": "",
                    "reason": platform.get("what_to_monitor", ""),
                }
            )
    return sorted(alerts, key=lambda r: int(to_float(r.get("score"))), reverse=True)


def classify_leader(row: dict[str, str]) -> tuple[str, int]:
    bucket = row.get("first_buy_bucket", "")
    liq = to_float(row.get("first_buy_approx_liquidity_usd_after"))
    priority = to_float(row.get("research_priority"))
    tag = row.get("narrative_tag", "")
    score = 0
    if bucket == "0-50k":
        score += 25
    elif bucket in {"50k-100k", "100k-200k"}:
        score += 12
    if 1_000 <= liq <= 30_000:
        score += 15
    if priority >= 100:
        score += 15
    if tag not in {"unknown", "pure_meme"}:
        score += 15
    if row.get("leader_or_copycat") == "leader":
        score += 20
    if score >= 70:
        label = "leader_candidate"
    elif score >= 45:
        label = "needs_human_check"
    else:
        label = "likely_copycat_or_noise"
    return label, min(score, 100)


def build_radar_model(candidates: list[dict[str, str]], platforms: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "module_id": "RADAR_SOURCE_DISCOVERY",
            "module_name": "源头发现",
            "trigger": "公司/创始人/项目/KOL/中文热梗/发币平台出现新叙事",
            "inputs": "X/Twitter, official sites, GitHub, product pages, Douyin/Bilibili/微博, launch platforms",
            "outputs": "source_event_id, source_time_utc, source_url, source_grade, source_entity",
            "score_fields": "source_quality_score,narrative_novelty_score",
            "human_gate": "必须复核原始链接或截图；无源头的名人名 token 降权",
            "automation_status": "radar_only",
        },
        {
            "module_id": "RADAR_FIRST_TOKEN_BATCH",
            "module_name": "第一批 token 捕捉",
            "trigger": "源头出现后监控 Four.meme/Pancake/launchpad 新 token",
            "inputs": "token deploy, pool creation, first swaps, token name/symbol similarity",
            "outputs": "token_address, deploy_time_utc, pool_time_utc, first_trade_time_utc, narrative_match",
            "score_fields": "time_advantage_score,source_match_score",
            "human_gate": "同名不等于强相关；需要看部署时间和源头语义是否匹配",
            "automation_status": "radar_only",
        },
        {
            "module_id": "RADAR_MARKET_WINDOW",
            "module_name": "FDV/流动性/成交窗口",
            "trigger": "首池形成和前几分钟成交出现",
            "inputs": "FDV, pool BNB/USD liquidity, buy/sell count, volume, unique buyers",
            "outputs": "fdv_bucket, liquidity_bucket, trade_window, onchain_quality_score",
            "score_fields": "onchain_quality_score,liquidity_execution_score",
            "human_gate": "薄池、异常税、疑似貔貅、假流动性直接跳过",
            "automation_status": "manual_confirm_only",
        },
        {
            "module_id": "RADAR_LEADER_COPYCAT",
            "module_name": "leader/copycat 判断",
            "trigger": "同一叙事短时间出现多个 token",
            "inputs": "deploy order, first liquidity, first volume, holder growth, source semantic fit",
            "outputs": "leader_score, leader_or_copycat, competing_tokens",
            "score_fields": "leader_score,risk_penalty",
            "human_gate": "只把 leader_candidate 推人工确认；copycat 默认观察",
            "automation_status": "manual_confirm_only",
        },
        {
            "module_id": "RADAR_HUMAN_CONFIRM",
            "module_name": "人工确认推送",
            "trigger": "总分达到提醒阈值",
            "inputs": "source evidence + onchain window + leader score + risk flags",
            "outputs": "email/telegram alert, review checklist, postmortem id",
            "score_fields": "total_radar_score",
            "human_gate": "样本库足够大之前，不自动买入",
            "automation_status": "alert_only",
        },
    ]
    rows.extend(
        {
            "module_id": f"PLATFORM_{platform.get('platform_id')}",
            "module_name": platform.get("platform_name", ""),
            "trigger": platform.get("what_to_monitor", ""),
            "inputs": "new launches, pool creation, creator/deployer, liquidity, first buyers",
            "outputs": "platform_event_id, platform_time_utc, candidate_token_batch",
            "score_fields": "platform_priority,launch_quality_score",
            "human_gate": platform.get("known_risks", ""),
            "automation_status": "platform_watch",
        }
        for platform in platforms
    )
    return rows


def build_time_edges(candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidates:
        token = row.get("token")
        token_label = row.get("token_label")
        first_buy = row.get("first_buy_time_utc")
        first_exit_window = row.get("first_exit_window", "")
        holding_window = row.get("holding_window", "")
        leader_label, leader_score = classify_leader(row)
        rows.append(
            {
                "token_label": token_label,
                "token_address": token,
                "source_time_utc": row.get("earliest_source_time_utc", ""),
                "token_deploy_time_utc": "",
                "pool_formed_time_utc": "",
                "first_trade_time_utc": "",
                "trader_first_buy_time_utc": first_buy,
                "first_amplifier_time_utc": "",
                "price_breakout_time_utc": "",
                "source_to_deploy_min": "",
                "deploy_to_pool_min": "",
                "pool_to_trader_buy_min": "",
                "trader_buy_to_amplifier_min": "",
                "amplifier_to_breakout_min": "",
                "first_exit_window": first_exit_window,
                "holding_window": holding_window,
                "leader_or_copycat": leader_label,
                "leader_score": leader_score,
                "status": "needs_source_and_platform_timestamps",
            }
        )
    return rows


def build_human_review_queue(backlog: list[dict[str, Any]], candidates: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_token = {row.get("token"): row for row in candidates}
    rows: list[dict[str, Any]] = []
    for item in backlog[:80]:
        candidate = by_token.get(item.get("token_address"), {})
        leader_label, leader_score = classify_leader(candidate)
        total = int(to_float(item.get("priority_score"))) + int(leader_score * 0.25)
        action = "人工确认" if total >= 75 else "观察补证据"
        rows.append(
            {
                "review_id": f"REV-{len(rows)+1:04d}",
                "total_radar_score": total,
                "action": action,
                "token_label": item.get("token_label", ""),
                "token_address": item.get("token_address", ""),
                "leader_or_copycat": leader_label,
                "leader_score": leader_score,
                "fdv_bucket": item.get("first_buy_bucket", ""),
                "source_type": item.get("source_type_guess", ""),
                "narrative_tag": item.get("narrative_tag", ""),
                "time_edge_missing": "source/deploy/pool/amplifier/breakout",
                "next_human_check": item.get("next_research_step", ""),
            }
        )
    return sorted(rows, key=lambda r: int(to_float(r.get("total_radar_score"))), reverse=True)


def build_email_preview(alerts: list[dict[str, Any]]) -> str:
    lines = [
        "# BSC Four.meme Source Alerts",
        "",
        f"Generated at UTC: {utc_now()}",
        "",
        "This is a dry-run preview. No email was sent.",
        "",
    ]
    for alert in alerts[:20]:
        lines.extend(
            [
                f"## {alert['alert_id']} / score {alert['score']} / {alert['action']}",
                f"- Target: {alert['token_label']}",
                f"- Type: {alert['source_type']} / {alert['narrative_tag']}",
                f"- Token: {alert['token_address']}",
                f"- Reason: {alert['reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild narrative source research package")
    parser.add_argument("--min-alert-score", type=int, default=int(os.environ.get("MIN_ALERT_SCORE", "60")))
    args = parser.parse_args()

    candidates = read_csv(DATA / "narrative_candidates.csv")
    platforms = read_csv(DATA / "launch_platforms.csv")
    backlog = build_source_backlog(candidates)
    alerts = build_alert_candidates(backlog, platforms, args.min_alert_score)
    radar_model = build_radar_model(candidates, platforms)
    time_edges = build_time_edges(candidates)
    human_review = build_human_review_queue(backlog, candidates)

    write_csv(
        DATA / "source_research_backlog.csv",
        backlog,
        [
            "priority_score",
            "research_priority",
            "token_label",
            "token_address",
            "first_buy_time_utc",
            "first_buy_bucket",
            "realized_pnl_bnb",
            "narrative_tag",
            "source_type_guess",
            "source_status",
            "source_score",
            "time_advantage_score",
            "onchain_score",
            "risk_penalty",
            "next_research_step",
        ],
    )
    write_csv(
        DATA / "alert_candidates.csv",
        alerts,
        ["alert_id", "score", "action", "token_label", "token_address", "source_type", "narrative_tag", "first_buy_time_utc", "reason"],
    )
    write_csv(
        DATA / "radar_model.csv",
        radar_model,
        ["module_id", "module_name", "trigger", "inputs", "outputs", "score_fields", "human_gate", "automation_status"],
    )
    write_csv(
        DATA / "radar_time_edges.csv",
        time_edges,
        [
            "token_label",
            "token_address",
            "source_time_utc",
            "token_deploy_time_utc",
            "pool_formed_time_utc",
            "first_trade_time_utc",
            "trader_first_buy_time_utc",
            "first_amplifier_time_utc",
            "price_breakout_time_utc",
            "source_to_deploy_min",
            "deploy_to_pool_min",
            "pool_to_trader_buy_min",
            "trader_buy_to_amplifier_min",
            "amplifier_to_breakout_min",
            "first_exit_window",
            "holding_window",
            "leader_or_copycat",
            "leader_score",
            "status",
        ],
    )
    write_csv(
        DATA / "human_review_queue.csv",
        human_review,
        [
            "review_id",
            "total_radar_score",
            "action",
            "token_label",
            "token_address",
            "leader_or_copycat",
            "leader_score",
            "fdv_bucket",
            "source_type",
            "narrative_tag",
            "time_edge_missing",
            "next_human_check",
        ],
    )
    write_json(
        DATA / "research_status.json",
        {
            "generated_at_utc": utc_now(),
            "candidate_count": len(candidates),
            "backlog_count": len(backlog),
            "platform_count": len(platforms),
            "alert_candidate_count": len(alerts),
            "radar_module_count": len(radar_model),
            "human_review_count": len(human_review),
            "min_alert_score": args.min_alert_score,
            "email_status": "dry_run_preview_only",
            "next_required_inputs": [
                "SMTP/email credentials",
                "official source API or scraping permissions",
                "Four.meme/PancakeSwap launch stream",
                "X/Twitter, Telegram, Douyin/Bilibili source feeds",
            ],
        },
    )
    preview = build_email_preview(alerts)
    (STATE / "email_preview.md").parent.mkdir(parents=True, exist_ok=True)
    (STATE / "email_preview.md").write_text(preview + "\n", encoding="utf-8")
    print(json.dumps({"alerts": len(alerts), "backlog": len(backlog), "platforms": len(platforms)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
