import sys
import numpy as np
import zarr
import pyqtgraph as pg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QLabel,
                             QGroupBox, QSplitter)
from PyQt5.QtCore import QTimer, Qt


class VirtualInstrument(QMainWindow):
    def __init__(self, instr, data_path='virtual_instrument.zarr'):
        super().__init__()
        self.instr = instr
        self.data_path = data_path

        ip = getattr(self.fsv, 'ip_address', 'Unknown')
        self.setWindowTitle(f"Address: {self.instr.ip_address}")
        self.resize(1200, 800)

        self.max_points = 10001
        self.store = zarr.open(self.zarr_path, mode='w', shape=(100, self.max_points), chunks=(1, self.max_points),
                               dtype='f4')
        self.frame_count = 0

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_and_plot)
        self.timer.start(200)

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        container_layout = QVBoxLayout(central_widget)

        self.splitter = QSplitter(Qt.Horizontal)

        control_panel = QWidget()
        v_layout = QVBoxLayout(control_panel)

        freq_group = QGroupBox("Frequency & Span")
        f_layout = QVBoxLayout()
        self.edit_center = self._add_input(f_layout, "Center (Hz):", "6.5e9")
        self.edit_span = self._add_input(f_layout, "Span (Hz):", "1e9")
        self.btn_set_freq = QPushButton("Apply Freq/Span")
        self.btn_set_freq.clicked.connect(self.update_frequency)
        f_layout.addWidget(self.btn_set_freq)
        freq_group.setLayout(f_layout)
        v_layout.addWidget(freq_group)

        acq_group = QGroupBox("Acquisition")
        a_layout = QVBoxLayout()
        self.edit_rbw = self._add_input(a_layout, "RBW (Hz):", "5e6")
        self.edit_vbw = self._add_input(a_layout, "VBW (Hz):", "1e6")
        self.edit_pts = self._add_input(a_layout, "Points:", "1001")
        self.btn_set_acq = QPushButton("Apply RBW/VBW/Pts")
        self.btn_set_acq.clicked.connect(self.update_acq)
        a_layout.addWidget(self.btn_set_acq)
        acq_group.setLayout(a_layout)
        v_layout.addWidget(acq_group)

        v_layout.addStretch()

        self.log_area = QLabel("System Ready")
        self.log_area.setStyleSheet(
            "background: black; color: #00FF00; font-family: Consolas; padding: 5px; min-height: 60px;")
        self.log_area.setWordWrap(True)
        v_layout.addWidget(self.log_area)

        # --- 右侧：绘图面板 ---
        self.plot_widget = pg.PlotWidget(title="Live Spectrum")
        self.plot_widget.setLabel('left', 'Amplitude', units='dBm')
        self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
        self.plot_widget.showGrid(x=True, y=True)  # 建议开启网格
        self.curve = self.plot_widget.plot(pen=pg.mkPen('y', width=1))

        # 2. 将面板加入 Splitter
        self.splitter.addWidget(control_panel)
        self.splitter.addWidget(self.plot_widget)
        self.splitter.setStretchFactor(1, 4)

        # 3. 关键：必须把 splitter 加入布局
        container_layout.addWidget(self.splitter)

    def _add_input(self, layout, label, default):
        h = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(80)  # 固定标签宽度使输入框对齐
        h.addWidget(lbl)
        edit = QLineEdit(default)
        h.addWidget(edit)
        layout.addLayout(h)
        return edit

    def update_frequency(self):
        try:
            cf = float(self.edit_center.text())
            sp = float(self.edit_span.text())
            self.fsv.center_frequency(cf)
            self.fsv.span(sp)
            self.log_area.setText(f"CMD Sent: CF={cf:.2e}, Span={sp:.2e}")
        except Exception as e:
            self.log_area.setText(f"Freq Error: {e}")

    def update_acq(self):
        try:
            rbw = float(self.edit_rbw.text())
            vbw = float(self.edit_vbw.text())
            pts = int(self.edit_pts.text())
            self.fsv.if_frequency(rbw)
            self.fsv.video_frequency(vbw)
            self.fsv.points(pts)
            self.log_area.setText(f"CMD Sent: RBW={rbw:.2e}, VBW={vbw:.2e}, Pts={pts}")
        except Exception as e:
            self.log_area.setText(f"Acq Error: {e}")

    def poll_and_plot(self):
        try:
            # 这里的 get_trace 如果返回 xarray 且包含坐标
            res_data = self.fsv.get_trace()

            y = res_data.values
            x = res_data.coords['frequency'].values

            self.curve.setData(x, y)

            # 动态适应写入 Zarr
            idx = self.frame_count % 100
            n = min(len(y), self.max_points)
            self.store[idx, :n] = y[:n]
            self.frame_count += 1
        except Exception as e:
            # 调试时可以取消注释看看为什么不刷新
            # print(f"Update error: {e}")
            pass