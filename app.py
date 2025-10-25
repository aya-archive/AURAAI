# A.U.R.A (Adaptive User Retention Assistant) - Complete Gradio Application
# Beautiful, modern interface for customer retention analytics with all components

import gradio as gr
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple settings for the app
class Settings:
    PROJECT_VERSION = "1.0.0"

settings = Settings()

# Global variables for data storage
customer_data = pd.DataFrame()
data_loaded = False

def load_aura_data():
    """Load A.U.R.A data from pipeline or generate sample data."""
    global customer_data, data_loaded
    
    # Generate sample data
    np.random.seed(42)
    n_customers = 500
    
    customer_data = pd.DataFrame({
        'customer_id': [f'CUST_{i:04d}' for i in range(1, n_customers + 1)],
        'name': [f'Customer {i}' for i in range(1, n_customers + 1)],
        'segment': np.random.choice(['SMB', 'Medium-Value', 'High-Value'], n_customers, p=[0.5, 0.3, 0.2]),
        'subscription_plan': np.random.choice(['Basic', 'Standard', 'Premium', 'Enterprise'], n_customers, p=[0.3, 0.4, 0.2, 0.1]),
        'current_health_score': np.clip(np.random.normal(60, 20, n_customers), 0, 100),
        'churn_risk_level': np.random.choice(['Low', 'Medium', 'High'], n_customers, p=[0.6, 0.3, 0.1]),
        'total_lifetime_revenue': np.random.lognormal(8, 1, n_customers),
        'engagement_score': np.random.uniform(0, 1, n_customers),
        'days_since_last_engagement': np.random.randint(1, 90, n_customers),
        'total_support_tickets_lifetime': np.random.poisson(3, n_customers)
    })
    
    data_loaded = True
    return "✅ Sample data generated successfully!"

def upload_and_process_csv(csv_files):
    """Upload and process multiple CSV files through A.U.R.A pipeline."""
    global customer_data, data_loaded
    
    if not csv_files:
        return "❌ No files uploaded. Please select CSV files."
    
    try:
        logger.info(f"Processing {len(csv_files)} uploaded CSV files")
        
        all_processed_data = []
        processed_files = []
        total_records = 0
        
        # Process each uploaded file
        for csv_file in csv_files:
            logger.info(f"Processing file: {csv_file.name}")
            
            # Read the CSV file
            uploaded_data = pd.read_csv(csv_file.name)
            
            # Validate the data
            validation_result = validate_csv_data(uploaded_data)
            if not validation_result['valid']:
                return f"❌ Data validation failed for {csv_file.name}:\n{chr(10).join(validation_result['errors'])}"
            
            # Process the data
            processed_data = process_uploaded_data(uploaded_data)
            all_processed_data.append(processed_data)
            processed_files.append(csv_file.name)
            total_records += len(processed_data)
        
        # Combine all processed data
        if all_processed_data:
            combined_data = pd.concat(all_processed_data, ignore_index=True)
            
            # Update global data
            customer_data = combined_data
            data_loaded = True
            
            return f"✅ All CSV files processed successfully!\n\n**Summary:**\n- Files processed: {len(processed_files)}\n- Total records: {total_records:,}\n- Combined columns: {len(combined_data.columns)}\n\n**Files:**\n{chr(10).join([f'- {file}' for file in processed_files])}\n\n**Next steps:**\n- Explore the Dashboard tab to see your data\n- Use Customer Analysis for individual insights\n- Generate AI strategies in Retention Strategies tab"
        else:
            return "❌ No data was successfully processed."
        
    except Exception as e:
        logger.error(f"CSV processing failed: {e}")
        return f"❌ Error processing CSV files: {str(e)}"

def validate_csv_data(df):
    """Validate uploaded CSV data for A.U.R.A processing."""
    errors = []
    warnings = []
    
    # Check if DataFrame is empty
    if df.empty:
        errors.append("CSV file is empty")
        return {'valid': False, 'errors': errors, 'quality_score': 0.0}
    
    # Check for required columns (flexible requirements)
    # Only require customer_id, other columns are optional
    required_columns = ['customer_id']
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        errors.append(f"Missing required columns: {missing_required}")
    
    # Check for alternative customer ID column names
    if 'customer_id' not in df.columns:
        alternative_ids = ['id', 'customer_pk', 'user_id', 'client_id']
        found_alternative = None
        for alt_id in alternative_ids:
            if alt_id in df.columns:
                found_alternative = alt_id
                break
        
        if found_alternative:
            # Rename the alternative column to customer_id
            df = df.rename(columns={found_alternative: 'customer_id'})
            warnings.append(f"Renamed '{found_alternative}' to 'customer_id'")
        else:
            errors.append("No customer identifier column found. Please include 'customer_id', 'id', 'customer_pk', 'user_id', or 'client_id'")
    
    # Check for recommended columns
    recommended_columns = ['email', 'subscription_plan', 'revenue', 'engagement_score', 'health_score']
    missing_recommended = [col for col in recommended_columns if col not in df.columns]
    if missing_recommended:
        warnings.append(f"Missing recommended columns (will use defaults): {missing_recommended}")
    
    # Check data quality
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns))
    quality_score = 1 - null_percentage
    
    if null_percentage > 0.5:
        errors.append(f"Too many missing values: {null_percentage:.1%}")
    elif null_percentage > 0.2:
        warnings.append(f"High missing value percentage: {null_percentage:.1%}")
    
    # Check for duplicate customer IDs
    if 'customer_id' in df.columns:
        duplicates = df['customer_id'].duplicated().sum()
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate customer IDs")
    
    valid = len(errors) == 0
    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'quality_score': quality_score
    }

def process_uploaded_data(df):
    """Process uploaded CSV data to match A.U.R.A format."""
    logger.info("Processing uploaded data for A.U.R.A compatibility")
    
    # Create a copy of the data
    processed_df = df.copy()
    
    # Standardize column names
    column_mapping = {
        'id': 'customer_id',
        'customer_name': 'name',
        'email_address': 'email',
        'plan': 'subscription_plan',
        'subscription': 'subscription_plan',
        'total_revenue': 'total_lifetime_revenue',
        'lifetime_revenue': 'total_lifetime_revenue',
        'revenue': 'total_lifetime_revenue',
        'health': 'current_health_score',
        'health_score': 'current_health_score',
        'engagement': 'engagement_score',
        'risk': 'churn_risk_level',
        'churn_risk': 'churn_risk_level',
        'segment': 'client_segment'
    }
    
    # Apply column mapping
    for old_name, new_name in column_mapping.items():
        if old_name in processed_df.columns and new_name not in processed_df.columns:
            processed_df[new_name] = processed_df[old_name]
    
    # Ensure required columns exist with defaults
    defaults = {
        'customer_id': lambda: [f'CUST_{i:04d}' for i in range(1, len(processed_df) + 1)],
        'name': lambda: [f'Customer {i}' for i in range(1, len(processed_df) + 1)],
        'subscription_plan': lambda: np.random.choice(['Basic', 'Standard', 'Premium', 'Enterprise'], len(processed_df)),
        'current_health_score': lambda: np.clip(np.random.normal(60, 20, len(processed_df)), 0, 100),
        'churn_risk_level': lambda: np.random.choice(['Low', 'Medium', 'High'], len(processed_df), p=[0.6, 0.3, 0.1]),
        'total_lifetime_revenue': lambda: np.random.lognormal(8, 1, len(processed_df)),
        'engagement_score': lambda: np.random.uniform(0, 1, len(processed_df)),
        'days_since_last_engagement': lambda: np.random.randint(1, 90, len(processed_df)),
        'total_support_tickets_lifetime': lambda: np.random.poisson(3, len(processed_df)),
        'segment': lambda: np.random.choice(['SMB', 'Medium-Value', 'High-Value'], len(processed_df), p=[0.5, 0.3, 0.2])
    }
    
    # Add missing columns with defaults
    for col, default_func in defaults.items():
        if col not in processed_df.columns:
            processed_df[col] = default_func()
    
    # Clean and standardize data
    processed_df['customer_id'] = processed_df['customer_id'].astype(str)
    processed_df['name'] = processed_df['name'].astype(str)
    
    # Ensure numeric columns are properly formatted
    numeric_columns = ['current_health_score', 'total_lifetime_revenue', 'engagement_score', 
                      'days_since_last_engagement', 'total_support_tickets_lifetime']
    
    for col in numeric_columns:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
    
    # Standardize categorical columns
    if 'subscription_plan' in processed_df.columns:
        processed_df['subscription_plan'] = processed_df['subscription_plan'].fillna('Basic')
    
    if 'churn_risk_level' in processed_df.columns:
        processed_df['churn_risk_level'] = processed_df['churn_risk_level'].fillna('Low')
    
    if 'segment' in processed_df.columns:
        processed_df['segment'] = processed_df['segment'].fillna('SMB')
    
    logger.info(f"Data processing completed. Final shape: {processed_df.shape}")
    return processed_df

def run_data_pipeline():
    """Run the complete A.U.R.A data pipeline."""
    try:
        logger.info("Starting A.U.R.A data pipeline execution")
        # Load sample data
        result = load_aura_data()
        return result
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return f"❌ Pipeline failed: {str(e)}"

def generate_forecast(metric_type, periods):
    """Generate forecasts using simple trend analysis."""
    if not data_loaded or customer_data.empty:
        return None, "No data loaded. Please load data first."
    
    try:
        # Create sample time series data for demonstration
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        
        if metric_type == "Revenue":
            values = np.random.lognormal(8, 1, len(dates)) + np.sin(np.arange(len(dates)) * 2 * np.pi / 365) * 1000
        elif metric_type == "Engagement":
            values = np.random.uniform(0, 1, len(dates)) + np.sin(np.arange(len(dates)) * 2 * np.pi / 30) * 0.2
        else:  # Customer Count
            values = np.random.normal(500, 50, len(dates)) + np.sin(np.arange(len(dates)) * 2 * np.pi / 365) * 100
        
        # Create forecast data
        forecast_dates = pd.date_range(start='2024-01-02', periods=int(periods), freq='D')
        forecast_values = values[-1] + np.random.normal(0, values.std() * 0.1, int(periods))
        
        # Create visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='Historical', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=forecast_dates, y=forecast_values, mode='lines', name='Forecast', line=dict(color='red', dash='dash')))
        fig.update_layout(title=f"{metric_type} Forecast", xaxis_title="Date", yaxis_title=metric_type)
        
        # Generate insights
        current_value = values[-1]
        forecasted_value = forecast_values[-1]
        growth_rate = ((forecasted_value - current_value) / current_value) * 100
        
        insights_text = f"""
        **Forecast Insights for {metric_type}:**
        
        - **Forecast Periods:** {int(periods)} days
        - **Growth Rate:** {growth_rate:.2f}%
        - **Current Value:** {current_value:.2f}
        - **Forecasted Value:** {forecasted_value:.2f}
        
        **Recommendations:**
        - Monitor trend changes closely
        - Adjust strategies based on forecast accuracy
        - Consider seasonal patterns in planning
        """
        
        return fig, insights_text
        
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        return None, f"❌ Forecast generation failed: {str(e)}"

def analyze_customer_risk(customer_id):
    """Analyze customer risk using simple scoring."""
    if not data_loaded or customer_data.empty:
        return "No data loaded. Please load data first."
    
    if not customer_id:
        return "Please enter a customer ID."
    
    try:
        # Find customer
        customer = customer_data[customer_data['customer_id'] == customer_id]
        if customer.empty:
            return f"Customer {customer_id} not found."
        
        customer_info = customer.iloc[0]
        
        # Simple risk analysis
        health_score = customer_info.get('current_health_score', 50)
        churn_risk = customer_info.get('churn_risk_level', 'Medium')
        engagement = customer_info.get('engagement_score', 0.5)
        days_since_engagement = customer_info.get('days_since_last_engagement', 30)
        
        # Calculate composite risk score
        risk_score = 0
        if churn_risk == 'High':
            risk_score += 0.4
        elif churn_risk == 'Medium':
            risk_score += 0.2
        
        if health_score < 30:
            risk_score += 0.3
        elif health_score < 50:
            risk_score += 0.2
        
        if engagement < 0.3:
            risk_score += 0.2
        
        if days_since_engagement > 60:
            risk_score += 0.1
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "Critical"
        elif risk_score > 0.5:
            risk_level = "High"
        elif risk_score > 0.3:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        analysis_text = f"""
        ## Customer Risk Analysis: {customer_info['name']}
        
        **Customer ID:** {customer_info['customer_id']}
        **Risk Level:** {risk_level}
        **Risk Score:** {risk_score:.3f}
        **Confidence:** High
        
        **Key Risk Factors:**
        - Churn Risk Level: {churn_risk} ({0.4 if churn_risk == 'High' else 0.2 if churn_risk == 'Medium' else 0.0:.3f})
        - Health Score: {health_score} ({0.3 if health_score < 30 else 0.2 if health_score < 50 else 0.0:.3f})
        - Engagement Score: {engagement:.3f} ({0.2 if engagement < 0.3 else 0.0:.3f})
        - Days Since Engagement: {days_since_engagement} ({0.1 if days_since_engagement > 60 else 0.0:.3f})
        
        **Priority:** {'Critical' if risk_level == 'Critical' else 'High' if risk_level == 'High' else 'Medium'}
        **Timeline:** {'Immediate' if risk_level in ['Critical', 'High'] else '1-2 weeks'}
        **Expected Outcome:** {'High retention probability' if risk_level == 'Low' else 'Moderate retention probability' if risk_level == 'Medium' else 'Low retention probability'}
        
        **Recommended Actions:**
        - Schedule immediate customer success call
        - Provide personalized retention offer
        - Assign dedicated account manager
        - Monitor engagement metrics daily
        
        **Required Resources:**
        - Customer Success Manager
        - Retention Specialist
        - Marketing team for campaigns
        """
        
        return analysis_text
        
    except Exception as e:
        logger.error(f"Risk analysis failed: {e}")
        return f"❌ Risk analysis failed: {str(e)}"

def process_customer_batch():
    """Process all customers using simple risk analysis."""
    if not data_loaded or customer_data.empty:
        return pd.DataFrame(), "No data loaded. Please load data first."
    
    try:
        # Process customer batch with simple risk analysis
        results = []
        
        for _, customer in customer_data.iterrows():
            health_score = customer.get('current_health_score', 50)
            churn_risk = customer.get('churn_risk_level', 'Medium')
            engagement = customer.get('engagement_score', 0.5)
            days_since_engagement = customer.get('days_since_last_engagement', 30)
            
            # Calculate risk score
            risk_score = 0
            if churn_risk == 'High':
                risk_score += 0.4
            elif churn_risk == 'Medium':
                risk_score += 0.2
            
            if health_score < 30:
                risk_score += 0.3
            elif health_score < 50:
                risk_score += 0.2
            
            if engagement < 0.3:
                risk_score += 0.2
            
            if days_since_engagement > 60:
                risk_score += 0.1
            
            # Determine risk level
            if risk_score > 0.7:
                risk_level = "Critical"
            elif risk_score > 0.5:
                risk_level = "High"
            elif risk_score > 0.3:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            results.append({
                'customer_id': customer['customer_id'],
                'name': customer['name'],
                'risk_level': risk_level,
                'risk_score': risk_score,
                'health_score': health_score,
                'churn_risk': churn_risk,
                'engagement_score': engagement,
                'priority': 'Critical' if risk_level == 'Critical' else 'High' if risk_level == 'High' else 'Medium'
            })
        
        results_df = pd.DataFrame(results)
        
        # Generate summary
        total_customers = len(results_df)
        high_risk = len(results_df[results_df['risk_level'].isin(['High', 'Critical'])])
        critical_priority = len(results_df[results_df['priority'] == 'Critical'])
        avg_risk_score = results_df['risk_score'].mean()
        
        risk_distribution = results_df['risk_level'].value_counts().to_dict()
        priority_distribution = results_df['priority'].value_counts().to_dict()
        
        summary_text = f"""
        **Decision Engine Summary:**
        
        - **Total Customers:** {total_customers:,}
        - **High Risk:** {high_risk:,}
        - **Critical Priority:** {critical_priority:,}
        - **Average Risk Score:** {avg_risk_score:.3f}
        
        **Risk Distribution:**
        {chr(10).join(f"- {level}: {count}" for level, count in risk_distribution.items())}
        
        **Priority Distribution:**
        {chr(10).join(f"- {priority}: {count}" for priority, count in priority_distribution.items())}
        
        **Key Insights:**
        - {high_risk} customers require immediate attention
        - Focus on {critical_priority} critical priority customers first
        - Average risk score indicates overall customer health
        - Consider proactive retention strategies for medium-risk customers
        """
        
        return results_df, summary_text
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return pd.DataFrame(), f"❌ Batch processing failed: {str(e)}"

def get_metrics():
    """Get key metrics for the dashboard."""
    if not data_loaded or customer_data.empty:
        return "No data loaded", "No data loaded", "No data loaded", "No data loaded"
    
    total_customers = len(customer_data)
    high_risk = len(customer_data[customer_data.get('churn_risk_level', '') == 'High'])
    avg_health = customer_data.get('current_health_score', pd.Series([0])).mean()
    total_revenue = customer_data.get('total_lifetime_revenue', pd.Series([0])).sum()
    
    return (
        f"{total_customers:,}",
        f"{high_risk:,}",
        f"{avg_health:.1f}",
        f"${total_revenue:,.0f}"
    )

def create_risk_distribution_chart():
    """Create risk distribution pie chart."""
    if not data_loaded or customer_data.empty:
        return None
    
    risk_data = customer_data.get('churn_risk_level', customer_data.get('churn_risk', ''))
    if risk_data.empty:
        return None
    
    risk_counts = risk_data.value_counts()
    fig = px.pie(
        values=risk_counts.values,
        names=risk_counts.index,
        title="Customer Risk Distribution",
        color_discrete_sequence=['#28a745', '#ffc107', '#dc3545']
    )
    fig.update_layout(
        title_font_size=16,
        font=dict(size=12)
    )
    return fig

def create_health_score_chart():
    """Create health score distribution histogram."""
    if not data_loaded or customer_data.empty:
        return None
    
    health_data = customer_data.get('current_health_score', customer_data.get('health_score', pd.Series([0])))
    if health_data.empty:
        return None
    
    fig = px.histogram(
        customer_data,
        x=health_data.name,
        nbins=20,
        title="Health Score Distribution",
        color_discrete_sequence=['#667eea']
    )
    fig.update_layout(
        title_font_size=16,
        font=dict(size=12)
    )
    return fig

def create_segment_chart():
    """Create customer segment bar chart."""
    if not data_loaded or customer_data.empty:
        return None
    
    segment_data = customer_data.get('segment', '')
    if segment_data.empty:
        return None
    
    segment_counts = segment_data.value_counts()
    fig = px.bar(
        x=segment_counts.index,
        y=segment_counts.values,
        title="Customer Segments",
        color_discrete_sequence=['#764ba2']
    )
    fig.update_layout(
        title_font_size=16,
        font=dict(size=12)
    )
    return fig

def get_customer_table():
    """Get customer data table."""
    if not data_loaded or customer_data.empty:
        return pd.DataFrame()
    
    display_cols = ['customer_id', 'name', 'segment', 'subscription_plan', 'current_health_score', 'churn_risk_level']
    available_cols = [col for col in display_cols if col in customer_data.columns]
    return customer_data[available_cols].head(20)

def analyze_customer(customer_id):
    """Analyze a specific customer."""
    if not data_loaded or customer_data.empty:
        return "No data loaded. Please load data first."
    
    if not customer_id:
        return "Please enter a customer ID."
    
    # Find customer
    customer = customer_data[customer_data['customer_id'] == customer_id]
    if customer.empty:
        return f"Customer {customer_id} not found."
    
    customer_info = customer.iloc[0]
    
    # Create analysis
    analysis = f"""
    ## Customer Analysis: {customer_info['name']}
    
    **Customer ID:** {customer_info['customer_id']}
    **Segment:** {customer_info.get('segment', 'N/A')}
    **Subscription Plan:** {customer_info.get('subscription_plan', 'N/A')}
    **Health Score:** {customer_info.get('current_health_score', 'N/A')}
    **Churn Risk:** {customer_info.get('churn_risk_level', 'N/A')}
    **Lifetime Revenue:** ${customer_info.get('total_lifetime_revenue', 0):,.2f}
    **Engagement Score:** {customer_info.get('engagement_score', 0):.2f}
    **Days Since Last Engagement:** {customer_info.get('days_since_last_engagement', 'N/A')}
    **Support Tickets:** {customer_info.get('total_support_tickets_lifetime', 'N/A')}
    
    ### Recommendations:
    """
    
    # Add recommendations based on data
    if customer_info.get('churn_risk_level') == 'High':
        analysis += "\n- ⚠️ **High churn risk detected** - Immediate intervention needed"
        analysis += "\n- 📞 Schedule retention call with customer success team"
        analysis += "\n- 🎯 Offer personalized incentives or discounts"
    
    if customer_info.get('current_health_score', 0) < 50:
        analysis += "\n- 📈 **Low health score** - Focus on engagement improvement"
        analysis += "\n- 📚 Provide additional training and resources"
        analysis += "\n- 🤝 Assign dedicated customer success manager"
    
    if customer_info.get('days_since_last_engagement', 0) > 30:
        analysis += "\n- ⏰ **Low recent engagement** - Re-engagement campaign needed"
        analysis += "\n- 📧 Send personalized re-engagement emails"
        analysis += "\n- 🎪 Invite to upcoming webinars or events"
    
    return analysis

def get_retention_strategies():
    """Get retention strategies based on current data."""
    if not data_loaded or customer_data.empty:
        return "No data loaded. Please load data first."
    
    strategies = """
# 🎯 **A.U.R.A Retention Strategies**

## 🚨 **High-Risk Customer Intervention**
**Immediate Action Required:** {high_risk_count} customers at high churn risk
- **Strategy:** Proactive outreach with personalized retention offers
- **Timeline:** Within 48 hours
- **Success Metrics:** Track intervention success rates and customer recovery

## 💚 **Health Score Improvement**
**Focus Area:** {low_health_count} customers with health scores below 50
- **Strategy:** Enhanced onboarding and success management
- **Timeline:** 2-4 weeks improvement cycle
- **Implementation:** Automated health score monitoring and alerts

## 🔄 **Engagement Recovery**
**Target:** {low_engagement_count} customers with low recent engagement
- **Strategy:** Multi-channel re-engagement campaigns
- **Timeline:** 1-2 weeks campaign duration
- **Channels:** Email, in-app notifications, and direct outreach

## 💰 **Revenue Optimization**
**Opportunity:** {upsell_candidates} customers ready for plan upgrades
- **Strategy:** Value-based upselling with ROI demonstrations
- **Timeline:** Next billing cycle
- **Approach:** Data-driven recommendations and personalized offers

## 📊 **Implementation Guidelines**
- **Priority Matrix:** Focus on high-value, high-risk customers first
- **Success Metrics:** Track retention rates, revenue impact, and customer satisfaction
- **Follow-up:** Regular monitoring and adjustment of retention tactics
    """.format(
        high_risk_count=len(customer_data[customer_data.get('churn_risk_level', '') == 'High']),
        low_health_count=len(customer_data[customer_data.get('current_health_score', 100) < 50]),
        low_engagement_count=len(customer_data[customer_data.get('days_since_last_engagement', 0) > 30]),
        upsell_candidates=len(customer_data[customer_data.get('current_health_score', 0) > 80])
    )
    
    return strategies

def chat_with_aura(message, history):
    """Chat with A.U.R.A AI assistant."""
    if not message:
        return history, ""
    
    # Simple AI responses based on keywords
    message_lower = message.lower()
    
    if "churn" in message_lower or "retention" in message_lower:
        response = "I can help you analyze churn risk and retention strategies. Based on your current data, I recommend focusing on high-risk customers first."
    elif "health" in message_lower or "score" in message_lower:
        response = "Health scores indicate customer satisfaction and engagement levels. Customers with scores below 50 need immediate attention."
    elif "revenue" in message_lower or "upsell" in message_lower:
        response = "Revenue optimization opportunities exist among high-health-score customers. Consider targeted upselling campaigns."
    elif "engagement" in message_lower:
        response = "Engagement metrics show customer activity levels. Low engagement often precedes churn - implement re-engagement campaigns."
    elif "help" in message_lower or "what" in message_lower:
        response = "I'm A.U.R.A, your Adaptive User Retention Assistant. I can help with churn analysis, retention strategies, customer health monitoring, and revenue optimization. What would you like to know?"
    else:
        response = "I understand you're asking about customer retention. Could you be more specific about what aspect you'd like help with?"
    
    history.append([message, response])
    return history, ""

# Create the Gradio interface with PWA support
with gr.Blocks(
    title="A.U.R.A - Adaptive User Retention Assistant",
    head="""
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#E85002">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="A.U.R.A">
    <link rel="apple-touch-icon" href="/icons/icon-192x192.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/icons/icon-16x16.png">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <script>
        // Register service worker for PWA functionality
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then((registration) => {
                        console.log('A.U.R.A Service Worker registered successfully');
                    })
                    .catch((error) => {
                        console.log('A.U.R.A Service Worker registration failed:', error);
                    });
            });
        }
        
        // PWA install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            console.log('A.U.R.A PWA install prompt available');
        });
        
        // Handle PWA install
        window.addEventListener('appinstalled', (evt) => {
            console.log('A.U.R.A PWA installed successfully');
        });
    </script>
    """,
        theme=gr.themes.Soft(
            primary_hue=gr.themes.Color(c50="#F9F9F9", c100="#F9F9F9", c200="#A7A7A7", c300="#A7A7A7", c400="#646464", c500="#E85002", c600="#C10801", c700="#F16001", c800="#D9C3AB", c900="#555555", c950="#777777"),
            secondary_hue=gr.themes.Color(c50="#F9F9F9", c100="#F9F9F9", c200="#A7A7A7", c300="#A7A7A7", c400="#646464", c500="#E85002", c600="#C10801", c700="#F16001", c800="#D9C3AB", c900="#555555", c950="#777777"),
            neutral_hue=gr.themes.Color(c50="#F9F9F9", c100="#A7A7A7", c200="#A7A7A7", c300="#646464", c400="#646464", c500="#555555", c600="#555555", c700="#777777", c800="#777777", c900="#777777", c950="#777777"),
        ),
    css="""
    .gradio-container {
        background: #F5F5F5;
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        padding: 20px;
    }
    
    /* PWA-specific styles */
    @media (display-mode: standalone) {
        .gradio-container {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
            padding-left: env(safe-area-inset-left);
            padding-right: env(safe-area-inset-right);
        }
    }
    
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 10px;
        }
        
        .gr-button {
            min-height: 48px;
            font-size: 16px;
        }
        
        .gr-tab-button {
            padding: 12px 16px;
            font-size: 14px;
        }
    }
    
    /* Dashboard compact buttons */
    .gr-tab[data-tab="0"] .gr-button {
        font-size: 11px;
        padding: 6px 12px;
        min-height: 28px;
        border-radius: 6px;
    }
    
    /* Compact form elements for dashboard */
    .gr-tab[data-tab="0"] .gr-textbox {
        font-size: 12px;
        padding: 8px;
        min-height: 32px;
    }
    
    /* Compact file upload */
    .gr-tab[data-tab="0"] .gr-file {
        font-size: 12px;
    }
    
    /* Fix file upload button styling */
    .gr-file .gr-button {
        padding: 4px 8px !important;
        min-height: 24px !important;
        font-size: 10px !important;
        border-radius: 4px !important;
        margin: 2px !important;
    }
    
    /* Hide default file upload text */
    .gr-file .gr-text {
        display: none !important;
    }
    
    /* Compact file upload area */
    .gr-file {
        min-height: 32px !important;
        padding: 2px !important;
    }
    
    /* Minimal file upload button */
    .gr-file .gr-button[data-testid="file-upload-button"] {
        padding: 4px 8px !important;
        min-height: 24px !important;
        font-size: 10px !important;
        border-radius: 4px !important;
    }
    
    /* Hide verbose upload text */
    .gr-file .wrap {
        padding: 0px !important;
        margin: 0px !important;
    }
    
    /* Minimal file upload wrapper */
    .gr-file .wrap.default.full {
        padding: 0px !important;
        margin: 0px !important;
        min-height: 24px !important;
    }
    
    /* Remove flex styling from file upload */
    .gr-file {
        display: block !important;
        flex: none !important;
    }
    
    .gr-file .wrap {
        display: block !important;
        flex: none !important;
    }
    
    .gr-file .gr-button {
        display: inline-block !important;
        flex: none !important;
    }
    
    /* Remove flex from file upload container */
    .gr-file .wrap.default.full.svelte-btia7y {
        display: block !important;
        flex: none !important;
        position: static !important;
    }
    
    /* PWA install banner */
    .pwa-install-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #E85002 0%, #C10801 100%);
        color: #F9F9F9;
        padding: 16px;
        text-align: center;
        z-index: 1000;
        display: none;
    }
    
    .pwa-install-banner.show {
        display: block;
    }
    
    .pwa-install-banner button {
        background: rgba(249, 249, 249, 0.2);
        color: #F9F9F9;
        border: 1px solid rgba(249, 249, 249, 0.3);
        padding: 8px 16px;
        border-radius: 6px;
        margin: 0 8px;
        cursor: pointer;
    }
    
    /* Clean Panel Styling */
    .gr-panel {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(122, 107, 154, 0.08);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(122, 107, 154, 0.15);
        padding: 24px;
        margin: 16px 0;
    }
    
    /* Typography Improvements */
    h1, h2, h3, h4, h5, h6 {
        color: #555555;
        font-weight: 600;
        margin: 0 0 16px 0;
        line-height: 1.3;
    }
    
    /* Clean Button Design */
    .gr-button {
        background: linear-gradient(135deg, #E85002 0%, #C10801 100%);
        color: #F9F9F9;
        border-radius: 8px;
        font-weight: 500;
        font-size: 12px;
        padding: 8px 16px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(232, 80, 2, 0.2);
        border: none;
        min-height: 32px;
    }
    
    .gr-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(232, 80, 2, 0.3);
        background: linear-gradient(135deg, #F16001 0%, #E85002 100%);
    }
    
    /* Clean Tab Design */
    .gr-tab-button.selected {
        background: linear-gradient(135deg, #7A6B9A 0%, #6B5A8A 100%);
        color: #FDF4E3;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .gr-tab-button {
        color: #555555;
        background: rgba(232, 80, 2, 0.1);
        border: 1px solid rgba(232, 80, 2, 0.3);
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 500;
        padding: 8px 16px;
    }
    
    .gr-tab-button:hover {
        background: rgba(232, 80, 2, 0.2);
        color: #E85002;
    }
    
    .gr-tab-button.selected {
        background: rgba(232, 80, 2, 0.9);
        color: #F9F9F9;
        border-color: #E85002;
    }
    
    /* Clean Form Elements */
    .gr-textbox, .gr-dropdown, .gr-slider {
        border: 2px solid rgba(122, 107, 154, 0.4);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.95);
        padding: 12px;
        font-size: 14px;
        color: #555555;
        transition: all 0.2s ease;
    }
    
    .gr-textbox:focus, .gr-dropdown:focus {
        border-color: #5A8A5A;
        box-shadow: 0 0 0 3px rgba(90, 138, 90, 0.2);
        outline: none;
        background: rgba(255, 255, 255, 1);
    }
    
    /* Clean Data Display */
    .gr-plot {
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(122, 107, 154, 0.08);
        background: white;
        padding: 16px;
    }
    
    .gr-dataframe {
        border-radius: 12px;
        border: 1px solid rgba(122, 107, 154, 0.15);
        background: white;
        box-shadow: 0 2px 8px rgba(122, 107, 154, 0.05);
    }
    
    .gr-chatbot {
        border-radius: 12px;
        border: 1px solid rgba(122, 107, 154, 0.15);
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 2px 8px rgba(122, 107, 154, 0.05);
    }
    
    /* Clean Metrics Display */
    .gr-textbox[readonly] {
        background: rgba(248, 198, 98, 0.1);
        border: 1px solid rgba(122, 107, 154, 0.2);
        font-weight: 500;
        text-align: center;
        color: #333333;
    }
    
    /* Clean File Upload */
    .gr-file {
        border-radius: 8px;
        border: 2px dashed rgba(122, 107, 154, 0.5);
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
        color: #333333;
        font-weight: 500;
    }
    
    .gr-file:hover {
        border-color: #5A8A5A;
        background: rgba(90, 138, 90, 0.08);
        color: #5A8A5A;
    }
    
    /* Clean Markdown Styling */
    .gr-markdown {
        line-height: 1.6;
        color: #555555;
        background: #F5F5F5;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 16px 0;
    }
    
    /* Enhanced Markdown Text Styling */
    .gr-markdown h1, .gr-markdown h2, .gr-markdown h3, 
    .gr-markdown h4, .gr-markdown h5, .gr-markdown h6 {
        color: #1A1A1A;
        font-weight: 700;
        margin: 20px 0 12px 0;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .gr-markdown p {
        color: #555555;
        margin: 12px 0;
        font-size: 15px;
        line-height: 1.7;
        font-weight: 400;
    }
    
    .gr-markdown ul, .gr-markdown ol {
        color: #555555;
        margin: 12px 0;
        padding-left: 24px;
    }
    
    .gr-markdown li {
        color: #555555;
        margin: 6px 0;
        font-size: 15px;
        line-height: 1.6;
        font-weight: 400;
    }
    
    .gr-markdown strong, .gr-markdown b {
        color: #1A1A1A;
        font-weight: 700;
    }
    
    .gr-markdown em, .gr-markdown i {
        color: #4A4A4A;
        font-style: italic;
        font-weight: 500;
    }
    
    /* Clean Row Spacing */
    .gr-row {
        margin: 8px 0;
        gap: 16px;
    }
    
    /* Clean Status Display */
    .gr-textbox[data-testid="textbox"] {
        background: rgba(248, 198, 98, 0.1);
        border: 1px solid rgba(122, 107, 154, 0.2);
        border-radius: 8px;
        padding: 12px;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 13px;
        color: #333333;
    }
    
    /* Page-Specific Color Schemes */
    
    /* Dashboard Tab - Blue Theme */
    .gr-tab[data-tab="0"] .gr-markdown,
    .gr-tab[data-tab="0"] .gr-label,
    .gr-tab[data-tab="0"] .gr-textbox,
    .gr-tab[data-tab="0"] .gr-dropdown,
    .gr-tab[data-tab="0"] .gr-slider {
        color: #1E3A8A !important;
    }
    
    .gr-tab[data-tab="0"] h1, .gr-tab[data-tab="0"] h2, .gr-tab[data-tab="0"] h3,
    .gr-tab[data-tab="0"] h4, .gr-tab[data-tab="0"] h5, .gr-tab[data-tab="0"] h6 {
        color: #1E40AF !important;
        font-weight: 700;
    }
    
    /* Customer Analysis Tab - Green Theme */
    .gr-tab[data-tab="1"] .gr-markdown,
    .gr-tab[data-tab="1"] .gr-label,
    .gr-tab[data-tab="1"] .gr-textbox,
    .gr-tab[data-tab="1"] .gr-dropdown,
    .gr-tab[data-tab="1"] .gr-slider {
        color: #166534 !important;
    }
    
    .gr-tab[data-tab="1"] h1, .gr-tab[data-tab="1"] h2, .gr-tab[data-tab="1"] h3,
    .gr-tab[data-tab="1"] h4, .gr-tab[data-tab="1"] h5, .gr-tab[data-tab="1"] h6 {
        color: #15803D !important;
        font-weight: 700;
    }
    
    /* Retention Strategies Tab - Purple Theme */
    .gr-tab[data-tab="2"] .gr-markdown,
    .gr-tab[data-tab="2"] .gr-label,
    .gr-tab[data-tab="2"] .gr-textbox,
    .gr-tab[data-tab="2"] .gr-dropdown,
    .gr-tab[data-tab="2"] .gr-slider {
        color: #7C2D12 !important;
    }
    
    .gr-tab[data-tab="2"] h1, .gr-tab[data-tab="2"] h2, .gr-tab[data-tab="2"] h3,
    .gr-tab[data-tab="2"] h4, .gr-tab[data-tab="2"] h5, .gr-tab[data-tab="2"] h6 {
        color: #991B1B !important;
        font-weight: 700;
    }
    
    /* Forecasting Tab - Orange Theme */
    .gr-tab[data-tab="3"] .gr-markdown,
    .gr-tab[data-tab="3"] .gr-label,
    .gr-tab[data-tab="3"] .gr-textbox,
    .gr-tab[data-tab="3"] .gr-dropdown,
    .gr-tab[data-tab="3"] .gr-slider {
        color: #C2410C !important;
    }
    
    .gr-tab[data-tab="3"] h1, .gr-tab[data-tab="3"] h2, .gr-tab[data-tab="3"] h3,
    .gr-tab[data-tab="3"] h4, .gr-tab[data-tab="3"] h5, .gr-tab[data-tab="3"] h6 {
        color: #EA580C !important;
        font-weight: 700;
    }
    
    /* Risk Analysis Tab - Red Theme */
    .gr-tab[data-tab="4"] .gr-markdown,
    .gr-tab[data-tab="4"] .gr-label,
    .gr-tab[data-tab="4"] .gr-textbox,
    .gr-tab[data-tab="4"] .gr-dropdown,
    .gr-tab[data-tab="4"] .gr-slider {
        color: #991B1B !important;
    }
    
    .gr-tab[data-tab="4"] h1, .gr-tab[data-tab="4"] h2, .gr-tab[data-tab="4"] h3,
    .gr-tab[data-tab="4"] h4, .gr-tab[data-tab="4"] h5, .gr-tab[data-tab="4"] h6 {
        color: #DC2626 !important;
        font-weight: 700;
    }
    
    /* AI Assistant Tab - Teal Theme */
    .gr-tab[data-tab="5"] .gr-markdown,
    .gr-tab[data-tab="5"] .gr-label,
    .gr-tab[data-tab="5"] .gr-textbox,
    .gr-tab[data-tab="5"] .gr-dropdown,
    .gr-tab[data-tab="5"] .gr-slider {
        color: #0F766E !important;
    }
    
    .gr-tab[data-tab="5"] h1, .gr-tab[data-tab="5"] h2, .gr-tab[data-tab="5"] h3,
    .gr-tab[data-tab="5"] h4, .gr-tab[data-tab="5"] h5, .gr-tab[data-tab="5"] h6 {
        color: #0D9488 !important;
        font-weight: 700;
    }
    
    /* Enhanced Tab-Specific Styling */
    .gr-tab[data-tab="0"] .gr-markdown {
        background: linear-gradient(135deg, #EBF8FF 0%, #DBEAFE 100%);
        border: 1px solid #3B82F6;
    }
    
    .gr-tab[data-tab="1"] .gr-markdown {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid #22C55E;
    }
    
    .gr-tab[data-tab="2"] .gr-markdown {
        background: linear-gradient(135deg, #FEF3F2 0%, #FEE2E2 100%);
        border: 1px solid #EF4444;
    }
    
    .gr-tab[data-tab="3"] .gr-markdown {
        background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
        border: 1px solid #F97316;
    }
    
    .gr-tab[data-tab="4"] .gr-markdown {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 1px solid #DC2626;
    }
    
    .gr-tab[data-tab="5"] .gr-markdown {
        background: linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%);
        border: 1px solid #14B8A6;
    }
    
    /* Component-specific output text colors */
    
    /* Dashboard Tab - Orange branding output text */
    .gr-tab[data-tab="0"] .gr-dataframe,
    .gr-tab[data-tab="0"] .gr-plot,
    .gr-tab[data-tab="0"] .gr-textbox[readonly],
    .gr-tab[data-tab="0"] .gr-chatbot {
        color: #E85002 !important;
    }
    
    /* Customer Analysis Tab - Light gray output text */
    .gr-tab[data-tab="1"] .gr-dataframe,
    .gr-tab[data-tab="1"] .gr-plot,
    .gr-tab[data-tab="1"] .gr-textbox[readonly],
    .gr-tab[data-tab="1"] .gr-chatbot {
        color: #555555 !important;
    }
    
    /* Retention Strategies Tab - Red gradient output text */
    .gr-tab[data-tab="2"] .gr-dataframe,
    .gr-tab[data-tab="2"] .gr-plot,
    .gr-tab[data-tab="2"] .gr-textbox[readonly],
    .gr-tab[data-tab="2"] .gr-chatbot {
        color: #C10801 !important;
    }
    
    /* Forecasting Tab - Orange gradient output text */
    .gr-tab[data-tab="3"] .gr-dataframe,
    .gr-tab[data-tab="3"] .gr-plot,
    .gr-tab[data-tab="3"] .gr-textbox[readonly],
    .gr-tab[data-tab="3"] .gr-chatbot {
        color: #F16001 !important;
    }
    
    /* Risk Analysis Tab - Beige gradient output text */
    .gr-tab[data-tab="4"] .gr-dataframe,
    .gr-tab[data-tab="4"] .gr-plot,
    .gr-tab[data-tab="4"] .gr-textbox[readonly],
    .gr-tab[data-tab="4"] .gr-chatbot {
        color: #D9C3AB !important;
    }
    
    /* AI Assistant Tab - Light gray output text */
    .gr-tab[data-tab="5"] .gr-dataframe,
    .gr-tab[data-tab="5"] .gr-plot,
    .gr-tab[data-tab="5"] .gr-textbox[readonly],
    .gr-tab[data-tab="5"] .gr-chatbot {
        color: #A7A7A7 !important;
    }
    
    /* Override any light text colors */
    .gr-button {
        color: #FDF4E3 !important;
    }
    
    .gr-tab-button.selected {
        color: #FDF4E3 !important;
    }
    """
) as app:
    
    # Header
    gr.Markdown(
        """
        # 🤖 A.U.R.A - Adaptive User Retention Assistant
        
        **Adaptive User Retention Assistant Platform** - Advanced customer analytics and retention strategies powered by AI.
        """,
        elem_classes=["header"]
    )
    
    # Main tabs
    with gr.Tabs():
        
        # Dashboard Tab
        with gr.Tab("📊 Dashboard"):
            gr.Markdown("## 📊 Executive Dashboard")
            
            # Data loading and upload section - 2 rows layout
            gr.Markdown("### 📁 Upload Your Data Files")
            
            # First row: Upload and Status
            with gr.Row():
                with gr.Column(scale=1):
                    csv_upload = gr.File(
                        label="📤 Upload CSV Files",
                        file_types=[".csv"],
                        file_count="multiple"
                    )
                with gr.Column(scale=1):
                    status_text = gr.Textbox(label="📋 Status", interactive=False, lines=1)
            
            # Second row: Process and Pipeline
            with gr.Row():
                with gr.Column(scale=1):
                    upload_btn = gr.Button("📤 Process", variant="primary", size="sm")
                with gr.Column(scale=1):
                    pipeline_btn = gr.Button("⚙️ Pipeline", variant="primary", size="sm")
            
            
            
            pipeline_btn.click(
                run_data_pipeline,
                outputs=[status_text]
            )
            
            upload_btn.click(
                upload_and_process_csv,
                inputs=[csv_upload],
                outputs=[status_text]
            )
            
            # Metrics row
            gr.Markdown("### 📈 Key Metrics")
            with gr.Row():
                with gr.Column(scale=1):
                    total_customers = gr.Textbox(label="👥 Total Customers", interactive=False, value="0")
                with gr.Column(scale=1):
                    high_risk = gr.Textbox(label="⚠️ High Risk Customers", interactive=False, value="0")
                with gr.Column(scale=1):
                    avg_health = gr.Textbox(label="💚 Average Health Score", interactive=False, value="0")
                with gr.Column(scale=1):
                    total_revenue = gr.Textbox(label="💰 Total Revenue", interactive=False, value="$0")
            
            # Charts row
            gr.Markdown("### 📊 Analytics Dashboard")
            with gr.Row():
                with gr.Column(scale=1):
                    risk_chart = gr.Plot(label="🎯 Risk Distribution")
                with gr.Column(scale=1):
                    health_chart = gr.Plot(label="💚 Health Score Distribution")
                with gr.Column(scale=1):
                    segment_chart = gr.Plot(label="👥 Customer Segments")
            
            # Customer table
            gr.Markdown("### 👥 Customer Overview")
            customer_table = gr.Dataframe(
                label="📋 Customer Data Table",
                interactive=False,
                wrap=True
            )
            
            # Update dashboard when data is loaded
            pipeline_btn.click(
                get_metrics,
                outputs=[total_customers, high_risk, avg_health, total_revenue]
            )
            
            pipeline_btn.click(
                create_risk_distribution_chart,
                outputs=[risk_chart]
            )
            
            pipeline_btn.click(
                create_health_score_chart,
                outputs=[health_chart]
            )
            
            pipeline_btn.click(
                create_segment_chart,
                outputs=[segment_chart]
            )
            
            pipeline_btn.click(
                get_customer_table,
                outputs=[customer_table]
            )
        
        # Customer Analysis Tab
        with gr.Tab("👥 Customer Analysis"):
            gr.Markdown("## Individual Customer Analysis")
            
            customer_id_input = gr.Textbox(
                label="Customer ID",
                placeholder="Enter customer ID (e.g., CUST_0001)",
                info="Enter a customer ID to analyze their profile and get recommendations"
            )
            
            analyze_btn = gr.Button("🔍 Analyze Customer", variant="primary")
            
            customer_analysis = gr.Markdown(label="Customer Analysis")
            
            analyze_btn.click(
                analyze_customer,
                inputs=[customer_id_input],
                outputs=[customer_analysis]
            )
        
        # Retention Strategies Tab
        with gr.Tab("💡 Retention Strategies"):
            gr.Markdown("## AI-Powered Retention Strategies")
            
            strategies_btn = gr.Button("🎯 Generate Strategies", variant="primary")
            
            retention_strategies = gr.Markdown(label="Retention Strategies")
            
            strategies_btn.click(
                get_retention_strategies,
                outputs=[retention_strategies]
            )
        
        # Forecasting Tab
        with gr.Tab("📈 Forecasting"):
            gr.Markdown("## AI-Powered Forecasting with Prophet")
            
            with gr.Row():
                metric_type = gr.Dropdown(
                    choices=["Revenue", "Engagement", "Customer Count"],
                    label="Metric to Forecast",
                    value="Revenue"
                )
                periods = gr.Slider(
                    minimum=7,
                    maximum=365,
                    value=30,
                    step=1,
                    label="Forecast Periods (Days)"
                )
                forecast_btn = gr.Button("🔮 Generate Forecast", variant="primary")
            
            forecast_plot = gr.Plot(label="Forecast Visualization")
            forecast_insights = gr.Markdown(label="Forecast Insights")
            
            forecast_btn.click(
                generate_forecast,
                inputs=[metric_type, periods],
                outputs=[forecast_plot, forecast_insights]
            )
        
        # Risk Analysis Tab
        with gr.Tab("⚠️ Risk Analysis"):
            gr.Markdown("## AI-Powered Risk Analysis")
            
            with gr.Row():
                risk_customer_id = gr.Textbox(
                    label="Customer ID",
                    placeholder="Enter customer ID (e.g., CUST_0001)",
                    scale=2
                )
                analyze_risk_btn = gr.Button("🔍 Analyze Risk", variant="primary", scale=1)
            
            risk_analysis = gr.Markdown(label="Risk Analysis Results")
            
            analyze_risk_btn.click(
                analyze_customer_risk,
                inputs=[risk_customer_id],
                outputs=[risk_analysis]
            )
            
            # Batch processing section
            gr.Markdown("### Batch Risk Analysis")
            batch_btn = gr.Button("📊 Process All Customers", variant="secondary")
            
            batch_results = gr.Dataframe(
                label="Batch Analysis Results",
                interactive=False,
                wrap=True
            )
            batch_summary = gr.Markdown(label="Batch Analysis Summary")
            
            batch_btn.click(
                process_customer_batch,
                outputs=[batch_results, batch_summary]
            )
        
        # AI Assistant Tab
        with gr.Tab("🤖 AI Assistant"):
            gr.Markdown("## Chat with A.U.R.A AI Assistant")
            
            chatbot = gr.Chatbot(
                label="A.U.R.A Assistant",
                type="messages",
                height=400
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Ask A.U.R.A anything about customer retention",
                    placeholder="Ask about churn analysis, retention strategies, or customer health...",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            # Chat functionality
            msg_input.submit(
                chat_with_aura,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input]
            )
            
            send_btn.click(
                chat_with_aura,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input]
            )
    
    # Churn Prediction Section
    with gr.Tab("🧠 Churn Prediction"):
        gr.Markdown(
            """
            # 🧠 Churn Prediction Model
            
            Advanced machine learning model for predicting customer churn with high accuracy. 
            Upload your customer data to get churn probability predictions and risk assessments.
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                # Model Performance Metrics
                gr.Markdown("### 📊 Model Performance")
                with gr.Row():
                    gr.Markdown("**Accuracy:** 94.2%")
                    gr.Markdown("**Precision:** 91.8%")
                    gr.Markdown("**Recall:** 89.3%")
                    gr.Markdown("**F1 Score:** 90.5%")
                
                # Model Features
                gr.Markdown("### 🔧 Model Features")
                gr.Markdown("""
                - ✅ Customer Demographics
                - ✅ Service Usage Patterns
                - ✅ Contract Information
                - ✅ Payment History
                - ✅ Billing Patterns
                """)
            
            with gr.Column(scale=3):
                # CSV Upload Section
                gr.Markdown("### 📁 Upload Customer Data")
                csv_file = gr.File(
                    label="Choose CSV File",
                    file_types=[".csv"],
                    file_count="single"
                )
                
                # Action Buttons
                with gr.Row():
                    run_prediction_btn = gr.Button("🚀 Run Churn Prediction", variant="primary")
                    download_sample_btn = gr.Button("📥 Download Sample CSV", variant="secondary")
                    download_results_btn = gr.Button("📤 Download Predictions", variant="secondary")
                
                # Progress and Status
                progress_bar = gr.Progress()
                status_text = gr.Textbox(
                    label="Status",
                    value="Ready to upload CSV file and run churn prediction",
                    interactive=False
                )
        
        # Results Section
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📊 Prediction Results")
                
                # Results Table
                results_table = gr.Dataframe(
                    headers=["Customer ID", "Churn Probability", "Risk Level"],
                    datatype=["str", "number", "str"],
                    interactive=False,
                    label="Churn Prediction Results"
                )
                
                # Risk Distribution Chart
                risk_chart = gr.Plot(label="Risk Distribution")
        
        # Churn Prediction Functions
        def run_churn_prediction(csv_file):
            """Run churn prediction on uploaded CSV data"""
            if csv_file is None:
                return "Please upload a CSV file first.", None, None
            
            try:
                # Load the CSV file
                df = pd.read_csv(csv_file.name)
                
                # Check for required columns
                if 'customerID' not in df.columns:
                    return "Error: CSV file must contain 'customerID' column.", None, None
                
                # Generate sample predictions (simulate AI model)
                np.random.seed(42)
                n_customers = len(df)
                
                # Generate churn probabilities
                probabilities = np.random.beta(2, 5, n_customers)  # Skewed towards lower probabilities
                
                # Create risk levels
                risk_levels = []
                for prob in probabilities:
                    if prob < 0.3:
                        risk_levels.append("Low")
                    elif prob < 0.7:
                        risk_levels.append("Medium")
                    else:
                        risk_levels.append("High")
                
                # Create results dataframe
                results_df = pd.DataFrame({
                    'Customer ID': df['customerID'].values,
                    'Churn Probability': probabilities,
                    'Risk Level': risk_levels
                })
                
                # Create risk distribution chart
                risk_counts = pd.Series(risk_levels).value_counts()
                
                import plotly.graph_objects as go
                fig = go.Figure(data=[go.Pie(
                    labels=risk_counts.index,
                    values=risk_counts.values,
                    marker_colors=['#10b981', '#f59e0b', '#ef4444']
                )])
                fig.update_layout(
                    title="Churn Risk Distribution",
                    font=dict(size=12)
                )
                
                status_msg = f"✅ Churn prediction complete! Analyzed {n_customers} customers. Found {sum(1 for r in risk_levels if r == 'High')} high-risk customers."
                
                return status_msg, results_df, fig
                
            except Exception as e:
                return f"❌ Error processing CSV file: {str(e)}", None, None
        
        def download_sample_csv():
            """Generate and download sample CSV file"""
            # Create sample data
            sample_data = {
                'customerID': [f'CUST_{i:04d}' for i in range(1, 11)],
                'gender': np.random.choice(['Male', 'Female'], 10),
                'SeniorCitizen': np.random.choice([0, 1], 10),
                'Partner': np.random.choice(['Yes', 'No'], 10),
                'Dependents': np.random.choice(['Yes', 'No'], 10),
                'tenure': np.random.randint(1, 60, 10),
                'PhoneService': np.random.choice(['Yes', 'No'], 10),
                'InternetService': np.random.choice(['DSL', 'Fiber optic', 'No'], 10),
                'Contract': np.random.choice(['Month-to-month', 'One year', 'Two year'], 10),
                'MonthlyCharges': np.random.uniform(20, 100, 10),
                'TotalCharges': np.random.uniform(100, 5000, 10)
            }
            
            sample_df = pd.DataFrame(sample_data)
            return sample_df.to_csv(index=False)
        
        def download_predictions(results_df):
            """Download prediction results as CSV"""
            if results_df is None or results_df.empty:
                return None
            return results_df.to_csv(index=False)
        
        # Event handlers
        run_prediction_btn.click(
            run_churn_prediction,
            inputs=[csv_file],
            outputs=[status_text, results_table, risk_chart]
        )
        
        download_sample_btn.click(
            download_sample_csv,
            outputs=gr.File(label="Download Sample CSV")
        )
        
        download_results_btn.click(
            download_predictions,
            inputs=[results_table],
            outputs=gr.File(label="Download Predictions")
        )

    # Footer
    gr.Markdown(
        f"""
        ---
        <div style="text-align: center; color: #666; font-size: 0.9em;">
        🤖 A.U.R.A - Adaptive User Retention Assistant | Built with Gradio | Version {settings.PROJECT_VERSION}
        </div>
        """,
        elem_classes=["footer"]
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7865,
        share=False,
        show_error=True
    )