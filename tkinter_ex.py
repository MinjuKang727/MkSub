# from tkinter import *


# #  예제 1) tkinter 파이썬 GUI 레이블(label)
# # tkinter를 사용하여 텍스트를 나타내보자

# # 1. 루트화면 (root window) 생성
# tk = Tk() 
# # 2. 텍스트 표시
# label = Label(tk,text='Hello World!') 
# # 3. 레이블 배치 실행
# label.pack()
# # 4. 메인루프 실행
# tk.mainloop()

# # 예제2) 버튼만들기
# tk = Tk()
# # 함수 정의 (버튼을 누르면 텍스트 내용이 바뀜)
# def event():
#     button['text'] = '버튼 누름!'

# button = Button(tk,text='버튼입니다. 누르면 함수가 실행됩니다.',command=event)
# button2 = Button(tk,text='버튼2 입니다.')
# button.pack(side=LEFT,padx=10,pady=10) #side로 배치설정, padx로 좌우 여백설정, pady로 상하 여백설정 
# button2.pack(side=LEFT, padx=10, pady= 10)
# tk.mainloop()

# tk = Tk()
# button = Button(tk)
# button2 = Button(tk)
# button.pack(side=LEFT,padx=10,pady=10)
# button2.pack(side=LEFT, padx=10, pady= 10)
# button['text'] = 'Button1'
# button2['text'] = 'Button2'                        
# tk.mainloop()

# # 예제 3) 버튼 클릭시 실행될 이벤트(함수) 설정
# tk = Tk()

# # 다른 함수 정의(버튼 누를때마다 카운트를 세는 함수)
# counter = 0
# def clicked():
#     global counter #전역변수 counter
#     counter += 1
#     label1['text'] = '버튼 클릭 수: ' + str(counter)

# # 리셋 함수(카운트 초기화)
# def reset():
#     global counter
#     counter = 0
#     label1['text'] = '옆에 버튼이 있습니다.'
# ## GUI 구성(텍스트,버튼) ##

# # 창 이름 설정
# tk.title('GUI예제') 

# # 텍스트
# label1=Label(tk, text='옆에 버튼이 있습니다.',fg='blue',font=20) # fg는 글자 색 지정, font로 글자 설정
# label1.pack(side=LEFT, padx=10, pady=10)
# # 버튼1
# button3 = Button(tk,text='클릭해 보세요.',bg='green',font=15,width=30,height=5,command= clicked) #command로 버튼 클릭 시 동작할 함수 지정, bg로 색상지정, width,height로 각각 넓이 높이 지정
# button3.pack(side=LEFT, padx=10, pady=10)
# # 버튼2
# button4 = Button(tk,text='reset',bg='red',width=30,height=5,font=15,command=reset)
# button4.pack(side=LEFT,padx=10, pady=10)
# tk.mainloop()

# ###예제4) ft -> cm로 바꾸는 단위 변환기 만들기
# # Entry: input과 비슷한 역할 (사용자가 입력한 내용 전달)
# # get: Entry를 사용한 입력 내용 가져올 수 있다.
# # delete: 사용자 입력 삭제
# # Frame: 컨테이너, 창 안에 프레임 생성
# # grid: 격자 배치
# tk = Tk()
# tk.title('길이 변환기')
# def Ft2Cm():
#     ft2cm = entry1.get()
#     entry2.delete(0,"end")
#     entry2.insert(0,round(float(ft2cm)*30.48,4))
# def Cm2Ft():
#     cm2ft = entry2.get()
#     entry1.delete(0,"end")
#     entry1.insert(0,round(float(cm2ft)/30.48,4))

# label1 = Label(tk,text='피트(ft)').grid(row=0, column=0)
# label2 = Label(tk,text='센티미터(cm)').grid(row=1,column=0)

# # 각 단위 입력받는 부분 만들기
# entry1 = Entry(tk)
# entry2 = Entry(tk)


# entry1.grid(row=0,column=1)
# entry2.grid(row=1,column=1)

# btn1 = Button(tk,text='ft->cm',bg='black',fg='white',command=Ft2Cm).grid(row=2,column=0)
# btn2 = Button(tk,text='cm->ft',bg='black',fg='white',command=Cm2Ft).grid(row=2,column=1)

# tk.mainloop()


# # 저장 경로 지정
# import tkinter as tk
# from tkinter import filedialog
# from tkinter import *
# from pathlib import Path

# # 현재 파일이 위치한 디렉토리 경로 (절대 경로)
# current_dir = Path(__file__).parent.absolute()

# def select_folder():
#     # 폴더 선택 대화상자 호출
#     folder_selected = filedialog.askdirectory()
    
#     if folder_selected:
#         # print(f"선택된 폴더: {folder_selected}")
#         # 선택한 경로를 활용한 추가 작업 수행
#         path_entry.config(state="normal")
#         path_entry.delete(0,"end")
#         path_entry.insert(0, folder_selected)
#         path_entry.config(state="readonly")

# # GUI 창 생성
# root = tk.Tk()
# root.title("폴더 경로 지정")
# root.geometry("300x150")

# # 폴더 선택 버튼 생성
# btn = Button(root, text="폴더 선택", command=select_folder).grid(row=0, column=0)
# path_entry = Entry(root, state="readonly")
# path_entry.grid(row=0, column=1)


# root.mainloop()


import tkinter as tk
from tkinter import filedialog
from tkinter import *
from pathlib import Path

# 현재 파일이 위치한 디렉토리 경로 (절대 경로)
current_dir = Path(__file__).parent.absolute()

def select_folder():
    # 폴더 선택 대화상자 호출
    folder_selected = filedialog.askdirectory()
    
    if folder_selected:
        # print(f"선택된 폴더: {folder_selected}")
        # 선택한 경로를 활용한 추가 작업 수행
        path_entry.config(state="normal")
        path_entry.delete(0,"end")
        path_entry.insert(0, folder_selected)
        path_entry.config(state="readonly")

# GUI 창 생성
root = tk.Tk()
root.title("폴더 경로 지정")
root.geometry("300x150")

# 폴더 선택 버튼 생성
btn = Button(root, text="폴더 선택", command=select_folder).grid(row=0, column=0)
path_entry = Entry(root, state="readonly")
path_entry.grid(row=0, column=1)
url_label = Label(root, text="유튜브 링크: ").grid(row=1,column=0)
url_entry = Entry(root)
url_entry.grid(row=1, column=1)
download_btn = Button(root, text="실행", command=).grid(row=1, column=2)


root.mainloop()
