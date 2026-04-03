import sys
import os
import threading
import subprocess
import platform
import socket
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject, QTimer

from pynput import mouse, keyboard

from config import config


def is_wayland() -> bool:
    """現在のセッションがWaylandかどうかを判定する。"""
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


# Android keyevent コード
ANDROID_KEYEVENTS: dict[str, int] = {
    "home": 3,
    "back": 4,
    "recent": 187,
    "lock": 26,
    "vol_up": 24,
    "vol_down": 25,
}


class AppController(QObject):
    trigger_overlay_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Allow Ctrl+C to work in terminal
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)

        self.scrcpy_proc = None
        self.is_capturing = False

        self.mouse_ctrl = mouse.Controller()
        self.kb_ctrl = keyboard.Controller()

        self.trigger_overlay_signal.connect(self.toggle_scrcpy)

        # Start a local socket server to receive external triggers
        threading.Thread(target=self.run_socket_server, daemon=True).start()

        # scrcpyコマンドを構築してconnection_modeを設定
        self._build_scrcpy_cmd()

        # USBモード: 起動時にscrcpy OTGを開始（常駐）
        # WiFiモード: トグル操作時にstart/stopする
        if self.connection_mode == "usb":
            self.start_scrcpy()
            # scrcpyプロセスの終了を監視 → アプリも終了
            self._watch_timer = QTimer()
            self._watch_timer.timeout.connect(self._check_scrcpy_alive)
            self._watch_timer.start(1000)

    def _check_scrcpy_alive(self):
        """scrcpyプロセスが終了したらアプリも終了する。"""
        if self.scrcpy_proc and self.scrcpy_proc.poll() is not None:
            print("scrcpy terminated. Exiting...")
            self.app.quit()

    def send_android_keyevent(self, keyevent_code: int):
        """adb経由でAndroid端末にキーイベントを送信する。"""
        try:
            cmd = ["adb", "shell", "input", "keyevent", str(keyevent_code)]
            serial = config.get("device_serial")
            if serial:
                cmd = ["adb", "-s", serial, "shell", "input", "keyevent", str(keyevent_code)]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"adb keyevent error: {e}")

    def run_socket_server(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('localhost', 41234))
            server.listen(1)
            while True:
                client, addr = server.accept()
                data = client.recv(1024)
                if data == b'activate':
                    self.trigger_overlay_signal.emit()
                client.close()
        except Exception as e:
            print(f"Socket server error: {e}")

    def _build_scrcpy_cmd(self) -> list[str]:
        """接続モードに応じたscrcpyコマンドを構築する。"""
        mode = config.get("connection_mode", "usb").lower()
        serial = config.get("device_serial")
        self.connection_mode = mode

        if mode == "usb":
            cmd = ["scrcpy", "--otg",
                   "--window-title", "ConnectKbM",
                   "--window-x", "10", "--window-y", "10"]
        else:
            cmd = ["scrcpy", "--no-video", "--no-audio"]

        if serial:
            cmd.extend(["--serial", serial])
        return cmd

    def start_scrcpy(self):
        cmd = self._build_scrcpy_cmd()
        print(f"Starting scrcpy ({self.connection_mode} mode)...")
        self.scrcpy_proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def stop_scrcpy(self):
        """scrcpyプロセスを停止する。"""
        if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
            self.scrcpy_proc.terminate()
            self.scrcpy_proc.wait()
            self.scrcpy_proc = None

    def activate_scrcpy(self):
        """Android操作モードに切り替える。"""
        if self.is_capturing:
            return

        self.is_capturing = True

        if self.connection_mode == "wifi":
            if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
                print("scrcpy is already running.")
            else:
                self.start_scrcpy()
            print("Android操作中 (WiFi)")
        else:
            self._focus_scrcpy_window()
            QTimer.singleShot(150, self._simulate_capture_key)
            print("Android操作中 (USB)")

    def deactivate_scrcpy(self):
        """PCモードに戻る。"""
        if not self.is_capturing:
            return

        self.is_capturing = False

        if self.connection_mode == "wifi":
            self.stop_scrcpy()
        else:
            self._simulate_capture_key()

        print("PCモード (待機中)")

    def toggle_scrcpy(self):
        """Android/PCモードをトグル切替する。"""
        if self.is_capturing:
            self.deactivate_scrcpy()
        else:
            self.activate_scrcpy()

    def _focus_scrcpy_window(self):
        """scrcpyウィンドウを最前面にフォーカスする。"""
        try:
            system = platform.system()
            if system == "Linux":
                subprocess.run(["wmctrl", "-R", "ConnectKbM"])
            elif system == "Darwin":
                script = 'tell application "System Events" to set frontmost of every process whose name is "scrcpy" to true'
                subprocess.run(["osascript", "-e", script])
            elif system == "Windows":
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = user32.FindWindowW(None, "ConnectKbM")
                if hwnd:
                    user32.ShowWindow(hwnd, 5)
                    user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Error activating window: {e}")

    def _simulate_capture_key(self):
        """scrcpyのキャプチャ切替キー(LAlt)をシミュレートする。"""
        self.kb_ctrl.press(keyboard.Key.alt_l)
        self.kb_ctrl.release(keyboard.Key.alt_l)

    def quit_app(self):
        print("Quitting application...")
        self.stop_scrcpy()
        self.app.quit()

    def _parse_shortcut(self, raw: str) -> str:
        """config形式のショートカット文字列をpynput GlobalHotKeys形式に変換する。"""
        parts = raw.lower().split('+')
        return "+".join(f"<{p.strip()}>" if len(p.strip()) > 1 else p.strip() for p in parts)

    def start(self):
        # USBモード: Alt押下でPCモード復帰を検出
        if self.connection_mode == "usb":
            def on_press(key):
                if key == keyboard.Key.alt_l:
                    self.is_capturing = False
            self.kb_listener = keyboard.Listener(on_press=on_press)
            self.kb_listener.start()

        # Setup Global Hotkeys
        raw_shortcut = config.get("shortcut_toggle", "ctrl+shift+f1")
        hotkey_map: dict[str, callable] = {
            self._parse_shortcut(raw_shortcut): self.toggle_scrcpy,
        }

        # Android操作用ショートカットを登録
        for action, keyevent_code in ANDROID_KEYEVENTS.items():
            raw = config.get(f"shortcut_{action}")
            if raw:
                code = keyevent_code
                hotkey_map[self._parse_shortcut(raw)] = lambda c=code: self.send_android_keyevent(c)

        self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
        self.hotkey_listener.start()

        mode_label = "USB(OTG)" if self.connection_mode == "usb" else "WiFi"
        print(f"Application started. [{mode_label}]")
        print(f"Press [{raw_shortcut}] to toggle Android control.")
        if self.connection_mode == "usb":
            print("scrcpyウィンドウの✗ボタンで終了します。")

        # Wayland環境の場合の案内
        if is_wayland():
            print("")
            print("=" * 60)
            print("[注意] Wayland環境が検出されました。")
            print("pynputのグローバルホットキーはWaylandでは動作しません。")
            print("代わりに、デスクトップ環境のカスタムショートカット設定で")
            print(f"  python {os.path.abspath(__file__)} --activate")
            print("を割り当ててください。")
            print("  GNOME: 設定 > キーボード > キーボードショートカット")
            print("  KDE:   システム設定 > ショートカット > カスタムショートカット")
            print("=" * 60)

        try:
            sys.exit(self.app.exec())
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--activate":
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 41234))
            client.sendall(b'activate')
            client.close()
            print("Trigger sent successfully.")
        except Exception as e:
            print("Failed to send trigger. Is the main application running?")
        sys.exit(0)

    controller = AppController()
    controller.start()