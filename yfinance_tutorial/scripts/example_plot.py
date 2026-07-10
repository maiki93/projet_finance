import datetime

import matplotlib.pyplot as plt
import yfinance as yf


def main():
    print("Hello from yahoo-finance!")

    # Fetch historical data for Apple Inc. (AAPL)
    ticker = "AAPL"

    today = datetime.date.today().isoformat()
    print("today: {}".format(today))
    data = yf.download(ticker, start="2026-01-01", end=today)

    print(data)

    plt.figure(figsize=(10, 5))
    # plt.plot(data.index, data["Volume"], label=f"{ticker} Volume")
    plt.bar(data.index, data["Volume"].values.flatten(), label=f"{ticker} Volume")
    plt.title(f"{ticker} Historical Volume")
    plt.xlabel("Date")
    plt.ylabel("Volume")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
