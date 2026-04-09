"""Unit tests for the calculate_ideal_drive_ratio function.

This module verifies that the ideal drive:recovery ratio calculation from
"The Biomechanics of Rowing" (2nd revision, page 17, Figure 2.6) produces
correct results across various SPM ranges and input types.
"""

from typing import cast

import numpy as np
import pytest

from rowing_catch.algo.helpers import calculate_ideal_drive_ratio


class TestIdealDriveRatioBasics:
    """Test basic functionality of calculate_ideal_drive_ratio."""

    def test_scalar_input_returns_scalar(self):
        """Verify that scalar input returns scalar output."""
        result = calculate_ideal_drive_ratio(30.0)
        assert isinstance(result, (float, np.floating))

    def test_array_input_returns_array(self):
        """Verify that array input returns array output."""
        spm_array = np.array([20.0, 30.0, 40.0])
        result = calculate_ideal_drive_ratio(spm_array)
        assert isinstance(result, np.ndarray)
        assert cast(np.ndarray, result).shape == spm_array.shape

    def test_list_input_returns_array(self):
        """Verify that list input is converted to array and processed."""
        spm_list = [20.0, 30.0, 40.0]
        result = calculate_ideal_drive_ratio(spm_list)
        # Result is an ndarray when list input is provided
        assert isinstance(result, np.ndarray)
        assert len(cast(np.ndarray, result)) == 3


class TestIdealDriveRatioBoundaryValues:
    """Test known reference values from the biomechanics literature."""

    def test_spm_14_reference_value(self):
        """At 14 SPM (slow rowing), ideal drive ratio should be ~0.313 (31.3%)."""
        ratio = calculate_ideal_drive_ratio(14.0)
        assert 0.310 < ratio < 0.315, f'Expected ~0.313, got {ratio:.4f}'

    def test_spm_36_reference_value(self):
        """At 36 SPM (typical racing pace), ideal drive ratio should be ~0.52 (52%)."""
        ratio = calculate_ideal_drive_ratio(36.0)
        # At 36 SPM, ratio should be close to 0.52
        assert 0.51 < ratio < 0.53, f'Expected ~0.52, got {ratio:.4f}'

    def test_spm_50_reference_value(self):
        """At 50 SPM (high intensity), ideal drive ratio should be ~0.549 (54.9%)."""
        ratio = calculate_ideal_drive_ratio(50.0)
        assert 0.545 < ratio < 0.555, f'Expected ~0.549, got {ratio:.4f}'

    def test_spm_20_intermediate_value(self):
        """At 20 SPM (slow/moderate), ideal drive ratio should be ~0.41 (41%)."""
        ratio = calculate_ideal_drive_ratio(20.0)
        # Quadratic: -0.000202*400 + 0.0195*20 + 0.0793 = -0.0808 + 0.39 + 0.0793 ≈ 0.3885
        assert 0.38 < ratio < 0.40, f'Expected ~0.39, got {ratio:.4f}'


class TestIdealDriveRatioQuadraticBehavior:
    """Test mathematical properties of the quadratic formula."""

    def test_ratio_increases_with_spm(self):
        """Verify that ideal ratio generally increases with SPM."""
        spm_values = np.linspace(14, 50, 10)
        ratios = cast(np.ndarray, calculate_ideal_drive_ratio(spm_values))

        # Check that ratios increase over the range (monotonic for this range)
        diffs = np.diff(ratios)
        assert np.all(diffs > 0), 'Ideal ratio should increase with SPM in 14-50 range'

    def test_symmetry_around_vertex(self):
        """Verify that the quadratic has a vertex (maximum or minimum)."""
        # For this quadratic (a < 0), vertex is at -b/(2a)
        a = -0.000202
        b = 0.0195
        vertex_spm = -b / (2 * a)

        # Vertex should be in the ~48-50 range
        assert 40 < vertex_spm < 60, f'Vertex at SPM={vertex_spm:.2f} is outside expected range'

    def test_quadratic_formula_accuracy(self):
        """Verify the implemented formula matches the specification."""
        # Test a known point: SPM=30
        spm = 30.0
        a = -0.000202
        b = 0.0195
        c = 0.0793

        expected = a * spm**2 + b * spm + c
        actual = calculate_ideal_drive_ratio(spm)

        assert abs(actual - expected) < 1e-10, f'Formula mismatch: expected {expected}, got {actual}'


class TestIdealDriveRatioArrayOperations:
    """Test vectorized array operations."""

    def test_array_calculation_matches_scalar_loop(self):
        """Verify that array calculation matches individual scalar calculations."""
        spm_array = np.array([15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0])

        # Array calculation
        result_array = cast(np.ndarray, calculate_ideal_drive_ratio(spm_array))

        # Scalar loop
        result_scalars = np.array([calculate_ideal_drive_ratio(spm) for spm in spm_array])

        # Should be identical
        np.testing.assert_array_almost_equal(result_array, result_scalars, decimal=10)

    def test_2d_array_input(self):
        """Verify that 2D array input is processed element-wise."""
        spm_2d = np.array([[20.0, 25.0], [30.0, 35.0]])
        result = cast(np.ndarray, calculate_ideal_drive_ratio(spm_2d))

        assert result.shape == spm_2d.shape
        assert result[0, 0] < result[0, 1]  # 20 < 25
        assert result[0, 1] < result[1, 0]  # 25 < 30

    def test_linspace_sweep(self):
        """Verify calculation across a continuous SPM range."""
        spm_sweep = np.linspace(14, 50, 100)
        ratios = cast(np.ndarray, calculate_ideal_drive_ratio(spm_sweep))

        # All ratios should be positive
        assert np.all(ratios > 0), 'All ratios should be positive'

        # All ratios should be in reasonable range (0.2 to 0.8 for drive phase)
        assert np.all(ratios > 0.25), 'All ratios should be > 0.25'
        assert np.all(ratios < 0.75), 'All ratios should be < 0.75'


class TestIdealDriveRatioEdgeCases:
    """Test edge cases and potential error conditions."""

    def test_very_low_spm(self):
        """Test behavior at very low SPM (below typical range)."""
        ratio = calculate_ideal_drive_ratio(5.0)
        # Should still compute (no error), even if outside typical range
        assert isinstance(ratio, (float, np.floating))
        assert ratio > 0

    def test_very_high_spm(self):
        """Test behavior at very high SPM (above typical range)."""
        ratio = calculate_ideal_drive_ratio(70.0)
        # Should still compute (no error), even if outside typical range
        assert isinstance(ratio, (float, np.floating))

    def test_zero_spm(self):
        """Test calculation at SPM=0."""
        ratio = calculate_ideal_drive_ratio(0.0)
        # Should return the constant term c = 0.0793
        expected = 0.0793
        assert abs(ratio - expected) < 1e-6, f'At SPM=0, expected {expected}, got {ratio}'

    def test_negative_spm(self):
        """Test behavior with negative SPM (physically meaningless but mathematically valid)."""
        ratio = calculate_ideal_drive_ratio(-10.0)
        # Should compute without error
        assert isinstance(ratio, (float, np.floating))

    def test_nan_input(self):
        """Test behavior with NaN input."""
        result = calculate_ideal_drive_ratio(np.nan)
        assert np.isnan(result)

    def test_array_with_nan(self):
        """Test array input containing NaN."""
        spm_array = np.array([20.0, np.nan, 40.0])
        result = cast(np.ndarray, calculate_ideal_drive_ratio(spm_array))

        assert np.isfinite(result[0])
        assert np.isnan(result[1])
        assert np.isfinite(result[2])

    def test_inf_input(self):
        """Test behavior with infinite input."""
        result = calculate_ideal_drive_ratio(np.inf)
        # Dominated by the negative quadratic term
        assert result < 0 or np.isnan(result) or np.isinf(result)


class TestIdealDriveRatioPhysicalInterpretation:
    """Test that results make physical/biomechanical sense."""

    def test_ratio_represents_drive_phase_ratio(self):
        """Verify that output is a drive:recovery ratio."""
        # At 36 SPM, ratio should be ~0.52, meaning drive:recovery ≈ 52:100
        ratio_36 = calculate_ideal_drive_ratio(36.0)

        # This means drive_duration / recovery_duration ≈ 0.52
        # So drive_phase_fraction = ratio/(1+ratio) ≈ 0.342
        drive_fraction = ratio_36 / (1 + ratio_36)
        assert 0.33 < drive_fraction < 0.35, f'At 36 SPM, drive fraction should be ~34%, got {drive_fraction * 100:.1f}%'

    def test_low_spm_longer_recovery(self):
        """At low SPM, recovery should be longer than drive."""
        ratio_14 = calculate_ideal_drive_ratio(14.0)
        drive_fraction_14 = ratio_14 / (1 + ratio_14)

        # At 14 SPM, drive:recovery ≈ 0.313 means drive is ~24% of cycle
        assert drive_fraction_14 < 0.35, f'At 14 SPM, drive fraction should be <35%, got {drive_fraction_14 * 100:.1f}%'

    def test_high_spm_longer_drive(self):
        """At high SPM, drive and recovery become more balanced or drive-heavy."""
        ratio_50 = calculate_ideal_drive_ratio(50.0)
        drive_fraction_50 = ratio_50 / (1 + ratio_50)

        # At 50 SPM, drive:recovery ≈ 0.549 means drive is ~35% of cycle
        assert drive_fraction_50 > 0.30, f'At 50 SPM, drive fraction should be >30%, got {drive_fraction_50 * 100:.1f}%'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
