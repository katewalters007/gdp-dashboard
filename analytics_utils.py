import pandas as pd

# Tax rates by area (as decimal)
TAX_RATES = {
    'US-Federal': 0.22,
    'US-State-CA': 0.133,
    'US-State-NY': 0.109,
    'US-State-TX': 0.0,
    'UK': 0.20,
    'Canada-Federal': 0.267,
    'Germany': 0.263,
    'Japan': 0.40,
    'Australia': 0.37,
    'Other': 0.25,
}

def build_profit_analytics(transactions):
    """
    Build analytics dataframe from transactions.
    
    Args:
        transactions: List of transaction dicts from database
        
    Returns:
        DataFrame with columns: date, ticker, action, quantity, price, 
                               realized_profit, estimated_tax, net_profit
    """
    if not transactions:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    # Convert date strings to datetime
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    
    # Sort by date
    df = df.sort_values('trade_date')
    
    # Initialize profit tracking
    df['realized_profit'] = 0.0
    df['estimated_tax'] = 0.0
    df['net_profit'] = 0.0
    
    # Simple profit calculation: for SELL transactions, assume cost basis is stored or calculated
    # For now, we'll use a simplified approach where we track average cost per ticker
    
    cost_basis = {}  # ticker -> {'total_cost': float, 'total_shares': float}
    
    for idx, row in df.iterrows():
        ticker = row['ticker']
        action = row['action']
        quantity = row['quantity']
        price = row['price']
        tax_rate = row['tax_rate']
        
        if action == 'BUY':
            # Add to cost basis
            if ticker not in cost_basis:
                cost_basis[ticker] = {'total_cost': 0.0, 'total_shares': 0.0}
            cost_basis[ticker]['total_cost'] += quantity * price
            cost_basis[ticker]['total_shares'] += quantity
        
        elif action == 'SELL':
            if ticker in cost_basis and cost_basis[ticker]['total_shares'] > 0:
                available_shares = cost_basis[ticker]['total_shares']
                sell_quantity = min(quantity, available_shares)  # Cap at available
                avg_cost = cost_basis[ticker]['total_cost'] / available_shares
                profit = (price - avg_cost) * sell_quantity
                
                cost_basis[ticker]['total_shares'] -= sell_quantity
                cost_basis[ticker]['total_cost'] = max(0, cost_basis[ticker]['total_cost'] - avg_cost * sell_quantity)
                
                if cost_basis[ticker]['total_shares'] <= 0:
                    cost_basis[ticker] = {'total_cost': 0.0, 'total_shares': 0.0}
                
                df.at[idx, 'realized_profit'] = profit
                df.at[idx, 'estimated_tax'] = profit * tax_rate if profit > 0 else 0.0
                df.at[idx, 'net_profit'] = profit - df.at[idx, 'estimated_tax']
        # else: SELL with no cost basis - profit stays 0 (correct default)
    # else: SELL with no cost basis - profit stays 0 (correct default)
    
    df['cumulative_net_profit'] = df['net_profit'].cumsum()
    df['tax_rate_pct'] = df['tax_rate'] * 100
    return df