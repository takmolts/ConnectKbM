# ConnectKbM

PCのキーボードとマウスを、接続されたAndroid端末へシームレスに共有するアプリケーションです。
設定したショートカットキーを押すだけで即座にスマホの操作へ切り替わり、再度押すことでPCへ戻ることができます。

## 主な特徴
- **ゼロ遅延（USB）**: `scrcpy` のOTGモードにより、物理USB入力デバイスとして認識されるため遅延がありません。
- **WiFi接続対応**: ワイヤレスADB経由での操作にも対応しています。
- **Androidショートカット**: ホーム / 戻る / 最近のアプリ / 画面ロック / 音量をキーボードから操作できます。
- **クロスプラットフォーム**: Windows / macOS / Linux に対応しています。

## 必須要件

| ソフトウェア | 用途 | インストール方法 |
|---|---|---|
| **scrcpy** | キーボード・マウス転送 | 下記参照 |
| **adb** | Androidショートカット・WiFi接続 | scrcpyに同梱、または別途インストール |

### scrcpy のインストール

- **Windows**: [scrcpy リリースページ](https://github.com/Genymobile/scrcpy/releases)からzipをダウンロードし、解凍先にパスを通す
- **macOS**: `brew install scrcpy`
- **Linux**: `sudo apt install scrcpy`

## Android端末の準備

本ツールを使用するには、Android端末側で **開発者オプション** と **USBデバッグ** を有効にする必要があります。

### 開発者オプションの有効化

1. **設定** > **デバイス情報**（または「端末情報」）を開く
2. **ビルド番号** を **7回連続でタップ** する
3. 「開発者になりました」と表示されれば成功

### USBデバッグの有効化

1. **設定** > **システム** > **開発者オプション** を開く（機種によっては 設定 > 開発者オプション）
2. **USBデバッグ** をONにする
3. USB接続時に「USBデバッグを許可しますか？」と表示されたら **許可** をタップする（「このコンピュータを常に許可する」にチェック推奨）

> **注意**: メニューの名称や場所は機種・Androidバージョンによって異なる場合があります。

## 使い方

### USB接続（OTGモード）

1. Android端末をUSBケーブルでPCに接続する
2. `ConnectKbM` を起動する（scrcpyのOTGウィンドウが表示される）
3. **`Alt + F1`** でAndroid操作に切り替え（マウスカーソルがAndroid上に出現）
4. **`左Alt`** でPC操作に戻る
5. scrcpyウィンドウの **✗ボタン** でアプリ終了

### WiFi接続

1. Android端末とPCを同じネットワークに接続する
2. 事前にadbを接続する:
   ```bash
   adb connect <端末のIP>:5555
   ```
3. `config.yaml` を編集する:
   ```yaml
   connection_mode: wifi
   device_serial: "192.168.1.10:5555"
   ```
4. `ConnectKbM` を起動する
5. **`Alt + F1`** でAndroid操作開始（scrcpyがバックグラウンドで起動、ウィンドウ表示なし）
6. もう一度 **`Alt + F1`** でPC操作に戻る（scrcpyが停止）
7. ターミナルで `Ctrl + C` でアプリ終了

### Androidショートカットキー

Android操作中に以下のショートカットが使えます:

| 操作 | デフォルトキー |
|---|---|
| ホームボタン | `Ctrl + Shift + H` |
| 戻るボタン | `Ctrl + Shift + B` |
| 最近のアプリ | `Ctrl + Shift + R` |
| 画面ロック | `Ctrl + Shift + L` |
| 音量アップ | `Ctrl + ↑` |
| 音量ダウン | `Ctrl + ↓` |

## 設定（config.yaml）

初回起動時または手動で `config.yaml` を作成してカスタマイズできます:

```yaml
connection_mode: usb        # usb または wifi
device_serial: null          # 端末シリアル（WiFi時は "IP:port"）
shortcut_toggle: alt+f1      # Android/PC切替キー
shortcut_home: ctrl+shift+h
shortcut_back: ctrl+shift+b
shortcut_recent: ctrl+shift+r
shortcut_lock: ctrl+shift+l
shortcut_vol_up: ctrl+up
shortcut_vol_down: ctrl+down
```

## Wayland環境について

Linux（Wayland）では、OSのセキュリティ制約によりグローバルホットキーが動作しません。
代わりに、**OS側のカスタムショートカット設定**で以下のコマンドを登録してください:

```bash
python /path/to/main.py --activate
```

- **GNOME**: 設定 > キーボード > キーボードショートカット
- **KDE**: システム設定 > ショートカット > カスタムショートカット

## ビルド

### ローカルビルド（Linux）
```bash
chmod +x build.sh
./build.sh
```
`dist/ConnectKbM/` に実行ファイルが生成されます。

### GitHub Actions（全OS自動ビルド）
`v1.0.0` のようなタグをpushすると、GitHub Actionsが Windows / macOS / Linux 用のバイナリを自動生成します。
手動実行も可能です（Actions > Build Binaries > Run workflow）。