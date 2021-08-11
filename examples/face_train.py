from vilib import Vilib
from vilib import Face
import pickle


def main():
    
    pic_path='/home/pi/trainer/WuJing'
    model_path="/home/pi/trainer/encodings.pickle"
    Face.training("WuJing", pic_path,model_path)

    datas = []
    with open(model_path,'rb') as f:
        while True:
            try:
                datas.append(pickle.load(f))              
            except EOFError:
                break

    print(datas)
        
if __name__ == "__main__":
    main()