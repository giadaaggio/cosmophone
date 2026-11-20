import streamlit as st
import io 
import numpy as np
import random
import pandas as pd
import altair as alt
from pathlib import Path
from scipy.io import wavfile
from cosmophone import (
    apply_fade,
    fill_missing,
    generate_tone,
    load_lightcurve,
    map_to_frequency,
    normalize,
    quantize_frequencies,
    smooth_data,
)    

# Cache astronomical downloads so repeated visits to the same target avoid
# downloading and parsing the same light curve again.
@st.cache_data
def cached_lightcurve(target, mission, quarter, sector):
    return load_lightcurve(
        target,
        mission=mission,
        quarter=quarter,
        sector=sector,
    )

st.set_page_config(
    page_title='Cosmophone',
    page_icon='*',
)

st.title('Cosmophone')
st.write('Turn astronomical data into sound.')

# Curated targets used by the random-target button.
RANDOM_TARGETS = [
    {
        "target": "Kepler-10",
        "mission": "Kepler",
        "quarter": 3,
        "sector": None,
    },
    {
        "target": "Pi Mensae",
        "mission": "TESS",
        "quarter": None,
        "sector": 1,
    },
]

if "target_name" not in st.session_state:
    st.session_state.target_name = "Kepler-22"
if "mission" not in st.session_state:
    st.session_state.mission = "Kepler"
if "quarter" not in st.session_state:
    st.session_state.quarter = 3
if "sector" not in st.session_state:
    st.session_state.sector = 1


def choose_random_target():
    selected = random.choice(RANDOM_TARGETS)
    st.session_state.target_name = selected["target"]
    st.session_state.mission = selected["mission"]
    st.session_state.quarter = selected["quarter"] or 3
    st.session_state.sector = selected["sector"] or 1


# Update Streamlit session state before the corresponding controls are built.
st.button(
    "Choose a random astronomical target",
    on_click=choose_random_target,
)

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
        key="target_name",
    )

    mission = st.selectbox(
        "Mission",
        ["Kepler", "TESS"],
        key="mission",
    )

    if mission == "Kepler":
        quarter = st.number_input(
            "Kepler quarter",
            min_value=1,
            key="quarter",
            step=1,
        )
    else:
        sector = st.number_input(
            "TESS sector",
            min_value=1,
            key="sector",
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

output_filename = st.text_input(
    "Output filename",
    "cosmophone.wav",
)

# Load and validate data from the selected source before any processing.
if st.button('Generate sound'):
    if input_mode == "Astronomical target":
        if not target:
            st.warning("Enter an astronomical target first.")
            st.stop()

        try:
            with st.spinner("Downloading light curve..."):
                values = cached_lightcurve(
                    target,
                    mission,
                    quarter,
                    sector,
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

    # Summarize the loaded source and the mission-specific parameters.
    st.write(f'Loaded samples: {len(values)}')
    if input_mode == "Astronomical target":
        st.write(f"Target: {target}")
        st.write(f"Mission: {mission}")

        if mission == "Kepler":
            st.write(f"Quarter: {quarter}")
        else:
            st.write(f"Sector: {sector}")

    # Clean and scale the signal before mapping it to audible frequencies.
    values = fill_missing(values)
    values = normalize(values)
    values = smooth_data(values, smooth_window)

    frequencies = map_to_frequency(
        values,
        f_min=f_min,
        f_max=f_max,
    )

    if quantize:
        frequencies = quantize_frequencies(frequencies)

    time_axis = np.linspace(
        0,
        duration,
        len(values),
    )

    processed_data_frame = pd.DataFrame(
        {
            "Time (seconds)": time_axis,
            "Value": values,
        }
    ).set_index("Time (seconds)")

    frequency_data_frame = pd.DataFrame(
        {
            "Time (seconds)": time_axis,
            "Frequency (Hz)": frequencies,
        }
    ).set_index("Time (seconds)")

    # Altair charts keep the time axis and measurement units explicit.
    processed_chart = alt.Chart(
        processed_data_frame.reset_index()
    ).mark_line().encode(
        x=alt.X(
            "Time (seconds):Q",
            title="Time (seconds)",
        ),
        y=alt.Y(
            "Value:Q",
            title="Normalized value",
        ),
        tooltip=["Time (seconds)", "Value"],
    ).properties(height=300)

    frequency_chart = alt.Chart(
        frequency_data_frame.reset_index()
    )

    if quantize:
        frequency_chart = frequency_chart.mark_point(size=20)
    else:
        frequency_chart = frequency_chart.mark_line()

    frequency_chart = frequency_chart.encode(
        x=alt.X(
            "Time (seconds):Q",
            title="Time (seconds)",
        ),
        y=alt.Y(
            "Frequency (Hz):Q",
            title="Frequency (Hz)",
        ),
        tooltip=["Time (seconds)", "Frequency (Hz)"],
    ).properties(height=300)

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Processed data")
        st.altair_chart(
            processed_chart,
            use_container_width=True,
        )

    with right_column:
        st.subheader("Mapped frequencies")
        st.altair_chart(
            frequency_chart,
            use_container_width=True,
        )

    # A continuous frequency curve or discrete quantized notes can be used.
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

    audio_bytes = audio_buffer.getvalue()

    st.audio(
        audio_bytes,
        format='audio/wav',
    )

    st.download_button(
        "Download WAV",
        data=audio_bytes,
        file_name=output_filename,
        mime="audio/wav",
    )

# Display locally generated examples independently of the interactive session.
st.divider()
st.header("Example sonifications")
st.write("Listen to generated examples and compare them with their plots.")

output_dir = Path(__file__).parent / "output"
examples = [
    ("Kepler-10", "kepler10.wav", "kepler10.png"),
    ("RR Lyrae", "rr_lyrae.wav", "rr_lyrae.png"),
    ("V1154 Cygni", "v1154_cyg.wav", "v1154_cyg.png"),
    ("KIC 9832227", "kic9832227.wav", "kic9832227.png"),
    ("Boyajian's Star", "boyajian.wav", "boyajian.png"),
]

for title, audio_name, plot_name in examples:
    audio_path = output_dir / audio_name
    plot_path = output_dir / plot_name

    if not audio_path.exists() or not plot_path.exists():
        continue

    with st.expander(title):
        st.image(str(plot_path), caption=f"{title} light curve")
        st.audio(str(audio_path), format="audio/wav")