import tkinter as tk
from tkinter import ttk, messagebox
import psychrolib as psy
import bisect

# 初始化psychrolib
psy.SetUnitSystem(psy.SI)

class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("热力学计算工具集")
        master.geometry("400x300")
        
        self.create_main_interface()

    def create_main_interface(self):
        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=50, expand=True)
        
        buttons = [
            ("焓湿图计算", self.open_psychrometrics),
            ("饱和水查询", self.open_saturated_water),
            ("水蒸气查询", self.open_steam),
            ("干空气查询", self.open_dry_air)
        ]
        
        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.pack(fill=tk.X, padx=20, pady=5)

    # 子窗口打开方法
    def open_psychrometrics(self):
        PsychrometricsWindow(tk.Toplevel(self.master))
        
    def open_saturated_water(self):
        SaturatedWaterWindow(tk.Toplevel(self.master))
        
    def open_steam(self):
        SteamWindow(tk.Toplevel(self.master))
        
    def open_dry_air(self):
        DryAirWindow(tk.Toplevel(self.master))


        

# ========== 焓湿图计算模块 ==========
class PsychrometricsWindow:
    def __init__(self, master):
        self.master = master
        master.title("焓湿图参数计算")
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="干球温度 (℃):").grid(row=0, column=0, padx=5)
        self.entry_temp = ttk.Entry(input_frame, width=10)
        self.entry_temp.grid(row=0, column=1)
        
        ttk.Label(input_frame, text="相对湿度 (%):").grid(row=1, column=0, padx=5)
        self.entry_rh = ttk.Entry(input_frame, width=10)
        self.entry_rh.grid(row=1, column=1)
        
        # 计算按钮
        ttk.Button(main_frame, text="计算", command=self.calculate).pack(pady=5)
        
        # 结果表格
        self.tree = ttk.Treeview(main_frame, 
                               columns=("参数", "值"), 
                               show="headings",
                               height=11)
        self.tree.heading("参数", text="参数")
        self.tree.heading("值", text="数值")
        self.tree.column("参数", width=200, anchor=tk.W)
        self.tree.column("值", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 初始化表格数据
        parameters = [
            "环境压力 (kPa)", "含湿量 (g/kg)", "湿球温度 (℃)",
            "露点温度 (℃)", "饱和温度 (℃)", "焓 (kJ/kg)",
            "蒸汽压力 (kPa)", "比热 [kJ/(kg·K)]", "比容 (m³/kg)",
            "密度 (kg/m³)"
        ]
        for param in parameters:
            self.tree.insert("", tk.END, values=(param, "等待输入..."))

    def calculate(self):
        try:
            T_db = float(self.entry_temp.get())
            RH = float(self.entry_rh.get())
            
            if not (-50 <= T_db <= 100):
                raise ValueError("温度范围应在-50℃~100℃")
            if not (0 <= RH <= 100):
                raise ValueError("相对湿度应为0~100%")
                
            results = self.calculate_psychrometrics(T_db, RH)
            
            for i, (param, value) in enumerate(results.items()):
                if "压力" in param or "焓" in param:
                    formatted_value = f"{value:.3f}"
                elif "温度" in param:
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = f"{value:.4f}"
                self.tree.set(self.tree.get_children()[i], 1, formatted_value)
                
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            messagebox.showerror("计算错误", f"发生意外错误: {str(e)}")

    def calculate_psychrometrics(self, T_db, RH):
        P = 101325  # 标准大气压 (Pa)
        RH /= 100  # 转换为小数
        
        W = psy.GetHumRatioFromRelHum(T_db, RH, P)
        T_wb = psy.GetTWetBulbFromRelHum(T_db, RH, P)
        T_dp = psy.GetTDewPointFromRelHum(T_db, RH)
        h = psy.GetMoistAirEnthalpy(T_db, W)
        p_v = psy.GetVapPresFromRelHum(T_db, RH)
        v = psy.GetMoistAirVolume(T_db, W, P)
        rho = 1 / v
        c_p = 1.006 + 1.86 * W
        T_sat = 100  # 假设的饱和温度
        
        return {
            "环境压力 (kPa)": P/1000,
            "含湿量 (g/kg)": W*1000,
            "湿球温度 (℃)": T_wb,
            "露点温度 (℃)": T_dp,
            "饱和温度 (℃)": T_sat,
            "焓 (kJ/kg)": h,
            "蒸汽压力 (kPa)": p_v/1000,
            "比热 [kJ/(kg·K)]": c_p,
            "比容 (m³/kg)": v,
            "密度 (kg/m³)": rho
        }


    

# ========== 饱和水查询模块 ==========
class SaturatedWaterWindow:
    def __init__(self, master):
        self.master = master
        master.title("饱和水性质查询")
        self.saturated_water_data = [ # 数据来自文档2
            [0, 0.00611 * 10 ** (-5), 999.9, 0, 4.212, 0.551, 13.1 * 10 ** (-6), 1788 * 10 ** (-6), 1.789 * 10 ** (-6), -0.63 * 10 ** (-4), 756.4 * 10 ** (-4), 13.67],
            [10, 0.01227 * 10 ** (-5), 999.7, 42.04, 4.191, 0.574, 13.7 * 10 ** (-6), 1306 * 10 ** (-6), 1.306 * 10 ** (-6), 0.70 * 10 ** (-4), 741.6 * 10 ** (-4), 9.52],
            [20, 0.02338 * 10 ** (-5), 998.2, 83.91, 4.183, 0.599, 14.3 * 10 ** (-6), 1004 * 10 ** (-6), 1.006 * 10 ** (-6), 1.82 * 10 ** (-4), 726.2 * 10 ** (-4), 5.42],
            [30, 0.04241 * 10 ** (-5), 995.7, 125.7, 4.174, 0.618, 14.9 * 10 ** (-6), 801.5 * 10 ** (-6), 0.805 * 10 ** (-6), 3.21 * 10 ** (-4), 712.2 * 10 ** (-4), 4.31],
            [40, 0.07375 * 10 ** (-5), 992.2, 167.5, 4.174, 0.635, 15.3 * 10 ** (-6), 653.3 * 10 ** (-6), 0.659 * 10 ** (-6), 3.87 * 10 ** (-4), 696.5 * 10 ** (-4), 3.54],
            [50, 0.12335 * 10 ** (-5), 988.1, 209.3, 4.174, 0.648, 15.7 * 10 ** (-6), 549.4 * 10 ** (-6), 0.556 * 10 ** (-6), 4.49 * 10 ** (-4), 676.9 * 10 ** (-4), 3.54],
            [60, 0.19920 * 10 ** (-5), 983.2, 251.1, 4.179, 0.659, 16.0 * 10 ** (-6), 469.9 * 10 ** (-6), 0.478 * 10 ** (-6), 5.11 * 10 ** (-4), 662.2 * 10 ** (-4), 2.98],
            [70, 0.3116 * 10 ** (-5), 977.8, 293.0, 4.187, 0.668, 16.3 * 10 ** (-6), 406.1 * 10 ** (-6), 0.415 * 10 ** (-6), 5.70 * 10 ** (-4), 643.5 * 10 ** (-4), 2.55],
            [80, 0.4736 * 10 ** (-5), 971.8, 335.0, 4.195, 0.674, 16.6 * 10 ** (-6), 355.1 * 10 ** (-6), 0.365 * 10 ** (-6), 6.32 * 10 ** (-4), 625.9 * 10 ** (-4), 2.21],
            [90, 0.7011 * 10 ** (-5), 965.3, 377.0, 4.208, 0.680, 16.8 * 10 ** (-6), 314.9 * 10 ** (-6), 0.325 * 10 ** (-6), 6.95 * 10 ** (-4), 607.2 * 10 ** (-4), 1.95],
            [100, 1.013 * 10 ** (-5), 958.4, 419.1, 4.220, 0.683, 16.9 * 10 ** (-6), 282.5 * 10 ** (-6), 0.295 * 10 ** (-6), 7.52 * 10 ** (-4), 588.6 * 10 ** (-4), 1.75],
            [110, 1.43 * 10 ** (-5), 951.0, 461.4, 4.233, 0.685, 17.0 * 10 ** (-6), 259.0 * 10 ** (-6), 0.272 * 10 ** (-6), 8.08 * 10 ** (-4), 569.0 * 10 ** (-4), 1.60],
            [120, 1.98 * 10 ** (-5), 943.1, 503.7, 4.250, 0.686, 17.1 * 10 ** (-6), 237.4 * 10 ** (-6), 0.252 * 10 ** (-6), 8.64 * 10 ** (-4), 548.4 * 10 ** (-4), 1.47],
            [130, 2.7 * 10 ** (-5), 934.8, 546.4, 4.266, 0.686, 17.2 * 10 ** (-6), 217.8 * 10 ** (-6), 0.233 * 10 ** (-6), 9.19 * 10 ** (-4), 528.8 * 10 ** (-4), 1.36],
            [140, 3.61 * 10 ** (-5), 926.1, 589.1, 4.287, 0.685, 17.2 * 10 ** (-6), 201.1 * 10 ** (-6), 0.217 * 10 ** (-6), 9.72 * 10 ** (-4), 507.2 * 10 ** (-4), 1.26],
            [150, 4.76 * 10 ** (-5), 917.0, 632.2, 4.313, 0.684, 17.3 * 10 ** (-6), 186.4 * 10 ** (-6), 0.203 * 10 ** (-6), 10.3 * 10 ** (-4), 486.6 * 10 ** (-4), 1.17],
            [160, 6.18 * 10 ** (-5), 907.4, 675.4, 4.264, 0.683, 17.3 * 10 ** (-6), 173.6 * 10 ** (-6), 0.191 * 10 ** (-6), 10.7 * 10 ** (-4), 466.0 * 10 ** (-4), 1.10],
            [170, 7.92 * 10 ** (-5), 897.3, 719.3, 4.380, 0.679, 17.3 * 10 ** (-6), 162.8 * 10 ** (-6), 0.181 * 10 ** (-6), 11.3 * 10 ** (-4), 443.4 * 10 ** (-4), 1.05],
            [180, 10.03 * 10 ** (-5), 886.9, 763.3, 4.417, 0.674, 17.2 * 10 ** (-6), 153.0 * 10 ** (-6), 0.173 * 10 ** (-6), 11.9 * 10 ** (-4), 422.8 * 10 ** (-4), 1.00],
            [190, 12.55 * 10 ** (-5), 870.0, 807.8, 4.459, 0.670, 17.1 * 10 ** (-6), 144.2 * 10 ** (-6), 0.165 * 10 ** (-6), 12.6 * 10 ** (-4), 400.2 * 10 ** (-4), 0.96],
            [200, 15.55 * 10 ** (-5), 863.0, 852.5, 4.505, 0.663, 17.0 * 10 ** (-6), 136.4 * 10 ** (-6), 0.158 * 10 ** (-6), 13.3 * 10 ** (-4), 376.7 * 10 ** (-4), 0.93],
            [210, 19.08 * 10 ** (-5), 852.3, 897.7, 4.555, 0.655, 16.9 * 10 ** (-6), 130.5 * 10 ** (-6), 0.153 * 10 ** (-6), 14.1 * 10 ** (-4), 354.1 * 10 ** (-4), 0.91],
            [220, 23.20 * 10 ** (-5), 840.3, 943.7, 4.614, 0.645, 16.6 * 10 ** (-6), 124.6 * 10 ** (-6), 0.148 * 10 ** (-6), 14.8 * 10 ** (-4), 331.6 * 10 ** (-4), 0.89],
            [230, 27.98 * 10 ** (-5), 827.3, 990.2, 4.681, 0.637, 16.4 * 10 ** (-6), 119.7 * 10 ** (-6), 0.145 * 10 ** (-6), 15.9 * 10 ** (-4), 310.0 * 10 ** (-4), 0.88],
            [240, 33.48 * 10 ** (-5), 813.6, 1037.5, 4.756, 0.628, 16.2 * 10 ** (-6), 114.8 * 10 ** (-6), 0.141 * 10 ** (-6), 16.8 * 10 ** (-4), 285.5 * 10 ** (-4), 0.87],
            [250, 39.78 * 10 ** (-5), 799.0, 1085.7, 4.844, 0.618, 15.9 * 10 ** (-6), 109.9 * 10 ** (-6), 0.137 * 10 ** (-6), 18.1 * 10 ** (-4), 261.9 * 10 ** (-4), 0.86],
            [260, 46.94 * 10 ** (-5), 784.0, 1135.1, 4.949, 0.605, 15.6 * 10 ** (-6), 105.9 * 10 ** (-6), 0.135 * 10 ** (-6), 19.7 * 10 ** (-4), 237.4 * 10 ** (-4), 0.87],
            [270, 55.05 * 10 ** (-5), 767.9, 1185.3, 5.070, 0.590, 15.1 * 10 ** (-6), 102.0 * 10 ** (-6), 0.133 * 10 ** (-6), 21.6 * 10 ** (-4), 214.8 * 10 ** (-4), 0.88],
            [280, 64.20 * 10 ** (-5), 750.7, 1236.8, 5.230, 0.574, 14.6 * 10 ** (-6), 98.1 * 10 ** (-6), 0.131 * 10 ** (-6), 23.7 * 10 ** (-4), 191.3 * 10 ** (-4), 0.90],
            [290, 74.46 * 10 ** (-5), 732.3, 1290.0, 5.485, 0.558, 13.9 * 10 ** (-6), 94.2 * 10 ** (-6), 0.129 * 10 ** (-6), 26.2 * 10 ** (-4), 168.7 * 10 ** (-4), 0.93],
            [300, 85.92 * 10 ** (-5), 712.5, 1344.9, 5.736, 0.540, 13.2 * 10 ** (-6), 91.2 * 10 ** (-6), 0.128 * 10 ** (-6), 29.2 * 10 ** (-4), 144.2 * 10 ** (-4), 0.97],
            [310, 98.70 * 10 ** (-5), 691.1, 1402.2, 6.071, 0.523, 12.5 * 10 ** (-6), 88.3 * 10 ** (-6), 0.128 * 10 ** (-6), 32.9 * 10 ** (-4), 120.7 * 10 ** (-4), 1.03],
            [320, 112.89 * 10 ** (-5), 667.1, 1462.1, 6.574, 0.506, 11.5 * 10 ** (-6), 85.3 * 10 ** (-6), 0.128 * 10 ** (-6), 32.9 * 10 ** (-4), 120.7 * 10 ** (-4), 1.03],
            [330, 128.63 * 10 ** (-5), 640.2, 1526.2, 7.244, 0.484, 10.4 * 10 ** (-6), 81.4 * 10 ** (-6), 0.127 * 10 ** (-6), 43.3 * 10 ** (-4), 76.71 * 10 ** (-4), 1.22],
            [340, 146.05 * 10 ** (-5), 610.1, 1594.8, 8.165, 0.457, 9.17 * 10 ** (-6), 77.5 * 10 ** (-6), 0.127 * 10 ** (-6), 53.4 * 10 ** (-4), 56.70 * 10 ** (-4), 1.39],
            [350, 165.35 * 10 ** (-5), 574.4, 1671.4, 9.504, 0.430, 7.88 * 10 ** (-6), 72.6 * 10 ** (-6), 0.126 * 10 ** (-6), 66.8 * 10 ** (-4), 38.16 * 10 ** (-4), 1.60],
            [360, 186.75 * 10 ** (-5), 528.0, 1761.5, 13.984, 0.395, 5.36 * 10 ** (-6), 66.7 * 10 ** (-6), 0.126 * 10 ** (-6), 109 * 10 ** (-4), 20.21 * 10 ** (-4), 2.35],
            [370, 210.54 * 10 ** (-5), 450.5, 1892.5, 40.321, 0.337, 1.86 * 10 ** (-6), 56.9 * 10 ** (-6), 0.126 * 10 ** (-6), 264 * 10 ** (-4), 4.709 * 10 ** (-4), 6.79]
        ]
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="温度 (℃):").grid(row=0, column=0, padx=5)
        self.entry_temp = ttk.Entry(input_frame, width=10)
        self.entry_temp.grid(row=0, column=1)
        
        ttk.Label(input_frame, text="压力 (Pa):").grid(row=1, column=0, padx=5)
        self.entry_press = ttk.Entry(input_frame, width=10)
        self.entry_press.grid(row=1, column=1)
        
        # 按钮区域
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="温度查询", command=self.query_by_temp).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="压力查询", command=self.query_by_press).pack(side=tk.LEFT, padx=5)
        
        # 结果表格
        self.tree = ttk.Treeview(main_frame, 
                               columns=("参数", "值"), 
                               show="headings",
                               height=12)
        self.tree.heading("参数", text="参数")
        self.tree.heading("值", text="数值")
        self.tree.column("参数", width=200, anchor=tk.W)
        self.tree.column("值", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 初始化表格数据
        parameters = [
            "温度 (℃)", "压力 (Pa)", "密度 (kg/m³)",
            "焓 (kJ/kg)", "质量定压热容 [kJ/(kg·K)]", "导热系数 [W/(m·K)]",
            "热扩散系数 (m²/s)", "动力粘度 (Pa·s)",
            "运动粘度 (m²/s)", "普朗特系数"
        ]
        for param in parameters:
            self.tree.insert("", tk.END, values=(param, "等待查询..."))

    def linear_interpolation(self, x, x1, x2, y1, y2):
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

    def query_by_temp(self):
        try:
            temperature = float(self.entry_temp.get())
            if temperature < self.saturated_water_data[0][0]:
                messagebox.showerror("输入错误", "输入温度低于数据范围")
                return
            if temperature > self.saturated_water_data[-1][0]:
                messagebox.showerror("输入错误", "输入温度高于数据范围")
                return
            
            # 精确匹配检查
            for row in self.saturated_water_data:
                if row[0] == temperature:
                    self.fill_table(row)
                    return
            
            # 线性插值（所有参数明确写出）
            for i in range(len(self.saturated_water_data)-1):
                if self.saturated_water_data[i][0] < temperature < self.saturated_water_data[i+1][0]:
                    row1, row2 = self.saturated_water_data[i], self.saturated_water_data[i+1]
                    interpolated = [
                        temperature,  # 温度直接使用输入值
                        # 压力（列1）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[1], row2[1]),
                        # 密度（列2）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[2], row2[2]),
                        # 焓（列3）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[3], row2[3]),
                        # 质量定压热容（列4）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[4], row2[4]),
                        # 导热系数（列5）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[5], row2[5]),
                        # 热扩散系数（列6）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[6], row2[6]),
                        # 动力粘度（列7）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[7], row2[7]),
                        # 运动粘度（列8）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[8], row2[8]),
                        # 普朗特系数（列11）按温度插值
                        self.linear_interpolation(temperature, row1[0], row2[0], row1[11], row2[11])
                    ]
                    self.fill_table(interpolated)
                    return
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的温度数值")

    def query_by_press(self):
        try:
            pressure = float(self.entry_press.get())
            if pressure < self.saturated_water_data[0][1]:
                messagebox.showerror("输入错误", "输入压力低于数据范围")
                return
            if pressure > self.saturated_water_data[-1][1]:
                messagebox.showerror("输入错误", "输入压力高于数据范围")
                return
            
            # 精确匹配检查
            for row in self.saturated_water_data:
                if row[1] == pressure:
                    self.fill_table(row)
                    return
            
            # 线性插值（所有参数明确写出）
            for i in range(len(self.saturated_water_data)-1):
                if self.saturated_water_data[i][1] < pressure < self.saturated_water_data[i+1][1]:
                    row1, row2 = self.saturated_water_data[i], self.saturated_water_data[i+1]
                    # 温度（列0）按压力插值
                    temperature = self.linear_interpolation(pressure, row1[1], row2[1], row1[0], row2[0])
                    interpolated = [
                        temperature,
                        pressure,  # 压力直接使用输入值
                        # 密度（列2）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[2], row2[2]),
                        # 焓（列3）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[3], row2[3]),
                        # 质量定压热容（列4）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[4], row2[4]),
                        # 导热系数（列5）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[5], row2[5]),
                        # 热扩散系数（列6）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[6], row2[6]),
                        # 动力粘度（列7）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[7], row2[7]),
                        # 运动粘度（列8）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[8], row2[8]),
                        # 普朗特系数（列11）按压力插值
                        self.linear_interpolation(pressure, row1[1], row2[1], row1[11], row2[11])
                    ]
                    self.fill_table(interpolated)
                    return
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的压力数值")

    def fill_table(self, data):
        parameters = [
            ("温度 (℃)", data[0]),
            ("压力 (Pa)", data[1]),
            ("密度 (kg/m³)", data[2]),
            ("焓 (kJ/kg)", data[3]),
            ("质量定压热容 [kJ/(kg·K)]", data[4]),
            ("导热系数 [W/(m·K)]", data[5]),
            ("热扩散系数 (m²/s)", data[6]),
            ("动力粘度 (Pa·s)", data[7]),
            ("运动粘度 (m²/s)", data[8]),
            ("普朗特系数", data[9])
        ]
        for i, (name, value) in enumerate(parameters):
            self.tree.set(self.tree.get_children()[i], 1, f"{value:.6g}")







            


# ========== 水蒸气查询模块 ==========
class SteamWindow:
    def __init__(self, master):
        self.master = master
        master.title("干饱和水蒸气性质查询")
        self.raw_data = [  # 来自文档3
            # 温度℃ | 压力×10⁵Pa | 密度kg/m³ | 焓kJ/kg | 汽化潜热kJ/kg | 定压热容kJ/(kg·K) | 导热系数W/(m·K) | 热扩散系数m²/s | 动力粘度Pa·s | 运动粘度m²/s | 普朗特数
            [0, 0.00611, 0.004847, 2501.6, 2501.6, 1.8543, 1.83e-2, 7.313e-5, 8.022e-6, 1.655e-6, 0.815],
            [10, 0.01227, 0.009396, 2520.0, 2477.7, 1.8594, 1.88e-2, 3.8813e-5, 8.424e-6, 8.9654e-7, 0.831],
            [20, 0.02338, 0.01729, 2538.0, 2454.3, 1.8661, 1.94e-2, 2.1672e-5, 8.84e-6, 5.099e-7, 0.847],
            [30, 0.04241, 0.03037, 2556.5, 2430.9, 1.8744, 2.00e-2, 1.2651e-5, 9.218e-6, 3.0353e-7, 0.863],
            [40, 0.07375, 0.05116, 2574.5, 2407.0, 1.8853, 2.06e-2, 7.6845e-6, 9.62e-6, 1.8804e-7, 0.883],
            [50, 0.12335, 0.08302, 2592.0, 2382.7, 1.8987, 2.12e-2, 4.8359e-6, 1.022e-5, 1.2072e-7, 0.896],
            [60, 0.19920, 0.1302, 2609.6, 2358.4, 1.9155, 2.19e-2, 3.1555e-6, 1.0424e-5, 8.007e-8, 0.913],
            [70, 0.3116, 0.1982, 2626.8, 2334.1, 1.9364, 2.25e-2, 2.1057e-6, 1.0817e-5, 5.457e-8, 0.930],
            [80, 0.4736, 0.2993, 2643.5, 2309.0, 1.9615, 2.33e-2, 1.4553e-6, 1.1219e-5, 3.825e-8, 0.947],
            [90, 0.7011, 0.4235, 2660.3, 2238.1, 1.9921, 2.40e-2, 1.0222e-6, 1.1621e-5, 2.744e-8, 0.966],
            [100, 1.0130, 0.5977, 2676.2, 2257.1, 2.0281, 2.48e-2, 7.357e-7, 1.2023e-5, 2.012e-8, 0.984],
            [110, 1.4327, 0.8265, 2691.3, 2229.9, 2.0704, 2.56e-2, 5.383e-7, 1.2425e-5, 1.503e-8, 1.00],
            [120, 1.9854, 1.122, 2705.9, 2202.3, 2.1198, 2.65e-2, 4.015e-7, 1.2798e-5, 1.141e-8, 1.02],
            [130, 2.7013, 1.497, 2719.7, 2173.8, 2.1763, 2.76e-2, 3.046e-7, 1.317e-5, 8.8e-9, 1.04],
            [140, 3.614, 1.967, 2733.1, 2144.1, 2.2408, 2.85e-2, 2.338e-7, 1.3543e-5, 6.89e-9, 1.06],
            [150, 4.760, 2.548, 2745.3, 2113.1, 2.3142, 2.97e-2, 1.81e-7, 1.3896e-5, 5.45e-9, 1.08],
            [160, 6.181, 3.260, 2756.6, 2081.3, 2.3974, 3.08e-2, 1.42e-7, 1.4249e-5, 4.37e-9, 1.11],
            [170, 7.920, 4.123, 2767.1, 2047.8, 2.4911, 3.21e-2, 1.125e-7, 1.4612e-5, 3.54e-9, 1.13],
            [180, 10.027, 5.165, 2776.3, 2013.0, 2.5958, 3.36e-2, 9.03e-8, 1.4965e-5, 2.9e-9, 1.15],
            [190, 12.551, 6.397, 2784.2, 1976.6, 2.7126, 3.51e-2, 7.29e-8, 1.5298e-5, 2.39e-9, 1.18],
            [200, 15.549, 7.864, 2790.9, 1938.5, 2.8428, 3.68e-2, 5.92e-8, 1.5651e-5, 1.99e-9, 1.21],
            [210, 19.077, 9.593, 2796.4, 1898.3, 2.9877, 3.87e-2, 4.86e-8, 1.5995e-5, 1.67e-9, 1.24],
            [220, 23.198, 11.62, 2799.7, 1856.4, 3.1497, 4.07e-2, 4.0e-8, 1.6338e-5, 1.41e-9, 1.26],
            [230, 27.976, 14.00, 2801.8, 1811.6, 3.3310, 4.30e-2, 3.32e-8, 1.6701e-5, 1.19e-9, 1.29],
            [240, 33.478, 16.76, 2802.2, 1764.7, 3.5366, 4.54e-2, 2.76e-8, 1.7073e-5, 1.02e-9, 1.33],
            [250, 39.776, 19.99, 2800.6, 1714.5, 3.7723, 4.84e-2, 2.31e-8, 1.7446e-5, 8.73e-10, 1.36],
            [260, 46.943, 23.73, 2796.4, 1661.3, 4.0470, 5.18e-2, 1.94e-8, 1.7848e-5, 7.52e-10, 1.40],
            [270, 55.058, 23.10, 2789.7, 1604.8, 4.3735, 5.55e-2, 1.63e-8, 1.828e-5, 6.51e-10, 1.44],
            [280, 64.202, 33.19, 2780.5, 1543.7, 4.7675, 6.00e-2, 1.37e-8, 1.875e-5, 5.65e-10, 1.49],
            [290, 74.461, 39.16, 2767.5, 1477.5, 5.2528, 6.55e-2, 1.15e-8, 1.927e-5, 4.92e-10, 1.54],
            [300, 85.927, 46.19, 2751.1, 1405.9, 5.8632, 7.22e-2, 9.6e-9, 1.9839e-5, 4.30e-10, 1.61],
            [310, 98.700, 54.54, 2730.2, 1327.6, 6.6503, 8.02e-2, 8.0e-9, 2.0691e-5, 3.80e-10, 1.71],
            [320, 112.89, 64.60, 2703.8, 1241.0, 7.7217, 8.65e-2, 6.2e-9, 2.1691e-5, 3.36e-10, 1.94],
            [330, 128.63, 76.99, 2670.3, 1143.8, 9.3613, 9.61e-2, 4.8e-9, 2.3093e-5, 3.0e-10, 2.24],
            [340, 146.05, 92.76, 2626.0, 1030.8, 12.2103, 1.07e-1, 3.4e-9, 2.4692e-5, 2.66e-10, 2.82],
            [350, 165.35, 113.6, 2567.8, 895.6, 17.1504, 1.19e-1, 2.2e-9, 2.6594e-5, 2.34e-10, 3.83],
            [360, 186.75, 144.1, 2485.3, 721.4, 25.1162, 1.37e-1, 1.4e-9, 2.9193e-5, 2.03e-10, 5.34],
            [370, 210.54, 201.1, 2342.9, 452.6, 81.1025, 1.66e-1, 4.0e-10, 3.3989e-5, 1.69e-10, 15.7],
        ]
        self.calc = self.SteamCalculator(self.raw_data)  # 关键修正：传递数据
        self.setup_ui()

    class SteamCalculator:
        def __init__(self, raw_data):
            self.data = []
            # 单位转换修正
            for row in raw_data:
                self.data.append([
                    row[0],             # 温度 ℃
                    row[1] * 1e5,       # 压力 → Pa (原数据为×10⁵Pa)
                    row[2],             # 密度 kg/m³
                    row[3],             # 焓 kJ/kg
                    row[4],             # 汽化潜热 kJ/kg
                    row[5],             # 质量定压热容 kJ/(kg·K)
                    row[6],             # 导热系数 W/(m·K)
                    row[7] * 1e-6,      # 热扩散系数 → m²/s (原数据为×1e-6)
                    row[8] * 1e-6,      # 动力粘度 → Pa·s (原数据为×1e-6)
                    row[9] * 1e-6,      # 运动粘度 → m²/s (原数据为×1e-6)
                    row[10]             # 普朗特数
                ])
            # 创建排序列表
            self.temp_list = sorted([x[0] for x in self.data])
            self.press_list = sorted([x[1] for x in self.data])
            

        def get_by_temp(self, temp):
            idx = bisect.bisect_left(self.temp_list, temp)
            return self._interpolate(idx, temp, self.temp_list)

        def get_by_pressure(self, press):
            idx = bisect.bisect_left(self.press_list, press)
            return self._interpolate(idx, press, self.press_list)

        def _interpolate(self, idx, x, x_list):
            if idx == 0: return self.data[0]
            if idx >= len(x_list): return self.data[-1]
            x0, x1 = x_list[idx-1], x_list[idx]
            y0 = [item for item in self.data if item[0] == x0][0] if x_list is self.temp_list else \
                 [item for item in self.data if item[1] == x0][0]
            y1 = [item for item in self.data if item[0] == x1][0] if x_list is self.temp_list else \
                 [item for item in self.data if item[1] == x1][0]
            ratio = (x - x0) / (x1 - x0) if (x1 - x0) != 0 else 0
            return [y0[i] + (y1[i] - y0[i]) * ratio for i in range(len(y0))]

    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="温度(℃):").grid(row=0, column=0, padx=5)
        self.entry_temp = ttk.Entry(input_frame, width=12)
        self.entry_temp.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="压力(×10⁵Pa):").grid(row=0, column=2, padx=5)
        self.entry_press = ttk.Entry(input_frame, width=12)
        self.entry_press.grid(row=0, column=3, padx=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, columnspan=4, pady=5)
        ttk.Button(btn_frame, text="温度查询", command=self.temp_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="压力查询", command=self.press_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT, padx=5)
        
        # 结果表格
        self.tree = ttk.Treeview(main_frame, 
                               columns=("参数", "数值"), 
                               show="headings",
                               height=12)
        self.tree.heading("参数", text="参数", anchor=tk.CENTER)
        self.tree.heading("数值", text="数值", anchor=tk.CENTER)
        self.tree.column("参数", width=250, anchor=tk.W)
        self.tree.column("数值", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 初始化表格
        parameters = [
            "温度 (℃)", "压力 (×10⁵ Pa)", "密度 (kg/m³)",
            "焓 (kJ/kg)", "汽化潜热 (kJ/kg)", "质量定压热容 (kJ/(kg·K))",
            "导热系数 (W/(m·K))", "热扩散系数 (m²/s)", "动力粘度 (Pa·s)",
            "运动粘度 (m²/s)", "普朗特数"
        ]
        for param in parameters:
            self.tree.insert("", tk.END, values=(param, "等待查询..."))

    def temp_query(self):
        try:
            temp = float(self.entry_temp.get())
            if temp < self.calc.temp_list[0] or temp > self.calc.temp_list[-1]:
                raise ValueError(f"温度范围：{self.calc.temp_list[0]}℃~{self.calc.temp_list[-1]}℃")
            result = self.calc.get_by_temp(temp)
            self.display_result(result, is_temp=True)
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def press_query(self):
        try:
            press = float(self.entry_press.get()) * 1e5  # 输入为×10⁵Pa需转换
            if press < self.calc.press_list[0] or press > self.calc.press_list[-1]:
                raise ValueError(f"压力范围：{self.calc.press_list[0]/1e5:.3f}~{self.calc.press_list[-1]/1e5:.1f}×10⁵Pa")
            result = self.calc.get_by_pressure(press)
            self.display_result(result, is_temp=False)
        except Exception as e:
            messagebox.showerror("错误", str(e))
            

    def display_result(self, data, is_temp):
        self.tree.delete(*self.tree.get_children())
        properties = [
            ('温度 (℃)', f"{data[0]:.2f}"),
            ('压力 (×10⁵ Pa)', f"{data[1]/1e5:.5f}"),
            ('密度 (kg/m³)', f"{data[2]:.5f}"),
            ('焓 (kJ/kg)', f"{data[3]:.1f}"),
            ('汽化潜热 (kJ/kg)', f"{data[4]:.1f}"),
            ('质量定压热容 (kJ/(kg·K))', f"{data[5]:.4f}"),
            ('导热系数 (W/(m·K))', f"{data[6]:.4f}"),
            ('热扩散系数 (m²/s)', f"{data[7]:.2e}"),
            ('动力粘度 (Pa·s)', f"{data[8]:.2e}"),
            ('运动粘度 (m²/s)', f"{data[9]:.2e}"),
            ('普朗特数', f"{data[10]:.3f}")
        ]
        if not is_temp:
            properties[0], properties[1] = properties[1], properties[0]
        for prop in properties:
            self.tree.insert('', 'end', values=prop)

    def clear(self):
        self.entry_temp.delete(0, tk.END)
        self.entry_press.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())


        
        

# ========== 干空气查询模块 ==========
class DryAirWindow:
    def __init__(self, master):
        self.master = master
        master.title("干空气热物理性质查询")
        self.dry_air_data = [  # 来自文档4
            [-50, 1.584, 1.013, 2.034, 1.27, 1.46, 9.23, 0.728],
            [-40, 1.515, 1.013, 2.115, 1.38, 1.52, 10.04, 0.728],
            [-30, 1.453, 1.013, 2.196, 1.49, 1.57, 10.80, 0.723],
            [-20, 1.395, 1.009, 2.278, 1.62, 1.62, 11.60, 0.716],
            [-10, 1.342, 1.009, 2.359, 1.74, 1.67, 12.43, 0.712],
            [0, 1.293, 1.005, 2.440, 1.88, 1.72, 13.28, 0.707],
            [10, 1.247, 1.005, 2.510, 2.01, 1.77, 14.16, 0.705],
            [20, 1.205, 1.005, 2.581, 2.14, 1.81, 15.06, 0.703],
            [30, 1.165, 1.005, 2.673, 2.29, 1.86, 16.00, 0.701],
            [40, 1.128, 1.005, 2.754, 2.43, 1.91, 16.96, 0.699],
            [50, 1.093, 1.005, 2.824, 2.57, 1.96, 17.95, 0.698],
            [60, 1.060, 1.005, 2.893, 2.72, 2.01, 18.97, 0.696],
            [70, 1.029, 1.009, 2.963, 2.86, 2.06, 20.02, 0.694],
            [80, 1.000, 1.009, 3.004, 3.02, 2.11, 21.09, 0.692],
            [90, 0.972, 1.009, 3.126, 3.19, 2.15, 22.10, 0.690],
            [100, 0.946, 1.009, 3.207, 3.36, 2.19, 23.13, 0.688],
            [120, 0.898, 1.009, 3.335, 3.68, 2.29, 25.45, 0.686],
            [140, 0.854, 1.013, 3.486, 4.03, 2.37, 27.80, 0.684],
            [160, 0.815, 1.017, 3.637, 4.39, 2.45, 30.09, 0.682],
            [180, 0.779, 1.022, 3.777, 4.75, 2.53, 32.49, 0.681],
            [200, 0.746, 1.026, 3.928, 5.14, 2.60, 34.85, 0.680],
            [250, 0.674, 1.038, 4.625, 6.10, 2.74, 40.61, 0.677],
            [300, 0.615, 1.047, 4.602, 7.16, 2.97, 48.33, 0.674],
            [350, 0.566, 1.059, 4.904, 8.19, 3.14, 55.46, 0.676],
            [400, 0.524, 1.068, 5.206, 9.31, 3.31, 63.09, 0.678],
            [500, 0.456, 1.093, 5.740, 11.53, 3.62, 79.38, 0.687],
            [600, 0.404, 1.114, 6.217, 13.83, 3.91, 96.89, 0.699],
            [700, 0.362, 1.135, 6.70, 16.34, 4.018, 115.4, 0.706],
            [800, 0.329, 1.156, 7.170, 18.88, 4.43, 134.8, 0.713],
            [900, 0.301, 1.172, 7.623, 21.82, 4.67, 155.1, 0.717],
            [1000, 0.277, 1.185, 8.064, 24.59, 4.90, 177.1, 0.719],
            [1100, 0.257, 1.197, 8.494, 27.63, 5.12, 199.3, 0.722],
            [1200, 0.239, 1.210, 9.145, 31.65, 5.35, 233.7, 0.724],
        ]
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="温度 (℃):").grid(row=0, column=0, padx=5)
        self.entry_temp = ttk.Entry(input_frame, width=10)
        self.entry_temp.grid(row=0, column=1, padx=5)
        
        # 查询按钮
        ttk.Button(main_frame, text="查询", command=self.query).pack(pady=5)
        
        # 结果表格
        self.tree = ttk.Treeview(main_frame,
                               columns=("参数", "数值"),
                               show="headings",
                               height=9)
        self.tree.heading("参数", text="参数")
        self.tree.heading("数值", text="数值")
        self.tree.column("参数", width=200, anchor=tk.W)
        self.tree.column("数值", width=150, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 初始化数据
        parameters = [
            "密度 (kg/m³)", "质量定压热容 [kJ/(kg·K)]", 
            "导热系数 [W/(m·K)]", "导温系数 (m²/s)",
            "动力粘度 (Pa·s)", "运动粘度 (m²/s)", "普朗特数"
        ]
        for param in parameters:
            self.tree.insert("", tk.END, values=(param, "等待查询..."))

    def linear_interpolation(self, x, x_list, y_list):
        for i in range(len(x_list)-1):
            if x_list[i] <= x <= x_list[i+1]:
                return y_list[i] + (x - x_list[i]) * (y_list[i+1] - y_list[i]) / (x_list[i+1] - x_list[i])
        return None

    def query(self):
        try:
            temp = float(self.entry_temp.get())
            temp_list = [row[0] for row in self.dry_air_data]
            
            if temp < temp_list[0] or temp > temp_list[-1]:
                raise ValueError("温度范围：-50℃ ~ 1200℃")
            
            # 提取各参数列表
            params = {
                '密度': [row[1] for row in self.dry_air_data],
                '定压热容': [row[2] for row in self.dry_air_data],
                '导热系数': [row[3] for row in self.dry_air_data],
                '导温系数': [row[4] for row in self.dry_air_data],
                '动力粘度': [row[5] for row in self.dry_air_data],
                '运动粘度': [row[6] for row in self.dry_air_data],
                '普朗特数': [row[7] for row in self.dry_air_data]
            }
            
            # 执行插值计算
            results = []
            for param in ['密度', '定压热容', '导热系数', 
                         '导温系数', '动力粘度', '运动粘度', '普朗特数']:
                results.append(self.linear_interpolation(temp, temp_list, params[param]))
            
            # 更新表格
            for i, value in enumerate(results):
                self.tree.set(self.tree.get_children()[i], 1, f"{value:.4f}")
                
        except Exception as e:
            messagebox.showerror("错误", str(e))



            

# ========== 启动主程序 ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()


 
