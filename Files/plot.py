import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
FILE_KSP = 'KSP_Stats.csv'
FILE_MM = 'mission_data.csv'
OUTPUT_DIR = 'Graphs'
LIMIT_TIME = 400
LIMIT_HEIGHT = 210000
LIMIT_ERROR = 200
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data(path, is_ksp=False):
    print(f'Чтение {path}...')
    try:
        df = pd.read_csv(path, sep='[,;]\\\\s*', engine='python')
        if 'apoapsis' in df.columns:
            df = df[['time', 'altitude', 'speed', 'mass']]
            df['mass'] = df['mass'] / 1000.0
            df.columns = ['time', 'height', 'speed', 'mass']
        if is_ksp:
            if df['mass'].mean() > 1000000:
                df['mass'] = df['mass'] / 1000000.0
            else:
                df['mass'] = df['mass'] / 1000.0
            start_idx = df[df['speed'] > 1.0].index.min()
            if pd.notna(start_idx):
                print(
                    f'KSP: Старт обнаружен на строке {start_idx}. Сдвигаем время.'
                    )
                df = df.iloc[start_idx:].copy()
                df['time'] = df['time'] - df['time'].iloc[0]
            else:
                print('KSP: Старт не найден, используем как есть.')
        df = df[df['time'] <= LIMIT_TIME]
        df = df[df['height'] <= LIMIT_HEIGHT * 1.5]
        return df.reset_index(drop=True)
    except Exception as e:
        print(f'Ошибка {path}: {e}')
        return pd.DataFrame()

def save_plot(name, x_limit=None, y_limit=None):
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    if x_limit:
        plt.xlim(0, x_limit)
    if y_limit:
        plt.ylim(0, y_limit)
    plt.savefig(f'{OUTPUT_DIR}/{name}.png', dpi=100)
    plt.clf()
    print(f'Сохранен {name}.png')
ksp = load_data(FILE_KSP, True)
mm = load_data(FILE_MM, False)
if ksp.empty or mm.empty:
    print('Ошибка: один из файлов пуст или не найден.')
    exit()
(c_ksp, c_mm) = ('#008000', '#ff0000')
print('Построение графиков...')
plt.title('Изменение массы')
plt.xlabel('Время, с')
plt.ylabel('Масса, т')
plt.plot(ksp['time'], ksp['mass'], label='KSP', color=c_ksp)
plt.plot(mm['time'], mm['mass'], label='Модель', color=c_mm)
save_plot('TimeMassa', x_limit=LIMIT_TIME)
plt.title('Набор высоты')
plt.xlabel('Время, с')
plt.ylabel('Высота, м')
plt.plot(ksp['time'], ksp['height'], label='KSP', color=c_ksp)
plt.plot(mm['time'], mm['height'], label='Модель', color=c_mm)
save_plot('TimeHeight', x_limit=LIMIT_TIME, y_limit=LIMIT_HEIGHT)
plt.title('Набор скорости')
plt.xlabel('Время, с')
plt.ylabel('Скорость, м/с')
plt.plot(ksp['time'], ksp['speed'], label='KSP', color=c_ksp)
plt.plot(mm['time'], mm['speed'], label='Модель', color=c_mm)
save_plot('TimeSpeed', x_limit=LIMIT_TIME)
plt.title('Скорость от высоты')
plt.xlabel('Высота, м')
plt.ylabel('Скорость, м/с')
plt.plot(ksp['height'], ksp['speed'], label='KSP', color=c_ksp)
plt.plot(mm['height'], mm['speed'], label='Модель', color=c_mm)
save_plot('HeightSpeed', x_limit=LIMIT_HEIGHT)
plt.title('Относительная погрешность (%)')
plt.xlabel('Время, с')
t_common = np.arange(0, LIMIT_TIME, 0.1)

def interp(df, col):
    return np.interp(t_common, df['time'], df[col])
(k_m, m_m) = (interp(ksp, 'mass'), interp(mm, 'mass'))
(k_h, m_h) = (interp(ksp, 'height'), interp(mm, 'height'))
(k_v, m_v) = (interp(ksp, 'speed'), interp(mm, 'speed'))
err_m = np.abs(k_m - m_m) / (m_m + 0.1) * 100
err_h = np.abs(k_h - m_h) / (m_h + 100.0) * 100
err_v = np.abs(k_v - m_v) / (m_v + 1.0) * 100
start_cut = int(10 / 0.1)
t_plot = t_common[start_cut:]
err_m = err_m[start_cut:]
err_h = err_h[start_cut:]
err_v = err_v[start_cut:]
plt.plot(t_plot, err_m, label='Масса')
plt.plot(t_plot, err_h, label='Высота')
plt.plot(t_plot, err_v, label='Скорость')
save_plot('ErrorRate', x_limit=LIMIT_TIME, y_limit=LIMIT_ERROR)
print('Все графики сохранены в папку Graphs.')

