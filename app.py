import streamlit as st
import io 
import numpy as np
from scipy.io import wavfile
from cosmophone import (
    apply_fade,
    generate_tone,
    load_lightcurve,
    map_to_frequency,
    normalize,
    quantize_frequencies,
    smooth_data,
)    

st.set_page_config(
    page_title='Cosmophone',
    page_icon='*',
)

st.title('Cosmophone')
st.write('Turn astronomical data into sound.')

input_mode = st.radio(
    "Input source",
    [
        "Manual values",
        "CSV file",
        "Astronomical target",
    ],
)

uploaded_file = None
data_text = None
target = None
mission = "Kepler"
quarter = None
sector = None

if input_mode == "Manual values":
    data_text = st.text_input(
        "Input data",
        "10, 12, 15, 20",
    )
elif input_mode == "CSV file":
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
    )
else:
    target = st.text_input(
        "Target name or catalog ID",
        "Kepler-22",
    )

    mission = st.selectbox(
        "Mission",
        ["Kepler", "TESS"],
    )

    if mission == "Kepler":
        quarter = st.number_input(
            "Kepler quarter",
            min_value=1,
            value=3,
            step=1,
        )
    else:
        sector = st.number_input(
            "TESS sector",
            min_value=1,
            value=1,
            step=1,
        )

f_min = st.number_input(
    "Minimum frequency (Hz)",
    min_value=20.0,
    max_value=2000.0,
    value=220.0,
)

f_max = st.number_input(
    "Maximum frequency (Hz)",
    min_value=20.0,
    max_value=4000.0,
    value=880.0,
)

smooth_window = st.slider(
    "Smoothing window",
    min_value=1,
    max_value=501,
    value=1,
    step=2,
)

duration = st.slider('Duration of the sound (seconds):', min_value=1, max_value=30, value=5)

quantize = st.checkbox('Use pentatonic scale')

if st.button('Generate sound'):
    if input_mode == "Astronomical target":
        if not target:
            st.warning("Enter an astronomical target first.")
            st.stop()

        try:
            values = load_lightcurve(
                target,
                mission=mission,
                quarter=quarter,
                sector=sector,
            )
        except ValueError as error:
            st.error(str(error))
            st.stop()
    elif input_mode == "CSV file":
        if uploaded_file is None:
            st.warning("Upload a CSV file first.")
            st.stop()

        try:
            values = np.loadtxt(
                uploaded_file,
                delimiter=",",
                dtype=float,
            )
        except ValueError:
            st.error("The CSV contains invalid numeric values.")
            st.stop()
    else:
        try:
            values = np.array(
                [
                    float(value.strip())
                    for value in data_text.split(",")
                ]
            )
        except ValueError:
            st.error("Enter only comma-separated numeric values.")
            st.stop()

    if f_max <= f_min:
        st.error("Maximum frequency must be greater than minimum frequency.")
        st.stop()

    values = normalize(values)
    values = smooth_data(values, smooth_window)

    frequencies = map_to_frequency(
        values,
        f_min=f_min,
        f_max=f_max,
    )

    st.subheader("Processed data")
    st.line_chart(values)

    st.subheader("Mapped frequencies")
    st.line_chart(frequencies)

    if quantize:
        frequencies = quantize_frequencies(frequencies)

    tone = generate_tone(
        frequencies,
        duration,
        quantized=quantize,
    )
    tone = apply_fade(tone)

    audio_buffer = io.BytesIO()
    wavfile.write(
        audio_buffer,
        44100,
        (tone * 32767).astype(np.int16),
    )

    st.audio(
        audio_buffer.getvalue(),
        format='audio/wav',
    )