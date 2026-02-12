# AVR Push - AVRマイコン書き込みGUIツール

AVRマイコンへのファームウェア書き込みを簡単に行うためのGUIアプリケーションです。avrdude.exeをGUIから実行できます。

## 機能

- **COMポート選択**: プルダウンメニューから書き込みに使用するCOMポートを選択
- **ファームウェアファイル選択**: firmwareフォルダー内のファイルをリストから選択
- **ワンクリック書き込み**: 選択したCOMポートとファームウェアで書き込み実行
- **リアルタイム出力表示**: avrdude.exeの実行結果をターミナル画面に表示

## 必要なもの

- Python 3.7以上
- avrdude.exe（本プログラムと同じディレクトリに配置）
- AVRマイコン書き込み用のハードウェア（Arduino等）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. フォルダー構成の作成

プログラムと同じディレクトリに `firmware` フォルダーを作成してください。

```
avrPush/
├── avrPush.py
├── firmware/          ← ここにファームウェアファイルを配置
│   ├── program1.hex
│   └── program2.hex
├── avrdude.exe
└── requirements.txt
```

### 3. avrdude.exeの配置

avrdude.exeを本プログラム（avrPush.py）と同じディレクトリに配置してください。

avrdudeは以下から入手できます:
- Arduino IDEに同梱されています
- https://github.com/avrdudes/avrdude/releases

### 4. 設定の調整（必要に応じて）

[avrPush.py](avrPush.py) の `execute_avrdude` メソッド内で、使用する環境に合わせてavrdudeのパラメータを変更してください。

```python
cmd = [
    avrdude_path,
    "-c", "arduino",      # プログラマタイプ（環境に応じて変更）
    "-P", com_port,
    "-p", "atmega328p",   # マイコンタイプ（環境に応じて変更）
    "-U", f"flash:w:{firmware_path}:i"
]
```

## 使用方法

### 1. アプリケーションの起動

```bash
python avrPush.py
```

### 2. COMポートの選択

- プルダウンメニューから書き込みに使用するCOMポートを選択します
- COMポートが表示されない場合は「更新」ボタンをクリックしてください

### 3. ファームウェアファイルの選択

- `firmware` フォルダー内に書き込むファームウェアファイル（.hex等）を配置します
- リストから書き込むファームウェアファイルをクリックして選択します
- ファイルが表示されない場合は「更新」ボタンをクリックしてください
- firmwareフォルダーが存在しない場合は警告が表示されます

### 4. 書き込み実行

- 「書き込み実行」ボタンをクリックします
- 実行結果がターミナル画面にリアルタイムで表示されます
- 書き込み中は操作がロックされます

## トラブルシューティング

### COMポートが表示されない

- デバイスが正しく接続されているか確認してください
- ドライバが正しくインストールされているか確認してください
- 「更新」ボタンをクリックしてポートを再取得してください

### ファームウェアファイルが表示されない

- `firmware` フォルダーが存在するか確認してください
- ファームウェアファイルが `firmware` フォルダー内に配置されているか確認してください
- 「更新」ボタンをクリックしてファイルリストを再取得してください

### avrdude.exeが見つからない

- avrdude.exeが本プログラムと同じディレクトリに配置されているか確認してください
- 実行結果ターミナルにエラーメッセージが表示されます

### 書き込みに失敗する

- 正しいCOMポートを選択しているか確認してください
- マイコンの種類やプログラマの設定が正しいか確認してください
- [avrPush.py:149-157](avrPush.py#L149-L157) のavrdudeコマンドパラメータを環境に合わせて変更してください

## avrdudeパラメータの例

### Arduino Uno (ATmega328P)
```bash
avrdude -c arduino -P COM3 -p atmega328p -U flash:w:firmware.hex:i
```

### Arduino Mega (ATmega2560)
```bash
avrdude -c wiring -P COM3 -p atmega2560 -U flash:w:firmware.hex:i
```

### USBasp プログラマ
```bash
avrdude -c usbasp -P usb -p atmega328p -U flash:w:firmware.hex:i
```

詳細はavrdudeのドキュメントを参照してください。

## EXE化（配布用）

Pythonがインストールされていない環境でも実行できるように、Windows実行ファイル（.exe）に変換できます。

### 手順

1. **PyInstallerのインストール**
```bash
pip install pyinstaller
```

2. **EXE化の実行**
```bash
pyinstaller --onefile --windowed --name=avrPush avrPush.py
```

3. **生成されたファイル**
```
dist/
└── avrPush.exe  ← 実行ファイル
```

### オプション説明
- `--onefile`: 全てを1つのexeファイルにまとめる
- `--windowed`: コンソールウィンドウを表示しない（GUI専用）
- `--name=avrPush`: 出力ファイル名を指定

### 配布方法

配布する際は、以下のファイル/フォルダーをまとめて配布してください：

```
配布フォルダ/
├── avrPush.exe      ← 生成されたexe
├── avrdude.exe      ← 必須
├── avrdude.conf     ← avrdudeの設定（必要に応じて）
└── firmware/        ← ファームウェアフォルダー
    └── (空でOK)
```

**注意**: avrPush.exeは単体では動作しません。avrdude.exeが同じフォルダーに必要です。

## ライセンス

このプロジェクトはオープンソースです。自由に使用、改変できます。

## 貢献

バグ報告や機能追加の提案は歓迎します。

## 注意事項

- 書き込み中はマイコンの電源を切らないでください
- 誤ったファームウェアを書き込むとマイコンが動作しなくなる可能性があります
- 書き込み前にファームウェアファイルが正しいことを確認してください
