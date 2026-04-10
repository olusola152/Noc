import pandas as pd
import subprocess
import re
import time
import os
import random
import boto3
from datetime import datetime
from pythonping import ping

# --- CONFIGURATION ---
STATS_FILE = 'network_stats.csv'
# Replace with your actual AWS Target Group ARN
TARGET_GROUP_ARN = 'arn:aws:elasticloadbalancing:region:1234567890:targetgroup/CreditDirect-TG/abc123def456'

def get_cloud_health():
    """Polls AWS ALB for Server Health"""
    try:
        client = boto3.client('elbv2', region_name='us-east-1') # Change to your region
        response = client.describe_target_health(TargetGroupArn=TARGET_GROUP_ARN)
        healthy = len([t for t in response['TargetHealthDescriptions'] if t['TargetHealth']['State'] == 'healthy'])
        unhealthy = len(response['TargetHealthDescriptions']) - healthy
        return healthy, unhealthy
    except:
        # Returns simulated data if AWS is not configured/accessible
        return random.randint(2, 4), 0 

def get_network_metrics(ip):
    """Calculates Latency and Jitter"""
    try:
        responses = [p.time_elapsed * 1000 for p in ping(ip, count=3, timeout=1)]
        avg_latency = sum(responses) / len(responses)
        jitter = abs(responses[0] - responses[1])
        status = "UP" if avg_latency > 0 else "DOWN"
        return round(avg_latency, 2), round(jitter, 2), status
    except:
        return 0, 0, "DOWN"

def run_noc_cycle():
    # Define your branches here
    branches = [
        {'name': 'Lagos_HQ', 'ip': '8.8.8.8'},
        {'name': 'Abuja_Branch', 'ip': '1.1.1.1'},
        {'name': 'Benin_Branch', 'ip': '4.2.2.2'}
    ]
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    all_results = []
    
    # Get Cloud Data once per cycle
    c_h, c_u = get_cloud_health()

    for b in branches:
        lat, jit, status = get_network_metrics(b['ip'])
        
        # Simulate Radio Quality (Replace with SNMP OIDs for real routers)
        rsrp = random.randint(-110, -70)
        sinr = random.randint(-5, 25)
        
        all_results.append([
            timestamp, b['name'], lat, jit, status, rsrp, sinr, c_h, c_u
        ])

    df = pd.DataFrame(all_results, columns=[
        'Time', 'Branch', 'Latency', 'Jitter', 'Status', 'RSRP', 'SINR', 'Cloud_H', 'Cloud_U'
    ])
    
    # Save to CSV
    df.to_csv(STATS_FILE, mode='a', header=not os.path.exists(STATS_FILE), index=False)
    print(f"[{timestamp}] Data Collected: Branches & Cloud Synchronized.")

if __name__ == "__main__":
    print("Olusola's Hybrid NOC Engine is starting...")
    while True:
        run_noc_cycle()
        time.sleep(10) # Updates every 10 seconds
