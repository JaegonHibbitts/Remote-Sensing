import cv2 as cv
import numpy as np

def median_filter(image, kernel_size):
    # Pad the image to handle borders
    pad_size = kernel_size // 2
    padded_image = cv.copyMakeBorder(image, pad_size, pad_size, pad_size, pad_size, cv.BORDER_REFLECT)

    # Prepare an empty image for the output
    output_image = np.zeros_like(image)

    # Apply median filter
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            # Extract the kernel region
            kernel_region = padded_image[i:i+kernel_size, j:j+kernel_size]
            # Compute the median value for each channel
            output_image[i, j] = np.median(kernel_region.reshape(-1, 3), axis=0)

    return output_image

def main():
    # Load the image
    image = cv.imread('images/SleepyJay.JPEG')

    # Add text to the image
    cv.putText(image, 'Hibbitts', (30, 90), cv.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)

    # Modify every 4th pixel
    for i in range(0, image.shape[0], 4): #width of the image; step of 4
        for j in range(0, image.shape[1], 4): #height of the image; step of 4
            image[i, j] = np.random.randint(0, 256, 3) #size 3 for RGB channels

    # Save the modified image
    cv.imwrite('images/ModifiedSleepyJay.jpg', image)
    cv.imshow('Modified Image', image)
    cv.waitKey(0)
    cv.destroyAllWindows()

    # Apply median filter with different kernel sizes
    kernel_size_1 = 3
    kernel_size_2 = 5
    median_filtered_image_1 = median_filter(image, kernel_size_1)
    median_filtered_image_2 = median_filter(image, kernel_size_2)
    
    # Save the median filtered images
    cv.imwrite('images/median_filtered_image_3.jpg', median_filtered_image_1)
    cv.imwrite('images/median_filtered_image_5.jpg', median_filtered_image_2)
    cv.imshow('Median Filtered Image (3x3)', median_filtered_image_1)
    cv.imshow('Median Filtered Image (5x5)', median_filtered_image_2)
    cv.waitKey(0)
    cv.destroyAllWindows()

if __name__ == "__main__":    
    main()

