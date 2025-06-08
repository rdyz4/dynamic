import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sounddevice as sd

MU_0 = 4 * np.pi * 1e-7

SPEAKER_RESISTANCE = 8.0
COIL_TURNS_PER_METER = 2000
COIL_LENGTH = 0.05
PERMANENT_MAGNET_FIELD = 1.0

SAMPLING_RATE = 44100
DURATION = 1.0
TIME_VECTOR = np.linspace(0, DURATION, int(SAMPLING_RATE * DURATION), endpoint=False)

# --- UI приложения ---
st.set_page_config(layout="wide", page_title="Модель Динамика")

st.title("Интерактивная модель динамика")
st.write("""
Это приложение моделирует работу электродинамического громкоговорителя.
Вы можете изменять параметры входного сигнала (напряжение) и наблюдать, как это влияет на
ток в катушке, силу, действующую на диффузор, и его смещение.
""")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Устройство и принцип работы")
    st.write("""
    1.  **Входной сигнал**: Переменный электрический ток (моделируемый как напряжение) от усилителя подается на звуковую катушку.
    2.  **Звуковая катушка**: Катушка, жестко соединенная с диффузором, находится в радиальном магнитном поле, создаваемом постоянным магнитом.
    3.  **Взаимодействие полей**: Протекающий по катушке ток создает собственное переменное магнитное поле. Взаимодействие этого поля с полем постоянного магнита порождает **силу Ампера**.
    4.  **Движение диффузора**: Сила Ампера заставляет катушку и связанный с ней диффузор колебаться вперед и назад в соответствии с формой входного сигнала.
    5.  **Создание звука**: Колебания диффузора создают в окружающем воздухе волны сжатия и разрежения, которые мы воспринимаем как звук.
    """)
    st.info(
        "В данной модели мы упрощаем многие аспекты, например, считаем смещение диффузора прямо пропорциональным силе Ампера.")

with col2:
    st.header("Настройки входного сигнала")
    voltage_amplitude = st.slider("Амплитуда напряжения (U, Вольт)", 0.1, 20.0, 5.0, 0.1)
    signal_frequency = st.slider("Частота сигнала (f, Герц)", 20, 2000, 440, 10)

    if st.button("Воспроизвести звук", use_container_width=True):
        # Генерация звуковой волны
        audio_wave = voltage_amplitude * np.sin(2 * np.pi * signal_frequency * TIME_VECTOR)
        # Нормализуем относительно максимальной возможной амплитуды (20В),
        # чтобы сохранить разницу в громкости. Делим на 2, чтобы не было слишком громко.
        audio_wave_normalized = (audio_wave / 20.0) * 0.5

        try:
            sd.play(audio_wave_normalized, SAMPLING_RATE)
            sd.wait()
            st.success("Воспроизведение завершено.")
        except Exception as e:
            st.error(f"Не удалось воспроизвести звук: {e}")

voltage_t = voltage_amplitude * np.sin(2 * np.pi * signal_frequency * TIME_VECTOR)
current_t = voltage_t / SPEAKER_RESISTANCE

coil_magnetic_field_t = MU_0 * COIL_TURNS_PER_METER * current_t
force_t = PERMANENT_MAGNET_FIELD * current_t * COIL_LENGTH
displacement_t = force_t * 100  # Умножаем, чтобы получить смещение в мм

st.header("Визуализация процессов")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=TIME_VECTOR, y=voltage_t, mode='lines', name='Напряжение (В)'
))

fig.add_trace(go.Scatter(
    x=TIME_VECTOR, y=current_t, mode='lines', name='Ток (А)', yaxis='y2'
))

fig.add_trace(go.Scatter(
    x=TIME_VECTOR, y=displacement_t, mode='lines', name='Смещение (мм)', yaxis='y3'
))

fig.add_trace(go.Scatter(
    x=TIME_VECTOR, y=coil_magnetic_field_t, mode='lines', name='Магнитное поле (Тл)', yaxis='y4'
))

MAX_VOLTAGE = 20.0
MAX_CURRENT = MAX_VOLTAGE / SPEAKER_RESISTANCE
MAX_FORCE = PERMANENT_MAGNET_FIELD * (MAX_CURRENT) * COIL_LENGTH
DISPLACEMENT_FACTOR = 100
MAX_DISPLACEMENT = MAX_FORCE * DISPLACEMENT_FACTOR

fig.update_layout(
    xaxis=dict(title='Время (с)'),
    yaxis=dict(
        title=dict(text='Напряжение (В)', font=dict(color="#1f77b4")),
        tickfont=dict(color="#1f77b4"),
        range=[-MAX_VOLTAGE * 1.1, MAX_VOLTAGE * 1.1]
    ),
    yaxis2=dict(
        title=dict(text='Ток (А)', font=dict(color="#ff7f0e")),
        tickfont=dict(color="#ff7f0e"),
        overlaying='y',
        side='right',
        range=[-MAX_CURRENT * 1.1, MAX_CURRENT * 1.1]
    ),
    yaxis3=dict(
        title=dict(text='Смещение (мм)', font=dict(color="#2ca02c")),
        tickfont=dict(color="#2ca02c"),
        overlaying='y',
        side='right',
        range=[-MAX_DISPLACEMENT * 1.1, MAX_DISPLACEMENT * 1.1]
    ),
    yaxis4=dict(
        title=dict(text='Магнитное поле (Тл)', font=dict(color="#d62728")),
        tickfont=dict(color="#d62728"),
        overlaying='y',
        side='right',
        range=[-0.1, 0.1]
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=50, r=100, t=50, b=50),
    height=500,
    title="Зависимость параметров от времени"
)

fig.update_xaxes(range=[0, 0.05])

st.plotly_chart(fig, use_container_width=True)

st.header("Ключевые расчетные показатели")
col1, col2, col3, col4 = st.columns(4)
peak_current = voltage_amplitude / SPEAKER_RESISTANCE
peak_force = PERMANENT_MAGNET_FIELD * peak_current * COIL_LENGTH

with col1:
    st.metric("Пиковый ток в катушке", f"{peak_current:.2f} А")

with col2:
    st.metric("Пиковая сила Ампера", f"{peak_force * 1000:.2f} мН")

with col3:
    st.metric("Пиковое смещение диффузора", f"{abs(peak_force * DISPLACEMENT_FACTOR):.2f} мм")

with col4:
    peak_magnetic_field = MU_0 * COIL_TURNS_PER_METER * peak_current
    st.metric("Пиковое магнитное поле катушки", f"{peak_magnetic_field:.6f} Тл")

with st.expander("Показать используемые формулы"):
    st.write("В модели используются следующие упрощенные соотношения:")
    st.latex(r'''
    \text{1. Напряжение (входной сигнал):} \quad U(t) = U_{amp} \cdot \sin(2 \pi f t)
    ''')
    st.write(r"где $U_{amp}$ - амплитуда напряжения (В), $f$ - частота (Гц), $t$ - время (с).")

    st.latex(r'''
    \text{2. Ток в катушке (Закон Ома):} \quad I(t) = \frac{U(t)}{R}
    ''')
    st.write(r"где $R$ - сопротивление катушки (Ом).")

    st.latex(r'''
    \text{3. Сила Ампера:} \quad F(t) = B \cdot I(t) \cdot L
    ''')
    st.write(r"где $B$ - индукция поля постоянного магнита (Тл), $L$ - длина провода в поле (м).")

    st.latex(r'''
    \text{4. Смещение диффузора:} \quad d(t) \propto F(t)
    ''')
    st.write(r"В данной модели смещение считается прямо пропорциональным силе для наглядности.")

st.markdown("---")
st.write("© Замальдинов Роман M3208.")
