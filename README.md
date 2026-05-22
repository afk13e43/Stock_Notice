# Stock Notice

每個交易日跑在 GitHub Actions 上，盯著以下 6 個指標，跨越門檻就用 Discord Webhook 通知一次。

## 監控項目

| # | 指標 | 門檻 | Market | 資料來源 |
|---|------|------|--------|----------|
| 1 | 台股大盤 (^TWII) 回檔 | -10% / -20% / -30%（自歷史 ATH） | TW | yfinance |
| 2 | 台股大盤跌破 MA240 | 收盤 < MA240 | TW | yfinance |
| 3 | 台股上市市場融資維持率 | < 135% | TW | TWSE（自行計算，見下） |
| 4 | VOO MDD | -10% / -20% / -30%（自歷史 ATH） | US | yfinance |
| 5 | BRK.B P/B Ratio | 1.35 / 1.30 / 1.25 / 1.20 | US | yfinance（用 BRK-A 資料） |
| 6 | USD/TWD 匯率 | < 30 | TW | yfinance (TWD=X) |

## 通知策略

- **只在跨越門檻時推一次**：狀態保存在 `state/{tw,us}_state.json`，每次跑完由 bot commit 回 repo。
- 回升不重推；回升後再跌過同門檻，會再次通知。
- 多個 check 同時觸發時，會合併成一則 Discord 訊息送出（避免 rate limit）。

## 設定步驟

1. 在 Discord 目標頻道建立 Webhook（齒輪 → 整合 → Webhook → 新增 → 複製 URL）。
2. **Settings → Secrets and variables → Actions** 新增 repository secret：
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: 剛剛複製的 webhook URL
3. **Settings → Actions → General → Workflow permissions** 改成 `Read and write permissions`（讓 bot 能 commit 狀態回來）。
4. Actions 頁面手動觸發 `Taiwan Market Check` 與 `US Market Check` 各一次確認可運作。

## 排程

- 台股：每週一到五 06:30 UTC（台北 14:30）
- 美股：每週一到五 22:30 UTC（美東 17:30 EST / 18:30 EDT）

GitHub Actions cron 可能延遲 5–15 分鐘，這對日線通知影響不大。

## 實作細節

### 台股維持率（指標 3）

TWSE 並未直接公佈「整體市場融資維持率」這個彙整指標，但所有原始資料都在 OpenAPI 裡。本專案自行用標準公式計算：

```
維持率 = Σ(每檔融資餘額張數 × 1000 × 當日收盤價) / 整體融資金額餘額 × 100
```

資料源：
- `MI_MARGN`（OpenAPI）— 每檔股票融資今日餘額（張）
- `STOCK_DAY_ALL`（OpenAPI）— 每檔股票當日收盤價
- `MI_MARGN?selectType=MS`（傳統端點）— 整體融資金額餘額（仟元，分母）

涵蓋範圍為上市股票（不含上櫃），對「整體市場」是合理近似。

### BRK.B P/B（指標 5）

yfinance 對 `BRK-B` 回傳的 `bookValue` 其實是 BRK-A 每股淨值（兩類股股本結構固定 1500:1），導致直接計算 BRK-B 的 P/B 會得到 0.0009 之類的錯誤值。

由於 P/B 在 A/B 兩類股之間在數學上必然相同，本專案改去查 BRK-A 拿正確的 P/B 數字。並對所有 P/B 套用 (0.2, 20.0) 的 sanity check，任何超出區間的值都當作壞資料、不通知。

## 本地查看當下數字

`scripts/status.py` 是個 read-only 工具，列印 6 個指標的當下值，不會寫 state、不會發 Discord：

```powershell
pip install -r requirements.txt
$env:PYTHONIOENCODING = "utf-8"
python scripts/status.py
```

## 本地手動觸發完整流程（會發 Discord）

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

- **假日**：TWSE 假日打 API 會回空陣列；yfinance 連假日會回上一交易日資料。當天 check 會 skip 或不重複通知，不會誤發。
- **yfinance `priceToBook` 不穩**：除了 BRK.B 的 class 混淆，其他標的也可能偶爾回 None。當天該 check 會 skip。
- **TWSE 端點延遲**：傳統 MS 端點偶爾較慢（已設 30s timeout），但仍有可能 timeout。當天 check 3 會 skip。

## 結構

```
src/
  main.py            # 入口
  notifier.py        # Discord webhook
  state.py           # state.json + threshold-crossing 邏輯
  data/
    yahoo.py         # yfinance 包裝（含 P/B sanity check）
    twse.py          # TWSE OpenAPI + 維持率計算
  checks/            # 6 個 check module
scripts/
  status.py          # 本地查看當下數字（read-only）
.github/workflows/
  taiwan-market.yml
  us-market.yml
state/
  tw_state.json
  us_state.json
```
