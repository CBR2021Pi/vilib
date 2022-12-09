import cv2
import numpy as np
import os
from tflite_runtime.interpreter import Interpreter


'''Define parameters for traffic sign detection object'''
traffic_sign_obj_parameter = {}
traffic_sign_obj_parameter['x'] = 320   # Maximum traffic sign block center x-axis coordinate
traffic_sign_obj_parameter['y'] = 240   # Maximum traffic sign block center y-axis coordinate
traffic_sign_obj_parameter['w'] = 0     # Maximum face block pixel width
traffic_sign_obj_parameter['h'] = 0     # Maximum face block pixel height
traffic_sign_obj_parameter['t'] = 'None'    # traffic sign text, could be: 'None', 'stop','right','left','forward'
traffic_sign_obj_parameter['acc'] = 0        

'''Default model and labels'''
traffic_sign_model_path = "/opt/vilib/traffic_sign_150_dr0.2.tflite"  # default model path
traffic_sign_labels_path = '/opt/vilib/traffic_sign_150_dr0.2_labels.txt'  # default model path


def get_traffic_sign_obj_parameter(obj_parameter):
    '''
    Returns the coordinates, size, number, type and  accuracy of detected traffic sign

    :param parameter: Parameter to be returned, could be: "all", "x", "y", "width", "height", "number", "type", 'accuracy'
    :type name: str
    :returns: The coordinates, size, type and  accuracy of detected color, or all of them.
    :rtype: int or dict
    '''
    if obj_parameter == 'x':
        return int(traffic_sign_obj_parameter['x']/214.0)-1
    elif obj_parameter == 'y':
        return -1*(int(traffic_sign_obj_parameter['y']/160.2)-1) # max_size_object_coordinate_y
    elif obj_parameter == 'width':
        return traffic_sign_obj_parameter['w']   # objects_max_width
    elif obj_parameter == 'height':
        return traffic_sign_obj_parameter['h']   # objects_max_height
    elif obj_parameter == 'number':      
        return traffic_sign_obj_parameter['traffic_sign_n']   # objects_count
    elif obj_parameter == 'type':      
        return traffic_sign_obj_parameter['t']   # objects_type
    elif obj_parameter == 'accuracy':      
        return traffic_sign_obj_parameter['acc']    # objects_type
    return 'none'

def traffic_sign_predict(interpreter, img):
    '''
    Traffic sign predict type

    :param img: The detected image data
    :type img: list
    :param img: The detected image data
    :type img: list
    :returns: The confidence value and index of type
    :rtype: tuple (confidence:float, type:str)
    '''
    _, model_width, model_height, model_depth = interpreter.get_input_details()[0]['shape']  
    if model_depth != 3 and model_depth != 1:
        raise ValueError('Unsupported model depth')

    # resize the image according to the model size
    resize_img = cv2.resize(img, (model_width, model_height), interpolation=cv2.INTER_LINEAR)
    
    flatten_img = np.reshape(resize_img, (model_width, model_height, model_depth))
    im5 = np.expand_dims(flatten_img, axis = 0)
    img_np_expanded = im5.astype('float32')

    # Perform the actual detection by running the model with the image as input
    tensor_index = interpreter.get_input_details()[0]['index']
    interpreter.set_tensor(tensor_index, img_np_expanded)
    interpreter.invoke() 

    output_details = interpreter.get_output_details()[0]
    output_data = interpreter.get_tensor(output_details['index'])  

    result = np.squeeze(output_data)
    accuracy = round(np.max(result), 2)
    type_idnex = np.where(result==np.max(result))[0][0]

    return accuracy, type_idnex

def cnt_area(cnt):
    # Return the coordinate(top left), width and height of contour
    x, y, w, h = cv2.boundingRect(cnt)
    return w*h

def load_labels(path):
  with open(path, 'r') as f:
    return {i: line.strip() for i, line in enumerate(f.readlines())}

def traffic_sign_detect(img, model=None, labels=None, border_rgb=(255, 0, 0)):
    '''
    Traffic sign detection

    :param img: The detected image data
    :type img: list
    :param model: The tflite model file path, if 'None' use default path
    :type model: str
    :param labels: The labels file path, if 'None' use default path
    :type labels: str
    :param border_rgb: The color (RGB, tuple) of border. Eg: (255, 0, 0).
    :type color_name: tuple
    :returns: The image returned after detection
    :rtype: Binary list
    '''
    # border_rgb to border_bgr
    r, g, b = border_rgb
    border_bgr = (b, g, r)

    # loading model and corresponding label
    if model == None:
        model = traffic_sign_model_path
    if labels == None:
        labels = traffic_sign_labels_path

    if not os.path.exists(model):
        raise('incorrect model path ')
        return img
    if not os.path.exists(labels):
        raise('incorrect labels path ')
        return img

    labels = load_labels(labels)
    interpreter = Interpreter(model)
    interpreter.allocate_tensors()

    # _, model_height, model_width, _ = interpreter.get_input_details()[0]['shape']  
    # print('get_input_details', interpreter.get_input_details()[0]['shape'] )

    # get img shape
    width, height, depth = np.shape(img)

    # Convert the image in BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Set range for red color and  define mask
    mask_red_1 = cv2.inRange(hsv, (157,20,20), (180,255,255))
    mask_red_2 = cv2.inRange(hsv, (0,20,20), (10,255,255))

    # Set range for blue color and  define mask
    mask_blue = cv2.inRange(hsv, (102,50,50), (125,255,255))

    ### all
    mask_all = cv2.bitwise_or(mask_red_1, mask_blue)
    mask_all = cv2.bitwise_or(mask_red_2, mask_all)

    # define a 5*5 kernel
    kernel_5 = np.ones((5, 5), np.uint8)

    # opening the image (erosion followed by dilation), to remove the image noise
    open_img = cv2.morphologyEx(mask_all, cv2.MORPH_OPEN, kernel_5, iterations=1)  
    # cv2.imshow('open_img', open_img)

    # Find contours in binary image
    _tuple = cv2.findContours(open_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
    # compatible with opencv3.x and openc4.x
    if len(_tuple) == 3:
        _, contours, hierarchy = _tuple
    else:
        contours, hierarchy = _tuple

    # Sort contours by area from smallest to largest 
    contours = sorted(contours, key=cnt_area, reverse=False)
    
    contours_num = len(contours)
    traffic_sign_num = 0
    if contours_num > 0: 
        # Iterate over all contours
        max_area = 0
        for i in contours:   
            # Return the coordinate(top left), width and height of contour
            x, y, w, h = cv2.boundingRect(i)      

            if w > 48 and h > 48:
                # Convert img to gray, if grayscale model
                model_depth = interpreter.get_input_details()[0]['shape'][3]
                if model_depth == 1:
                    img_possible_part = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    img_possible_part = img

                # Cut out the contour image
                x1 = int(x)
                x2 = int(x + width)
                y1 = int(y)
                y2 = int(y + height)
                img_possible_part = img_possible_part[y1:y2, x1:x2]
                img_possible_part = (img_possible_part / 255.0)   
                img_possible_part = (img_possible_part - 0.5) * 2.0

                # cv2.imshow('img_possible_part', img_possible_part)

                # predict traffic sign type
                acc_val, traffic_type = traffic_sign_predict(interpreter, img_possible_part)
                # Convert confidence to percentage
                acc_val = round(acc_val*100)
                traffic_type = labels[traffic_type]

                if acc_val >= 75: 
                    # print(traffic_type, acc_val)

                    # If it is a forward, turn left or right traffic sign, outline a circle 
                    if traffic_type == 'left' or \
                        traffic_type == 'right' or \
                        traffic_type == 'forward':
                        
                        # Convert to grayscale image and detect circle
                        simple_gray = cv2.cvtColor(img[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
                        circles = cv2.HoughCircles(
                                    simple_gray,
                                    cv2.HOUGH_GRADIENT, 1, 32,
                                    param1=140,
                                    param2=70,
                                    minRadius=int(w/4.0),
                                    maxRadius=max(w,h)
                                )

                        # Draw a circle outline, add text description
                        if circles is not None:
                            # Iterate over all circles and find the circle with the largest radius
                            max_radius = 0
                            max_circle_index = 0
                            max_circle = None
                            for circle in circles[0,:]:
                                # circle[center_xpos, center_ypos, radius]
                                if circle[2] > max_radius:
                                    max_radius = circle[2]
                                    max_circle = circle
                            traffic_sign_coor = (int(x+max_circle[0]),int(y+max_circle[1]))
                            cv2.circle(img, traffic_sign_coor, int(max_circle[2]), border_bgr, 2)
                            cv2.putText(img,str(traffic_type) +': ' + str(round(acc_val)),(int(x+max_circle[0]-max_circle[2]),int(y+max_circle[1]-max_circle[2])), cv2.FONT_HERSHEY_SIMPLEX, 1, border_bgr, 2)

                        if w * h > max_area:    
                            max_area = w * h
                            max_obj_x = x
                            max_obj_y = y
                            max_obj_w = w
                            max_obj_h = h
                            max_obj_t = traffic_type
                            max_obj_acc = acc_val
                            traffic_sign_num += 1

                    # If it is a STOP traffic sign, outline a rectangle 
                    elif traffic_type == 'stop':
                        red_mask_1 = cv2.inRange(hsv[y:y+h,x:x+w],(0,50,20), (4,255,255))           # 3.inRange()：介于lower/upper之间的为白色，其余黑色
                        red_mask_2 = cv2.inRange(hsv[y:y+h,x:x+w],(163,50,20), (180,255,255))
                        red_mask_all = cv2.bitwise_or(red_mask_1,red_mask_2)

                        open_img = cv2.morphologyEx(red_mask_all, cv2.MORPH_OPEN,kernel_5,iterations=1)              #开运算  
                        open_img = cv2.dilate(open_img, kernel_5,iterations=5) 
                        # Find contours in binary image
                        _tuple = cv2.findContours(open_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
                        # compatible with opencv3.x and openc4.x
                        if len(_tuple) == 3:
                            _, blue_contours, hierarchy = _tuple
                        else:
                            blue_contours, hierarchy = _tuple

                        contours_count = len(blue_contours)
                        if contours_count >=1:
                            blue_contours = sorted(blue_contours,key = cnt_area, reverse=True)
                        
                            epsilon = 0.025 * cv2.arcLength(blue_contours[0], True)
                            approx = cv2.approxPolyDP(blue_contours[0], epsilon, True)
                            corners = len(approx)
                            if corners >= 0:
                                traffic_sign_coor = (int(x+w/2),int(y+h/2))
                                cv2.rectangle(img, (x,y), (x+w,y+h), border_bgr, 2)
                                cv2.putText(img,str(traffic_type) +': ' + str(round(acc_val)),(x,y), cv2.FONT_HERSHEY_SIMPLEX, 1, border_bgr, 2)
                                if w * h > max_area:
                                    max_area = w * h
                                    max_obj_x = x
                                    max_obj_y = y
                                    max_obj_w = w
                                    max_obj_h = h
                                    max_obj_t = traffic_type
                                    max_obj_acc = acc_val
                                    traffic_sign_num += 1
                                
        if traffic_sign_num > 0:
            traffic_sign_obj_parameter['x'] = int(max_obj_x + max_obj_w/2)
            traffic_sign_obj_parameter['y'] = int(max_obj_y + max_obj_h/2)
            traffic_sign_obj_parameter['w'] = max_obj_w
            traffic_sign_obj_parameter['h'] = max_obj_h
            traffic_sign_obj_parameter['t'] = max_obj_t
            traffic_sign_obj_parameter['acc'] = max_obj_acc
        
    if contours_num <= 0 or traffic_sign_num <= 0:
        traffic_sign_obj_parameter['x'] = 320
        traffic_sign_obj_parameter['y'] = 240
        traffic_sign_obj_parameter['w'] = 0
        traffic_sign_obj_parameter['h'] = 0
        traffic_sign_obj_parameter['t'] = 'none'
        traffic_sign_obj_parameter['acc'] = 0

    return img


# Test
def test():
    print("traffic sign detection ...")

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while cap.isOpened():
        success,frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # frame = cv2.flip(frame, 0) # Flip camera horizontally 
        # frame = cv2.flip(frame, 1) # Flip camera vertically
        # frame = cv2.flip(frame, -1) # Flip camera vertically & horizontally

        out_img = traffic_sign_detect(frame, border_rgb=(255, 255, 0))

        cv2.imshow('Traffic sign detecting ...', out_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.waitKey(1) & 0xff == 27: # press 'ESC' to quit
            break
        if cv2.getWindowProperty('Traffic sign detecting ...', 1) < 0:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()
