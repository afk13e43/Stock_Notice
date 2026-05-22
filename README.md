# Stock Notice

每個交易日跑在 GitHub Actions 上，盯著以下 6 個指標，跨越門檻就用 Discord Webhook 通知一次。

## 監控項目

| # | 指標 | 門檻 | Market | 資料來源 |
|---|------|------|--------|----------|
| 1 | 台股大盤 (^TWII) 回檔 | -10% / -20% / -30%（自歷史 ATH） | TW | yfinance |
| 2 | 台股大盤跌破 MA240 | 收盤 < MA240 | TW | yfinance |
| 3 | 台股融資維持率（整體） | < 135% | TW | TWSE OpenAPI |
| 4 | VOO MDD | -10% / -20% / -30%（自歷史 ATH） | US | yfinance |
| 5 | BRK.B P/B Ratio | 1.35 / 1.30 / 1.25 / 1.20 | US | yfinance |
| 6 | USD/TWD 匯率 | < 30 | TW | yfinance (TWD=X) |

## 通知策略

- **只在跨越門檻時推一次**：狀態保存在 `state/{tw,us}_state.json`，每次跑完 commit 回 repo。
- 回升不重推；回升後再跌過同門檻，會再次通知。
- 多個 check 同時觸發時，會合併成一則 Discord 訊息送出（避免 rate limit）。

## 設定步驟

1. 建立 Discord Webhook（頻道設定 → 整合 → Webhook → 新增）。
2. 把這個 repo 推到 GitHub，到 **Settings → Secrets and variables → Actions** 新增一個 secret：
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: 剛剛複製的 webhook URL
3. **Settings → Actions → General → Workflow permissions** 改為 `Read and write permissions`（讓 bot 能 commit 狀態回來）。
4. 到 Actions 頁面手動觸發一次 `Taiwan Market Check` 和 `US Market Check` 確認可運作。

## 排程

- 台股：每週一到五 14:30 (UTC+8) ≈ 06:30 UTC
- 美股：每週一到五 22:30 UTC（≈ 美東 17:30 EST / 18:30 EDT）

GitHub Actions cron 可能延遲 5–15 分鐘，這對日線通知影響不大。

## 本地測試

```powershell
pip install -r requirements.txt
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
python -m src.main --market tw
python -m src.main --market us
```

未設定 `DISCORD_WEBHOOK_URL` 時，訊息會印到 stderr 而不發送，方便 dry-run。

## 首次跑

首跑時 state 為空（drawdown level = 0、所有 bool = false）。若當下指標已經在門檻內，會立刻推一波「目前已觸發」的通知 — 這是預期行為。

## 已知限制

- TWSE OpenAPI 假日打會回空陣列：當天 check 3 會 skip。
- yfinance 的 `priceToBook` 偶爾抓不到值（回 None / 0）：當天 check 5 會 skip 不誤通知。
- 台股連假時 cron 仍會跑，但因 yfinance 回上一交易日資料，不會觸發新通知。

## 結構

```
src/
  main.py            # 入口
  notifier.py        # Discord webhook
  state.py           # state.json + threshold-crossing 邏輯
  data/
    yahoo.py         # yfinance 包裝
    twse.py          # TWSE OpenAPI
  checks/            # 6 個 check module
.github/workflows/
  taiwan-market.yml
  us-market.yml
state/
  tw_state.json
  us_state.json
```
