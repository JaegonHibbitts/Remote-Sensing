import cv2 as cv
import numpy as np

def median_filter(image, kernel_size):
    output = image.copy() # Create a copy of the image to store the output
    half = kernel_size // 2

    # Need to start at middle of kernel to avoid border issues
    for i in range(kernel_size//2, image.shape[0] -kernel_size//2):
        # Print progress every 50 rows
        if (i - half) % 50 == 0:
            print(f"Processing row {i}/{image.shape[0]}") 
        for j in range(kernel_size//2, image.shape[1] -kernel_size//2):
            for k in range(3): #for each color channel
                # Extract the neighborhood
                neighborhood = []
                for di in range(-half, half + 1):      # -1, 0, 1 if 3x3 kernel
                    for dj in range(-half, half + 1):  # -1, 0, 1 if 3x3 kernel
                        neighborhood.append(image[i + di, j + dj, k]) #append the pixel value to the neighborhood list

                output[i, j, k] = np.median(neighborhood) #flatten the neighborhood and compute the median
    return output

def main():
    # Load the image
    image = cv.imread('images/SleepyJay.JPEG')

    # Add text to the image
    cv.putText(image, 'Hibbitts', (30, 90), cv.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)

    # Modify every 4th pixel
    for i in range(0, image.shape[0], 4): #height of the image; step of 4
        for j in range(0, image.shape[1], 4): #width of the image; step of 4
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

