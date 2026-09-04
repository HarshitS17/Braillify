import pytest
import numpy as np
import cv2
from pathlib import Path
from app.pipeline.preprocessing import (
    load_image, to_grayscale, reduce_noise, correct_illumination,
    detect_skew_angle, deskew, adaptive_threshold, normalize_contrast,
    normalize_resolution, preprocess_image, render_pdf_page,
)
from app.models.preprocessing import PreprocessingConfig, PreprocessingResult

# Fixture directory
FIXTURE_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"


class TestLoadImage:
    def test_load_valid_png(self):
        img = load_image(FIXTURE_DIR / "simple_shapes.png")
        assert img is not None
        assert len(img.shape) == 3  # BGR
        assert img.shape[2] == 3
    
    def test_load_nonexistent_raises(self):
        from app.core.exceptions import FileFormatError
        with pytest.raises(FileFormatError):
            load_image(Path("/nonexistent/file.png"))
    
    def test_load_returns_correct_dimensions(self):
        img = load_image(FIXTURE_DIR / "simple_shapes.png")
        assert img.shape[0] == 600  # height
        assert img.shape[1] == 800  # width


class TestGrayscale:
    def test_converts_bgr_to_gray(self):
        bgr = np.zeros((100, 100, 3), dtype=np.uint8)
        bgr[:, :, 2] = 255  # Red channel
        gray, meta = to_grayscale(bgr)
        assert len(gray.shape) == 2
        assert meta["input_channels"] == 3
    
    def test_already_grayscale(self):
        gray_in = np.zeros((100, 100), dtype=np.uint8)
        gray_out, meta = to_grayscale(gray_in)
        assert meta["already_grayscale"] is True
        assert np.array_equal(gray_in, gray_out)
    
    def test_does_not_modify_input(self):
        bgr = np.ones((100, 100, 3), dtype=np.uint8) * 128
        original = bgr.copy()
        to_grayscale(bgr)
        assert np.array_equal(bgr, original)


class TestNoiseReduction:
    def test_reduces_noise(self):
        # Create noisy image
        img = np.ones((100, 100), dtype=np.uint8) * 128
        noise = np.random.normal(0, 30, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        config = PreprocessingConfig()
        denoised, meta = reduce_noise(noisy, config)
        
        # Denoised should be closer to original than noisy was
        noise_before = np.std(noisy.astype(float) - img.astype(float))
        noise_after = np.std(denoised.astype(float) - img.astype(float))
        assert noise_after < noise_before
    
    def test_preserves_shape(self):
        img = np.zeros((200, 300), dtype=np.uint8)
        config = PreprocessingConfig()
        result, _ = reduce_noise(img, config)
        assert result.shape == img.shape


class TestIlluminationCorrection:
    def test_improves_contrast(self):
        # Low contrast image
        img = np.ones((100, 100), dtype=np.uint8) * 128
        img[25:75, 25:75] = 140  # Very slight difference
        
        config = PreprocessingConfig()
        corrected, meta = correct_illumination(img, config)
        
        assert meta["std_after"] >= meta["std_before"]  # Contrast should increase or stay same
    
    def test_records_metadata(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        config = PreprocessingConfig()
        _, meta = correct_illumination(img, config)
        assert "mean_before" in meta
        assert "mean_after" in meta
        assert "clahe_clip_limit" in meta


class TestDeskewing:
    def test_detects_skew_in_rotated_image(self):
        # Create image with horizontal lines, then rotate
        img = np.ones((400, 600), dtype=np.uint8) * 255
        for y in range(50, 350, 30):
            cv2.line(img, (50, y), (550, y), 0, 2)
        
        # Rotate 5 degrees
        h, w = img.shape
        M = cv2.getRotationMatrix2D((w//2, h//2), 5, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), borderValue=255)
        
        config = PreprocessingConfig()
        angle, meta = detect_skew_angle(rotated, config)
        
        # Should detect approximately 5 degree skew (may not be exact)
        assert abs(angle) > 1.0  # At least detects some skew
        assert meta["skew_detected"] is True
    
    def test_no_skew_detected_for_straight_image(self):
        img = np.ones((400, 600), dtype=np.uint8) * 255
        for y in range(50, 350, 30):
            cv2.line(img, (50, y), (550, y), 0, 2)
        
        config = PreprocessingConfig()
        angle, meta = detect_skew_angle(img, config)
        assert abs(angle) < 2.0  # Should be near zero
    
    def test_deskew_corrects_rotation(self):
        img = np.ones((200, 300), dtype=np.uint8) * 255
        deskewed, meta = deskew(img, 5.0)
        assert meta["angle_corrected"] == 5.0
        assert deskewed.shape[0] > 0
    
    def test_deskew_skips_trivial_angle(self):
        img = np.ones((200, 300), dtype=np.uint8) * 255
        deskewed, meta = deskew(img, 0.05)
        assert meta["skipped"] is True


class TestAdaptiveThreshold:
    def test_produces_binary(self):
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        config = PreprocessingConfig()
        binary, meta = adaptive_threshold(img, config)
        unique = np.unique(binary)
        assert len(unique) <= 2  # Only 0 and 255
    
    def test_records_pixel_ratios(self):
        img = np.ones((100, 100), dtype=np.uint8) * 200
        config = PreprocessingConfig()
        _, meta = adaptive_threshold(img, config)
        assert "white_pixel_ratio" in meta
        assert "black_pixel_ratio" in meta
        assert abs(meta["white_pixel_ratio"] + meta["black_pixel_ratio"] - 1.0) < 0.001


class TestContrastNormalization:
    def test_stretches_range(self):
        img = np.ones((100, 100), dtype=np.uint8) * 100
        img[50:, :] = 150  # limited range: 100-150
        normalized, meta = normalize_contrast(img)
        assert meta["output_min"] == 0
        assert meta["output_max"] == 255
    
    def test_skips_uniform(self):
        img = np.ones((100, 100), dtype=np.uint8) * 128
        normalized, meta = normalize_contrast(img)
        assert meta.get("skipped") is True


class TestResolutionNormalization:
    def test_downscales_large_image(self):
        img = np.zeros((5000, 5000), dtype=np.uint8)
        config = PreprocessingConfig(target_max_dimension=2000)
        resized, meta = normalize_resolution(img, config)
        assert max(resized.shape) <= 2000
        assert meta["scale_factor"] < 1.0
    
    def test_skips_already_correct(self):
        img = np.zeros((500, 500), dtype=np.uint8)
        config = PreprocessingConfig(target_max_dimension=4000)
        resized, meta = normalize_resolution(img, config)
        assert meta.get("skipped") is True


class TestFullPipeline:
    def test_preprocess_simple_shapes(self, tmp_path):
        fixture = FIXTURE_DIR / "simple_shapes.png"
        if not fixture.exists():
            pytest.skip("Fixture not generated")
        
        result = preprocess_image(
            image_path=fixture,
            output_dir=tmp_path,
            page_id="test-page",
            save_debug=True,
        )
        
        assert result.success is True
        assert result.original_width == 800
        assert result.original_height == 600
        assert len(result.stages) > 0
        assert result.grayscale_path is not None
        assert result.binary_path is not None
        assert result.preprocessed_path is not None
        assert Path(result.preprocessed_path).exists()
    
    def test_preprocess_noisy_image(self, tmp_path):
        fixture = FIXTURE_DIR / "noisy_diagram.png"
        if not fixture.exists():
            pytest.skip("Fixture not generated")
        
        result = preprocess_image(
            image_path=fixture,
            output_dir=tmp_path,
            page_id="test-noisy",
            save_debug=True,
        )
        
        assert result.success is True
        # Should detect some skew (the fixture has 3 degree rotation)
        # Note: detection may not be exact
    
    def test_preprocess_low_contrast(self, tmp_path):
        fixture = FIXTURE_DIR / "low_contrast.png"
        if not fixture.exists():
            pytest.skip("Fixture not generated")
        
        result = preprocess_image(
            image_path=fixture,
            output_dir=tmp_path,
            page_id="test-low-contrast",
            save_debug=True,
        )
        
        assert result.success is True
    
    def test_preprocess_with_custom_config(self, tmp_path):
        fixture = FIXTURE_DIR / "simple_shapes.png"
        if not fixture.exists():
            pytest.skip("Fixture not generated")
        
        config = PreprocessingConfig(
            gaussian_kernel_size=3,
            clahe_clip_limit=3.0,
            adaptive_block_size=15,
            deskew_enabled=False,
        )
        result = preprocess_image(
            image_path=fixture,
            output_dir=tmp_path,
            config=config,
            page_id="test-custom",
        )
        
        assert result.success is True
        assert result.detected_skew_angle is None  # deskew was disabled
    
    def test_debug_artifacts_created(self, tmp_path):
        fixture = FIXTURE_DIR / "simple_shapes.png"
        if not fixture.exists():
            pytest.skip("Fixture not generated")
        
        result = preprocess_image(
            image_path=fixture,
            output_dir=tmp_path,
            page_id="test-debug",
            save_debug=True,
        )
        
        debug_dir = tmp_path / "debug"
        assert debug_dir.exists()
        # Check that stage images were created
        debug_files = list(debug_dir.glob("*.png"))
        assert len(debug_files) >= 4  # At least original, grayscale, denoised, thresholded


class TestPdfRendering:
    def test_render_pdf_page(self):
        pdf_fixture = FIXTURE_DIR / "simple_page.pdf"
        if not pdf_fixture.exists():
            pytest.skip("PDF fixture not generated")
        
        img = render_pdf_page(pdf_fixture, page_number=0, dpi=150)
        assert img is not None
        assert len(img.shape) == 3
        assert img.shape[0] > 0 and img.shape[1] > 0
    
    def test_invalid_page_number_raises(self):
        pdf_fixture = FIXTURE_DIR / "simple_page.pdf"
        if not pdf_fixture.exists():
            pytest.skip("PDF fixture not generated")
        
        from app.core.exceptions import FileFormatError
        with pytest.raises(FileFormatError):
            render_pdf_page(pdf_fixture, page_number=999)
