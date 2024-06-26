import streamlit as st
import os
import base64
import pickle
import datetime
import subprocess
import pandas as pd
import face_recognition
import numpy as np
import pytz
from PIL import Image
import PIL
import PIL.Image
import PIL.ImageFont
from PIL import ImageOps
import dlib
import PIL.ImageDraw
import image_dehazer
import math
if True:

    # Load your logo image

    stud_list = {
            "name": [],
            "usn":[]
    }
    if 'sl' not in st.session_state:
        st.session_state.sl = stud_list

    cnt=-1
    absent_list={
            "name": [],
            "usn":[]
    }
    if 'al' not in st.session_state:
        st.session_state.al = absent_list
    local_tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(local_tz)           
    def main():
        # st.title("Student Attendance System")
        menu = ["Home","Take Attendance","Manual Attendance"]
        choice = st.sidebar.selectbox("Select Option", menu)

        if choice == "Home":

            st.title("Welcome to the Attendance System")
            st.write(
                """
                This attendance system uses facial recognition to mark attendance for students.
                It allows the teacher to upload images of the classroom in order to get the list of students present in the class. 

                """
            )
                
            st.write(str(now.strftime("%a|%d/%b/%Y|%H:%M")))        
        if choice == "Take Attendance":
            take_attendance()
        if choice == "Manual Attendance":
            st.title("Manual Attendance")    

    # Load existing encodings and student IDs

    # New one with enhanced options  
    def take_attendance():
        with open('encoded_people.pickle', 'rb') as filename:
            people = pickle.load(filename)
        st.subheader("Take Attendance")
        semester = st.selectbox("Select Class", options=[1, 2, 3, 4, 5, 6, 7, 8])
        section = st.selectbox("Select Section", options=["A", "B", "C", "D"])
        department = st.selectbox("Select department", options = ["CSE", "ISE", "ECE", "EEE", "AI&ML", "DS", "Mech", "Civil"])
        shname= str(semester) + "|"+str(section) +"|"+str(department) +"|"+str(now.strftime("%a|%d/%b/%Y|%H:%M"))
        option = st.radio("Select Option", ("Upload Image","Take Live Image"))
        if option == "Upload Image" or option == "Take Live Image":
            if option == "Upload Image":   
            # Read in the uploaded image
                uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"],accept_multiple_files=True)
            # Read in the live image from camera
            elif option == "Take Live Image":
                uploaded_file = st.camera_input("Choose an image file")    
            img=[]
            img_np=[]
            if uploaded_file is not None:
                for i in uploaded_file:
                    file_bytes = i.getvalue()
                    nparr = np.frombuffer(file_bytes, np.uint8)
                    img.append(Image.open(i))
                    #img = [x.convert("RGB") for x in img]   
                    img = [x.resize((1920,1080)) for x in img]
                st.subheader("Uploaded Image: ")
                st.image(img,channels="RGB")
                for k,v in people.items():
                    x,y=k.split("_")   
                    absent_list["name"].append(x)
                    absent_list["usn"].append(y)
                option = st.radio("Select Option", ("Select Dehazing/No Dehazing","DeHazing", "No Dehazing"))
                if option == "Select Dehazing/No Dehazing":
                    input()
                elif option =="No Dehazing":
                    for i in img:
                        img_np.append(np.array(i))
                elif option == "DeHazing":
                    st.write("""Please wait for image to be dehazed.""")
                    for i in img:
                        img_np.append(np.array(i))
                    final_images=[]
                    dehaze_img=[]
                    dehaze_imgnp=[]    
                    for i in img_np:
                        HazeCorrectedImg, HazeMap = image_dehazer.remove_haze(i,boundaryConstraint_windowSze=3,showHazeTransmissionMap=False)
                        dehaze_img.append(Image.fromarray(HazeCorrectedImg))
                    for i in dehaze_img:
                        dehaze_imgnp.append(np.array(i)) 
                    st.subheader("DeHazed Image:")
                    st.image(dehaze_img,channels="RGB")
                st.write("""Face Detection and Tagging in progress....""")
                #Face Detection
                cnt=-1    
                for x in dehaze_imgnp:
                    img_loc = face_recognition.face_locations(x,number_of_times_to_upsample=3,model="hog")
                    img_enc = face_recognition.face_encodings(x,known_face_locations=img_loc,num_jitters=1)
                    face_img = PIL.Image.fromarray(x)
                #Face Tagging
                    unknown_faces_location = []
                    unknown_faces_enconded = []
                    for i in range(0,len(img_enc)):
                        best_match_count = 0
                        best_match_name = "unknown"
                        for k,v in people.items():
                            result = face_recognition.compare_faces(v,img_enc[i],tolerance=0.475)
                            count_true = result.count(True)
                            if  count_true > best_match_count: # To find the best person that matches with the face
                                best_match_count = count_true
                                best_match_name = k
                        if best_match_name != "unknown":
                            a,b=best_match_name.split("_")
                            if a not in stud_list["name"]:
                                stud_list["name"].append(a)
                                stud_list["usn"].append(b)
                        else:
                            cnt=cnt+1
                    # Draw and write on photo
                        top,right,bottom,left = img_loc[i]
                        draw = PIL.ImageDraw.Draw(face_img)
                        font = PIL.ImageFont.load_default()
                        draw.rectangle([left,top,right,bottom], outline="red", width=3)
                        draw.rectangle((left, bottom, left + font.getsize(best_match_name)[0] , bottom +  font.getsize(best_match_name)[1]*1.2), fill='black')
                        draw.text((left,bottom), best_match_name, font=font)
                    final_images.append(face_img)
                st.write("""Face Detection and Tagging completed!!""")
                st.image(final_images)
                for a in stud_list["name"]:
                    if a in absent_list["name"]:   
                            absent_list["usn"].remove(absent_list["usn"][absent_list["name"].index(a)])
                            absent_list["name"].remove(a)
                stud_list["name"].append("Unknown Faces")
                if cnt==-1:
                    cnt=0
                stud_list["usn"].append(cnt)
                st.subheader("Students detected from Uploaded Images are:")
                st.dataframe(pd.DataFrame(stud_list,index=range(1, len(stud_list["name"])+1)))
                st.subheader("Absentees:")
                st.dataframe(pd.DataFrame(absent_list,index=range(1, len(absent_list["name"])+1)))    
                st.write("Proceed to Manual Attendance tab for adding more students!!!")  
                st.session_state.sl = stud_list
                st.session_state.al = absent_list
                st.session_state.shname =shname

               
                # with st.form("manattdn"):
                #     manattdn=st.form_submit_button("Manual Attendance")
                # if manattdn:
                #     st.subheader("Manual Attendance")
                #     with st.form("abslist"):
                #         manual_attdn=st.multiselect("Choose the students to be included:",absent_list)
                #         conf=st.form_submit_button("Confirm")
                #     if conf: 
                #         for ma in manual_attdn:
                #             a,b=ma.split("_")
                #         if a not in stud_list["name"]:
                #             stud_list["name"].append(a)
                #             stud_list["usn"].append(b)
                #         st.subheader("List of Students after Manual Attendance:")
                #         st.dataframe(pd.DataFrame(stud_list))
                

    if __name__ == '__main__':
        main()
