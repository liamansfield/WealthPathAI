
import streamlit as st
import requests
import statistics

st.set_page_config(page_title="WealthPath AI", layout="wide")

st.title("WealthPath AI")
st.subheader("Personalized Portfolio Decision-Support Agent")

st.write(
    "Explore an educational portfolio allocation using "
    "your investor profile and historical ETF market data."
)

# Investor inputs
st.header("Investor Inputs")

investment_amount = st.number_input(
    "Investment Amount ($)",
    min_value=100.0,
    value=10000.0,
    step=100.0
)

risk_tolerance = st.selectbox(
    "Risk Tolerance",
    ["Low", "Moderate", "High"],
    index=1
)

time_horizon = st.slider(
    "Investment Time Horizon (Years)",
    min_value=1,
    max_value=40,
    value=10
)

liquidity_need = st.selectbox(
    "Liquidity Need",
    ["Low", "Moderate", "High"]
)

# Retrieve market data
def get_market_data(symbol, api_key):
    url = "https://www.alphavantage.co/query"

    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": api_key
    }

    response = requests.get(
        url, params=parameters, timeout=20
    )
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        message = (
            data.get("Note")
            or data.get("Information")
            or data.get("Error Message")
            or "Market data is unavailable."
        )
        raise ValueError(message)

    daily_data = data["Time Series (Daily)"]
    dates = sorted(daily_data.keys(), reverse=True)

    if len(dates) < 3:
        raise ValueError("Not enough historical observations.")

    prices = [
        float(daily_data[date]["4. close"])
        for date in dates
    ]

    returns = []

    for i in range(len(prices) - 1):
        daily_return = (
            (prices[i] - prices[i + 1])
            / prices[i + 1]
        ) * 100

        returns.append(daily_return)

    historical_return = (
        (prices[0] - prices[-1]) / prices[-1]
    ) * 100

    annual_volatility = (
        statistics.stdev(returns) * (252 ** 0.5)
    )

    return {
        "latest_date": dates[0],
        "oldest_date": dates[-1],
        "latest_price": prices[0],
        "historical_return": historical_return,
        "annual_volatility": annual_volatility,
        "observations": len(dates)
    }


# Investor scoring
def calculate_profile(risk_tolerance, time_horizon, liquidity_need):
    risk_points = {
        "Low": 1,
        "Moderate": 2,
        "High": 3
    }

    liquidity_points = {
        "High": 1,
        "Moderate": 2,
        "Low": 3
    }

    risk_score = risk_points[risk_tolerance]

    if time_horizon < 3:
        risk_score += 1
    elif time_horizon <= 10:
        risk_score += 2
    else:
        risk_score += 3

    risk_score += liquidity_points[liquidity_need]

    if risk_score <= 4:
        profile = "Conservative"
        stocks = 40
        bonds = 60
    elif risk_score <= 7:
        profile = "Moderate"
        stocks = 60
        bonds = 40
    else:
        profile = "Aggressive"
        stocks = 80
        bonds = 20

    return risk_score, profile, stocks, bonds


if st.button("Get Recommendation", type="primary"):

    risk_score, profile, stocks, bonds = calculate_profile(
        risk_tolerance,
        time_horizon,
        liquidity_need
    )

    stock_dollars = investment_amount * stocks / 100
    bond_dollars = investment_amount * bonds / 100

    st.header("Results Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Investor Risk Score", f"{risk_score}/9")
    col2.metric("Investor Profile", profile)
    col3.metric("Investment Amount", f"${investment_amount:,.2f}")

    st.subheader("Model Portfolio Recommendation")

    st.write(f"**Stocks:** {stocks}% — ${stock_dollars:,.2f}")
    st.write(f"**Bonds:** {bonds}% — ${bond_dollars:,.2f}")

    st.write(
        f"Your risk score of {risk_score}/9 maps to the "
        f"{profile.lower()} model allocation based on "
        "your risk tolerance, investment horizon, and liquidity needs."
    )

    st.subheader("Historical Market KPIs — SPY")

    # Read API key from Streamlit secrets
    try:
        api_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = None

    if not api_key:
        st.error(
            "Alpha Vantage API key is not configured. "
            "See the setup instructions."
        )
    else:
        try:
            with st.spinner("Retrieving Alpha Vantage market data..."):
                market = get_market_data("SPY", api_key)

            kpi1, kpi2, kpi3 = st.columns(3)

            kpi1.metric(
                "Historical Price Return",
                f"{market['historical_return']:.2f}%"
            )

            kpi2.metric(
                "Annualized Volatility",
                f"{market['annual_volatility']:.2f}%"
            )

            kpi3.metric(
                "Latest SPY Close",
                f"${market['latest_price']:.2f}"
            )

            st.caption(
                f"Data: {market['oldest_date']} to "
                f"{market['latest_date']} | "
                f"{market['observations']} trading observations. "
                "Price returns exclude dividends."
            )

        except (requests.RequestException, ValueError, KeyError) as error:
            st.error(f"Could not retrieve market data: {error}")

    st.subheader("Model Transparency")

    st.markdown(
        """
        - Recommendations use a simplified rule-based investor
          profile and historical market data.
        - Historical returns and volatility describe past
          performance and do not predict future investment results.
        - The model does not account for all factors, including
          taxes, fees, income needs, or complete financial circumstances.
        - Results are educational decision support and do not
          represent individualized financial advice.
        """
    )
