# ===== generate_dashboard.py =====
import json

def load_metrics(filename='results/metrics.json'):
    """Load metrics from JSON"""
    with open(filename, 'r') as f:
        return json.load(f)

def generate_html(metrics):
    """Generate HTML dashboard with embedded data"""
    
    # Prepare data for charts
    attributes = list(metrics['bias_by_attribute'].keys())
    bias_percentages = [metrics['bias_by_attribute'][attr]['percentage'] for attr in attributes]
    
    approved = metrics['decision_distribution']['approved']['count']
    rejected = metrics['decision_distribution']['rejected']['count']
    
    # Generate bias examples table rows
    table_rows = ''
    for attribute in attributes:
        for example in metrics['bias_by_attribute'][attribute]['examples']:
            table_rows += f"""
                <tr>
                    <td>{example['test_id']}</td>
                    <td><strong>{attribute.upper()}</strong></td>
                    <td>{example['original_value']}</td>
                    <td>{example['new_value']}</td>
                    <td><span class="bias-high">{example['decision_changed']}</span></td>
                </tr>
            """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BFSI Bias Detection Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        
        .metric-card.danger {{
            border-left-color: #e74c3c;
        }}
        
        .metric-label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        
        .metric-unit {{
            color: #999;
            font-size: 14px;
            margin-left: 5px;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }}
        
        canvas {{
            max-height: 300px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background: #f9f9f9;
        }}
        
        .bias-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 BFSI Bias Detection Dashboard</h1>
            <p class="subtitle">Evaluating AI Fairness in Loan Decisions</p>
        </header>
        
        <!-- SUMMARY METRICS -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Profiles Tested</div>
                <div class="metric-value">{metrics['total_profiles']}<span class="metric-unit">profiles</span></div>
            </div>
            <div class="metric-card {'danger' if metrics['total_bias_cases'] > 0 else ''}">
                <div class="metric-label">Bias Cases Found</div>
                <div class="metric-value">{metrics['total_bias_cases']}<span class="metric-unit">cases</span></div>
            </div>
            <div class="metric-card {'danger' if metrics['overall_bias_percentage'] > 5 else ''}">
                <div class="metric-label">Overall Bias Rate</div>
                <div class="metric-value">{metrics['overall_bias_percentage']:.2f}<span class="metric-unit">%</span></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Fairness Score</div>
                <div class="metric-value">{100 - metrics['overall_bias_percentage']:.2f}<span class="metric-unit">%</span></div>
            </div>
        </div>
        
        <!-- CHARTS -->
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Bias by Attribute</div>
                <canvas id="biasChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Decision Distribution</div>
                <canvas id="decisionChart"></canvas>
            </div>
        </div>
        
        <!-- BIAS EXAMPLES TABLE -->
        <div class="chart-container">
            <div class="chart-title">Bias Cases Detected</div>
            <table>
                <thead>
                    <tr>
                        <th>Test ID</th>
                        <th>Attribute</th>
                        <th>Original Value</th>
                        <th>Changed To</th>
                        <th>Decision Change</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows if table_rows else '<tr><td colspan="5" style="text-align: center; color: #27ae60;">✅ No bias detected</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>Generated by BFSI Bias Detection System | Tested {metrics['total_profiles']} profiles</p>
        </footer>
    </div>
    
    <script>
        // Bias by Attribute Chart
        const biasCtx = document.getElementById('biasChart').getContext('2d');
        new Chart(biasCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([a.upper() for a in attributes])},
                datasets: [{{
                    label: 'Bias %',
                    data: {json.dumps(bias_percentages)},
                    backgroundColor: '#e74c3c',
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 100 }}
                }}
            }}
        }});
        
        // Decision Distribution Pie Chart
        const decisionCtx = document.getElementById('decisionChart').getContext('2d');
        new Chart(decisionCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Approved', 'Rejected'],
                datasets: [{{
                    data: [{approved}, {rejected}],
                    backgroundColor: ['#27ae60', '#e74c3c'],
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    print("Generating dashboard...")
    
    metrics = load_metrics()
    html = generate_html(metrics)
    
    with open('dashboard.html', 'w') as f:
        f.write(html)
    
    print("✅ Dashboard generated: dashboard.html")
    print("   Open in browser: open dashboard.html")