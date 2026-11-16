import numpy as np
import argparse
from scipy.io import wavfile
import warnings
warnings.filterwarnings(
    "ignore",
    message="Warning: the tpfmodel submodule is not available.*",
    category=UserWarning,
    module="lightkurve.prf",
)
import lightkurve as lk
import matplotlib.pyplot as plt
from pathlib import Path

# load data from a light curve file
def load_lightcurve(target, mission='Kepler', quarter=None, sector=None, download_all=False):
    search_parameters = {'mission': mission}

    if mission == 'Kepler' and quarter is not None:
        search_parameters['quarter'] = quarter
    elif mission == 'TESS' and sector is not None:
        search_parameters['sector'] = sector

    search_result = lk.search_lightcurve(target, **search_parameters)

    # check if any light curve files were found
    if len(search_result) == 0:
        raise ValueError(f"No light curve files found for target '{target}' with the specified parameters.")

    if download_all:
        lightcurve = search_result.download_all().stitch().flatten()
    else: 
        lightcurve = search_result[0].download().flatten()

    flux = lightcurve.flux.value
    return flux


# load data from a CSV file
def load_data(filename):
    return np.loadtxt(filename, delimiter=',', dtype=float) 


# normalize function to scale data to [0, 1] range
def normalize(data, lower_percentile=1, upper_percentile=99):
    data = np.asarray(data, dtype=float)  # ensure data is a NumPy array of floats
    # check if all values are nan
    if np.all(np.isnan(data)):
        raise ValueError("All values are NaN. Cannot normalize.")
    # if there are NaN values, we can ignore them in min/max calculations
    min_val = np.nanpercentile(data, lower_percentile)
    max_val = np.nanpercentile(data, upper_percentile)
    data = np.clip(data, min_val, max_val)  
    # check if min and max are the same (all values are the same)
    if min_val == max_val:
        result = np.zeros_like(data)  # return an array of zero
    else: 
        result = (data - min_val) / (max_val - min_val)  # normalize the data
    # keep NaN values in their original positions
    result[np.isnan(data)] = np.nan
    return result

# smooth data using a moving average filter
def smooth_data(data, window_size):
    if window_size <= 1:
        return data
    kernel = np.ones(window_size) / window_size
    padding = window_size // 2
    padded_data = np.pad(
        data,
        padding,
        mode="edge",
    )
    return np.convolve(
        padded_data,
        kernel,
        mode="valid",
    )

# fill missing values in the data using linear interpolation
def fill_missing(data):
    data = np.asarray(data, dtype=float)  
    indices = np.arange(len(data))
    valid = ~np.isnan(data)

    return np.interp(indices, indices[valid], data[valid])  # linear interpolation for NaN values


# generate sinusoidal wave function
def generate_tone(
    frequencies,
    duration,
    sample_rate=44100,
    quantized=False,
):
    number_of_samples = int(sample_rate * duration)
    source_positions = np.linspace(
        0,
        len(frequencies) - 1,
        number_of_samples,
    )
    if quantized:
        nearest_indices = np.rint(source_positions).astype(int)
        frequency_over_time = frequencies[nearest_indices]
    else:
        frequency_over_time = np.interp(
            source_positions,
            np.arange(len(frequencies)),
            frequencies,
        )
    phase = 2 * np.pi * np.cumsum(frequency_over_time) / sample_rate
    wave = 0.5 * np.sin(phase)
    return wave


# audio fade
def apply_fade(audio, sample_rate = 44100, fade_duration=0.02):
    fade_samples = int(sample_rate * fade_duration)
    if fade_samples * 2 > len(audio):
        raise ValueError("Fade duration is too long for the audio length.")
    envelope = np.ones(len(audio))
    envelope[:fade_samples] = np.linspace(
        0,
        1,
        fade_samples,
    )
    envelope[-fade_samples:] = np.linspace(
        1,
        0,
        fade_samples,
    )
    return audio * envelope

# save wave to wav file function
def save_wav(audio, sample_rate, filename):
    # Ensure audio is in the range [-1, 1]
    audio = np.clip(audio, -1, 1)
    # Convert to 16-bit PCM format
    audio_int16 = np.int16(audio * 32767)
    wavfile.write(filename, sample_rate, audio_int16)
    return filename

# save plot of the audio waveform function
def save_plot(data, frequencies, filename):
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(data)
    plt.title("Input Data")
    plt.xlabel("Sample Index")
    plt.ylabel("Value")

    plt.subplot(2, 1, 2)
    plt.plot(frequencies)
    plt.title("Mapped Frequencies")
    plt.xlabel("Sample Index")
    plt.ylabel("Frequency (Hz)")

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename


# map normalized value to frequency range function
def map_to_frequency(value, f_min=220, f_max=880):
    # Map normalized value [0, 1] to frequency range [f_min, f_max] - exponential mapping for better perceptual scaling
    return f_min *(f_max / f_min) ** value


# pentatonic scale mapping function
def quantize_frequencies(frequencies, scale = (0,2,4,7,9), base = 220.0, octaves = 3): 
    semitones = 12 * np.log2(frequencies / base)
    notes = np.array ([octave * 12 + step for octave in range(octaves +1) for step in scale])
    nearest = np.abs(semitones[:, None] - notes[None, :]).argmin(axis=1)
    return base * 2 ** (notes[nearest] / 12)


# MAIN
if __name__ == "__main__":

    # create output directory if it doesn't exist
    OUTPUT_DIR = Path(__file__).parent / "output"
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("--target",           # parameter name
                        type = str,              # type of the values
                        required=False,          # required parameter
                        help = "Target name for light curve data (e.g., Kepler ID)",  # help text
                        )
    parser.add_argument("--mission",           # parameter name
                        type = str,              # type of the values
                        default = 'Kepler',      # default value
                        required=False,          # optional parameter
                        help = "Mission name for light curve data (default: Kepler)",  # help text
                        )
    parser.add_argument("--quarter",           # parameter name
                        type = int,              # type of the values
                        required=False,          # required parameter
                        help = "Quarter number for light curve data (optional)",  # help text
                        )
    parser.add_argument("--sector",           # parameter name
                        type = int,              # type of the values
                        required=False,          # required parameter
                        help = "Sector number for light curve data (optional)",  # help text
                        )
    parser.add_argument("--all-files",           # parameter name
                        action = 'store_true',   # flag to download all files
                        help = "Download all available light curve files for the target (optional)",  # help text
                        )
    parser.add_argument("--smooth",           # parameter name
                        type = int,              # type of the values
                        default = 1,          # required parameter
                        help = "Window size for smoothing the data (optional)",  # help text
                        )
    parser.add_argument("--data-file",           # parameter name
                        type = str,              # type of the values
                        required=False,          # required parameter
                        help = "Path to the input CSV file containing data values",  # help text
                        )
    parser.add_argument("--data",           # parameter name
                        nargs = '+',        # accepts one or more values
                        type = float,       # type of the values
                        required=False,       # required parameter
                        help = "Input data values (space-separated floats)",  # help text
                        )
    parser.add_argument("--f-min",           # parameter name
                        type = float,        # type of the values
                        default = 220.0,     # default value
                        help = "Minimum frequency for mapping (default: 220 Hz)",  # help text
                        )
    parser.add_argument("--f-max",           # parameter name
                        type = float,        # type of the values
                        default = 880.0,     # default value
                        help = "Maximum frequency for mapping (default: 880 Hz)",  # help text
                        )
    parser.add_argument("--duration",           # parameter name
                        type = float,           # type of the values
                        default = 2.0,          # default value
                        required=False,          # optional parameter
                        help = "Duration of the generated tone in seconds (default: 2.0)",  # help text
                        )
    parser.add_argument("--quantize",           # parameter name
                        action = 'store_true',  # flag to enable quantization
                        help = "Enable quantization to pentatonic scale",  # help text
                        )
    parser.add_argument("--output",               # parameter name
                        type = str,               # type of the values
                        default = "output.wav",   # default value
                        required=False,           # optional parameter
                        )
    parser.add_argument("--plot",               # parameter name
                        type = str,               # type of the values
                        default = None,           # default value
                        required=False,           # optional parameter
                        help = "Path to save the plot of input data and mapped frequencies (optional)",  # help text
                        )
    args = parser.parse_args()

    # check if data is provided either via --data-file or --data
    if args.target:
        data = load_lightcurve(
            args.target, 
            mission=args.mission, 
            quarter=args.quarter, 
            sector=args.sector, 
            download_all=args.all_files)
    elif args.data_file:
        data = load_data(args.data_file)
    elif args.data is not None:
        data = np.array(args.data)
    else:
        parser.error("You must provide data either via --target, --data-file or --data.")

    # check if the input data are valid numbers
    if args.duration <= 0:
        parser.error("Duration must be a positive number.")
    if args.f_min <= 0:
        parser.error("f-min must be a positive number.")
    if args.f_min >= args.f_max:
        parser.error("f-min must be less than f-max.")
    if args.smooth <= 0:
        parser.error("Smooth window size must be a positive integer.")
    if args.smooth % 2 == 0:
        parser.error("Smooth window size must be an odd integer.")
    if args.mission not in ['Kepler', 'TESS']:
        parser.error("Mission must be either 'Kepler' or 'TESS'.")
    if args.mission == 'TESS' and args.quarter is not None:
        parser.error("Quarter is only applicable for Kepler mission. Please provide a valid quarter number.")
    if args.mission == 'Kepler' and args.sector is not None:
        parser.error("Sector is only applicable for TESS mission. Please provide a valid sector number.")

    print(f"Data loaded. Number of samples: {len(data)}")
    if args.target:
        print(f'Source: {args.target}')
        print(f'Mission: {args.mission}')
    if args.mission == 'Kepler' and args.quarter is not None:
        print(f'Quarter: {args.quarter}')
    if args.mission == 'TESS' and args.sector is not None:
        print(f'Sector: {args.sector}')

    data = fill_missing(data) 
    normalized_data = normalize(data) 
    normalized_data = smooth_data(normalized_data, args.smooth) 

    frequencies = map_to_frequency(normalized_data,
                                    f_min=args.f_min,
                                    f_max=args.f_max)

    # quantize frequencies to pentatonic scale if the flag is set
    if args.quantize:
        frequencies = quantize_frequencies(frequencies)  

    # save plot if the plot path is provided
    if args.plot:
        plot_path = OUTPUT_DIR / args.plot
        save_plot(normalized_data, frequencies, plot_path)
        print(f"Plot saved to {plot_path}")

    sample_rate = 44100  # standard sample rate for audio
    tone = generate_tone(frequencies, args.duration, sample_rate, quantized=args.quantize)  
    tone = apply_fade(tone, sample_rate)  # apply fade to the generated tone

    output_path = OUTPUT_DIR / args.output
    save_wav(tone, sample_rate, output_path)

    print(f"Tone generated and saved to {output_path}")
    print(tone.shape)