"""
APEX Trading Blueprint PDF Generator
Hedge Fund-Grade Reports with Hyper-Council Analysis
"""
import json
import time
import base64
import io
from datetime import datetime, timezone

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ═══════════════════════════════════════════════════════════════
#  CHART GENERATORS
# ═══════════════════════════════════════════════════════════════

def generate_radar_chart(labels, datasets, title="Strategy Capability Radar"):
    """Generate radar/spider chart as base64 PNG"""
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#0a0e1a')
    ax.set_facecolor('#0a0e1a')
    
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    colors = ['#4a9eff', '#00e5a0', '#ff6b6b', '#ffd93d']
    
    for i, ds in enumerate(datasets):
        values = ds['data'] + ds['data'][:1]
        color = colors[i % len(colors)]
        ax.plot(angles, values, 'o-', linewidth=2, label=ds['label'], color=color)
        ax.fill(angles, values, alpha=0.15, color=color)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=9, color='#8892a0')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=7, color='#555')
    ax.tick_params(colors='#555')
    ax.spines['polar'].set_color('#1a2035')
    ax.grid(color='#1a2035', linewidth=0.5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=8, 
              facecolor='#0f1424', edgecolor='#1a2035', labelcolor='#8892a0')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='#0a0e1a', edgecolor='none')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def generate_bar_chart(labels, datasets, title="Projected PnL Profile"):
    """Generate grouped bar chart as base64 PNG"""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor('#0a0e1a')
    ax.set_facecolor('#0a0e1a')
    
    x = np.arange(len(labels))
    width = 0.25
    colors = ['#333845', '#4a9eff', '#00e5a0']
    
    for i, ds in enumerate(datasets):
        offset = (i - len(datasets)/2 + 0.5) * width
        bars = ax.bar(x + offset, ds['data'], width, label=ds['label'], 
                      color=colors[i % len(colors)], edgecolor='none', alpha=0.9)
        for bar, val in zip(bars, ds['data']):
            if val != 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                       f'{val}%', ha='center', va='bottom', fontsize=7, color='#8892a0')
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color='#8892a0', fontsize=10)
    ax.set_ylabel('Return %', color='#8892a0', fontsize=10)
    ax.tick_params(colors='#555')
    ax.spines['bottom'].set_color('#1a2035')
    ax.spines['left'].set_color('#1a2035')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=8, facecolor='#0f1424', edgecolor='#1a2035', labelcolor='#8892a0')
    ax.axhline(y=0, color='#1a2035', linewidth=0.5)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#0a0e1a', edgecolor='none')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def generate_swot_chart(swot_data):
    """Generate SWOT quadrant as base64 PNG"""
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    fig.patch.set_facecolor('#0a0e1a')
    
    quadrants = [
        ('Strengths', swot_data.get('strengths', []), '#00e5a0', 0, 0),
        ('Weaknesses', swot_data.get('weaknesses', []), '#ff6b6b', 0, 1),
        ('Opportunities', swot_data.get('opportunities', []), '#4a9eff', 1, 0),
        ('Threats', swot_data.get('threats', []), '#ffd93d', 1, 1),
    ]
    
    for title, items, color, row, col in quadrants:
        ax = axes[row][col]
        ax.set_facecolor('#0f1424')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color('#1a2035')
        
        ax.text(0.5, 0.92, title, ha='center', va='top', fontsize=12, 
                fontweight='bold', color=color)
        
        for i, item in enumerate(items[:4]):
            y = 0.75 - i * 0.18
            ax.text(0.08, y, f"• {item[:60]}", ha='left', va='top', fontsize=8, 
                    color='#c0c8d4', wrap=True)
    
    plt.tight_layout(pad=0.5)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='#0a0e1a', edgecolor='none')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ═══════════════════════════════════════════════════════════════
#  HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════

def build_blueprint_html(report_data: dict, charts: dict) -> str:
    """Build premium HTML for PDF rendering"""
    
    title = report_data.get('title', 'APEX Trading Blueprint')
    subtitle = report_data.get('subtitle', 'NeuroAether Hyper-Council Edition')
    summary = report_data.get('executive_summary', '')
    snapshot = report_data.get('strategy_snapshot', {})
    modules = report_data.get('modules', [])
    footer = report_data.get('footer', 'Generated by NeuroAether APEX')
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    # Build modules HTML
    modules_html = ""
    for mod in modules:
        mod_type = mod.get('type', '')
        mod_title = mod.get('title', '')
        
        if mod_type == 'swot' and 'swot' in charts:
            modules_html += f"""
            <div class="module">
                <h2>{mod_title}</h2>
                <img src="data:image/png;base64,{charts['swot']}" class="chart-img">
            </div>"""
        
        elif mod_type == 'chart_bar' and 'bar' in charts:
            insight = mod.get('insight', '')
            modules_html += f"""
            <div class="module">
                <h2>{mod_title}</h2>
                <img src="data:image/png;base64,{charts['bar']}" class="chart-img">
                <p class="insight">"{insight}"</p>
            </div>"""
        
        elif mod_type == 'chart_radar' and 'radar' in charts:
            insight = mod.get('insight', '')
            modules_html += f"""
            <div class="module">
                <h2>{mod_title}</h2>
                <img src="data:image/png;base64,{charts['radar']}" class="chart-img">
                <p class="insight">"{insight}"</p>
            </div>"""
        
        elif mod_type == 'hyper_council':
            agents_html = ""
            agents = mod.get('agents', [])
            for agent in agents:
                sentiment = agent.get('sentiment', 'N/A')
                s_color = {'LONG': '#00e5a0', 'STRONG_LONG': '#00e5a0', 
                          'SHORT': '#ff6b6b', 'STRONG_SHORT': '#ff6b6b',
                          'VETO': '#ff3333', 'NEUTRAL': '#ffd93d', 'INFO': '#4a9eff'}.get(sentiment, '#888')
                agents_html += f"""
                <div class="agent-card">
                    <div class="agent-header">
                        <span class="agent-role">{agent.get('role', '')}</span>
                        <span class="agent-name">{agent.get('name', '')}</span>
                        <span class="sentiment" style="color:{s_color}">{sentiment}</span>
                        <span class="weight">W: {agent.get('weight', 0)}</span>
                    </div>
                    <p class="agent-summary">{agent.get('summary', '')}</p>
                    <p class="agent-dialogue">{agent.get('dialogue', '')}</p>
                </div>"""
            
            consensus = mod.get('consensus', {})
            status = consensus.get('status', 'N/A')
            score = consensus.get('consensus_score', 0)
            st_color = {'ALPHA_GO': '#00e5a0', 'HOLD': '#ffd93d', 'WAIT': '#4a9eff', 'VETOED': '#ff3333'}.get(status, '#888')
            
            modules_html += f"""
            <div class="module">
                <h2>{mod_title}</h2>
                {agents_html}
                <div class="consensus-box">
                    <div class="consensus-status" style="color:{st_color}">{status}</div>
                    <div class="consensus-score">Consensus Score: {score}/100</div>
                    <div class="consensus-log">{consensus.get('execution_log', '')}</div>
                </div>
            </div>"""
        
        elif mod_type == 'roadmap':
            phases_html = ""
            for phase in mod.get('phases', []):
                phases_html += f"""
                <div class="phase">
                    <div class="phase-header">
                        <span class="phase-name">{phase.get('name', '')}</span>
                        <span class="phase-time">{phase.get('time', '')}</span>
                    </div>
                    <p class="phase-action">{phase.get('action', '')}</p>
                </div>"""
            
            modules_html += f"""
            <div class="module">
                <h2>{mod_title}</h2>
                <div class="roadmap">{phases_html}</div>
            </div>"""

    # Status badge
    status_val = snapshot.get('status', 'WATCH')
    conviction = snapshot.get('conviction_level', 'MEDIUM')
    risk = snapshot.get('risk_profile', 'Moderate')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@page {{
    size: A4;
    margin: 15mm 18mm;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background: #0a0e1a;
    color: #c0c8d4;
    font-size: 10pt;
    line-height: 1.5;
}}
.header {{
    text-align: center;
    padding: 20px 0;
    border-bottom: 2px solid #4a9eff;
    margin-bottom: 20px;
}}
.header h1 {{
    font-size: 22pt;
    color: #ffffff;
    letter-spacing: 2px;
    margin-bottom: 5px;
}}
.header .subtitle {{
    font-size: 10pt;
    color: #4a9eff;
    letter-spacing: 1px;
}}
.header .timestamp {{
    font-size: 8pt;
    color: #555;
    margin-top: 5px;
}}
.snapshot {{
    display: flex;
    justify-content: space-between;
    background: #0f1424;
    border: 1px solid #1a2035;
    border-radius: 6px;
    padding: 12px 18px;
    margin-bottom: 20px;
}}
.snapshot-item {{
    text-align: center;
}}
.snapshot-label {{
    font-size: 7pt;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
.snapshot-value {{
    font-size: 11pt;
    color: #ffffff;
    font-weight: bold;
}}
.executive-summary {{
    background: #0f1424;
    border-left: 3px solid #4a9eff;
    padding: 15px 20px;
    margin-bottom: 20px;
    border-radius: 0 6px 6px 0;
}}
.executive-summary h2 {{
    color: #4a9eff;
    font-size: 13pt;
    margin-bottom: 10px;
}}
.executive-summary p {{
    color: #c0c8d4;
    font-size: 9.5pt;
    margin-bottom: 8px;
}}
.module {{
    margin-bottom: 25px;
    page-break-inside: avoid;
}}
.module h2 {{
    color: #4a9eff;
    font-size: 13pt;
    border-bottom: 1px solid #1a2035;
    padding-bottom: 5px;
    margin-bottom: 12px;
}}
.chart-img {{
    width: 100%;
    max-width: 100%;
    border-radius: 6px;
    margin: 10px 0;
}}
.insight {{
    font-style: italic;
    color: #8892a0;
    font-size: 9pt;
    padding: 8px 12px;
    background: #0f1424;
    border-radius: 4px;
    margin-top: 8px;
}}
.agent-card {{
    background: #0f1424;
    border: 1px solid #1a2035;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
}}
.agent-header {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 6px;
}}
.agent-role {{
    background: #1a2035;
    color: #4a9eff;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 8pt;
    font-weight: bold;
}}
.agent-name {{
    color: #ffffff;
    font-size: 9.5pt;
    font-weight: bold;
}}
.sentiment {{
    font-weight: bold;
    font-size: 9pt;
}}
.weight {{
    color: #555;
    font-size: 8pt;
}}
.agent-summary {{
    color: #c0c8d4;
    font-size: 9pt;
    margin-bottom: 4px;
}}
.agent-dialogue {{
    color: #8892a0;
    font-size: 8.5pt;
    font-style: italic;
}}
.consensus-box {{
    background: #0f1424;
    border: 2px solid #4a9eff;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    margin-top: 12px;
}}
.consensus-status {{
    font-size: 20pt;
    font-weight: bold;
    letter-spacing: 3px;
}}
.consensus-score {{
    font-size: 11pt;
    color: #8892a0;
    margin: 5px 0;
}}
.consensus-log {{
    font-size: 9pt;
    color: #c0c8d4;
}}
.roadmap {{
    position: relative;
    padding-left: 20px;
}}
.phase {{
    border-left: 2px solid #4a9eff;
    padding: 8px 0 8px 18px;
    margin-bottom: 5px;
    position: relative;
}}
.phase::before {{
    content: '';
    position: absolute;
    left: -6px;
    top: 12px;
    width: 10px;
    height: 10px;
    background: #4a9eff;
    border-radius: 50%;
}}
.phase-header {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}}
.phase-name {{
    color: #ffffff;
    font-weight: bold;
    font-size: 9.5pt;
}}
.phase-time {{
    color: #4a9eff;
    font-size: 8.5pt;
}}
.phase-action {{
    color: #c0c8d4;
    font-size: 9pt;
}}
.footer {{
    text-align: center;
    font-size: 7.5pt;
    color: #444;
    border-top: 1px solid #1a2035;
    padding-top: 10px;
    margin-top: 30px;
}}
</style>
</head>
<body>

<div class="header">
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
    <div class="timestamp">{timestamp}</div>
</div>

<div class="snapshot">
    <div class="snapshot-item">
        <div class="snapshot-label">Symbol</div>
        <div class="snapshot-value">{snapshot.get('symbol', 'N/A')}</div>
    </div>
    <div class="snapshot-item">
        <div class="snapshot-label">Timeframe</div>
        <div class="snapshot-value">{snapshot.get('timeframe', 'N/A')}</div>
    </div>
    <div class="snapshot-item">
        <div class="snapshot-label">Market</div>
        <div class="snapshot-value">{snapshot.get('market', 'N/A')}</div>
    </div>
    <div class="snapshot-item">
        <div class="snapshot-label">Status</div>
        <div class="snapshot-value">{status_val}</div>
    </div>
    <div class="snapshot-item">
        <div class="snapshot-label">Conviction</div>
        <div class="snapshot-value">{conviction}</div>
    </div>
    <div class="snapshot-item">
        <div class="snapshot-label">Risk</div>
        <div class="snapshot-value">{risk}</div>
    </div>
</div>

<div class="executive-summary">
    <h2>Executive Summary</h2>
    <p>{summary}</p>
</div>

{modules_html}

<div class="footer">{footer} • {timestamp}</div>

</body>
</html>"""
    
    return html


# ═══════════════════════════════════════════════════════════════
#  MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_blueprint_pdf(report_json: dict, output_path: str) -> str:
    """Generate complete trading blueprint PDF from JSON"""
    import weasyprint
    
    charts = {}
    
    for mod in report_json.get('modules', []):
        mod_type = mod.get('type', '')
        
        if mod_type == 'swot':
            charts['swot'] = generate_swot_chart(mod.get('data', {}))
        
        elif mod_type == 'chart_bar':
            charts['bar'] = generate_bar_chart(
                mod.get('labels', []),
                mod.get('datasets', []),
                mod.get('title', '')
            )
        
        elif mod_type == 'chart_radar':
            charts['radar'] = generate_radar_chart(
                mod.get('labels', []),
                mod.get('datasets', []),
                mod.get('title', '')
            )
    
    html = build_blueprint_html(report_json, charts)
    
    pdf = weasyprint.HTML(string=html).write_pdf()
    
    with open(output_path, 'wb') as f:
        f.write(pdf)
    
    return output_path


# Quick test
if __name__ == "__main__":
    test_data = {
        "title": "THE BTC/USDT TRADING & MACRO BLUEPRINT",
        "subtitle": "NeuroAether APEX Hyper-Council Edition",
        "executive_summary": "Bitcoin is currently in a consolidation phase following a significant pullback from all-time highs. The macro regime remains cautiously constructive with institutional flows gradually building. Risk-reward favors patient accumulation near support with strict risk management.",
        "strategy_snapshot": {
            "symbol": "BTC/USDT",
            "timeframe": "4H",
            "market": "Crypto Perps",
            "status": "WATCH",
            "conviction_level": "MEDIUM",
            "risk_profile": "Moderate"
        },
        "modules": [
            {
                "type": "swot",
                "title": "Strategic Market Position (SWOT)",
                "data": {
                    "strengths": ["Clear momentum in high-liquidity sessions", "Strategy aligns with macro risk-on regime"],
                    "weaknesses": ["Susceptible to whipsaws in vol compression", "Execution dependent on orderbook depth"],
                    "opportunities": ["Rising institutional BTC derivatives inflows", "Volatility expansion around macro events"],
                    "threats": ["Regime flip to risk-off with liquidity drain", "Exchange counterparty risk"]
                }
            },
            {
                "type": "chart_bar",
                "title": "Projected PnL Profile (Next 12 Months)",
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [
                    {"label": "No Strategy", "data": [0, 0, 0, 0]},
                    {"label": "APEX Base Case", "data": [8, 14, 18, 22]},
                    {"label": "APEX Stress Case", "data": [2, 4, 6, 8]}
                ],
                "insight": "Base case compounds capital with controlled max drawdown."
            },
            {
                "type": "chart_radar",
                "title": "Strategy Capability Radar",
                "labels": ["Alpha Potential", "Risk Control", "Liquidity Fit", "Execution Complexity", "Robustness"],
                "datasets": [
                    {"label": "Current Setup", "data": [40, 55, 60, 45, 50]},
                    {"label": "With APEX", "data": [85, 80, 75, 60, 80]}
                ],
                "insight": "APEX layer upgrades alpha and robustness significantly."
            },
            {
                "type": "hyper_council",
                "title": "Hyper-Council Institutional View",
                "agents": [
                    {"role": "MACRO", "name": "Global Macro CIO", "sentiment": "LONG", "weight": 30,
                     "summary": "Macro regime supportive with easing cycle underway.",
                     "dialogue": "Central banks pivoting dovish, liquidity improving."},
                    {"role": "QUANT", "name": "Head of Quant Research", "sentiment": "LONG", "weight": 25,
                     "summary": "Momentum signals turning positive on 4H timeframe.",
                     "dialogue": "Sharpe ratio improving, hit-rate above 55%."},
                    {"role": "RISK", "name": "CRO Damocles", "sentiment": "NEUTRAL", "weight": -20,
                     "summary": "Acceptable risk with proper sizing.",
                     "dialogue": "Max drawdown bounded at 8% with current parameters."},
                    {"role": "EXECUTION", "name": "Execution Architect", "sentiment": "INFO", "weight": 0,
                     "summary": "Spread tight, orderbook deep enough for target size.",
                     "dialogue": "Limit orders recommended over market for better fills."}
                ],
                "consensus": {
                    "raw_sum": 35,
                    "consensus_score": 72,
                    "status": "ALPHA_GO",
                    "execution_log": "Council approves controlled entry with 2% portfolio allocation."
                }
            },
            {
                "type": "roadmap",
                "title": "Implementation Roadmap",
                "phases": [
                    {"name": "Phase 1: Backtest & Sandbox", "time": "Weeks 1-2",
                     "action": "Validate parameters, run historical and paper trading."},
                    {"name": "Phase 2: Controlled Deployment", "time": "Weeks 3-6",
                     "action": "Deploy small capital with tight risk limits."},
                    {"name": "Phase 3: Scale & Institutionalize", "time": "Weeks 7+",
                     "action": "Scale position size, integrate into core portfolio."}
                ]
            }
        ],
        "footer": "Generated by NeuroAether APEX Trading Blueprint Studio • Confidential"
    }
    
    path = generate_blueprint_pdf(test_data, "/tmp/test_blueprint.pdf")
    print(f"✅ Test PDF generated: {path}")
    import os
    print(f"📄 Size: {os.path.getsize(path) / 1024:.0f} KB")
