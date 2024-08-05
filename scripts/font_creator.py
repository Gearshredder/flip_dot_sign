import json
import customtkinter
import os

#============================================== CTKinter window - main frames ======================================


app = customtkinter.CTk()
app.geometry("600x400")

character_frame= customtkinter.CTkFrame(app,fg_color='#494949')
character_frame.pack(side='left',padx=10,pady=10)

dots_frame=customtkinter.CTkFrame(character_frame,fg_color='#494949')
for i in range(6):
    dots_frame.columnconfigure(i,weight=1)
    if i == 5:
        dots_frame.columnconfigure(5,weight = 0)
dots_frame.pack(padx = 20, pady = 20)


#============================================== Functions ======================================


def toggle_btn (x:int,y:int):
    btn_clicked[x][y] = not(btn_clicked[x][y])
    out_byte = ascii_dict[ascii_select][y+1]

    if btn_clicked[x][y]:
        btn[x][y].configure(fg_color = '#d4ff00') #Yellow
        out_byte = out_byte + (1 << x)
    else:
        btn[x][y].configure(fg_color = '#202020') #Black
        out_byte = out_byte - (1 << x)
    ascii_dict[ascii_select][y+1] = out_byte
    print(ascii_dict[ascii_select])

def set_btn_true():
    #ascii_dict[ascii_select][0]=True
    ascii_dict[ascii_select][0]=True
    ascii_btn[ascii_select].configure(fg_color='#00cc31')
    save_to_json()
    
def set_btn_false():
    ascii_dict[ascii_select][0]=False
    ascii_btn[ascii_select].configure(fg_color='#0066cc')
    for i in range(7):
        ascii_dict[ascii_select][i+1] = 0
    update_dots_from_ascii(ascii_select)

def save_to_json():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of the script
    json_path = os.path.join(script_dir, "..", "config", "font1.json")
    with open(json_path, "w") as out_file:
        json.dump(ascii_dict, out_file, indent=6)
"""
def save_to_json():
    out_file = open("font1.json","w")
    json.dump(ascii_dict,out_file,indent=6)
    out_file.close()
"""
def choose_ascii(i:int):
    global ascii_select
    if ascii_dict[ascii_select][0]:
        ascii_btn[ascii_select].configure(fg_color="green")
    else:
        ascii_btn[ascii_select].configure(fg_color="#3399ff")
    ascii_select = i
    ascii_btn[i].configure(fg_color="blue")

    update_dots_from_ascii(i)

def update_ascii_btn_color(character_decimal:int,approved_character:bool):
    if approved_character:
        ascii_btn[character_decimal].configure(fg_color="green")
    else:
        ascii_btn[character_decimal].configure(fg_color="#3399ff")

def update_dots_from_ascii(character_decimal:int):
    print(ascii_dict[character_decimal])
    for a in range(7):
        x=0
        row = ascii_dict[character_decimal][a+1]
        for i in range(5):
            if row % 2:
                print("yellow - Row: " + str(row) + " x: " + str(x) + " i: " + str(i))
                btn[x][a].configure(fg_color = '#d4ff00') #Yellow
                btn_clicked[x][a] = True
                row //= 2
                x += 1
            else:
                #print(x)
                #print(i)
                btn[x][a].configure(fg_color = '#202020') #Black
                btn_clicked[x][a] = False
                row //= 2
                x += 1




#============================================== CTKinter Content ======================================


btn = [[None for i in range(7)] for i in range(5)]

z = 0
for y in range(7):
    for x in range(5):
        btn[x][y] = customtkinter.CTkButton(dots_frame,text = str(z),fg_color='#202020',command= lambda x=x, y=y: toggle_btn(x,y),width=28,height = 34,corner_radius=10)
        z = z+1
z = 0

for y in range(7):
    for x in range(5):
        #print(str(x) + str(y) + " " + str(z))
        btn[x][y].grid(row = y, column = x, sticky = 'nesw',padx = 1, pady = 1)

accept_btn = customtkinter.CTkButton(dots_frame,text = "Accept",command=set_btn_true,width=0)
accept_btn.grid(row = 7,column = 0, columnspan = 2,pady = 5,sticky="nesw")
clear_btn = customtkinter.CTkButton(dots_frame,text = "Clear",command=set_btn_false,width=0)
clear_btn.grid(row = 7,column = 3,columnspan = 2,pady = 5,sticky="nswe")

data_tabview = customtkinter.CTkTabview(app)
data_tabview.add("select")
data_tabview.add("settings")
data_tabview.pack(side='right',padx = 5, pady=5, expand = True,fill='y')

ascii_btn = [0 for i in range(127)]
for i in range(33,123):
    ascii_btn[i] = customtkinter.CTkButton(data_tabview.tab("select"),text = str(chr(i)),command=lambda i=i: choose_ascii(i),width=28,height = 34,fg_color="#3399ff",hover_color='#0066cc')

z= 33
x = 0
y = 0

while z < 123:
    ascii_btn[z].grid(row = y, column = x, sticky = 'nesw',padx = 1, pady = 1)
    z = z+1
    x = x+1
    if x > 9:
        x=0
        y = y + 1

#============================================== Setup ======================================


script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
json_path = os.path.join(script_dir, "..", "config", "font1.json")  # Construct the full path for the JSON file

try:
    with open(json_path, 'r') as json_file:
        ascii_dict = json.load(json_file)
except FileNotFoundError:
    print("Error: font1.json file not found. Loading default configuration.")
    ascii_dict = [[False, 0, 0, 0, 0, 0, 0, 0] for _ in range(127)]  # Default configuration
except json.JSONDecodeError:
    print("Error: Could not decode the JSON file. Loading default configuration.")
    ascii_dict = [[False, 0, 0, 0, 0, 0, 0, 0] for _ in range(127)]  # Default configuration
print(ascii_dict)

for i in range(33,123):
    if ascii_dict[i][0]:
        ascii_btn[i].configure(fg_color="green")
    else:
        ascii_btn[i].configure(fg_color="#3399ff")
#ascii_dict = [[False,0,0,0,0,0,0,0] for i in range(127)]

ascii_select = 33 #first character to be displayed, all previous are unused

btn_clicked = [[False for i in range(7)] for i in range(5)]


app.mainloop()
