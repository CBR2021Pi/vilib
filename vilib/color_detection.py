import cv2
import numpy as np


'''The range of H in HSV space for colors'''
color_dict = {
        'red':[0,4],
        'orange':[5,18],
        'yellow':[22,37],
        'green':[42,85],
        'blue':[92,110],
        'purple':[115,165],
        'red_2':[165,180],
    }

'''Define parameters for color detection object'''
color_obj_parameter = {}

color_obj_parameter['color'] = 'red'    # color to be detected

color_obj_parameter['x'] = 320    # Maximum color block center x-axis coordinate
color_obj_parameter['y'] = 240    # Maximum color block center y-axis coordinate
color_obj_parameter['w'] = 0  # Maximum color block pixel width
color_obj_parameter['h'] = 0  # Maximum color block pixel height
color_obj_parameter['n'] = 0  # Number of color blocks detected


def get_color_obj_parameter(parameter):
    '''
    Returns the coordinates, size, and number of detected color

    :param parameter: Parameter to be returned, could be: "all", "x", "y", "width", "height", "number"
    :type name: str
    :returns: The coordinates, size, and number of detected color, or all of them.
    :rtype: int or dict
    '''
    if parameter == 'x':       
        return int(color_obj_parameter['x']/214.0)-1 # max_size_object_coordinate_y
    elif parameter == 'y':
        return -1*(int(color_obj_parameter['y']/160.2)-1) # max_size_object_coordinate_y
    elif parameter == 'width':
        return color_obj_parameter['w']   # objects_max_width
    elif parameter == 'height':
        return color_obj_parameter['h']   # objects_max_height
    elif parameter == 'number':      
        return color_obj_parameter['n']   # objects_count
    elif parameter == 'all':
        return dict.copy(color_obj_parameter) 
    return None

def color_detect(img, width, height, color_name, rectangle_color=(0, 0, 255)):
    '''
    Color detection with opencv

    :param img: The detected image data
    :type img: list
    :param width: The width of the image data
    :type width: int
    :param height: The height of the image data
    :type height: int
    :param color_name: The name of the color to be detected. Eg: "red". For supported colors, please see [color_dict].
    :type color_name: str
    :param rectangle_color: The color (BGR, tuple) of rectangle. Eg: (0, 0, 255).
    :type color_name: tuple
    :returns: The image returned after detection.
    :rtype: Binary list
    '''
    color_obj_parameter['color'] = color_name   
    
    # Reduce image for faster recognition 
    zoom = 4 # reduction ratio
    width_zoom = int(width / zoom)
    height_zoom = int(height / zoom)
    resize_img = cv2.resize(img, (width_zoom, height_zoom), interpolation=cv2.INTER_LINEAR)
    
    # Convert the image in BGR to HSV
    hsv = cv2.cvtColor(resize_img, cv2.COLOR_BGR2HSV) 
   
    # Set range for red color and  define mask
    color_lower = np.array([min(color_dict[color_name]), 60, 60])
    color_upper = np.array([max(color_dict[color_name]), 255, 255])
    mask = cv2.inRange(hsv, color_lower, color_upper)          
    if color_name == 'red':
        mask_2 = cv2.inRange(hsv, (167,0,0), (180,255,255))
        mask = cv2.bitwise_or(mask, mask_2)

    # define a 5*5 kernel
    kernel_5 = np.ones((5,5),np.uint8)

    # opening the image (erosion followed by dilation), to remove the image noise
    open_img = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_5, iterations=1)      

    # Find contours in binary image
    _tuple = cv2.findContours(open_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
    # compatible with opencv3.x and openc4.x
    if len(_tuple) == 3:
        _, contours, hierarchy = _tuple
    else:
        contours, hierarchy = _tuple

    color_obj_parameter['n'] = len(contours)
    
    if color_obj_parameter['n'] < 1:
        color_obj_parameter['x'] = width/2
        color_obj_parameter['y'] = height/2
        color_obj_parameter['w'] = 0
        color_obj_parameter['h'] = 0
        color_obj_parameter['n'] = 0
    else:
        # Iterate over all contours
        max_area = 0
        for contour in contours:  
            # Return the coordinate(top left), width and height of contour
            x, y, w, h = cv2.boundingRect(contour)      
            if w >= 8 and h >= 8: 
                x = x * zoom
                y = y * zoom
                w = w * zoom
                h = h * zoom
                # Draw rectangle around  the color block
                cv2.rectangle(img, (x, y), (x+w, y+h), rectangle_color, 2)
                # Draw color name
                cv2.putText(img, color_name, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, rectangle_color, 2)
            else:
                continue

            # Save the attribute of the largest color block
            object_area = w*h
            if object_area > max_area: 
                max_area = object_area
                color_obj_parameter['x'] = int(x + w/2)
                color_obj_parameter['y'] = int(y + h/2)
                color_obj_parameter['w'] = w
                color_obj_parameter['h'] = h

    return img

# Test
def test(color):
    print("color detection: %s"%color)

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while cap.isOpened():
        success,frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # frame = cv2.flip(frame, -1) # Flip camera vertically

        out_img = color_detect(frame, 640, 480, color)

        cv2.imshow('Color detecting ...', out_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.waitKey(1) & 0xff == 27: # press 'ESC' to quit
            break
        if cv2.getWindowProperty('Color detecting ...', 1) < 0:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test('red')
