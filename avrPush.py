import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports
import subprocess
import threading
import queue
import os
import re


class AvrPushApp:
    def __init__(self, master):
        self.master = master
        self.master.title("AVR Push - AVRマイコン書き込みツール")
        self.master.geometry("800x600")
        self.master.resizable(True, True)

        # キューを作成（スレッドセーフな出力用）
        self.output_queue = queue.Queue()

        # 実行中フラグ
        self.is_running = False

        # ファイル名マッピング（表示名 -> 実際のファイル名）
        self.filename_map = {}

        # UI構築
        self.create_widgets()

        # 初期データ読み込み
        self.refresh_com_ports()
        self.refresh_firmware_files()

        # 定期的にキューをチェック
        self.process_output_queue()

    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ウィンドウのリサイズ設定
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # COMポート選択部
        com_frame = ttk.LabelFrame(main_frame, text="COMポート選択", padding="5")
        com_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        com_frame.columnconfigure(1, weight=1)

        ttk.Label(com_frame, text="COMポート:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.com_port_combo = ttk.Combobox(com_frame, state="readonly")
        self.com_port_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        self.refresh_com_button = ttk.Button(com_frame, text="更新", command=self.refresh_com_ports)
        self.refresh_com_button.grid(row=0, column=2, padx=5)

        # ファームウェアファイル選択部
        file_frame = ttk.LabelFrame(main_frame, text="ファームウェアファイル選択", padding="5")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)

        ttk.Label(file_frame, text="ファイル:").grid(row=0, column=0, sticky=tk.W, padx=5)

        # リストボックスとスクロールバー
        listbox_frame = ttk.Frame(file_frame)
        listbox_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(listbox_frame, height=8)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        file_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        file_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)

        self.refresh_files_button = ttk.Button(file_frame, text="更新", command=self.refresh_firmware_files)
        self.refresh_files_button.grid(row=2, column=0, padx=5, pady=5)

        # 書き込みボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=10)

        self.write_button = ttk.Button(button_frame, text="書き込み実行", command=self.on_write_button_click)
        self.write_button.grid(row=0, column=0, padx=5)

        # ターミナル出力部
        terminal_frame = ttk.LabelFrame(main_frame, text="実行結果", padding="5")
        terminal_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        terminal_frame.columnconfigure(0, weight=1)
        terminal_frame.rowconfigure(1, weight=1)

        # クリアボタン（右上に配置）
        clear_button_frame = ttk.Frame(terminal_frame)
        clear_button_frame.grid(row=0, column=0, sticky=tk.E, pady=(0, 5))

        self.clear_terminal_button = ttk.Button(clear_button_frame, text="クリア", command=self.clear_terminal, width=8)
        self.clear_terminal_button.pack()

        # テキストウィジェットとスクロールバー
        text_frame = ttk.Frame(terminal_frame)
        text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.terminal_text = tk.Text(text_frame, height=15, state=tk.DISABLED, wrap=tk.WORD)
        self.terminal_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        terminal_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.terminal_text.yview)
        terminal_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.terminal_text.config(yscrollcommand=terminal_scrollbar.set)

    def refresh_com_ports(self):
        """利用可能なCOMポートを取得してコンボボックスを更新"""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [port.device for port in ports]

            self.com_port_combo['values'] = port_list

            if port_list:
                self.com_port_combo.current(0)
                self.update_terminal(f"COMポートを検出しました: {', '.join(port_list)}\n")
            else:
                self.update_terminal("COMポートが見つかりませんでした。\n")
        except Exception as e:
            self.update_terminal(f"COMポート取得エラー: {str(e)}\n")

    def refresh_firmware_files(self):
        """firmwareフォルダー内のファイルを取得してリストボックスを更新"""
        try:
            self.file_listbox.delete(0, tk.END)
            self.filename_map.clear()

            current_dir = os.path.dirname(os.path.abspath(__file__))
            firmware_dir = os.path.join(current_dir, "firmware")

            # firmwareフォルダーの存在確認
            if not os.path.exists(firmware_dir):
                self.update_terminal("警告: firmwareフォルダーが見つかりません。フォルダーを作成してください。\n")
                return

            files = [f for f in os.listdir(firmware_dir) if os.path.isfile(os.path.join(firmware_dir, f))]

            # ファイル名のパターン: IDxx_firm.hex -> IDxx
            pattern = re.compile(r'^(ID\d+)_firm\.hex$', re.IGNORECASE)

            for file in sorted(files):
                match = pattern.match(file)
                if match:
                    # パターンに一致する場合は整形した表示名を使用
                    display_name = match.group(1)
                    self.filename_map[display_name] = file
                    self.file_listbox.insert(tk.END, display_name)
                else:
                    # パターンに一致しない場合はそのまま表示
                    self.filename_map[file] = file
                    self.file_listbox.insert(tk.END, file)

            self.update_terminal(f"firmwareフォルダー内に{len(files)}個のファイルを検出しました。\n")
        except Exception as e:
            self.update_terminal(f"ファイル一覧取得エラー: {str(e)}\n")

    def on_write_button_click(self):
        """書き込みボタンクリック時の処理"""
        # 実行中は何もしない
        if self.is_running:
            messagebox.showwarning("実行中", "既にavrdude実行中です。完了するまでお待ちください。")
            return

        # COMポート選択確認
        com_port = self.com_port_combo.get()
        if not com_port:
            messagebox.showerror("エラー", "COMポートを選択してください。")
            return

        # ファームウェアファイル選択確認
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showerror("エラー", "ファームウェアファイルを選択してください。")
            return

        display_name = self.file_listbox.get(selection[0])

        # 表示名から実際のファイル名を取得
        firmware_file = self.filename_map.get(display_name, display_name)

        # ターミナルクリア
        self.terminal_text.config(state=tk.NORMAL)
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.config(state=tk.DISABLED)

        # 実行情報表示
        self.update_terminal(f"=== AVR書き込み開始 ===\n")
        self.update_terminal(f"COMポート: {com_port}\n")
        if display_name != firmware_file:
            self.update_terminal(f"選択: {display_name} ({firmware_file})\n")
        else:
            self.update_terminal(f"ファームウェア: {firmware_file}\n")
        self.update_terminal(f"{'=' * 40}\n\n")

        # UIロック
        self.is_running = True
        self.write_button.config(state=tk.DISABLED)
        self.refresh_com_button.config(state=tk.DISABLED)
        self.refresh_files_button.config(state=tk.DISABLED)

        # 別スレッドでavrdude実行
        thread = threading.Thread(target=self.execute_avrdude, args=(com_port, firmware_file))
        thread.daemon = True
        thread.start()

    def execute_avrdude(self, com_port, firmware_file):
        """avrdudeを実行"""
        try:
            # カレントディレクトリを取得
            current_dir = os.path.dirname(os.path.abspath(__file__))
            avrdude_path = os.path.join(current_dir, "avrdude.exe")
            firmware_path = os.path.join(current_dir, "firmware", firmware_file)

            # avrdude.exeの存在確認
            if not os.path.exists(avrdude_path):
                self.output_queue.put(f"エラー: avrdude.exeが見つかりません。\n")
                self.output_queue.put(f"パス: {avrdude_path}\n")
                self.output_queue.put(f"avrdude.exeを本プログラムと同じディレクトリに配置してください。\n")
                return

            # avrdudeコマンド構築
            # 注: programmer、deviceなどは環境に応じて変更が必要
            # 以下は一般的なArduino用の設定例
            cmd = [
                avrdude_path,
                "-c", "serialupdi",  # プログラマタイプ（要調整）
                "-P", com_port,
                "-p", "t1616",  # マイコンタイプ（要調整）
                "-b", "57600",  # ボーレート
                "-U", f"flash:w:{firmware_path}:i",
                "-V"
            ]

            self.output_queue.put(f"実行コマンド:\n{' '.join(cmd)}\n\n")

            # プロセス実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # リアルタイムで出力を読み取り
            for line in process.stdout:
                self.output_queue.put(line)

            # プロセス終了待ち
            return_code = process.wait()

            # 結果表示
            self.output_queue.put(f"\n{'=' * 40}\n")
            if return_code == 0:
                self.output_queue.put("=== 書き込み成功 ===\n")
            else:
                self.output_queue.put(f"=== 書き込み失敗 (終了コード: {return_code}) ===\n")

        except Exception as e:
            self.output_queue.put(f"\nエラーが発生しました: {str(e)}\n")

        finally:
            # UIロック解除
            self.is_running = False
            self.master.after(0, self.unlock_ui)

    def unlock_ui(self):
        """UI要素のロックを解除"""
        self.write_button.config(state=tk.NORMAL)
        self.refresh_com_button.config(state=tk.NORMAL)
        self.refresh_files_button.config(state=tk.NORMAL)

    def update_terminal(self, text):
        """ターミナルにテキストを追加（メインスレッドから呼び出す）"""
        self.terminal_text.config(state=tk.NORMAL)
        self.terminal_text.insert(tk.END, text)
        self.terminal_text.see(tk.END)
        self.terminal_text.config(state=tk.DISABLED)

    def clear_terminal(self):
        """ターミナルの内容をクリア"""
        self.terminal_text.config(state=tk.NORMAL)
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.config(state=tk.DISABLED)

    def process_output_queue(self):
        """キューから出力を取得してターミナルに表示"""
        try:
            while True:
                text = self.output_queue.get_nowait()
                self.update_terminal(text)
        except queue.Empty:
            pass

        # 定期的に呼び出す
        self.master.after(100, self.process_output_queue)


def main():
    root = tk.Tk()
    app = AvrPushApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
