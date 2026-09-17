import os
import json
import time
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SAMPLE_PATH = os.path.join(DATA_DIR, "apple_support_sample.json")
GOLDEN_PATH = os.path.join(DATA_DIR, "golden_set.json")
RESULTS_PATH = os.path.join(DATA_DIR, "results_summary.json")

from src.baselines import TrivialBaseline, SimpleMLBaseline
from src.agent import AntigravitySupportAgent
from src.eval_harness import evaluate_system_performance
from src.llm_judge import LLMJudgeEvaluator, compute_judge_human_alignment

def run_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("  ANTIGRAVITY AI TWITTER CUSTOMER SUPPORT AGENT: BENCHMARK PIPELINE  ")
    print("=" * 70)

    # 1. Load Data
    print(f"\n[1/6] Loading data files...")
    if not os.path.exists(SAMPLE_PATH) or not os.path.exists(GOLDEN_PATH):
        raise FileNotFoundError("Data files missing. Please run src/data_pipeline.py and src/golden_builder.py first.")
        
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        sample_records = json.load(f)
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    # Exclude golden set items from training set
    golden_ids = {g['customer_tweet_id'] for g in golden_set}
    train_records = [r for r in sample_records if r['customer_tweet_id'] not in golden_ids]
    print(f"[*] Training records: {len(train_records)} | Golden evaluation items: {len(golden_set)}")

    # 2. Train Systems
    print(f"\n[2/6] Training baseline models and headline agent...")
    b1_trivial = TrivialBaseline(majority_intent="TECHNICAL_TROUBLESHOOTING")
    
    b2_simple = SimpleMLBaseline()
    b2_simple.fit(train_records)
    
    headline_agent = AntigravitySupportAgent(confidence_threshold=0.70)
    headline_agent.train(train_records)

    # 3. Generate Predictions on Golden Set
    print(f"\n[3/6] Running predictions on Golden Set (200 items)...")
    b1_preds = []
    b2_preds = []
    agent_preds = []

    for item in golden_set:
        text = item['customer_text']
        b1_preds.append(b1_trivial.predict(text))
        b2_preds.append(b2_simple.predict(text))
        agent_preds.append(headline_agent.process_tweet(text))

    # 4. Compute Automated Metrics
    print(f"\n[4/6] Computing automated performance metrics...")
    b1_metrics = evaluate_system_performance(b1_preds, golden_set)
    b2_metrics = evaluate_system_performance(b2_preds, golden_set)
    agent_metrics = evaluate_system_performance(agent_preds, golden_set)

    # 5. LLM-as-Judge & Judge-Human Alignment Analysis
    print(f"\n[5/6] Running LLM-as-Judge evaluation & Judge-Human alignment analysis...")
    judge = LLMJudgeEvaluator()
    
    agent_judge_scores = []
    for g, p in zip(golden_set, agent_preds):
        res = judge.evaluate_reply(
            g['customer_text'],
            p['reply'],
            g['gold_reference_reply'],
            p['decision'],
            g['gold_escalate']
        )
        agent_judge_scores.append(res['overall_score'])

    human_scores = [g['human_quality_score'] for g in golden_set]
    alignment_metrics = compute_judge_human_alignment(agent_judge_scores, human_scores)

    # 6. Extract Top 5 Failure Modes for Headline Agent
    failures = []
    for idx, (g, p) in enumerate(zip(golden_set, agent_preds)):
        intent_mis = (g['gold_intent'] != p['intent'])
        esc_mis = (g['gold_escalate'] != (p['decision'] == 'ESCALATE'))
        if intent_mis or esc_mis:
            failures.append({
                "item_id": g['id'],
                "customer_text": g['customer_text'],
                "gold_intent": g['gold_intent'],
                "pred_intent": p['intent'],
                "gold_escalate": g['gold_escalate'],
                "pred_decision": p['decision'],
                "pred_reason": p['escalation_reason'],
                "gold_reason": g['gold_escalation_reason']
            })

    elapsed_time = time.time() - start_time

    # Output Benchmark Results Table
    print("\n" + "=" * 70)
    print("                     HEADLINE BENCHMARK RESULTS                       ")
    print("=" * 70)
    
    summary_df = pd.DataFrame([
        {
            "System": "Baseline 1 (Trivial)",
            "Intent Acc": f"{b1_metrics['intent_accuracy']*100:.1f}%",
            "Intent Macro F1": f"{b1_metrics['intent_macro_f1']:.3f}",
            "Escalation Acc": f"{b1_metrics['escalation_accuracy']*100:.1f}%",
            "Escalation F1": f"{b1_metrics['escalation_f1']:.3f}",
            "False Auto-Handle Rate": f"{b1_metrics['false_auto_handle_rate']*100:.1f}%",
            "ROUGE-1": f"{b1_metrics['reply_rouge_1']:.3f}"
        },
        {
            "System": "Baseline 2 (Simple ML)",
            "Intent Acc": f"{b2_metrics['intent_accuracy']*100:.1f}%",
            "Intent Macro F1": f"{b2_metrics['intent_macro_f1']:.3f}",
            "Escalation Acc": f"{b2_metrics['escalation_accuracy']*100:.1f}%",
            "Escalation F1": f"{b2_metrics['escalation_f1']:.3f}",
            "False Auto-Handle Rate": f"{b2_metrics['false_auto_handle_rate']*100:.1f}%",
            "ROUGE-1": f"{b2_metrics['reply_rouge_1']:.3f}"
        },
        {
            "System": "Headline Agent (Antigravity)",
            "Intent Acc": f"{agent_metrics['intent_accuracy']*100:.1f}%",
            "Intent Macro F1": f"{agent_metrics['intent_macro_f1']:.3f}",
            "Escalation Acc": f"{agent_metrics['escalation_accuracy']*100:.1f}%",
            "Escalation F1": f"{agent_metrics['escalation_f1']:.3f}",
            "False Auto-Handle Rate": f"{agent_metrics['false_auto_handle_rate']*100:.1f}%",
            "ROUGE-1": f"{agent_metrics['reply_rouge_1']:.3f}"
        }
    ])
    print(summary_df.to_string(index=False))

    print("\n" + "-" * 70)
    print("           LLM-AS-JUDGE & HUMAN ALIGNMENT VALIDATION           ")
    print("-" * 70)
    print(f"  - Mean LLM Judge Quality Score: {np.mean(agent_judge_scores):.2f} / 5.0")
    print(f"  - Quadratic Weighted Kappa (\u03ba_w): {alignment_metrics['cohens_kappa_quadratic']:.3f}")
    print(f"  - Linear Weighted Kappa (\u03ba):     {alignment_metrics['cohens_kappa_linear']:.3f}")
    print(f"  - Pearson Correlation (r):       {alignment_metrics['pearson_correlation']:.3f}")
    print(f"  - Spearman Correlation (\u03c1):      {alignment_metrics['spearman_correlation']:.3f}")
    print(f"  - Exact Score Agreement:         {alignment_metrics['exact_agreement_pct']:.1f}%")
    print(f"  - Close Agreement (+/- 1 score):  {alignment_metrics['close_agreement_pct']:.1f}%")

    print("\n" + "-" * 70)
    print(f"  Pipeline completed successfully in {elapsed_time:.2f} seconds.")
    print("=" * 70)

    # Save summary results
    results_payload = {
        "b1_metrics": b1_metrics,
        "b2_metrics": b2_metrics,
        "agent_metrics": agent_metrics,
        "alignment_metrics": alignment_metrics,
        "mean_judge_score": float(np.mean(agent_judge_scores)),
        "total_failures_count": len(failures),
        "failures_sample": failures[:10],
        "elapsed_seconds": elapsed_time
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    run_pipeline()
