# services/hmpi_calculator.py
import pandas as pd
import numpy as np

def calculate_hpi(sample_data):
    """Calculate Heavy Metal Pollution Index for a single sample"""
    
    metals = ['arsenic', 'lead', 'cadmium', 'chromium']
    standards = {
        'arsenic': 0.01,  # WHO standards in mg/L
        'lead': 0.01,
        'cadmium': 0.003,
        'chromium': 0.05
    }
    
    qi_sum = 0
    wi_sum = 0
    
    for metal in metals:
        if metal in sample_data and sample_data[metal] is not None:
            si = sample_data[metal]
            wi = 1 / standards[metal]  # Weight factor
            qi = (si / standards[metal]) * 100  # Sub-index
            qi_sum += qi * wi
            wi_sum += wi
    
    hpi = qi_sum / wi_sum if wi_sum > 0 else 0
    return hpi

def calculate_hei(sample_data):
    """Calculate Heavy Metal Evaluation Index"""
    metals = ['arsenic', 'lead', 'cadmium', 'chromium']
    standards = {'arsenic': 0.01, 'lead': 0.01, 'cadmium': 0.003, 'chromium': 0.05}
    
    hei_sum = 0
    count = 0
    
    for metal in metals:
        if metal in sample_data and sample_data[metal] is not None:
            hei_sum += sample_data[metal] / standards[metal]
            count += 1
    
    return hei_sum / count if count > 0 else 0

def categorize_quality(hpi_value):
    """Categorize water quality based on HPI value"""
    if hpi_value < 25:
        return "excellent"
    elif hpi_value < 50:
        return "good"
    elif hpi_value < 75:
        return "poor"
    else:
        return "very_poor"

def calculate_hmpi_batch(df):
    """Process entire DataFrame and calculate indices"""
    df['hpi_value'] = df.apply(lambda row: calculate_hpi(row.to_dict()), axis=1)
    df['hei_value'] = df.apply(lambda row: calculate_hei(row.to_dict()), axis=1)
    df['quality_category'] = df['hpi_value'].apply(categorize_quality)
    
    return df
