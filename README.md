# ⚾ NPB 一軍試合速報ウィジェット

GitHub Pages + GitHub Actions で動くNPB一軍全試合リアルタイムウィジェット。  
外部サービス不要・完全無料・サーバーレスで動きます。

## 仕組み

```
GitHub Actions (5分ごと / JST 12:00〜24:00)
    │
    ▼
scrape.py
─ baseball.yahoo.co.jp/npb/schedule/ をスクレイピング
─ data/today.json を生成 → コミット & プッシュ
    │
    ▼
GitHub Pages
─ index.html が data/today.json を fetch して表示
─ ブラウザが1分ごとに自動リロード
```

## セットアップ

### 1. GitHub Pages を有効化

Settings → Pages → Source: **Deploy from a branch** → **main / (root)** → Save

### 2. GitHub Actions を有効化

Actions タブ → Enable workflows

### 3. 動作確認

Actions タブ → **NPB Score Updater** → **Run workflow** で手動実行。  
`data/today.json` が更新されれば成功です。

## ウィジェットURL

```
https://ryo0w0.github.io/npb_action/
```

## Static JSON API

```
GET https://ryo0w0.github.io/npb_action/data/today.json
```

## ファイル構成

```
npb_action/
├── index.html                   # ウィジェット本体
├── scrape.py                    # スクレイパー (標準ライブラリのみ)
├── data/
│   └── today.json               # 試合データ (Actions が自動更新)
└── .github/
    └── workflows/
        └── update.yml           # 定期実行ジョブ
```

## 注意事項

- データ元: スポーツナビ (baseball.yahoo.co.jp)
- 非商用・個人利用の範囲でご利用ください
- 公式データではないため正確性は保証しません

## ライセンス

MIT
