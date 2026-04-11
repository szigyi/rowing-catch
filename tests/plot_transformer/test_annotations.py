"""Tests for the annotation data model and color assignment utility."""

from rowing_catch.plot_transformer.annotations import (
    ANNOTATION_COLORS,
    AnnotationDefinition,
    BandAnnotation,
    PhaseAnnotation,
    PointAnnotation,
    SegmentAnnotation,
    assign_annotation_colors,
)

# ---------------------------------------------------------------------------
# PointAnnotation
# ---------------------------------------------------------------------------


class TestPointAnnotation:
    def test_defaults(self):
        ann = PointAnnotation(label='[A1]', description='Peak: 10°', x=5.0, y=10.0)
        assert ann.style == 'label'
        assert ann.color is None
        assert ann.axis_id == 'main'

    def test_callout_style(self):
        ann = PointAnnotation(label='[A1]', description='Peak', x=1.0, y=2.0, style='callout')
        assert ann.style == 'callout'

    def test_custom_axis_id(self):
        ann = PointAnnotation(label='[A1]', description='', x=0.0, y=0.0, axis_id='top')
        assert ann.axis_id == 'top'

    def test_explicit_color(self):
        ann = PointAnnotation(label='[A1]', description='', x=0.0, y=0.0, color='#FF0000')
        assert ann.color == '#FF0000'


# ---------------------------------------------------------------------------
# SegmentAnnotation
# ---------------------------------------------------------------------------


class TestSegmentAnnotation:
    def test_defaults(self):
        ann = SegmentAnnotation(label='[S1]', description='Drive', x_start=0.0, x_end=10.0)
        assert ann.style == 'glow'
        assert ann.x == []
        assert ann.y == []
        assert ann.color is None
        assert ann.axis_id == 'main'

    def test_with_data(self):
        ann = SegmentAnnotation(
            label='[S1]',
            description='Drive',
            x_start=0.0,
            x_end=3.0,
            x=[0.0, 1.0, 2.0, 3.0],
            y=[5.0, 6.0, 7.0, 8.0],
            style='highlight+glow',
        )
        assert len(ann.x) == 4
        assert ann.style == 'highlight+glow'


# ---------------------------------------------------------------------------
# BandAnnotation
# ---------------------------------------------------------------------------


class TestBandAnnotation:
    def test_defaults(self):
        ann = BandAnnotation(label='[Z1]', description='Zone', y_low=-33.0, y_high=-27.0)
        assert ann.x_start is None
        assert ann.x_end is None
        assert ann.color is None
        assert ann.axis_id == 'main'

    def test_bounded_band(self):
        ann = BandAnnotation(label='[Z1]', description='Zone', y_low=0.0, y_high=5.0, x_start=10.0, x_end=50.0)
        assert ann.x_start == 10.0
        assert ann.x_end == 50.0


# ---------------------------------------------------------------------------
# PhaseAnnotation
# ---------------------------------------------------------------------------


class TestPhaseAnnotation:
    def test_defaults(self):
        ann = PhaseAnnotation(label='[Ph1]', description='Drive Phase', x_start=10.0, x_end=40.0)
        assert ann.color is None
        assert ann.axis_id == 'main'

    def test_custom_color(self):
        ann = PhaseAnnotation(label='[Ph1]', description='Drive', x_start=0.0, x_end=10.0, color='#00CC96')
        assert ann.color == '#00CC96'


# ---------------------------------------------------------------------------
# AnnotationDefinition
# ---------------------------------------------------------------------------


class TestAnnotationDefinition:
    def test_defaults(self):
        defn = AnnotationDefinition(id='A1', name='Catch Lean', description='Trunk angle at catch')
        assert defn.default_on is True

    def test_default_off(self):
        defn = AnnotationDefinition(id='S1', name='Drive Segment', description='Drive segment backdrop', default_on=False)
        assert defn.default_on is False


# ---------------------------------------------------------------------------
# assign_annotation_colors
# ---------------------------------------------------------------------------


class TestAssignAnnotationColors:
    def test_assigns_palette_colors_to_none(self):
        anns = [
            PointAnnotation(label='[A1]', description='', x=0.0, y=0.0),
            PointAnnotation(label='[A2]', description='', x=1.0, y=1.0),
        ]
        result = assign_annotation_colors(anns)
        assert result[0].color == ANNOTATION_COLORS[0]
        assert result[1].color == ANNOTATION_COLORS[1]

    def test_preserves_explicit_colors(self):
        anns = [
            PointAnnotation(label='[A1]', description='', x=0.0, y=0.0, color='#FF0000'),
            PointAnnotation(label='[A2]', description='', x=1.0, y=1.0),
        ]
        result = assign_annotation_colors(anns)
        assert result[0].color == '#FF0000'  # unchanged
        assert result[1].color == ANNOTATION_COLORS[0]  # first palette color (skipped explicit)

    def test_does_not_mutate_originals(self):
        ann = PointAnnotation(label='[A1]', description='', x=0.0, y=0.0)
        assign_annotation_colors([ann])
        assert ann.color is None  # original unchanged

    def test_fallback_color_when_palette_exhausted(self):
        # More annotations than palette entries → fallback color '#888888'
        anns = [PointAnnotation(label=f'[A{i}]', description='', x=float(i), y=0.0) for i in range(len(ANNOTATION_COLORS) + 2)]
        result = assign_annotation_colors(anns)
        assert result[-1].color == '#888888'
        assert result[-2].color == '#888888'

    def test_custom_palette(self):
        palette = ['#111111', '#222222']
        anns = [
            PointAnnotation(label='[A1]', description='', x=0.0, y=0.0),
            PointAnnotation(label='[A2]', description='', x=1.0, y=0.0),
        ]
        result = assign_annotation_colors(anns, palette=palette)
        assert result[0].color == '#111111'
        assert result[1].color == '#222222'

    def test_mixed_types(self):
        """assign_annotation_colors handles all AnnotationEntry types."""
        from rowing_catch.plot_transformer.annotations import AnnotationEntry

        anns: list[AnnotationEntry] = [
            PointAnnotation(label='[A1]', description='', x=0.0, y=0.0),
            SegmentAnnotation(label='[S1]', description='', x_start=0.0, x_end=1.0),
            BandAnnotation(label='[Z1]', description='', y_low=0.0, y_high=1.0),
            PhaseAnnotation(label='[Ph1]', description='', x_start=0.0, x_end=1.0),
        ]
        result = assign_annotation_colors(anns)
        for i, r in enumerate(result):
            assert r.color == ANNOTATION_COLORS[i]

    def test_empty_list(self):
        assert assign_annotation_colors([]) == []
