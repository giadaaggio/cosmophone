# Cosmophone

**Listen to the light of the stars.**

Cosmophone turns astronomical data into sound, transforming variations in
brightness into evolving melodies, continuous glissandi, or discrete musical
notes. The same pipeline can be used with synthetic data, CSV files, or real
light curves from the Kepler and TESS missions.

## How the sonification works

The input samples are interpreted as a one-dimensional signal:

- sample position → position in playback time;
- data value → pitch;
- missing values → linear interpolation;
- smoothing → noise reduction;
- frequency range → selectable minimum and maximum pitch;
- optional quantization → pentatonic musical scale.

The signal is resampled to match the selected audio duration. Frequencies are
converted into a continuous oscillator phase, which avoids clicks during pitch
changes. A short fade-in and fade-out are applied before writing the WAV file.

## What to listen for

- **Kepler-10**: mostly stable brightness with subtle variations ([Kepler-10 audio](output/kepler10.wav) · [plot](output/kepler10.png));
- **RR Lyrae**: a repeating pulsation pattern ([RR Lyrae audio](output/rr_lyrae.wav) · [plot](output/rr_lyrae.png));
- **V1154 Cygni**: a slower, more regular stellar cycle ([V1154 Cygni audio](output/v1154_cyg.wav) · [plot](output/v1154_cyg.png));
- **KIC 9832227**: sharp changes associated with eclipses ([KIC 9832227 audio](output/kic9832227.wav) · [plot](output/kic9832227.png));
- **KIC 8462852**: irregular brightness variations and abrupt events ([Boyajian's Star audio](output/boyajian.wav) · [plot](output/boyajian.png)).

The audio is not a literal recording of the stars. It is a mapping from
measured brightness variations to audible frequencies.

## Requirements

Python 3.13 is recommended because some scientific dependencies may not yet
provide pre-built packages for Python 3.15.

Install the dependencies in the virtual environment:

```powershell
python -m pip install -r requirements.txt
python --version
```

## Testing

Run the unit tests with:

```powershell
python -m unittest -v
```

The tests cover normalization, missing values, frequency mapping, and audio
sample generation without downloading astronomical data.

## Basic usage

From the project directory:

```powershell
python .\cosmophone.py `
  --data 10 12 15 20 `
  --duration 8 `
  --plot test.png `
  --output test.wav
```

Files are saved automatically in the `output/` directory.

## Streamlit interface

Cosmophone also includes an interactive web interface for experimenting with
the sonification parameters and listening directly in the browser.

Start it from the project directory:

```powershell
streamlit run .\app.py
```

The interface provides three input modes:

- manual numeric values;
- CSV file upload;
- astronomical target lookup from Kepler or TESS.

After processing the data, the app displays the mapped curve, plays the
generated sound in the browser, and provides a WAV download button.

The WAV filename can be customized directly from the interface.

## Main parameters

- `--data`: numeric values separated by spaces;
- `--data-file`: CSV file containing the data;
- `--target`: astronomical object to search for;
- `--mission`: `Kepler` or `TESS`;
- `--quarter`: Kepler quarter;
- `--sector`: TESS sector;
- `--duration`: audio duration in seconds;
- `--f-min`, `--f-max`: frequency range;
- `--smooth`: moving-average window size;
- `--quantize`: use a pentatonic scale;
- `--all-files`: download and combine all matching files;
- `--plot`: output PNG filename;
- `--output`: output WAV filename.

## Astronomical data

### Kepler-10

```powershell
python .\cosmophone.py `
  --target "Kepler-10" `
  --mission Kepler `
  --quarter 3 `
  --smooth 501 `
  --duration 10 `
  --plot kepler10.png `
  --output kepler10.wav
```

### RR Lyrae

RR Lyrae is a pulsating star and produces a more noticeable variation:

```powershell
python .\cosmophone.py `
  --target "KIC 7198959" `
  --mission Kepler `
  --smooth 11 `
  --duration 20 `
  --plot rr_lyrae.png `
  --output rr_lyrae.wav
```

### V1154 Cygni

V1154 Cygni is a Cepheid variable:

```powershell
python .\cosmophone.py `
  --target "KIC 7548061" `
  --mission Kepler `
  --smooth 51 `
  --duration 20 `
  --plot v1154_cyg.png `
  --output v1154_cyg.wav
```

### KIC 9832227

KIC 9832227 is an eclipsing binary:

```powershell
python .\cosmophone.py `
  --target "KIC 9832227" `
  --mission Kepler `
  --smooth 21 `
  --duration 20 `
  --plot kic9832227.png `
  --output kic9832227.wav
```

### KIC 8462852

KIC 8462852, also known as Boyajian's Star, shows irregular variations:

```powershell
python .\cosmophone.py `
  --target "KIC 8462852" `
  --mission Kepler `
  --smooth 101 `
  --duration 20 `
  --plot boyajian.png `
  --output boyajian.wav
```

## Notes

- Without `--quantize`, frequency changes continuously.
- With `--quantize`, frequencies are constrained to a pentatonic scale.
- A higher `--smooth` value reduces noise but may remove short-lived details.
- `--all-files` can take longer because it downloads and combines every
  matching file.
