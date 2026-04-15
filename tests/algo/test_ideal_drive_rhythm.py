"""Unit tests for the calculate_ideal_drive_rhythm function.

This module verifies that the ideal drive phase percentage calculation from
"The Biomechanics of Rowing" (2nd revision, page 17, Figure 2.6) produces
correct results across various SPM ranges and input types.
"""

from typing import cast

import numpy as np
import pytest

from rowing_catch.algo.helpers import calculate_ideal_drive_rhythm


class TestIdealDriveRhythmBasics:
    """Test basic functionality of calculate_ideal_drive_rhythm."""

    def test_scalar_input_returns_scalar(self):
        """Verify that scalar input returns scalar output."""
        result = calculate_ideal_drive_rhythm(30.0)
        assert isinstance(result, (float, np.floating))

    def test_array_input_returns_array(self):
        """Verify that array input returns array output."""
        spm_array = np.array([20.0, 30.0, 40.0])
        result = calculate_ideal_drive_rhythm(spm_array)
        assert isinstance(result, np.ndarray)
        assert cast(np.ndarray, result).shape == spm_array.shape

    def test_list_input_returns_array(self):
        """Verify that list input is converted to array and processed."""
        spm_list = [20.0, 30.0, 40.0]
        result = calculate_ideal_drive_rhythm(spm_list)
        assert isinstance(result, np.ndarray)
        assert len(cast(np.ndarray, result)) == 3


class TestIdealDriveRhythmBoundaryValues:
    """Test known reference values from the biomechanics literature."""

    def test_spm_14_reference_value(self):
        """At 14 SPM (slow rowing), ideal drive rhythm should be ~31.3%."""
        pct = calculate_ideal_drive_rhythm(14.0)
        assert 31.0 < pct < 31.5, f'Expected ~31.3%, got {pct:.2f}%'

    def test_spm_36_reference_value(self):
        """At 36 SPM (typical racing pace), ideal drive rhythm should be ~52%."""
        pct = calculate_ideal_drive_rhythm(36.0)
        assert 51.0 < pct < 53.0, f'Expected ~52%, got {pct:.2f}%'

    def test_spm_50_reference_value(self):
        """At 50 SPM (high intensity), ideal drive rhythm should be ~54.9%."""
        pct = calculate_ideal_drive_rhythm(50.0)
        assert 54.5 < pct < 55.5, f'Expected ~54.9%, got {pct:.2f}%'

    def test_spm_20_intermediate_value(self):
        """At 20 SPM (slow/moderate), ideal drive rhythm should be ~38.85%."""
        pct = calculate_ideal_drive_rhythm(20.0)
        # Quadratic: (-0.000202*400 + 0.0195*20 + 0.0793) * 100 ≈ 38.85%
        assert 38.0 < pct < 40.0, f'Expected ~38.85%, got {pct:.2f}%'


class TestIdealDriveRhythmQuadraticBehavior:
    """Test mathematical properties of the quadratic formula."""

    def test_pct_increases_with_spm(self):
        """Verify that ideal drive% generally increases with SPM."""
        spm_values = np.linspace(14, 50, 10)
        pcts = cast(np.ndarray, calculate_ideal_drive_rhythm(spm_values))

        diffs = np.diff(pcts)
        assert np.all(diffs > 0), 'Ideal drive% should increase with SPM in 14–50 range'

    def test_symmetry_around_vertex(self):
        """Verify that the quadratic has a vertex (maximum) above the typical SPM range."""
        a = -0.000202
        b = 0.0195
        vertex_spm = -b / (2 * a)
        assert 40 < vertex_spm < 60, f'Vertex at SPM={vertex_spm:.2f} is outside expected range'

    def test_quadratic_formula_accuracy(self):
        """Verify the implemented formula matches the specification."""
        spm = 30.0
        a = -0.000202
        b = 0.0195
        c = 0.0793

        expected = (a * spm**2 + b * spm + c) * 100
        actual = calculate_ideal_drive_rhythm(spm)

        assert abs(actual - expected) < 1e-8, f'Formula mismatch: expected {expected}, got {actual}'


class TestIdealDriveRhythmArrayOperations:
    """Test vectorized array operations."""

    def test_array_calculation_matches_scalar_loop(self):
        """Verify that array calculation matches individual scalar calculations."""
        spm_array = np.array([15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0])

        result_array = cast(np.ndarray, calculate_ideal_drive_rhythm(spm_array))
        result_scalars = np.array([calculate_ideal_drive_rhythm(spm) for spm in spm_array])

        np.testing.assert_array_almost_equal(result_array, result_scalars, decimal=10)

    def test_2d_array_input(self):
        """Verify that 2D array input is processed element-wise."""
        spm_2d = np.array([[20.0, 25.0], [30.0, 35.0]])
        result = cast(np.ndarray, calculate_ideal_drive_rhythm(spm_2d))

        assert result.shape == spm_2d.shape
        assert result[0, 0] < result[0, 1]  # 20 SPM < 25 SPM
        assert result[0, 1] < result[1, 0]  # 25 SPM < 30 SPM

    def test_linspace_sweep(self):
        """Verify calculation across a continuous SPM range."""
        spm_sweep = np.linspace(14, 50, 100)
        pcts = cast(np.ndarray, calculate_ideal_drive_rhythm(spm_sweep))

        assert np.all(pcts > 0), 'All drive% values should be positive'
        assert np.all(pcts > 25), 'All drive% values should be > 25%'
        assert np.all(pcts < 75), 'All drive% values should be < 75%'


class TestIdealDriveRhythmEdgeCases:
    """Test edge cases and potential error conditions."""

    def test_very_low_spm(self):
        """Test behavior at very low SPM (below typical range)."""
        pct = calculate_ideal_drive_rhythm(5.0)
        assert isinstance(pct, (float, np.floating))
        assert pct > 0

    def test_very_high_spm(self):
        """Test behavior at very high SPM (above typical range)."""
        pct = calculate_ideal_drive_rhythm(70.0)
        assert isinstance(pct, (float, np.floating))

    def test_zero_spm(self):
        """Test calculation at SPM=0 — should return c * 100 = 7.93%."""
        pct = calculate_ideal_drive_rhythm(0.0)
        expected = 0.0793 * 100
        assert abs(pct - expected) < 1e-6, f'At SPM=0, expected {expected:.2f}%, got {pct:.4f}%'

    def test_negative_spm(self):
        """Test behavior with negative SPM (physically meaningless but mathematically valid)."""
        pct = calculate_ideal_drive_rhythm(-10.0)
        assert isinstance(pct, (float, np.floating))

    def test_nan_input(self):
        """Test behavior with NaN input."""
        result = calculate_ideal_drive_rhythm(np.nan)
        assert np.isnan(result)

    def test_array_with_nan(self):
        """Test array input containing NaN."""
        spm_array = np.array([20.0, np.nan, 40.0])
        result = cast(np.ndarray, calculate_ideal_drive_rhythm(spm_array))

        assert np.isfinite(result[0])
        assert np.isnan(result[1])
        assert np.isfinite(result[2])

    def test_inf_input(self):
        """Test behavior with infinite input."""
        with np.errstate(invalid='ignore'):
            result = calculate_ideal_drive_rhythm(np.inf)
        assert result < 0 or np.isnan(result) or np.isinf(result)


class TestIdealDriveRhythmPhysicalInterpretation:
    """Test that results make physical/biomechanical sense."""

    def test_output_is_drive_phase_percentage(self):
        """Verify output is drive phase as a percentage of the total stroke cycle.

        Reference values from Coker (2012), Figure 2.6:
          ~32% at 15 SPM, ~40% at 20 SPM, ~48% at 30 SPM, ~53% at 40 SPM.
        """
        assert 31.0 < calculate_ideal_drive_rhythm(15.0) < 34.0
        assert 38.0 < calculate_ideal_drive_rhythm(20.0) < 41.0
        assert 47.0 < calculate_ideal_drive_rhythm(30.0) < 50.0
        assert 52.0 < calculate_ideal_drive_rhythm(40.0) < 55.0

    def test_low_spm_shorter_drive_fraction(self):
        """At low SPM, the drive phase should be a smaller fraction of the cycle."""
        pct_14 = calculate_ideal_drive_rhythm(14.0)
        assert pct_14 < 35.0, f'At 14 SPM, drive% should be <35%, got {pct_14:.1f}%'

    def test_high_spm_larger_drive_fraction(self):
        """At high SPM, the drive phase becomes a larger fraction of the cycle."""
        pct_50 = calculate_ideal_drive_rhythm(50.0)
        assert pct_50 > 45.0, f'At 50 SPM, drive% should be >45%, got {pct_50:.1f}%'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
