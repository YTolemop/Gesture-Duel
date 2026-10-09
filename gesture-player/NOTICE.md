# 第三方資源

本工具只使用 Hand Landmarker，不使用 Gesture Recognizer。

模型保存位置：`assets/models/hand_landmarker.task`。
來源：https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
SHA-256：`fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`。
MediaPipe 原始碼採 Apache-2.0；官方模型依官方模型資源與使用條款使用。官方指南：https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python 。部署前確認組織適用條款。

OpenCV（Apache-2.0）、NumPy（BSD-3-Clause）、python-socketio（MIT）、Pillow（HPND）、pytest（MIT）及其依賴的授權隨安裝套件保存；完整版本在 requirements-lock.txt。
安裝時可下載，活動執行不下載模型。未提供離線套件安裝包，不複製 .venv 到其他電腦。
