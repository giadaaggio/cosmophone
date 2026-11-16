# Cosmophone

**Listen to the light of the stars.**

Cosmophone turns astronomical data into sound, transforming variations in
brightness into evolving melodies, continuous glissandi, or discrete musical
notes. The same pipeline can be used with synthetic data, CSV files, or real
light curves from the Kepler and TESS missions.

The `output/` directory currently contains generated WAV files and plots for
several example targets, including Kepler-10, RR Lyrae, V1154 Cygni,
KIC 9832227, and KIC 8462852. These outputs make it possible to compare the
source data with the resulting sound while exploring the project. As the
collection grows, this directory will be cleaned up and renamed to
`examples/` to keep the project structure more organized.

### Current examples

- [Kepler-10 audio](output/kepler10.wav) · [plot](output/kepler10.png)
- [RR Lyrae audio](output/rr_lyrae.wav) · [plot](output/rr_lyrae.png)
- [V1154 Cygni audio](output/v1154_cyg.wav) · [plot](output/v1154_cyg.png)
- [KIC 9832227 audio](output/kic9832227.wav) · [plot](output/kic9832227.png)
- [Boyajian's Star audio](output/boyajian.wav) · [plot](output/boyajian.png)

The pipeline:

1. loads manual data, CSV files, or Kepler/TESS light curves;
2. handles missing values and noise;
3. normalizes the data;
4. maps values to audio frequencies;
5. generates a WAV file and, optionally, a plot.

## Requirements

Python 3.13 is recommended because some scientific dependencies may not yet
provide pre-built packages for Python 3.15.

Install the dependencies in the virtual environment:

```powershell
python -m pip install -r requirements.txt
python --version
```

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
