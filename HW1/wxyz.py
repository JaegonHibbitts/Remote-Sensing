import math

def wyxz():
    """
    Write a script that queries the user for four values — w, x, y, and z. Identify the smaller of w and x, the
    smaller of y and z, and swap their two values. Then print out the final, swapped values of w, x, y, and z.
    """

    # Your code here
    w = float(input("Enter value for w: "))
    x = float(input("Enter value for x: "))
    y = float(input("Enter value for y: "))
    z = float(input("Enter value for z: "))

    smaller_wx = min(w, x)
    smaller_yz = min(y, z)

    if smaller_wx == w and smaller_yz == y:
        w, y = y, w
    else:
        x, z = z, x


    print(f"Final values after swapping: w={w}, x={x}, y={y}, z={z}")

if __name__ == "__main__":
    wyxz()