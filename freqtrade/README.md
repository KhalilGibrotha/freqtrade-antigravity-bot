# Freqtrade Antigravity Bot 🚀

This repository contains a sophisticated, multi-instance algorithmic trading setup powered by [Freqtrade](https://www.freqtrade.io/). It was developed iteratively to evolve from a simple technical analysis bot into a machine-learning-driven trading system.

## 🛠️ Tools & Architecture

### Core Technologies
*   **[Freqtrade](https://www.freqtrade.io/en/latest/):** The core open-source algorithmic trading software used to run the strategies, backtest historical data, and execute trades.
*   **[FreqAI](https://www.freqtrade.io/en/latest/freqai/):** An advanced machine learning module within Freqtrade. We utilize it to train **XGBoost** regression models on rolling windows of data to predict future price movements and adapt to changing market regimes.
*   **[Podman](https://podman.io/) & Podman Compose:** Used for containerizing the bot instances. This ensures a clean, isolated, and reproducible environment without polluting the host operating system.
*   **PowerShell / Python:** Used for automation scripting, regression testing (`run_regression_tests.ps1`), reporting, and custom CLI dashboarding (`dashboard.py`).

### Project Structure (Multi-Bot Setup)
The system is designed to run multiple isolated bot instances concurrently via `docker-compose.yml`:
1.  **Production Bot (Port 8080):** Runs the highly optimized `CombinedStrategy` (RSI + Bollinger Bands). It utilizes dynamic pairlists and strict protections.
2.  **Experimental Bot (Port 8081):** Runs alternative strategies (like `SniperStrategy`) for testing hypotheses without risking the main portfolio logic.
3.  **FreqAI Bot (Port 8082):** The machine learning instance. It continuously trains models on live data to predict price action.

All bots share a persistent volume mapping to the Windows Host (`Documents/Freqtrade/user_data`) to ensure trade history and sqlite databases survive container restarts.

---

## ⚡ Capabilities & Limitations

### Capabilities
*   **Automated Trading:** 24/7 autonomous market scanning and execution.
*   **Dynamic Pair Selection:** Uses `VolumePairList` to actively hunt for the highest volume trading pairs (Top 20/40), rather than relying on a static list.
*   **Strategy-Embedded Protections:** Built-in circuit breakers (`MaxDrawdownStoploss`, `CooldownPeriod`, `StoplossGuard`) that automatically halt trading during market crashes to preserve capital.
*   **Machine Learning Adaptation:** FreqAI continuously retrains its model (Adaptive Rolling Window) to forget old market regimes (e.g., bull markets) and learn new ones (e.g., bear trends).
*   **Automated Regression Testing:** Custom PowerShell scripts backtest strategies against a defined baseline to prevent deploying changes that degrade performance.
*   **Real-time UI:** Accessible via the built-in Freqtrade Web UI and a custom rich CLI dashboard.

### Limitations
*   **Geographic Restrictions (Shorting):** The current configuration is tied to Binance US. Due to exchange api limitations and US regulations, shorting features cannot be properly tested or executed locally without migrating to an offshore exchange (e.g., Binance Global, ByBit).
*   **Host Dependency:** The bot currently runs on a local Windows machine. If the machine sleeps, loses power, or undergoes Windows Updates, the bot goes offline.
*   **Data Intensive:** Extended backtesting and FreqAI training require downloading massive amounts of historical candle data, which can consume significant local storage and time.

---

## 📜 Complete Work Log (Changelog)

Our iterative development process tracked the following milestones:

### 1. Research & Initial Setup
*   Researched algorithmic trading, DeFi automation, and Freqtrade.
*   Designed the initial configuration (Binance US, 5m timeframe, USDT stake).
*   Created initialization plans and downloaded historical data.
*   Ran initial backtests and started dry-run simulation mode.

### 2. Strategy Expansion & Comparison
*   Developed `SimpleStrategy`, `RSIStrategy`, `BollingerStrategy` (Mean Reversion), and `MACDStrategy` (Trend Following).
*   Created PowerShell scripts to automate comparative backtests.
*   Developed `CombinedStrategy` (RSI + Bollinger), which proved superior in backtesting.
*   Explored `TrailingStrategy` and attempted `ShortStrategy` (blocked by API limits).
*   Created `SniperStrategy` for high precision, low-frequency trades.

### 3. Engineering & DevOps
*   Initialized Git repository and pushed to GitHub.
*   Created `run_regression_tests.ps1` to programmatically ensure code changes don't drop profit below baseline or increase drawdown.
*   Created `generate_report.ps1` for detailed Markdown/HTML reporting via Plotly.
*   Built `dashboard.py` for a rich CLI terminal UI.
*   Installed and configured the Freqtrade Web UI.
*   Migrated from single-bot to a Multi-Bot Podman Compose setup (`freqtrade`, `freqtrade-experimental`).
*   Migrated data to persistent Windows Host storage for safety.

### 4. Advanced Configuration & Optimization
*   Implemented Freqtrade Native Features: **Dynamic Pairlists** (Volume, Age, Spread, Shuffle filters) and **Protections**.
*   Moved Protections into Strategy code for robust backtesting.
*   Utilized **Hyperopt** for 100 epochs to machine-optimize `CombinedStrategy`, resulting in a **+50% profit improvement and -64% drawdown reduction** in historical tests.
*   Integrated **FreqAI** (XGBoost Regressor) with custom feature engineering (`FreqAIStrategy`) and rolling window training.

---

## 🗺️ Future Roadmap

1.  **Cloud VPS Deployment:** Migrate the Podman compose stack from the local Windows machine to a dedicated Linux cloud server (e.g., DigitalOcean, AWS) for true 24/7/365 reliability and lower latency.
2.  **Continuous Integration (CI/CD):** Set up GitHub Actions to automatically run the `run_regression_tests.ps1` script whenever new strategy code is pushed to the repository.
3.  **FreqAI Tuning:** Tune the XGBoost hyperparameters, expand the feature set (e.g., adding correlating pairs), and evaluate the model's out-of-sample performance.
4.  **Live Trading Migration:** Once dry-run simulation proves profitable over a 1-month period on the VPS, configure live exchange API keys with a small initial capital allocation.
5.  **Offshore Exchange Integration:** Research and integrate an exchange that supports margin/shorting for US citizens (or using decentralization) to unlock the `ShortStrategy` potential during bear markets.
