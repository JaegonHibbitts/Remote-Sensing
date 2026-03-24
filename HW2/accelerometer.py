import numpy as np
import matplotlib.pyplot as plt

window_size = [2, 4, 8, 16, 64, 128]

# Load only the 5th column (pitch angle)
pitch_raw = np.genfromtxt("imudata.txt", usecols=4)

x = np.arange(len(pitch_raw))

#For each window size
for j in range(len(window_size)):
    window = window_size[j]
    averaged = []

    #For each data point
    for i in range(len(pitch_raw)):
        #Calculate start of the window (can't be negative)
        start = max(0, i + 1 - window)

        total = 0
        count = 0

        #For each data point IN the window --> Add to toal and count
        for k in range(start, i + 1):
            total += pitch_raw[k]
            count += 1

        averaged.append(total / count)

    averaged = np.array(averaged)

    mean_val = np.mean(averaged)
    std_val = np.std(averaged)

    plt.figure()

    #Plot stuff :(
    plt.plot(x, pitch_raw, label="Raw Data", alpha=0.5)
    plt.plot(x, averaged, label=f"Moving Avg (window={window})")

    plt.xlabel("Sample Number")
    plt.ylabel("Pitch Angle (degrees)")
    plt.title(f"Pitch Angle Moving Average (Window = {window})")

    plt.text(
        0.02, 0.95,
        f"Mean = {mean_val:.2f}\nStd = {std_val:.2f}",
        transform=plt.gca().transAxes,
        verticalalignment="top"
    )

    plt.legend()
    plt.grid()
    plt.show()