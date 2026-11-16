import unittest
import numpy as np
from cosmophone import (
    apply_fade,
    fill_missing,
    generate_tone,
    map_to_frequency,
    normalize,
    quantize_frequencies,
    smooth_data,
)


class TestCosmophone(unittest.TestCase):
    def test_normalize(self):
        result = normalize([10, 15, 20])

        np.testing.assert_allclose(
            result,
            [0.0, 0.5, 1.0],
        )

    def test_normalize_nan(self):
        result = normalize([10, np.nan, 20])

        self.assertEqual(result[0], 0.0)
        self.assertTrue(np.isnan(result[1]))
        self.assertEqual(result[2], 1.0)

    def test_map_to_frequency_endpoints(self):
        frequencies = map_to_frequency(
            np.array([0.0, 1.0])
        )

        np.testing.assert_allclose(
            frequencies,
            [220.0, 880.0],
        )

    def test_generate_tone_length(self):
        tone = generate_tone(
            np.array([220.0, 440.0]),
            duration=2,
            sample_rate=44100,
        )

        self.assertEqual(len(tone), 88200)
        self.assertLessEqual(np.max(np.abs(tone)), 1.0)

    def test_fill_missing(self):
        result = fill_missing(
            np.array([10.0, np.nan, 20.0])
        )

        np.testing.assert_allclose(
            result,
            [10.0, 15.0, 20.0],
        )

    def test_smooth_preserves_length(self):
        data = np.ones(10)

        result = smooth_data(data, 3)

        self.assertEqual(len(result), len(data))
        np.testing.assert_allclose(result, data)

    def test_quantize_frequencies(self):
        frequencies = np.array([220.0, 440.0, 880.0])

        result = quantize_frequencies(frequencies)

        np.testing.assert_allclose(
            result,
            [220.0, 440.0, 880.0],
        )

    def test_apply_fade(self):
        audio = np.ones(1000)

        result = apply_fade(
            audio,
            sample_rate=1000,
            fade_duration=0.1,
        )

        self.assertAlmostEqual(result[0], 0.0)
        self.assertAlmostEqual(result[-1], 0.0)
        self.assertAlmostEqual(result[500], 1.0)


if __name__ == "__main__":
    unittest.main()