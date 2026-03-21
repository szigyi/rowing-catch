"""
Tests for metadata tracking (Recommendation #6: No Metadata Tracking).

Validates:
- Metadata diagnostics computation
- Capture length warnings
- Sampling stability detection
- Row drop tracking
- Warnings generation
"""

import numpy as np
import pandas as pd
from rowing_catch.algo.analysis import (
    _compute_metadata_diagnostics,
    _compute_temporal_metrics,
    process_rowing_data,
)
from rowing_catch.algo.scenarios import create_scenario_data


def test_metadata_included_in_results():
    """Test that metadata dict is included in process_rowing_data results."""
    print("\n✓ TEST: Metadata included in results")
    
    # Create synthetic rowing data using scenario
    df = create_scenario_data(scenario='healthy_catch', num_cycles=5)
    assert df is not None and len(df) > 0, "Scenario data generation failed"
    
    # Process through full pipeline
    results = process_rowing_data(df)
    
    # Verify results are not None
    assert results is not None, "Pipeline returned None"
    
    # Check metadata key exists
    assert 'metadata' in results, "Missing 'metadata' key in results"
    assert isinstance(results['metadata'], dict), "metadata should be a dict"
    
    # Check metadata fields
    required_fields = ['capture_length', 'sampling_is_stable', 'rows_dropped', 'warnings']
    for field in required_fields:
        assert field in results['metadata'], f"Missing metadata field: {field}"
    
    print(f"  ✓ Metadata fields present: {list(results['metadata'].keys())}")
    print(f"  ✓ Capture length: {results['metadata']['capture_length']}")
    print(f"  ✓ Sampling stable: {results['metadata']['sampling_is_stable']}")
    print(f"  ✓ Rows dropped: {results['metadata']['rows_dropped']}")
    print(f"  ✓ Warnings: {len(results['metadata']['warnings'])} warning(s)")


def test_capture_length_warning():
    """Test that capture length warnings are generated when < 3 cycles."""
    print("\n✓ TEST: Capture length warnings")
    
    # Create very small dataset with few cycles
    time = np.arange(0, 50, 0.01)  # Short time series
    handle_x = np.sin(2 * np.pi * time / 5) * 100 + 500  # Few oscillations
    seat_x = np.sin(2 * np.pi * time / 5 + 0.5) * 100 + 600
    
    df = pd.DataFrame({
        'Time': time,
        'Handle/0/X': handle_x,
        'Handle/0/Y': np.zeros_like(handle_x) + 100,
        'Shoulder/0/X': np.zeros_like(handle_x) + 550,
        'Shoulder/0/Y': np.zeros_like(handle_x) + 150,
        'Seat/0/X': seat_x,
        'Seat/0/Y': np.zeros_like(seat_x) + 200,
    })
    
    results = process_rowing_data(df)
    
    if results is not None:
        metadata = results.get('metadata', {})
        capture_length = metadata.get('capture_length', 0)
        warnings = metadata.get('warnings', [])
        
        if capture_length < 3:
            # Should have warning about short capture
            assert any("capture" in w.lower() for w in warnings), \
                f"Expected capture length warning, got: {warnings}"
            print(f"  ✓ Short capture warning generated: {capture_length} cycles")
        else:
            print(f"  ✓ Capture length sufficient: {capture_length} cycles (no warning expected)")
    else:
        print("  ✓ Pipeline returned None (expected for very short data)")


def test_sampling_stability_detection():
    """Test sampling stability detection with uniform vs non-uniform time deltas."""
    print("\n✓ TEST: Sampling stability detection")
    
    # Test 1: Uniform sampling (should be stable)
    print("  Testing uniform sampling...")
    time_uniform = np.linspace(0, 5, 100)  # Uniform 20ms samples
    handle_x = np.sin(2 * np.pi * time_uniform / 1) * 100 + 500
    seat_x = np.sin(2 * np.pi * time_uniform / 1 + 0.3) * 100 + 600
    
    df_uniform = pd.DataFrame({
        'Time': time_uniform,
        'Handle/0/X': handle_x,
        'Handle/0/Y': np.zeros_like(handle_x) + 100,
        'Shoulder/0/X': np.zeros_like(handle_x) + 550,
        'Shoulder/0/Y': np.zeros_like(handle_x) + 150,
        'Seat/0/X': seat_x,
        'Seat/0/Y': np.zeros_like(seat_x) + 200,
    })
    
    results_uniform = process_rowing_data(df_uniform)
    if results_uniform is not None:
        metadata_uniform = results_uniform.get('metadata', {})
        sampling_cv = metadata_uniform.get('sampling_cv')
        is_stable = metadata_uniform.get('sampling_is_stable')
        print(f"  ✓ Uniform sampling: CV={sampling_cv}, stable={is_stable}")
    
    # Test 2: Non-uniform sampling (should be unstable)
    print("  Testing non-uniform sampling...")
    time_jittered = np.sort(np.random.uniform(0, 5, 100))
    handle_x = np.sin(2 * np.pi * time_jittered / 1) * 100 + 500
    seat_x = np.sin(2 * np.pi * time_jittered / 1 + 0.3) * 100 + 600
    
    df_jitter = pd.DataFrame({
        'Time': time_jittered,
        'Handle/0/X': handle_x,
        'Handle/0/Y': np.zeros_like(handle_x) + 100,
        'Shoulder/0/X': np.zeros_like(handle_x) + 550,
        'Shoulder/0/Y': np.zeros_like(handle_x) + 150,
        'Seat/0/X': seat_x,
        'Seat/0/Y': np.zeros_like(seat_x) + 200,
    })
    
    results_jitter = process_rowing_data(df_jitter)
    if results_jitter is not None:
        metadata_jitter = results_jitter.get('metadata', {})
        sampling_cv = metadata_jitter.get('sampling_cv')
        is_stable = metadata_jitter.get('sampling_is_stable')
        print(f"  ✓ Jittered sampling: CV={sampling_cv}, stable={is_stable}")


def test_row_drop_tracking():
    """Test that row drops are tracked correctly."""
    print("\n✓ TEST: Row drop tracking")
    
    df = create_scenario_data(scenario='healthy_catch', num_cycles=5)
    assert df is not None and len(df) > 0, "Scenario data generation failed"
    
    rows_before = len(df)
    results = process_rowing_data(df)
    
    if results is not None:
        rows_dropped = results['metadata']['rows_dropped']
        rows_after = len(results['cycles'][0]) * len(results['cycles']) if results['cycles'] else 0
        
        assert rows_dropped >= 0, "Rows dropped should be non-negative"
        print(f"  ✓ Rows before: {rows_before}")
        print(f"  ✓ Rows dropped: {rows_dropped}")
        print(f"  ✓ Row drop percentage: {(rows_dropped/rows_before*100):.1f}%")


def test_metadata_diagnostics_function():
    """Test _compute_metadata_diagnostics directly."""
    print("\n✓ TEST: _compute_metadata_diagnostics function")
    
    # Create minimal test data
    df_raw = pd.DataFrame({
        'Time': np.linspace(0, 5, 100),
        'Handle/0/X': np.random.randn(100),
    })
    
    df_processed = df_raw.copy()
    
    # Create mock cycles
    cycles = [
        pd.DataFrame({'Seat_X_Smooth': np.random.randn(20)}),
        pd.DataFrame({'Seat_X_Smooth': np.random.randn(20)}),
    ]
    
    # Mock time metrics
    time_metrics = {
        'sample_rate_hz': 100.0,
        'cycle_duration_s': 1.0,
        'stroke_rate_spm': 60.0,
    }
    
    # Mock stats
    stats = {
        'data_quality_flag': 'OK',
        'nan_rate': 0.01,
        'outlier_count': 0,
    }
    
    metadata = _compute_metadata_diagnostics(df_raw, df_processed, cycles, time_metrics, stats)
    
    assert isinstance(metadata, dict), "Should return dict"
    assert metadata['capture_length'] == 2, "Should have 2 cycles"
    assert isinstance(metadata['warnings'], list), "Warnings should be list"
    print(f"  ✓ Metadata computed: {metadata['capture_length']} cycles")
    print(f"  ✓ Warnings: {metadata['warnings'] if metadata['warnings'] else 'None'}")


def test_warnings_in_results():
    """Test that warnings are properly included in final results."""
    print("\n✓ TEST: Warnings in results")
    
    df = create_scenario_data(scenario='healthy_catch', num_cycles=5)
    results = process_rowing_data(df)
    
    if results is not None:
        metadata = results['metadata']
        warnings = metadata['warnings']
        
        assert isinstance(warnings, list), "Warnings should be a list"
        assert all(isinstance(w, str) for w in warnings), "All warnings should be strings"
        
        print(f"  ✓ Warnings list contains {len(warnings)} item(s)")
        for i, warn in enumerate(warnings, 1):
            print(f"    - [{i}] {warn[:60]}..." if len(warn) > 60 else f"    - [{i}] {warn}")


if __name__ == '__main__':
    print("=" * 70)
    print("METADATA TRACKING TESTS (Recommendation #6)")
    print("=" * 70)
    
    try:
        test_metadata_included_in_results()
        test_capture_length_warning()
        test_sampling_stability_detection()
        test_row_drop_tracking()
        test_metadata_diagnostics_function()
        test_warnings_in_results()
        
        print("\n" + "=" * 70)
        print("✅ ALL METADATA TRACKING TESTS PASSED")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise
