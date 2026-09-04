import os
import cv2
import numpy as np

def main():
    try:
        # Create output directory
        output_dir = "data/samples"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Create a synthetic test image programmatically
        # White background
        img = np.ones((500, 500, 3), dtype=np.uint8) * 255
        
        # Black rectangle
        cv2.rectangle(img, (50, 50), (200, 150), (0, 0, 0), -1)
        
        # Black circle
        cv2.circle(img, (350, 100), 50, (0, 0, 0), -1)
        
        # Black triangle
        pts = np.array([[250, 400], [150, 250], [350, 250]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(img, [pts], (0, 0, 0))
        
        # Save original test image
        img_path = os.path.join(output_dir, "spike_test_shapes.png")
        cv2.imwrite(img_path, img)
        print(f"Saved test image to {img_path}")
        
        # 2. Run OpenCV vectorization pipeline
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold (invert so shapes are white)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # findContours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Output image for debug
        debug_img = img.copy()
        
        detected_shapes = []
        
        for idx, contour in enumerate(contours):
            # approxPolyDP
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Classify shapes
            vertices = len(approx)
            if vertices == 3:
                shape_name = "Triangle"
            elif vertices == 4:
                shape_name = "Rectangle"
            else:
                shape_name = "Circle"
                
            detected_shapes.append({
                "id": idx,
                "type": shape_name,
                "vertices": vertices,
                "contour_points": len(contour)
            })
            
            # Draw contours on debug image
            cv2.drawContours(debug_img, [approx], 0, (0, 255, 0), 3)
            
            # Put text
            x, y = approx.ravel()[0], approx.ravel()[1]
            cv2.putText(debug_img, shape_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
        # Save debug visualization
        debug_path = os.path.join(output_dir, "spike_test_shapes_debug.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"Saved debug visualization to {debug_path}")
        
        # Print structured output
        print("Detected shapes:")
        for shape in detected_shapes:
            print(f" - {shape}")
            
        print(f"\nSPIKE RESULT: PASS ({len(detected_shapes)} shapes detected)")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nSPIKE RESULT: FAIL with error {e}")

if __name__ == "__main__":
    main()
